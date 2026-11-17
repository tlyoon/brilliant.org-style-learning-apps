"""Read-only, bounded provider-capacity cooldown for independent V3 work.

An ambiguous Google request is NOT retryable. This helper merely prevents
new, independent activity requests from stampeding the same failed provider.
Historical claim contents and result aggregate are immutable.
"""
from __future__ import annotations

from hashlib import sha256
import json
import time
from pathlib import Path

from app_generator.validation.reviewer_failure_policy import SERVER_CAPACITY_ERROR_NAMES

COOLDOWN_SECONDS = 30 * 60
BURST_WINDOW_SECONDS = 60 * 60
MAX_SERVER_FAILURES_PER_WINDOW = 2


def provider_capacity_gate(
    private_root: Path | None, section_progress: list[dict], *,
    now: float | None = None,
    additional_package_shas: tuple[str, ...] | list[str] = (),
    quarantined_historical_claim: tuple[str, str] | None = None,
) -> dict:
    """Return only a privacy-safe, deterministic decision; never contact Google.

    Uses file times solely to enforce backoff, NOT to prove request acceptance
    or grant review PASS. A later independent activity may select another\n    preconfigured key after cooldown; pending requests are never replayed.
    """
    if private_root is None:
        return {"status": "READY", "serverErrorsLastHour": 0, "serverErrorActivitiesHistorical": 0}
    clock = time.time() if now is None else float(now)
    root = private_root
    # One exact, pre-verified historical raw claim may be quarantined from
    # *provider capacity* classification for a NEW authorized activity.
    # This does NOT mark the old review as reconciled or allow its replay.
    # The caller must independently prove frozen source, old role identity,
    # new separate scope, owner authorization and current metadata access.
    if quarantined_historical_claim is not None:
        if (not isinstance(quarantined_historical_claim, tuple)
                or len(quarantined_historical_claim) != 2
                or any(not isinstance(item, str) or len(item) != 64
                       or set(item) - set("0123456789abcdef")
                       for item in quarantined_historical_claim)):
            raise ValueError("V3_PROVIDER_INVALID_HISTORICAL_CLAIM_WITNESS")
    quarantined_count = 0
    events: list[float] = []
    failed_activities: set[tuple[str,str]] = set()
    denied = False
    unclassified = False
    explicit_http_stops: set[str] = set()
    # BSA-186: independently reviewed original-tail slices must share the
    # same provider-wide circuit as the original frozen course.
    if (not isinstance(additional_package_shas, (tuple, list))
            or len(additional_package_shas) > 108
            or any(not isinstance(d, str) or len(d) != 64
                   or set(d) - set("0123456789abcdef")
                   for d in additional_package_shas)):
        raise ValueError("V3_PROVIDER_CAPACITY_INVALID_ADDITIONAL_DIGESTS")
    packages = list(dict.fromkeys(
        [row["packageSha256"] for row in section_progress]
        + list(additional_package_shas)))
    for digest in packages:
        folder = root / ("v3-generated-" + digest) / "batches"
        if folder.is_symlink():
            raise ValueError("V3_PROVIDER_CAPACITY_UNSAFE_CHECKPOINT")
        if not folder.exists():
            continue
        if not folder.is_dir():
            raise ValueError("V3_PROVIDER_CAPACITY_UNSAFE_CHECKPOINT")
        prefix = f"v3-review-{digest[:12]}-"
        for claim in folder.glob(prefix + "*.json"):
            if claim.is_symlink() or not claim.is_file() or claim.stat().st_size > 100_000:
                raise ValueError("V3_PROVIDER_CAPACITY_UNSAFE_CHECKPOINT")
            data = json.loads(claim.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or data.get("packageSha256") != digest:
                raise ValueError("V3_PROVIDER_CAPACITY_INVALID_CLAIM")
            if data.get("state") == "AMBIGUOUS":
                cause=data.get("providerFailureClass")
                code=data.get("providerHttpStatus")
                if cause is not None:
                    from app_generator.runtime.v3_gemini_diagnostics import (
                        classify_google_failure,
                    )
                    if (not isinstance(cause,str) or
                            cause not in {
                                "AUTH_OR_PROJECT_DENIED",
                                "BILLING_RESTRICTED","MODEL_NOT_FOUND",
                                "QUOTA_OR_RATE_LIMIT","INVALID_MODEL_REQUEST",
                                "TRANSPORT_UNCERTAIN","PROVIDER_CAPACITY",
                                "UNCLASSIFIED_PROVIDER_ERROR",
                            } or
                            (code is not None and
                             (type(code) is not int or
                              not 400 <= code <= 599 or
                              classify_google_failure(code, "ClientError") != cause))):
                        raise ValueError("V3_PROVIDER_INVALID_SANITIZED_ERROR")
                    if cause in {
                        "AUTH_OR_PROJECT_DENIED","BILLING_RESTRICTED",
                        "MODEL_NOT_FOUND","QUOTA_OR_RATE_LIMIT",
                        "INVALID_MODEL_REQUEST",
                    }:
                        explicit_http_stops.add(cause)
            if data.get("state") == "BLOCKED_EXTERNAL":
                denied = True
            elif (data.get("state") == "AMBIGUOUS"
                  and data.get("reasonCode") not in SERVER_CAPACITY_ERROR_NAMES
                  and data.get("providerFailureClass") != "PROVIDER_CAPACITY"):
                # Only one pinned, previously inspected old claim may be
                # excluded from *current provider health* when its exact
                # bytes still match a validated standalone quarantine.
                # All other unknown, denied and capacity failures stay live.
                verified_legacy = (
                    quarantined_historical_claim is not None
                    and digest == quarantined_historical_claim[0]
                    and sha256(claim.read_bytes()).hexdigest() ==
                        quarantined_historical_claim[1]
                    and data.get("reasonCode") == "ValueError"
                    and data.get("providerId") == "gemini_api"
                    and data.get("roleIndex") == 0)
                if verified_legacy:
                    quarantined_count += 1
                else:
                    unclassified = True
            if (data.get("state") == "AMBIGUOUS"
                and (data.get("reasonCode") in SERVER_CAPACITY_ERROR_NAMES
                     or data.get("providerFailureClass") == "PROVIDER_CAPACITY")):
                activity_id = data.get("activityId")
                if not isinstance(activity_id,str) or not activity_id:
                    raise ValueError("V3_PROVIDER_CAPACITY_INVALID_ACTIVITY_ID")
                failed_activities.add((digest,activity_id))
                when = claim.stat().st_mtime
                if when > clock + 300:
                    raise ValueError("V3_PROVIDER_CAPACITY_FUTURE_TIMESTAMP")
                if clock - BURST_WINDOW_SECONDS < when <= clock + 300:
                    events.append(when)
    events.sort()
    if (quarantined_historical_claim is not None
            and quarantined_count != 1):
        raise ValueError("V3_PROVIDER_HISTORICAL_CLAIM_WITNESS_MISMATCH")
    count = len(events)
    historic = len(failed_activities)
    if denied or "AUTH_OR_PROJECT_DENIED" in explicit_http_stops:
        return {"status": "BLOCKED_EXTERNAL_REVIEW_TRANSPORT",
                "serverErrorsLastHour": count,
                "serverErrorActivitiesHistorical": historic}
    for cls, status in (
        ("BILLING_RESTRICTED","STOP_PROVIDER_BILLING_RESTRICTED"),
        ("MODEL_NOT_FOUND","STOP_PROVIDER_MODEL_NOT_FOUND"),
        ("QUOTA_OR_RATE_LIMIT","STOP_PROVIDER_QUOTA_OR_RATE_LIMIT"),
        ("INVALID_MODEL_REQUEST","STOP_PROVIDER_INVALID_MODEL_REQUEST"),
    ):
        if cls in explicit_http_stops:
            return {"status":status,
                    "serverErrorsLastHour":count,
                    "serverErrorActivitiesHistorical":historic}
    if unclassified:
        return {"status": "STOP_UNCLASSIFIED_PROVIDER_REVIEW",
                "serverErrorsLastHour": count,
                "serverErrorActivitiesHistorical": historic}
    if count:
        newest = events[-1]
        # Cool down a single fault for 30 minutes. After two faults,
        # additionally wait for the older fault to leave a rolling
        # one-hour window; never hop across sections in a capacity outage.
        circuit = count >= MAX_SERVER_FAILURES_PER_WINDOW
        deadline = max(
            newest + COOLDOWN_SECONDS,
            events[-2] + BURST_WINDOW_SECONDS if circuit else 0,
        )
        if clock < deadline:
            return {
                "status": ("STOP_PROVIDER_CIRCUIT_OPEN" if circuit
                           else "WAIT_PROVIDER_COOLDOWN"),
                "serverErrorsLastHour": count,
                "serverErrorActivitiesHistorical": historic,
                "retryNewWorkAfterUnix": int(deadline),
            }
    return {"status": (
                "READY_RESTRICTED_HISTORICAL_QUARANTINE"
                if quarantined_historical_claim is not None else "READY"),
            "historicalUnrecoverableClaimsQuarantined": quarantined_count,
            "serverErrorsLastHour": count,
            "serverErrorActivitiesHistorical": historic}

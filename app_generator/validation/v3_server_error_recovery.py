"""Read-only, bounded provider-capacity cooldown for independent V3 work.

An ambiguous Google request is NOT retryable. This helper merely prevents
new, independent activity requests from stampeding the same failed provider.
Historical claim contents and result aggregate are immutable.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

COOLDOWN_SECONDS = 30 * 60
BURST_WINDOW_SECONDS = 60 * 60
MAX_SERVER_FAILURES_PER_WINDOW = 2
_SERVER_ERROR_TYPES = frozenset({"ServerError", "ServiceUnavailable", "TransientGeminiError"})


def provider_capacity_gate(
    private_root: Path | None, section_progress: list[dict], *,
    now: float | None = None,
) -> dict:
    """Return only a privacy-safe, deterministic decision; never contact Google.

    Uses file times solely to enforce backoff, NOT to prove request acceptance
    or grant review PASS. No key rotation and no pending request replays.
    """
    if private_root is None:
        return {"status": "READY", "serverErrorsLastHour": 0}
    clock = time.time() if now is None else float(now)
    root = private_root
    events: list[float] = []
    denied = False
    unclassified = False
    for row in section_progress:
        digest = row["packageSha256"]
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
            if data.get("state") == "BLOCKED_EXTERNAL":
                denied = True
            elif (data.get("state") == "AMBIGUOUS"
                  and data.get("reasonCode") not in _SERVER_ERROR_TYPES):
                # An unknown error could be authentication, quota, content
                # rejection, or a provider denial. Never route around it
                # by silently switching to a different frozen section.
                unclassified = True
            if (data.get("state") == "AMBIGUOUS"
                and data.get("reasonCode") in _SERVER_ERROR_TYPES):
                when = claim.stat().st_mtime
                if when > clock + 300:
                    raise ValueError("V3_PROVIDER_CAPACITY_FUTURE_TIMESTAMP")
                if clock - BURST_WINDOW_SECONDS < when <= clock + 300:
                    events.append(when)
    events.sort()
    count = len(events)
    if denied:
        return {"status": "BLOCKED_EXTERNAL_REVIEW_TRANSPORT",
                "serverErrorsLastHour": count}
    if unclassified:
        return {"status": "STOP_UNCLASSIFIED_PROVIDER_REVIEW",
                "serverErrorsLastHour": count}
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
                "retryNewWorkAfterUnix": int(deadline),
            }
    return {"status": "READY", "serverErrorsLastHour": count}

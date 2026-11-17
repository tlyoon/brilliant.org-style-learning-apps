"""V3 response-capture and activity-level failure-isolation primitives.

Only returned provider text can be recovered locally. These functions never
open a model or assign PASS. An older ambiguous request without a captured
response remains unresolved and non-replayable.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

MAX_CAPTURE_CHARS = 50_000
_LOCAL_FAILURES = {"PARSE_FAILED", "RUBRIC_FAILED"}


def normalize_complete_json_response(raw: str) -> str:
    """Repair only an exact, complete Markdown JSON wrapper—not its science."""
    if not isinstance(raw, str) or not raw or len(raw) > MAX_CAPTURE_CHARS:
        raise ValueError("V3_CAPTURED_RESPONSE_INVALID_SIZE")
    cleaned = raw.strip()
    fence = chr(96) * 3
    for lang in ("json", "JSON"):
        prefix = fence + lang + "\n"
        suffix = "\n" + fence
        if cleaned.startswith(prefix) and cleaned.endswith(suffix):
            cleaned = cleaned[len(prefix):-len(suffix)].strip()
            break
    # No fragment extraction, added fields, quote repair, or guessed decisions.
    return cleaned


def raw_capture_path(checkpoint: Any, claim: str) -> Path:
    if checkpoint is None or not hasattr(checkpoint, "batches"):
        raise ValueError("V3_CAPTURE_CHECKPOINT_REQUIRED")
    file = checkpoint.batches / (claim + ".response.txt")
    if file.is_symlink():
        raise ValueError("V3_CAPTURE_SYMLINK_FORBIDDEN")
    return file


def record_returned_response(
    checkpoint: Any, claim: str, identity: dict,
    reviewer: str, session: str, response: str,
) -> str:
    """Durable private text BEFORE parse/rubric; exactly one known request."""
    if not isinstance(response, str) or not response or len(response) > MAX_CAPTURE_CHARS:
        raise ValueError("V3_CAPTURED_RESPONSE_INVALID_SIZE")
    digest = sha256(response.encode("utf8")).hexdigest()
    path = raw_capture_path(checkpoint, claim)
    if path.exists():
        old = path.read_bytes()
        if old != response.encode("utf8"):
            raise ValueError("V3_CAPTURED_RESPONSE_CONFLICT")
    else:
        checkpoint.save_raw_response(claim, response)
    checkpoint.save_stage(claim, {
        **identity, "state": "RESPONSE_CAPTURED",
        "reviewerId": reviewer, "sessionId": session,
        "responseSha256": digest,
    })
    return digest


def verified_returned_response(
    checkpoint: Any, claim: str, previous: dict,
) -> str:
    """Reconstruct only captured bytes with a matching role hash."""
    file = raw_capture_path(checkpoint, claim)
    if (not file.is_file() or file.stat().st_size > MAX_CAPTURE_CHARS * 4):
        raise ValueError("V3_CAPTURED_RESPONSE_MISSING")
    raw = file.read_bytes()
    digest = previous.get("responseSha256")
    if (not isinstance(digest, str) or
            digest != sha256(raw).hexdigest()):
        raise ValueError("V3_CAPTURED_RESPONSE_SHA_MISMATCH")
    try:
        return raw.decode("utf8")
    except UnicodeError:
        raise ValueError("V3_CAPTURED_RESPONSE_UTF8_ERROR") from None


def classify_local_error(error: Exception) -> tuple[str, str]:
    """Distinguish local JSON syntax from semantic/rubric rejection."""
    if isinstance(error, json.JSONDecodeError):
        return "PARSE_FAILED", "V3_CAPTURED_PARSE_FAILED"
    return "RUBRIC_FAILED", "V3_CAPTURED_RUBRIC_FAILED"


def read_local_failure_claim(
    batches: Path, digest: str, index: int, role: int, activity_id: str, *,
    expected_prompt_sha256: str | None = None,
    reviewer_id: str | None = None,
    session_id: str | None = None,
    expected_reason_code: str | None = None,
) -> bool:
    """Only a hash-verified captured local fault can be isolated."""
    claim = f"v3-review-{digest[:12]}-{index:03d}-{role}"
    file = batches / (claim + ".json")
    capture = batches / (claim + ".response.txt")
    if (file.is_symlink() or capture.is_symlink()
            or not file.is_file() or not capture.is_file()
            or file.stat().st_size > 100_000
            or capture.stat().st_size > MAX_CAPTURE_CHARS * 4):
        return False
    try:
        state = json.loads(file.read_text(encoding="utf8"))
        body = capture.read_bytes()
    except (OSError, UnicodeError, ValueError):
        return False
    return (
        isinstance(state, dict)
        and state.get("state") in _LOCAL_FAILURES
        and state.get("packageSha256") == digest
        and state.get("activityId") == activity_id
        and state.get("roleIndex") == role
        and state.get("providerId") in {"gemini_api", "gemini_browser"}
        and state.get("responseSha256") == sha256(body).hexdigest()
        and state.get("reasonCode") == {
            "PARSE_FAILED": "V3_CAPTURED_PARSE_FAILED",
            "RUBRIC_FAILED": "V3_CAPTURED_RUBRIC_FAILED",
        }[state["state"]]
        and (expected_prompt_sha256 is None
             or state.get("promptSha256") == expected_prompt_sha256)
        and (reviewer_id is None or state.get("reviewerId") == reviewer_id)
        and (session_id is None or state.get("sessionId") == session_id)
        and (expected_reason_code is None
             or state.get("reasonCode") == expected_reason_code)
    )


def section_has_only_isolatable_uncertainty(
    private_root: Path | None, digest: str, package_path: Path,
) -> bool:
    """Only exact-prompt captured local failures allow later new review.

    Recheck immutable package SHA, activity ID, reviewer/prompt identity and
    returned bytes. Older transport ambiguity still quarantines the section.
    This is read-only and cannot create or replace an academic verdict.
    """
    if private_root is None or package_path.is_symlink():
        return False
    batches = private_root / ("v3-generated-" + digest) / "batches"
    report_path = batches / ("v3-assessment-" + digest + ".json")
    if (batches.is_symlink() or report_path.is_symlink()
            or not report_path.is_file()
            or report_path.stat().st_size > 8_000_000):
        return False
    try:
        from app_generator.validation.autonomous_completion import (
            package_identity, make_prompt,
        )
        package_bytes = package_path.read_bytes()
        actual_digest, activities = package_identity(package_bytes)
        if actual_digest != digest:
            return False
        report = json.loads(report_path.read_text(encoding="utf8"))
    except (OSError, UnicodeError, ValueError):
        return False
    uncertain = 0
    if (not isinstance(report, dict)
            or not isinstance(report.get("reviews"), list)
            or len(report["reviews"]) > len(activities)):
        return False
    for index, row in enumerate(report["reviews"]):
        if row.get("status") != "AI_UNCERTAIN":
            continue
        if row.get("activityId") != activities[index]["id"]:
            return False
        uncertain += 1
        for role, reviewer in enumerate(row["reviewers"]):
            if "decision" in reviewer:
                continue
            perspective = (
                "physics-adversary" if role == 0
                else "language-and-learner-adversary"
            )
            expected_prompt = sha256(make_prompt(
                activities[index], perspective).encode("utf8")).hexdigest()
            if (reviewer.get("reasonCode") not in (
                    "V3_CAPTURED_PARSE_FAILED", "V3_CAPTURED_RUBRIC_FAILED")
                    or not read_local_failure_claim(
                        batches, digest, index, role, row["activityId"],
                        expected_prompt_sha256=expected_prompt,
                        reviewer_id=reviewer.get("reviewerId"),
                        session_id=reviewer.get("sessionId"),
                        expected_reason_code=reviewer["reasonCode"])):
                return False
    return uncertain > 0

"""Source-free, exact-hash handoff for corrected V3 activity review.

The preflight writes ONLY local role metadata. It never sends private prompts,
calls a model, carries forward old scientific PASS or authorizes publication.
The full course scope remains frozen until an independent admission decision.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import tempfile

from app_generator.runtime.v3_auto_repair import (
    _ACTIVITY, _CANDIDATE, _CHANGES, _PARENT, _approved_parent_bytes,
)
from app_generator.validation.autonomous_completion import package_identity
from app_generator.validation.v3_locale_script_integrity import script_findings
from app_generator.validation.v3_versioned_text_repair import make_locale_repair

_ROLES = ("physics", "semantics")
_DIMS = ("physicsAnswer", "trilingualMeaning",
         "visualValue", "accessibleLearnerExperience")
_HANDOFF = "PENDING_AUTHORIZED_TWO_GEMINI_REVIEW"
_MAX_BYTES = 2_000_000


def _json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=True,
                      separators=(",", ":")).encode("ascii")


def _receipt(candidate_dir: Path, expected_sha: str,
             expected_parent_sha: str) -> dict:
    record = candidate_dir / "review-required.json"
    if record.is_symlink() or not record.is_file() or record.stat().st_size > 8000:
        raise ValueError("V3_HANDOFF_REPAIR_RECEIPT_MISSING")
    try:
        data = json.loads(record.read_text(encoding="utf8"))
    except (OSError, UnicodeError, ValueError):
        raise ValueError("V3_HANDOFF_REPAIR_RECEIPT_INVALID") from None
    if (not isinstance(data, dict)
            or data.get("status") != "PENDING_FRESH_GEMINI_TWO_REVIEWER_QA"
            or data.get("candidatePackageSha256") != expected_sha
            or data.get("parentPackageSha256") != expected_parent_sha
            or data.get("activityId") != _ACTIVITY
            or data.get("activityIndex") != 13
            or data.get("publicationAuthorized") is not False
            or data.get("newModelConsensusPassClaimed") is not False):
        raise ValueError("V3_HANDOFF_UNTRUSTED_REPAIR_RECEIPT")
    return data


def stage_changed_activity_review_handoff(
    course_dir: Path, private_root: Path, candidate_sha: str,
) -> dict:
    """Prepare two independent source-free review identities once.

    This can run after a known private repair has been staged. Its deterministic
    role rows cannot be used as Gemini replies or accepted release scope.
    """
    if (candidate_sha != _CANDIDATE
            or not isinstance(course_dir, Path) or not course_dir.is_dir()
            or not isinstance(private_root, Path)
            or not private_root.is_absolute() or private_root.is_symlink()):
        raise ValueError("V3_HANDOFF_UNAUTHORIZED_SCOPE")
    source = course_dir / "section-9-2" / "package.json"
    candidate = (private_root / "repair-proposals" /
                 "section-9-2" / candidate_sha)
    original = candidate / "package.json"
    if (source.is_symlink() or not source.is_file()
            or source.stat().st_size > _MAX_BYTES
            or candidate.is_symlink() or original.is_symlink()
            or not original.is_file() or original.stat().st_size > _MAX_BYTES):
        raise ValueError("V3_HANDOFF_UNSAFE_INPUTS")
    parent_raw = source.read_bytes()
    if not _approved_parent_bytes(parent_raw):
        raise ValueError("V3_HANDOFF_PARENT_NOT_FROZEN")
    candidate_raw = original.read_bytes()
    digest, activities = package_identity(candidate_raw)
    if digest != candidate_sha or len(activities) != 18:
        raise ValueError("V3_HANDOFF_CANDIDATE_CHANGED")
    if script_findings(json.loads(candidate_raw.decode("utf8"))):
        raise ValueError("V3_HANDOFF_SCRIPT_DEFECT_NOT_REPAIRED")
    # Regenerate the expected package and full versioned repair receipt from
    # immutable original bytes. The comparison is exact, even across
    # authorized archive CRLF vs Git checkout LF representations.
    expected_bytes, expected_receipt = make_locale_repair(
        parent_raw, _ACTIVITY, "ms", _CHANGES)
    if (candidate_raw != expected_bytes or
            _receipt(candidate, candidate_sha,
                     sha256(parent_raw).hexdigest()) != expected_receipt):
        raise ValueError("V3_HANDOFF_UNEXPECTED_REPAIR_DIFF")
    activity = activities[13]
    if activity["id"] != _ACTIVITY:
        raise ValueError("V3_HANDOFF_ACTIVITY_ID_CHANGED")
    activity_sha = sha256(_json(activity)).hexdigest()
    rows = []
    for role in _ROLES:
        identity = {
            "packageSha256": candidate_sha,
            "activityId": _ACTIVITY,
            "activitySha256": activity_sha,
            "reviewerRole": role,
        }
        rows.append({**identity, "rowSha256": sha256(_json(identity)).hexdigest()})
    unsigned = {
        "schema": "BOSLA_V3_CORRECTED_ACTIVITY_QA_HANDOFF_V1",
        "parentPackageSha256": _PARENT,
        "candidatePackageSha256": candidate_sha,
        "activityId": _ACTIVITY,
        "changedActivityIndex": 13,
        "requiredDimensions": list(_DIMS),
        "rows": rows,
        "status": _HANDOFF,
        "reviewClaimsCreated": False,
        "originalFailedAssessmentUnchanged": True,
        "wholeCourseScopeAccepted": False,
        "publicationAuthorized": False,
    }
    manifest = {**unsigned, "integritySha256": sha256(_json(unsigned)).hexdigest()}
    payload = (json.dumps(manifest, sort_keys=True, indent=2)+"\n").encode("utf8")
    # Persist in a separate immutable private directory. A crash before
    # directory promotion leaves no visible final handoff; an existing one
    # must match byte-for-byte. No API calls and no source text in payload.
    handoff_root = private_root / "review-handovers"
    final = handoff_root / candidate_sha
    if handoff_root.is_symlink() or final.is_symlink():
        raise ValueError("V3_HANDOFF_UNSAFE_PRIVATE_DESTINATION")

    def verify_existing() -> None:
        record = final / "review-handoff.json"
        if (final.is_symlink() or not final.is_dir()
                or record.is_symlink() or not record.is_file()
                or record.read_bytes() != payload):
            raise ValueError("V3_HANDOFF_EXISTING_MANIFEST_CONFLICT")

    if final.exists():
        verify_existing()
    else:
        handoff_root.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix=".v3-review-stage-", dir=handoff_root))
        try:
            with (stage / "review-handoff.json").open("xb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                stage.rename(final)
            except OSError:
                if not final.exists():
                    raise
                verify_existing()
        finally:
            if stage.exists():
                shutil.rmtree(stage)
    if source.read_bytes() != parent_raw or original.read_bytes() != candidate_raw:
        raise ValueError("V3_HANDOFF_INPUT_CHANGED_DURING_STAGE")
    return {
        "handoffStatus": _HANDOFF,
        "handoffStaged": True,
        "handoffSha256": manifest["integritySha256"],
        "candidateSha256": candidate_sha,
        "requiredReviewerRoles": 2,
        "actualGeminiResponses": 0,
        "wholeCourseScopeAccepted": False,
        "publicationAuthorized": False,
    }

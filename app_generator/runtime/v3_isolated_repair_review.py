"""Isolated one-activity V3 repair-review package, never original frozen scope.

The previously verified Section 9.2 private corrected package contains 18
activities. A fresh V3 reviewer must assess ONLY the changed activity, using
the ordinary exact-package two-Gemini checkpoint engine, without re-reviewing
or replaying the other 17. No model request or authorization is created here.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any

from app_generator.runtime.v3_auto_repair import _ACTIVITY, _CANDIDATE
from app_generator.runtime.v3_repair_review_handoff import (
    _json, stage_changed_activity_review_handoff,
)
from app_generator.validation.autonomous_completion import (
    make_prompt, package_identity,
)
from app_generator.validation.autonomous_ai_review import canonical_digest

_SCHEMA = "BOSLA_V3_ISOLATED_REPAIR_REVIEW_SLICE_V1"
_ROLES = (("physics", "physics-adversary"),
          ("semantics", "language-and-learner-adversary"))
_SCOPE = "ISOLATED_REVIEW_ONLY_NOT_COURSE_ACCEPTANCE"


def stage_isolated_review_slice(
    course_dir: Path, private_root: Path, candidate_sha: str,
) -> dict[str, Any]:
    """Create immutable private slice with ONE changed activity, two prompt IDs.

    Strictly repeat the complete parent/candidate/handoff validation before
    reading content. The external provider receives nothing here.
    """
    prior = stage_changed_activity_review_handoff(
        course_dir, private_root, candidate_sha)
    if (prior.get("handoffStatus") != "PENDING_AUTHORIZED_TWO_GEMINI_REVIEW"
            or prior.get("actualGeminiResponses") != 0
            or prior.get("publicationAuthorized") is not False):
        raise ValueError("V3_SLICE_UNTRUSTED_PRIOR_HANDOFF")
    original = (private_root / "repair-proposals" / "section-9-2" /
                candidate_sha / "package.json")
    if original.is_symlink() or not original.is_file():
        raise ValueError("V3_SLICE_UNSAFE_CORRECTED_PACKAGE")
    raw = original.read_bytes()
    digest, activities = package_identity(raw)
    if digest != candidate_sha or len(activities) != 18 or activities[13]["id"] != _ACTIVITY:
        raise ValueError("V3_SLICE_UNMATCHED_CORRECTED_SOURCE")
    selected = activities[13]
    # A private review-only artifact is intentionally NOT a new 18-activity
    # course scope. The standard V3 parser accepts one independently scored
    # activity and binds all requests to its own unique slice-byte hash.
    slice_raw = (json.dumps({
        "schema": _SCHEMA,
        "sourcePackageSha256": candidate_sha,
        "originalActivityIndex": 13,
        "activities": [selected],
    }, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf8")
    slice_digest, one = package_identity(slice_raw)
    if len(one) != 1 or one[0] != selected:
        raise ValueError("V3_SLICE_REVIEW_ACTIVITY_NOT_EXACT")
    handoff_sha = prior["handoffSha256"]
    prompts = [{
        "role": role,
        "reviewerPerspective": perspective,
        "promptSha256": sha256(make_prompt(selected, perspective).encode("utf8")).hexdigest(),
    } for role, perspective in _ROLES]
    head = {
        "schema": _SCHEMA,
        "slicePackageSha256": slice_digest,
        "sourcePackageSha256": candidate_sha,
        "parentReviewHandoffSha256": handoff_sha,
        "activityId": _ACTIVITY,
        "activitySha256": canonical_digest(selected),
        "reviewRows": prompts,
        "scope": _SCOPE,
        "modelRequestsSubmitted": 0,
        "genuineModelConsensusClaimed": False,
        "wholeCourseScopeAccepted": False,
        "publicationAuthorized": False,
    }
    receipt = {**head, "integritySha256": sha256(_json(head)).hexdigest()}
    receipt_bytes = (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode("utf8")
    # Atomic two-file identity. A crash before promotion cannot leave a
    # final directory missing the manifest, and a tampered final stops.
    private_slices = private_root / "single-activity-review-slices"
    final = private_slices / slice_digest
    if private_slices.is_symlink() or final.is_symlink():
        raise ValueError("V3_SLICE_UNSAFE_PRIVATE_DESTINATION")

    def check_existing() -> None:
        package_path = final / "package.json"
        manifest_path = final / "review-slice.json"
        if (final.is_symlink() or not final.is_dir()
                or package_path.is_symlink() or manifest_path.is_symlink()
                or not package_path.is_file() or not manifest_path.is_file()
                or package_path.read_bytes() != slice_raw
                or manifest_path.read_bytes() != receipt_bytes):
            raise ValueError("V3_SLICE_EXISTING_IDENTITY_CONFLICT")

    if final.exists():
        check_existing()
    else:
        private_slices.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix=".v3-slice-stage-", dir=private_slices))
        try:
            for name, data in (
                    ("package.json", slice_raw),
                    ("review-slice.json", receipt_bytes)):
                with (stage / name).open("xb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
            try:
                stage.rename(final)
            except OSError:
                if not final.exists():
                    raise
                check_existing()
        finally:
            if stage.exists():
                shutil.rmtree(stage)
    if original.read_bytes() != raw:
        raise ValueError("V3_SLICE_PARENT_CHANGED_DURING_STAGE")
    return {
        "status": "PENDING_AUTHORIZED_ISOLATED_TWO_GEMINI_REVIEW",
        "reviewSliceSha256": slice_digest,
        "sourcePackageSha256": candidate_sha,
        "reviewHandoffSha256": handoff_sha,
        "activityId": _ACTIVITY,
        "activityCount": 1,
        "reviewerCountRequired": 2,
        "actualGeminiResponses": 0,
        "wholeCourseScopeAccepted": False,
        "publicationAuthorized": False,
    }


def verify_isolated_review_slice(
    course_dir: Path, private_root: Path, candidate_sha: str,
    slice_sha: str,
) -> bytes:
    """Re-derive exact private bytes; safe to pass to existing V3 reviewer.

    Does not load/run Gemini, create role claims or recognize a PASS.
    """
    result = stage_isolated_review_slice(course_dir, private_root, candidate_sha)
    if result["reviewSliceSha256"] != slice_sha:
        raise ValueError("V3_SLICE_WRONG_REVIEW_IDENTITY")
    target = (private_root / "single-activity-review-slices" /
              slice_sha / "package.json")
    raw = target.read_bytes()
    digest, records = package_identity(raw)
    if digest != slice_sha or len(records) != 1 or records[0]["id"] != _ACTIVITY:
        raise ValueError("V3_SLICE_REVIEW_BYTES_CHANGED")
    return raw

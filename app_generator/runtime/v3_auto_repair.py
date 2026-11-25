"""Autonomous *source-free* repair staging in BOSLA's normal V3 worker.

Only a previously verified exact-parent, exact-activity correction is automatic.
Neither repair staging nor a passed local syntax check certifies learning content.
The original model FAIL is immutable; fresh two-Gemini review remains required.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.validation.autonomous_completion import package_identity
from app_generator.validation.v3_course_readiness import _verify_frozen_package_identity
from app_generator.validation.v3_locale_script_integrity import script_findings
from app_generator.validation.v3_versioned_text_repair import (
    make_locale_repair, store_private_repair,
)

_PARENT = "cfe7bab820aa01ce71bd7a6a334c742101ebd10d8895cccd5f05d599030f971c"
_PARENT_GIT_BLOB = "779deb4e207078f9081a9de78a14226d473f9b25"
_CANDIDATE = "49a7f18c7cc2b7c00e0b6b23838cca1ed7fe52262384e0c26bbc8360fa3e9174"
_SECTION = "section-9-2"
_ACTIVITY = "act-int-iso-05"
_CHANGES = (
    ("sebuah\u0e40\u0e25gelongsor", "sebuah kereta luncur"),
    ("legelongsor", "kereta luncur"),
    ("perlahaman", "perlambatan"),
)
_DIMS = ("physicsAnswer", "trilingualMeaning",
         "visualValue", "accessibleLearnerExperience")


def _approved_parent_bytes(raw: bytes) -> bool:
    """Reuse BSA-20261107-127's verified Windows-CRLF/Linux-LF identity.

    Exact archive SHA and Git blob are BOTH required. This is NOT a new
    review candidate and no mixed/partial line-ending changes are accepted.
    """
    try:
        digest, activities = package_identity(raw)
        _verify_frozen_package_identity(
            raw, digest, activities, (_PARENT, 18, _PARENT_GIT_BLOB))
        return True
    except (ValueError, KeyError, UnicodeError):
        return False


def _confirmed_failure(private_root: Path, raw: bytes) -> bool:
    """Require the genuine immutable two-reviewer FAIL, not a report count."""
    digest, activities = package_identity(raw)
    if not _approved_parent_bytes(raw) or len(activities) != 18:
        return False
    index = next((i for i, a in enumerate(activities)
                  if a["id"] == _ACTIVITY), None)
    if index != 13:
        return False
    assessment = (private_root / ("v3-generated-" + digest) /
                  "batches" / ("v3-assessment-" + digest + ".json"))
    if (assessment.is_symlink() or not assessment.is_file()
            or assessment.stat().st_size > 350_000):
        return False
    try:
        record = json.loads(assessment.read_text(encoding="utf-8"))
    except (UnicodeError, OSError, ValueError):
        return False
    if (record.get("packageSha256") != digest
            or record.get("activityIds") != [a["id"] for a in activities]
            or not isinstance(record.get("reviews"), list)
            or len(record["reviews"]) <= index):
        return False
    review = record["reviews"][index]
    if (not isinstance(review, dict) or review.get("activityId") != _ACTIVITY
            or review.get("status") != "AI_REPAIR_REQUIRED"
            or not isinstance(review.get("reviewers"), list)
            or len(review["reviewers"]) != 2
            or {row.get("reviewerId") for row in review["reviewers"]
                if isinstance(row, dict)} != {
                    "v3-gemini-api-physics", "v3-gemini-api-semantics"}
            or any(row.get("providerId") != "gemini_api"
                   for row in review["reviewers"])):
        # Provider-identity fail-closed: foreign/transplanted reviewer text
        # cannot trigger automatic staging or count as real two-Gemini QA.
        return False
    return all(
        isinstance(row.get("decision"), dict)
        and isinstance(row["decision"].get("dimensions"), dict)
        and all(row["decision"]["dimensions"].get(dim) ==
                ("FAIL" if dim == "trilingualMeaning" else "PASS")
                for dim in _DIMS)
        for row in review["reviewers"]
    )


def stage_known_language_repair(
    course_dir: Path, private_root: Path, plan: dict[str, Any],
) -> dict[str, Any]:
    """One finite evidence-bound recovery step followed by normal dispatch.

    Returns only sanitized metadata. No provider calls, schedules, credential
    lookups, public files, or changes to frozen source / historical review.
    Idempotent after crash: identical candidate is recognized, never replaced.
    Unknown corruptions stop as 'not automatically repairable' while other
    sections remain eligible under the original course planner.
    """
    if (not isinstance(course_dir, Path) or not course_dir.is_dir()
            or not isinstance(private_root, Path) or not private_root.is_absolute()
            or private_root.is_symlink() or not isinstance(plan, dict)
            or plan.get("publicationAuthorized") is not False):
        raise ValueError("V3_AUTOREPAIR_INVALID_SCOPE")
    quarantined = plan.get("scriptQuarantinedSections", {})
    if not isinstance(quarantined, dict):
        raise ValueError("V3_AUTOREPAIR_BAD_QUARANTINE_ROSTER")
    if _SECTION not in quarantined:
        return {"repairStatus": "NO_MATCHING_SCRIPT_REPAIR", "repairStaged": False}
    if quarantined[_SECTION] != 2:
        return {"repairStatus": "STOP_UNKNOWN_SCRIPT_DEFECT", "repairStaged": False}
    section = course_dir / _SECTION
    source = section / "package.json"
    if (section.is_symlink() or source.is_symlink()
            or not source.is_file() or source.stat().st_size > 2_000_000):
        raise ValueError("V3_AUTOREPAIR_SOURCE_UNSAFE")
    raw = source.read_bytes()
    digest = sha256(raw).hexdigest()
    if not _approved_parent_bytes(raw):
        return {"repairStatus": "STOP_UNRECOGNIZED_PARENT", "repairStaged": False}
    if not _confirmed_failure(private_root, raw):
        return {"repairStatus": "STOP_NO_GENUINE_REVIEW_EVIDENCE",
                "repairStaged": False}
    problems = script_findings(json.loads(raw.decode("utf-8")))
    if (len(problems) != 2 or
            {p["codepoint"] for p in problems} != {"U+0E40", "U+0E25"} or
            any(p["activityId"] != _ACTIVITY or
                p["path"] != "activities[13].prompt.ms" for p in problems)):
        return {"repairStatus": "STOP_UNRECOGNIZED_SOURCE_DEFECT",
                "repairStaged": False}
    updated, receipt = make_locale_repair(raw, _ACTIVITY, "ms", _CHANGES)
    if (receipt["candidatePackageSha256"] != _CANDIDATE
            or len(receipt["changedFieldPaths"]) != 7
            or [r["occurrences"] for r in receipt["replacementCounts"]] != [1, 6, 1]):
        raise ValueError("V3_AUTOREPAIR_UNEXPECTED_CANDIDATE")
    destination = (private_root / "repair-proposals" / _SECTION)
    if destination.is_symlink():
        raise ValueError("V3_AUTOREPAIR_PRIVATE_ROOT_UNSAFE")
    store_private_repair(destination, updated, receipt)
    # An unchanged source and an immutable candidate are the proof of repair
    # staging, NOT new model acceptability or release authorization.
    if source.read_bytes() != raw:
        raise ValueError("V3_AUTOREPAIR_PARENT_CHANGED_DURING_RUN")
    return {
        "repairStatus": "PRIVATE_REPAIR_STAGED_PENDING_TWO_GEMINI_REVIEWS",
        "repairStaged": True,
        "parentSha256": digest,
        "archivalParentSha256": _PARENT,
        "candidateSha256": receipt["candidatePackageSha256"],
        "publicationAuthorized": False,
    }

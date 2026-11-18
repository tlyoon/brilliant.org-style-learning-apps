"""BSA213: source-free reuse of four independent genuine Section9.2 QA results.

Read-only provenance of the original never-reviewed Section9.2 indices14-17.
The frozen 108 original assessment ledger, original idx13 science FAIL and
old unknowns remain untouched. Never conflate synthetic tests with Gemini QA.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from app_generator.runtime.v3_four_new92_review import (
    PINNED, exact_four_unreviewed, PARENT,
)
from app_generator.runtime.v3_frozen_original_tail import _bytes
from app_generator.runtime.v3_section96_authorized_revised_qa import (
    read_prior_two_role_science,
)
from app_generator.validation.autonomous_completion import (
    assessment_progress,
)
from app_generator.validation.autonomous_ai_review import canonical_digest


def verified_section92_original_tail_passes(
    course: Path, repo: Path, private: Path,
) -> list[dict]:
    """Return only exact fully saved two-Gemini PASSes, else omit/STOP safely."""
    run_dirs = [private / ("v3-generated-" + digest)
                for _, _, digest in PINNED]
    if not any(folder.exists() or folder.is_symlink() for folder in run_dirs):
        return []
    rows = exact_four_unreviewed(course, repo, private)
    if (len(rows) != len(PINNED)
            or [(x["index"],x["activityId"],x["sha"]) for x in rows]
               != list(PINNED)):
        raise ValueError("V3_SECTION92_SUPPLEMENTAL_SOURCE_IDENTITY_CHANGED")
    passed = []
    for entry in rows:
        state = entry["originalReviewState"]
        if state == "UNREVIEWED_ELIGIBLE":
            continue
        if state != "AGGREGATE_EXISTS":
            raise ValueError("V3_SECTION92_SUPPLEMENTAL_UNRECONCILED_ROLE_NO_REPLAY")
        result = read_prior_two_role_science(private, entry)
        if result["uncertain"]:
            continue
        if result["repair"]:
            continue
        if not result["pass"]:
            raise ValueError("V3_SECTION92_SUPPLEMENTAL_UNCLASSIFIED_GEMINI_REVIEW")
        source = private / "four-new-original92-slices" / entry["sha"]
        package_file = source / "package.json"
        manifest_file = source / "review-slice.json"
        if (source.is_symlink() or package_file.is_symlink()
                or manifest_file.is_symlink() or not package_file.is_file()
                or not manifest_file.is_file()
                or package_file.read_bytes() != entry["raw"]
                or manifest_file.read_bytes() != _bytes(entry["manifest"])):
            raise ValueError("V3_SECTION92_SUPPLEMENTAL_SAVED_SOURCE_CHANGED")
        assessment = (private / ("v3-generated-" + entry["sha"])
                      / "batches" / ("v3-assessment-" + entry["sha"] + ".json"))
        if (assessment.is_symlink() or not assessment.is_file()
                or assessment.stat().st_size > 8_000_000):
            raise ValueError("V3_SECTION92_SUPPLEMENTAL_UNSAFE_ASSESSMENT")
        saved = json.loads(assessment.read_text(encoding="utf8"))
        progress = assessment_progress(entry["raw"],saved)
        if (progress["activitiesAssessed"] != 1
                or progress["activitiesFullyModelReviewed"] != 1
                or progress["modelConsensusPassActivities"] != 1
                or len(saved["reviews"]) != 1
                or saved["reviews"][0]["activityId"] != entry["activityId"]):
            raise ValueError("V3_SECTION92_SUPPLEMENTAL_NOT_ACTUAL_ONE_PASS")
        original_items = json.loads(entry["raw"].decode("utf8"))["activities"]
        if len(original_items) != 1 or original_items[0]["id"] != entry["activityId"]:
            raise ValueError("V3_SECTION92_SUPPLEMENTAL_ACTIVITY_CHANGED")
        passed.append({
            "section": "section-9-2",
            "originalActivityIndex": entry["index"],
            "activityId":entry["activityId"],
            "activitySha256":canonical_digest(original_items[0]),
            "sourcePackageSha256":PARENT,
            "supplementalReviewSliceSha256":entry["sha"],
            "sourceReviewSha256":sha256(_bytes(saved["reviews"][0])).hexdigest(),
            "status":"POTENTIALLY_REUSABLE_NOT_RELEASE_ACCEPTED",
        })
    return passed

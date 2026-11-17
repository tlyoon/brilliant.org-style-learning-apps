"""Read-only V3 scientific evidence → immutable *unadmitted* corrected-course proposal.

Never edits an original Section 9.* package or its reviewer checkpoints.
Only source-free metadata is saved; real model PASS is never synthesized.
A proposal can advance into acceptance only through a separately verified,
owner-authorized version admission and all 108 real QA/release gates.
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
from app_generator.runtime.v3_course_review import plan_v3_course_review
from app_generator.runtime.v3_isolated_repair_review import stage_isolated_review_slice
from app_generator.validation.autonomous_completion import (
    assessment_progress, package_identity,
)
from app_generator.validation.autonomous_ai_review import canonical_digest

_SCOPE = "PROPOSAL_NOT_ADMITTED"
_SCHEMA = "BOSLA_V3_VERSIONED_COURSE_PROPOSAL_V1"
_SECTION = "section-9-2"
_HEX = frozenset("0123456789abcdef")


def _encoded(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("ascii")


def _hex64(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= _HEX


def _private_assessment(private_root: Path, raw: bytes, digest: str) -> dict | None:
    file = (private_root / ("v3-generated-" + digest) / "batches" /
            ("v3-assessment-" + digest + ".json"))
    if file.is_symlink() or (file.exists() and (
            not file.is_file() or file.stat().st_size > 8_000_000)):
        raise ValueError("V3_PROPOSAL_UNSAFE_PREVIOUS_MODEL_RECORD")
    if not file.exists():
        return None
    try:
        record = json.loads(file.read_text(encoding="utf8"))
    except (OSError, UnicodeError, ValueError):
        raise ValueError("V3_PROPOSAL_UNREADABLE_MODEL_RECORD") from None
    # Existing complete V3 validator verifies exact response and package
    # identities, all roles, true consensus and checkpoint reconciliation.
    assessment_progress(raw, record)
    return record


def prepare_versioned_course_proposal(
    course: Path, repo: Path, private_root: Path,
) -> dict[str, Any]:
    """Stage exact corrected six-section roster WITHOUT accepting it."""
    if (not isinstance(private_root, Path) or not private_root.is_absolute()
            or private_root.is_symlink() or private_root.resolve() == repo.resolve()
            or private_root.resolve().is_relative_to(repo.resolve())):
        raise ValueError("V3_PROPOSAL_UNSAFE_PRIVATE_ROOT")
    # Freeze the one-activity evidence chain first. This additionally proves
    # both source version & corrected activity were independently exact.
    slice_state = stage_isolated_review_slice(course, private_root, _CANDIDATE)
    if (slice_state.get("activityCount") != 1
            or slice_state.get("actualGeminiResponses") != 0
            or slice_state.get("wholeCourseScopeAccepted") is not False):
        raise ValueError("V3_PROPOSAL_UNTRUSTED_ISOLATED_SCOPE")
    progress = plan_v3_course_review(
        course, repo, private_root=private_root, continue_independent=True)
    if (progress.get("scopeSource") != "FROZEN_CANDIDATE_MANIFEST"
            or progress.get("sectionsTotal") != 6
            or progress.get("activitiesTotal") != 108
            or progress.get("publicationAuthorized") is not False):
        raise ValueError("V3_PROPOSAL_NOT_FROZEN_108_SCOPE")
    corrected = (private_root / "repair-proposals" / _SECTION /
                 _CANDIDATE / "package.json")
    corrected_raw = corrected.read_bytes()
    corrected_digest, corrected_items = package_identity(corrected_raw)
    if corrected_digest != _CANDIDATE or len(corrected_items) != 18:
        raise ValueError("V3_PROPOSAL_CHANGED_CORRECTED_CANDIDATE")
    # When a fresh authorized Gemini reviewer later records the isolated
    # corrected activity, derive its disposition from the SAME exact-hash,
    # two-role validator as the original assessment. A metadata handoff alone
    # never counts as a model answer.
    slice_sha = slice_state["reviewSliceSha256"]
    slice_file = (private_root / "single-activity-review-slices" /
                  slice_sha / "package.json")
    slice_raw = slice_file.read_bytes()
    slice_digest, slice_items = package_identity(slice_raw)
    if (slice_digest != slice_sha or len(slice_items) != 1
            or slice_items[0] != corrected_items[13]):
        raise ValueError("V3_PROPOSAL_SLICE_NOT_EXACT_CHANGED_ACTIVITY")
    revised = _private_assessment(private_root, slice_raw, slice_sha)
    revised_progress = assessment_progress(slice_raw, revised)
    corrected_pass = (revised_progress["modelConsensusPassActivities"] == 1
                      and revised_progress["activitiesFullyModelReviewed"] == 1)
    corrected_state = (
        "GENUINE_CORRECTED_MODEL_PASS_PROPOSED_NOT_ADMITTED"
        if corrected_pass else
        "REVISED_GEMINI_REPAIR_REQUIRED"
        if revised_progress["modelRepairRequiredActivities"] else
        "REVISED_GEMINI_UNCERTAIN_DO_NOT_REPLAY"
        if revised_progress["modelUncertainActivities"] else
        "PENDING_FRESH_GEMINI_TWO_REVIEWER_ASSESSMENT")

    rows = []
    original_roster = []
    new_roster = []
    reuse = []
    changed = 0
    for section in progress["sectionProgress"]:
        label = section["section"]
        if label not in {f"section-9-{n}" for n in range(1, 7)}:
            raise ValueError("V3_PROPOSAL_UNEXPECTED_SECTION")
        f = course / label / "package.json"
        if f.is_symlink() or not f.is_file() or f.stat().st_size > 2_000_000:
            raise ValueError("V3_PROPOSAL_UNSAFE_ORIGINAL_PACKAGE")
        raw = f.read_bytes()
        digest, activities = package_identity(raw)
        if digest != section["packageSha256"] or len(activities) != 18:
            raise ValueError("V3_PROPOSAL_SOURCE_CHANGED_DURING_READ")
        replacement_digest = digest
        if label == _SECTION:
            if ([a["id"] for a in activities] !=
                    [a["id"] for a in corrected_items]):
                raise ValueError("V3_PROPOSAL_CHANGED_ACTIVITY_IDS")
            differences = [i for i,(a,b) in enumerate(zip(activities,corrected_items))
                           if a != b]
            if differences != [13] or activities[13]["id"] != _ACTIVITY:
                raise ValueError("V3_PROPOSAL_UNEXPECTED_PATCH_SCOPE")
            replacement_digest = _CANDIDATE
            changed += 1
        old = _private_assessment(private_root, raw, digest)
        reviews = old["reviews"] if old else []
        if len(reviews) != section["activitiesAssessedRows"]:
            raise ValueError("V3_PROPOSAL_ASSESSMENT_ROSTER_CHANGED")
        for index, entry in enumerate(reviews):
            # Exclude the corrected activity even when its OLD record later
            # changes: the initial FAIL can never approve revised content.
            if (entry["status"] == "AI_CONSENSUS_PASS"
                    and not (label == _SECTION and index == 13)):
                new_activity = (corrected_items[index] if label == _SECTION
                                else activities[index])
                if new_activity != activities[index]:
                    raise ValueError("V3_PROPOSAL_CACHED_PASS_ON_CHANGED_ACTIVITY")
                reuse.append({
                    "section": label,
                    "activityId": activities[index]["id"],
                    "activitySha256": canonical_digest(activities[index]),
                    "sourcePackageSha256": digest,
                    "sourceReviewSha256": sha256(_encoded(entry)).hexdigest(),
                    # Reuse CANDIDATE: no accepted new version or new PASS.
                    "status": "POTENTIALLY_REUSABLE_NOT_RELEASE_ACCEPTED",
                })
        original_roster.append([label, digest, len(activities)])
        new_roster.append([label, replacement_digest, len(activities)])
        rows.append({
            "section": label,
            "originalPackageSha256": digest,
            "proposedPackageSha256": replacement_digest,
            "activities": len(activities),
            "assessedOriginal": len(reviews),
            "genuineConsensusPassOriginal": section["modelConsensusPassActivities"],
            "originalUncertain": section["modelUncertainActivities"],
            "originalRepairRequired": section["modelRepairRequiredActivities"],
        })
    if (changed != 1 or sum(x["activities"] for x in rows) != 108
            or len(reuse) != progress["modelConsensusPassActivities"]):
        raise ValueError("V3_PROPOSAL_CONFLICTING_REVIEW_INVENTORY")
    if (progress["activitiesAssessedRows"] !=
            progress["modelConsensusPassActivities"] +
            progress["modelUncertainActivities"] +
            progress["modelRepairRequiredActivities"]):
        raise ValueError("V3_PROPOSAL_UNCLASSIFIED_REVIEW_ROWS")
    unsigned = {
        "schema": _SCHEMA,
        "scope": _SCOPE,
        "oldRosterSha256": sha256(_encoded(original_roster)).hexdigest(),
        "proposedRosterSha256": sha256(_encoded(new_roster)).hexdigest(),
        "sections": rows,
        "correctedActivityId": _ACTIVITY,
        "correctedActivityIndex": 13,
        "correctedSection": _SECTION,
        "correctedPackageSha256": _CANDIDATE,
        "isolatedReviewSliceSha256": slice_state["reviewSliceSha256"],
        "potentiallyReusableOriginalPasses": reuse,
        "counts": {
            "originalTotalActivities": 108,
            "originalAssessed": progress["activitiesAssessedRows"],
            "originalFullyModelReviewed": progress["activitiesFullyModelReviewed"],
            "originalGenuineConsensusPasses": progress["modelConsensusPassActivities"],
            "potentiallyReusablePasses": len(reuse),
            "originalUncertain": progress["modelUncertainActivities"],
            "originalFailed": progress["modelRepairRequiredActivities"],
            "originalNotAssessed": 108-progress["activitiesAssessedRows"],
            "correctedActivityNewGeminiConsensusPass": int(corrected_pass),
            "correctedActivityReviewedRows": revised_progress["activitiesAssessed"],
            "correctedActivityFullyReviewed": revised_progress["activitiesFullyModelReviewed"],
        },
        "correctedActivityScientificStatus": corrected_state,
        "unresolved": [
            "ORIGINAL_SECTION_9_1_AMBIGUOUS_DO_NOT_REPLAY",
            *([] if corrected_pass else
              ["CORRECTED_SECTION_9_2_NEW_GEMINI_REVIEW_PENDING_OR_FAILED"]),
            *([] if progress["activitiesAssessedRows"] == 108 else
              ["REMAINING_ORIGINAL_ACTIVITIES_REQUIRE_GENUINE_REVIEW"]),
            "VERSIONED_SCOPE_ADMISSION_NOT_GRANTED",
            "FINAL_SCIENTIFIC_BROWSER_PRIVACY_RELEASE_PROOF_MISSING",
        ],
        "versionedScopeAdmitted": False,
        "all108ReviewedAndApproved": False,
        "publicationAuthorized": False,
    }
    manifest = {**unsigned, "integritySha256":sha256(_encoded(unsigned)).hexdigest()}
    payload = (json.dumps(manifest,indent=2,sort_keys=True)+"\n").encode("utf8")
    proposals = private_root / "versioned-course-proposals"
    final = proposals / manifest["integritySha256"]
    if proposals.is_symlink() or final.is_symlink():
        raise ValueError("V3_PROPOSAL_UNSAFE_DESTINATION")

    def check_existing() -> None:
        receipt = final / "scope-proposal.json"
        if (final.is_symlink() or not final.is_dir()
                or receipt.is_symlink() or not receipt.is_file()
                or receipt.read_bytes() != payload):
            raise ValueError("V3_PROPOSAL_EXISTING_SNAPSHOT_CONFLICT")

    if final.exists():
        check_existing()
    else:
        proposals.mkdir(parents=True,exist_ok=True)
        stage=Path(tempfile.mkdtemp(prefix=".v3-proposal-stage-",dir=proposals))
        try:
            with (stage/"scope-proposal.json").open("xb") as stream:
                stream.write(payload)
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
    return {
        "status":"VERSIONED_COURSE_PROPOSAL_STAGED_NOT_ADMITTED",
        "proposalSha256":manifest["integritySha256"],
        "oldRosterSha256":manifest["oldRosterSha256"],
        "proposedRosterSha256":manifest["proposedRosterSha256"],
        "potentiallyReusableGenuinePasses":len(reuse),
        "remainingOriginalUnassessed":108-progress["activitiesAssessedRows"],
        "originalUncertain":progress["modelUncertainActivities"],
        "originalFailed":progress["modelRepairRequiredActivities"],
        "correctedActivityNewGeminiConsensusPass":int(corrected_pass),
        "correctedActivityScientificStatus":corrected_state,
        "versionedScopeAdmitted":False,
        "publicationAuthorized":False,
    }

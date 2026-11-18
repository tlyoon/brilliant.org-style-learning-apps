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
from app_generator.runtime.v3_historical_role_rollforward import (
    stage_known_unrecoverable_section96,
)
from app_generator.runtime.v3_science_validated_roster import (
    validated_section96_two_science_revision,
)
from app_generator.runtime.v3_frozen_original_tail import (
    plan_frozen_original_tail, _slice as make_frozen_original_slice,
)
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
    # BSA-185: supplemental reviews of UNCHANGED original Section 9.6
    # activities have a distinct one-activity immutable identity after a
    # historical uncertain earlier role. They can contribute potential
    # content-level reuse, but never alter the old original 108 ledger,
    # retroactively resolve the ambiguous role or grant course admission.
    original_96 = next(r for r in progress["sectionProgress"]
                       if r["section"] == "section-9-6")
    independent = (
        plan_frozen_original_tail(
            course,repo,private_root,section="section-9-6")
        if original_96["modelUncertainActivities"] else None)
    supplementary_pass = {
        r["index"]: r for r in independent["rows"]
        if r["state"] == "GENUINE_SUPPLEMENTAL_CONSENSUS_PASS"
    } if independent else {}
    supplementary_metadata = []
    # BSA-190: a different, genuinely revised activity may replace an
    # unrecoverable *old* Section9.6 role in a NEW unadmitted course version.
    # Neither the old AI_UNCERTAIN nor a newly staged QA input counts as PASS.
    recovered_96 = stage_known_unrecoverable_section96(
        course, repo, private_root)
    has_revised_96 = (
        recovered_96["status"] ==
        "NEW_VERSIONED_SECTION96_REPAIR_STAGED_QA_NOT_AUTHORIZED")
    revised_96_raw = None
    revised_96_items = None
    revised_96_qa_state = None
    two_revision_science = None
    proposed_96_sha = None
    if has_revised_96:
        new_sha = recovered_96["candidatePackageSha256"]
        candidate_file = (private_root / "historical-role-rollforward" /
                          "section-9-6" / new_sha / "package.json")
        if (candidate_file.is_symlink() or not candidate_file.is_file()
                or candidate_file.stat().st_size > 2_000_000):
            raise ValueError("V3_PROPOSAL_MISSING_NEW_SECTION96_CONTENT")
        revised_96_raw = candidate_file.read_bytes()
        revised_sha, revised_96_items = package_identity(revised_96_raw)
        old_96_raw = (course / "section-9-6" / "package.json").read_bytes()
        old_96_sha, old_96_items = package_identity(old_96_raw)
        if (revised_sha != new_sha
                or old_96_sha != recovered_96["parentPackageSha256"]
                or len(revised_96_items) != 18
                or [i for i,(old,new) in enumerate(
                    zip(old_96_items,revised_96_items)) if old!=new] != [5]
                or set(k for k in revised_96_items[5]
                       if revised_96_items[5][k] != old_96_items[5][k])
                   != {"prompt"}):
            raise ValueError("V3_PROPOSAL_NEW_SECTION96_CHANGED_TOO_MUCH")
        new_review_sha = recovered_96["isolatedReviewInputSha256"]
        review_file = (private_root / "historical-role-review-inputs" /
                       "section-9-6" / new_review_sha / "package.json")
        if review_file.is_symlink() or not review_file.is_file():
            raise ValueError("V3_PROPOSAL_MISSING_NEW_SECTION96_REVIEW_INPUT")
        review_raw = review_file.read_bytes()
        review_digest, review_items = package_identity(review_raw)
        if (review_digest != new_review_sha
                or review_items != [revised_96_items[5]]):
            raise ValueError("V3_PROPOSAL_NEW_SECTION96_REVIEW_IDENTITY")
        qa_assessment = _private_assessment(
            private_root, review_raw, review_digest)
        qa_progress = assessment_progress(review_raw, qa_assessment)
        revised_96_qa_state = (
            "GENUINE_REVISED_SECTION96_GEMINI_PASS_NOT_ADMITTED"
            if qa_progress["modelConsensusPassActivities"] == 1
               and qa_progress["activitiesFullyModelReviewed"] == 1
            else "NEW_SECTION96_GEMINI_REPAIR_REQUIRED"
            if qa_progress["modelRepairRequiredActivities"] else
            "NEW_SECTION96_GEMINI_UNCERTAIN_NO_REPLAY"
            if qa_progress["modelUncertainActivities"] else
            "NEW_SECTION96_TWO_GEMINI_REVIEWS_NOT_YET_AUTHORIZED")

    # BSA-207: a genuinely new Section9.6 index9 correction was reviewed
    # ONLY AFTER the earlier versioned index5 correction. Both separately
    # submitted new identities must have two COMPLETE independent Gemini
    # consensus PASS records. Old original FAIL/unknown claims never change.
    if has_revised_96:
        proposed_96_sha = recovered_96["candidatePackageSha256"]
        two_revision_science=validated_section96_two_science_revision(
            course,repo,private_root,
            previous_sha=proposed_96_sha,previous_items=revised_96_items)
        if two_revision_science is not None:
            proposed_96_sha=two_revision_science["candidatePackageSha256"]
            revised_96_items=two_revision_science["activities"]

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
        elif label == "section-9-6" and has_revised_96:
            if (revised_96_items is None
                    or [item["id"] for item in activities] !=
                       [item["id"] for item in revised_96_items]
                    or [i for i,(a,b) in enumerate(
                        zip(activities,revised_96_items)) if a!=b] != (
                            [5,9] if two_revision_science is not None else [5])):
                raise ValueError("V3_PROPOSAL_REVISED_SECTION96_SCOPE_CHANGED")
            replacement_digest = proposed_96_sha
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
        if label == "section-9-6":
            for index, supplemental in sorted(supplementary_pass.items()):
                if not len(reviews) <= index < len(activities):
                    raise ValueError("V3_PROPOSAL_SUPPLEMENT_OVERLAPS_ORIGINAL_REVIEW")
                slice_raw, review_sha, expected = make_frozen_original_slice(
                    digest,label,index,activities[index])
                if supplemental["slicePackageSha256"] != review_sha:
                    raise ValueError("V3_PROPOSAL_SUPPLEMENT_IDENTITY_MISMATCH")
                parent = (private_root / "frozen-original-review-slices"
                          / review_sha)
                package_file = parent / "package.json"
                manifest_file = parent / "review-slice.json"
                if (parent.is_symlink() or package_file.is_symlink()
                        or manifest_file.is_symlink()
                        or not package_file.is_file()
                        or not manifest_file.is_file()
                        or package_file.read_bytes() != slice_raw
                        or json.loads(manifest_file.read_text(encoding="utf8")) != expected):
                    raise ValueError("V3_PROPOSAL_SUPPLEMENT_CHANGED_OR_MISSING")
                verified = _private_assessment(
                    private_root,slice_raw,review_sha)
                if (verified is None
                        or assessment_progress(slice_raw,verified)
                           ["modelConsensusPassActivities"] != 1
                        or len(verified["reviews"]) != 1
                        or verified["reviews"][0]["activityId"] != activities[index]["id"]):
                    raise ValueError("V3_PROPOSAL_SUPPLEMENT_NO_GENUINE_MODEL_PASS")
                source_review_sha = sha256(
                    _encoded(verified["reviews"][0])).hexdigest()
                supplement_link = {
                    "section": label,
                    "originalActivityIndex": index,
                    "activityId": activities[index]["id"],
                    "activitySha256": canonical_digest(activities[index]),
                    "sourcePackageSha256": digest,
                    "supplementalReviewSliceSha256": review_sha,
                    "sourceReviewSha256": source_review_sha,
                    "status": "POTENTIALLY_REUSABLE_NOT_RELEASE_ACCEPTED",
                }
                supplementary_metadata.append(supplement_link)
                reuse.append({
                    "section": label,
                    "activityId": activities[index]["id"],
                    "activitySha256": canonical_digest(activities[index]),
                    "sourcePackageSha256": digest,
                    "sourceReviewSha256": source_review_sha,
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
    if (changed != (2 if has_revised_96 else 1)
            or sum(x["activities"] for x in rows) != 108
            or len(reuse) != (progress["modelConsensusPassActivities"]
                              + len(supplementary_metadata))):
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
    if has_revised_96:
        # The NEW content version can have its own genuine two-role model
        # result later, but old ambiguous provider evidence always remains
        # unresolved and never upgrades the original frozen review.
        unsigned["section96UnrecoverableRoleReplacement"] = {
            "section": "section-9-6",
            "originalUnresolvedActivityIndex": 5,
            "originalUnresolvedActivityId":
                "mcq-mod-bat-cut-mass-comparison",
            "parentPackageSha256":
                recovered_96["parentPackageSha256"],
            "newContentPackageSha256": proposed_96_sha,
            "newOneActivityReviewInputSha256":
                recovered_96["isolatedReviewInputSha256"],
            "oldAmbiguousProviderRolePreserved": True,
            "newGeminiScientificStatus": revised_96_qa_state,
            "versionedScopeAdmitted": False,
            "publicationAuthorized": False,
        }
        unsigned["unresolved"].append(
            "HISTORICAL_SECTION96_PROVIDER_RESPONSE_UNRECOVERABLE_DO_NOT_REPLAY")
        if two_revision_science is not None:
            unsigned["section96ScientificFailureReplacement"] = {
                "section":"section-9-6",
                "newContentPackageSha256":proposed_96_sha,
                "changedActivityIndices":[5,9],
                "independentNewVersionGeminiEvidence":
                    two_revision_science["proofs"],
                "originalIndex9ScientificFailurePreserved":True,
                "originalIndex6ProviderUnknownPreserved":True,
                "versionedScopeAdmitted":False,
                "publicationAuthorized":False,
            }
            unsigned["counts"]["revisedSection96Index9NewGeminiConsensusPass"]=1
        if revised_96_qa_state != (
                "GENUINE_REVISED_SECTION96_GEMINI_PASS_NOT_ADMITTED"):
            unsigned["unresolved"].append(
                "NEW_SECTION96_REVISED_ACTIVITY_TWO_GEMINI_REVIEW_PENDING")
        unsigned["counts"]["revisedSection96NewGeminiConsensusPass"] = int(
            revised_96_qa_state ==
            "GENUINE_REVISED_SECTION96_GEMINI_PASS_NOT_ADMITTED")
    if supplementary_metadata:
        # Additions only when actual exact-version two-Gemini supplemental
        # evidence exists; historical proposal bytes remain unchanged when
        # no original tail has been independently reviewed.
        unsigned["supplementalFrozenOriginalReviews"] = supplementary_metadata
        unsigned["counts"]["supplementalFrozenOriginalConsensusPasses"] = (
            len(supplementary_metadata))
        unsigned["counts"]["originalNotAssessedAfterSupplemental"] = (
            108-progress["activitiesAssessedRows"]-len(supplementary_metadata))
        unsigned["unresolved"].append(
            "SUPPLEMENTAL_REVIEWS_NOT_YET_ADMITTED_INTO_NEW_COURSE_SCOPE")
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
        "verifiedSupplementalFrozenOriginalPasses":len(supplementary_metadata),
        "remainingOriginalUnassessed":108-progress["activitiesAssessedRows"],
        "remainingContentUnreviewedAfterSupplemental":
            108-progress["activitiesAssessedRows"]-len(supplementary_metadata),
        "originalUncertain":progress["modelUncertainActivities"],
        "originalFailed":progress["modelRepairRequiredActivities"],
        "correctedActivityNewGeminiConsensusPass":int(corrected_pass),
        "correctedActivityScientificStatus":corrected_state,
        "section96NewContentCandidateSha256": proposed_96_sha,
        "section96NewGeminiScientificStatus": revised_96_qa_state,
        "section96ScienceIntegrated":two_revision_science is not None,
        "section96Index9NewGeminiConsensusPass":int(
            two_revision_science is not None),
        "versionedScopeAdmitted":False,
        "publicationAuthorized":False,
    }

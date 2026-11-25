"""BSA-207: release-neutral TWO scientifically reviewed Section9.6 corrections.

A previously staged private content revision may join a NEW unadmitted
108-activity course proposal ONLY if both distinct new one-activity Gemini
inputs have genuine complete independently saved consensus PASS evidence.
No model I/O, original verdict edits, old-role replay or publication.
"""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path

from app_generator.runtime.v3_section96_scientific_failure_repair import (
    stage_known_section96_scientific_failure,
)
from app_generator.runtime.v3_section96_authorized_revised_qa import (
    _EXPECTED_SLICES, verify_persisted_two_role_science,
)
from app_generator.validation.autonomous_completion import (
    package_identity, assessment_progress,
)


def validated_section96_two_science_revision(
    course: Path, repo: Path, private: Path, *,
    previous_sha: str, previous_items: list,
) -> dict|None:
    """Return NEW immutable corrected version only on two verified model PASS."""
    state=stage_known_section96_scientific_failure(course,repo,private)
    if state.get("status")=="NO_REGISTERED_SECTION96_SCIENCE_FAILURE_REMEDY":
        return None
    if (state.get("status")!=
            "NEW_SECTION96_SCIENCE_REPAIR_STAGED_REVIEW_NOT_AUTHORIZED"
            or state.get("previousRevisedPackageSha256")!=previous_sha
            or state.get("oldScientificFailurePreserved") is not True
            or state.get("oldProviderUncertaintyPreserved") is not True
            or state.get("publicationAuthorized") is not False
            or state.get("newModelConsensusPassClaimed") is not False):
        raise ValueError("V3_2REV_SCIENCE_SOURCE_PROVENANCE_CHANGED")
    current_sha=state["candidatePackageSha256"]
    source=(private/"scientific-failure-rollforward"/"section-9-6"/
            current_sha/"package.json")
    if (source.is_symlink() or not source.is_file()
            or source.stat().st_size>2_000_000):
        raise ValueError("V3_2REV_SCIENCE_NEW_SOURCE_MISSING")
    raw=source.read_bytes()
    verified_sha,activities=package_identity(raw)
    oldfile=course/"section-9-6"/"package.json"
    if oldfile.is_symlink() or not oldfile.is_file():
        raise ValueError("V3_2REV_SCIENCE_FROZEN_SOURCE_MISSING")
    old_sha,original=package_identity(oldfile.read_bytes())
    if (verified_sha!=current_sha
            or old_sha!=state["originalPackageSha256"]
            or len(previous_items)!=18 or len(activities)!=18
            or [i for i,(a,b) in enumerate(zip(previous_items,activities))
                if a!=b]!=[9]
            or [i for i,(a,b) in enumerate(zip(original,activities))
                if a!=b]!=[5,9]
            or [x["id"] for x in activities]!=[x["id"] for x in original]):
        raise ValueError("V3_2REV_SCIENCE_BOTH_CHANGED_INDICES_NOT_EXACT")
    reviews=[]
    for index,activity,parent,review_sha,folder in _EXPECTED_SLICES:
        if ((index==5 and parent!=previous_sha)
                or (index==9 and parent!=current_sha)):
            raise ValueError("V3_2REV_SCIENCE_REVIEW_PARENT_CONFLICT")
        if (index==9 and
                state.get("isolatedReviewInputSha256")!=review_sha):
            raise ValueError("V3_2REV_SCIENCE_NEW_ROLE_INPUT_CHANGED")
        path=(private/folder/"section-9-6"/review_sha/"package.json")
        if (path.is_symlink() or not path.is_file()
                or path.stat().st_size>2_000_000):
            raise ValueError("V3_2REV_SCIENCE_REVIEW_SOURCE_MISSING")
        review_raw=path.read_bytes()
        digest,items=package_identity(review_raw)
        if (digest!=review_sha or len(items)!=1
                or items[0]!=activities[index]
                or items[0]["id"]!=activity):
            raise ValueError("V3_2REV_SCIENCE_REVIEW_IDENTITY_MISMATCH")
        assessment=(private/("v3-generated-"+review_sha)/"batches"/
                    ("v3-assessment-"+review_sha+".json"))
        if assessment.is_symlink():
            raise ValueError("V3_2REV_SCIENCE_UNSAFE_SAVED_REVIEW")
        if not assessment.exists():
            # A staged input alone must NEVER become scientific evidence.
            return None
        if not assessment.is_file() or assessment.stat().st_size>8_000_000:
            raise ValueError("V3_2REV_SCIENCE_BAD_SAVED_REVIEW")
        saved=json.loads(assessment.read_text(encoding="utf8"))
        progress=assessment_progress(review_raw,saved)
        if progress["activitiesAssessed"]!=1:
            raise ValueError("V3_2REV_SCIENCE_WRONG_ASSESSED_COUNT")
        if (progress["modelConsensusPassActivities"]!=1
                or progress["activitiesFullyModelReviewed"]!=1):
            return None
        proof=verify_persisted_two_role_science(
            private,review_raw,activity,review_sha,progress)
        if proof!={"pass":True,"repair":False,"uncertain":False}:
            raise ValueError("V3_2REV_SCIENCE_TWO_ROLE_PASS_NOT_PROVEN")
        reviews.append({
            "index":index,"activityId":activity,
            "reviewSliceSha256":review_sha,
            "genuineConsensusPass":True,
            "savedAssessmentSha256":sha256(assessment.read_bytes()).hexdigest(),
        })
    if len(reviews)!=2:
        raise ValueError("V3_2REV_SCIENCE_INCOMPLETE_PROOFS")
    return {"candidatePackageSha256":current_sha,
            "activities":activities,"proofs":reviews,
            "oldOriginalScientificFailurePreserved":True,
            "oldOriginalProviderUnknownPreserved":True,
            "newContentVersionAdmitted":False,
            "publicationAuthorized":False}

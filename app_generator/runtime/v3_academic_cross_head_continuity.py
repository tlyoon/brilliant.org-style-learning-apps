"""BSA272: independent acceptance persists safely across Bosla code revisions.

A genuine accepted academic task is bound to one original textbook, frozen
candidate and exact task ID. A new code HEAD creates fresh signed source-free
V36 evidence but MUST NOT silently revoke accepted original-source physics.
Revalidate the original immutable proof + original V36 predecessor, and
recompute the same proposition against the NEW signed V36 and its textbook.
Never copy an academic PASS across changed source or candidate content.
No provider replay, no new model calls, no publication.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_long_horizon_development import (
    read_long_horizon_development,_read_signed,
)
from app_generator.runtime.v3_first_academic_proof_admission import (
    _FRONTIER,_RECEIPT,_ID,_bound_inputs,_check_recomputed,
    verify_first_academic_frontier,
)
from app_generator.validation.section91_first_distractor_proof import (
    independent_distractor_science,
)
from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA,_CANDIDATE_SHA,
)


def verify_academic_across_git_heads(*,private:Path)->dict[str,Any]:
    latest=read_long_horizon_development(private)
    frontier=_read_signed(private/"long-horizon-development"/_FRONTIER)
    original={"gitHead":frontier.get("gitHead"),
              "proposalSha256":frontier.get("proposalSha256")}
    current={"gitHead":latest["gitHead"],
             "proposalSha256":latest["proposalSha256"]}
    old=(original!=current)
    if (frontier.get("sourceSha256")!=_SOURCE_SHA
        or frontier.get("candidateSha256")!=_CANDIDATE_SHA
        or latest.get("sourceSha256")!=_SOURCE_SHA
        or latest.get("candidateSha256")!=_CANDIDATE_SHA):
        raise ValueError("BSA272_ORIGINAL_TEXTBOOK_OR_CANDIDATE_CHANGED")
    admitted=verify_first_academic_frontier(
        private=private,ready=original,allow_historical=old)
    if (admitted.get("independentlyAcceptedAcademicTasks")!=1
        or admitted.get("otherFullAcademicTasksStillOpen")!=428
        or admitted.get("taskId")!=_ID
        or admitted.get("completeAcademicProofGatesStillOpen")!=90
        or admitted.get("publicationAuthorized") is not False):
        raise ValueError("BSA272_HISTORICAL_ACCEPTANCE_NOT_PROVEN")
    folder,v36,partition,pdf,candidate=_bound_inputs(private,current)
    new_proof=independent_distractor_science(
        source_pdf=pdf,candidate_path=candidate)
    _check_recomputed(new_proof)
    # Both proof-generation and readback are executed on the current
    # source/candidate, while the original immutable receipt is reopened.
    old_folder=private/"owner-five-stage-completion"/(
        original["gitHead"])/original["proposalSha256"]
    old_receipt=_signed(old_folder,_RECEIPT,original)
    if (old_receipt.get("independentTaskProof")!=new_proof
        or old_receipt.get("integritySha256")!=
           admitted.get("proofReceiptSha256")
        or v36.get("semanticTasksAutomaticallyDispatched")!=429
        or partition.get("activity",{}).get("activityId")!=
           "act-mcq-01-vector-nature"):
        raise ValueError("BSA272_NEW_HEAD_PROOF_NOT_SAME_SOURCE_BOUND_TASK")
    return {
        "status":"BSA272_ACADEMIC_PROOF_INDEPENDENTLY_VERIFIED_ON_CURRENT_GIT_HEAD",
        "currentGitHead":current["gitHead"],
        "academicProofOriginGitHead":original["gitHead"],
        "carriedAcrossGitHead":old,
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "taskId":_ID,
        "proofReceiptSha256":admitted["proofReceiptSha256"],
        "acceptedAcademicTasks":1,
        "independentlyAcceptedAcademicTasks":1,
        "fullAcademicTasksStillOpen":428,
        "otherFullAcademicTasksStillOpen":428,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    }

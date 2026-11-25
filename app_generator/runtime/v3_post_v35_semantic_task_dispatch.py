"""BSA264 V36 automatic 429-task signed, resumable, fail-isolated dispatch."""
from __future__ import annotations
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_nonmerging_draft_pr import _preflight
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_post_v34_interactive_source_roles import _V35, _STATUS35
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _SOURCE_BINDING
from app_generator.runtime.v3_exact_revised_review_reconciliation import _CANDIDATE
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.validation.section91_formal_physics import _SOURCE_SHA, _CANDIDATE_SHA, _digest
from app_generator.validation.section91_semantic_task_executor import audit_semantic_backlog

_V36="V36_EXACT_429_SEMANTIC_TASK_DISPATCH_NO_ACADEMIC_PASS.json"
_STATUS36="V36_ALL_429_SEMANTIC_TASKS_BOUNDED_ATTEMPTED_PRIVATE"
_PREFIX="V36_PARTITION_"

def run_post_v35_semantic_task_dispatch(
    repo:Path,private:Path,ready:dict[str,Any],
    v9:dict,v11:dict,v12:dict,v35_result:dict[str,Any],
)->dict[str,Any]:
    folder,_,_,_,_=_preflight(repo,private,ready,v9,v11,v12)
    v35=_signed(folder,_V35,ready)
    if (v35!=v35_result or v35.get("status")!=_STATUS35
            or v35.get("sourceSha256")!=_SOURCE_SHA
            or v35.get("revisedCandidateSha256")!=_CANDIDATE_SHA
            or v35.get("trilingualPromptRoleCuesChecked")!=27
            or v35.get("trilingualFirstItemRoleCuesChecked")!=27
            or v35.get("fullAcademicPASS")!=0
            or v35.get("publicationAuthorized") is not False):
        raise ValueError("BSA264_AUTHENTIC_SIGNED_V35_REQUIRED")
    binding=_trusted_json(private/_SOURCE_BINDING)
    proof=audit_semantic_backlog(
        source_pdf=Path(binding["sourcePdf"]),candidate_path=folder/_CANDIDATE)
    if (proof.get("status")!="BSA264_ALL_429_SOURCE_BOUND_TASKS_ATTEMPTED_ISOLATED_PENDING"
            or proof.get("totalTaskCount")!=429
            or proof.get("sourceAnchorsRechecked")!=18
            or proof.get("formalModelsRecomputed")!=18
            or proof.get("visualNecessityUndecided")!=18
            or proof.get("quarantinedTaskCount")!=0
            or proof.get("fullAcademicProofTasksAccepted")!=0
            or proof.get("fullAcademicProofTasksStillOpen")!=429
            or proof.get("completeAcademicProofGatesStillOpen")!=90
            or proof.get("fullAcademicPASS")!=0
            or proof.get("newModelCalls")!=0
            or proof.get("publicationAuthorized") is not False
            or proof.get("sourceSha256")!=_SOURCE_SHA
            or proof.get("candidateSha256")!=_CANDIDATE_SHA
            or len(proof.get("activityEvidenceRows",()))!=18):
        raise ValueError("BSA264_429_TASK_EXECUTION_PROOF_NOT_ACCEPTED")
    evidence=proof["activityEvidenceRows"]
    signed_rows=[]
    for i,row in enumerate(evidence,1):
        if row.get("taskCount")!=len(row.get("evidenceRows",())):
            raise ValueError("BSA264_ACTIVITY_EVIDENCE_LENGTH_MISMATCH")
        # Each exact source-pinned task is saved individually by activity and
        # then signed; restart never needs to replay a provider request.
        rec=_v6_checkpoint(folder/f"{_PREFIX}{i:02}.json",{
            "gitHead":ready["gitHead"],
            "proposalSha256":ready["proposalSha256"],
            "sourceV35ReceiptSha256":v35["integritySha256"],
            "sourceSha256":_SOURCE_SHA,
            "candidateSha256":_CANDIDATE_SHA,
            "status":"V36_PRIVATE_BOUNDED_ACTIVITY_TASK_EVIDENCE_NOT_ACADEMIC_PASS",
            "activity":row,
            "publicationAuthorized":False,
            "academicPASS":0,
        })
        if (folder/f"{_PREFIX}{i:02}.json").stat().st_size>=12000:
            raise ValueError("BSA264_ACTIVITY_PARTITION_RECEIPT_TOO_LARGE")
        signed_rows.append({
            "activityId":row["activityId"],
            "taskCount":row["taskCount"],
            "signedEvidenceSha256":rec["integritySha256"],
        })
    if sum(x["taskCount"] for x in signed_rows)!=429:
        raise ValueError("BSA264_PARTITION_COUNTS_NOT_429")
    return _v6_checkpoint(folder/_V36,{
        "status":_STATUS36,
        "gitHead":ready["gitHead"],
        "proposalSha256":ready["proposalSha256"],
        "sourceV35ReceiptSha256":v35["integritySha256"],
        "sourceSha256":_SOURCE_SHA,
        "revisedCandidateSha256":_CANDIDATE_SHA,
        "exactTaskRosterSha256":proof["queueSha256"],
        "taskEvidenceRowsSha256":proof["activityEvidenceRowsSha256"],
        "sourceAnchorRechecks":18,
        "independentFormalAnswerModelsRecomputed":18,
        "semanticTasksAutomaticallyDispatched":429,
        "activitySignedPartitionCount":18,
        "signedPartitionHashes":signed_rows,
        "taskKindCounts":proof["taskKindCounts"],
        "taskDispositionCounts":proof["taskDispositionCounts"],
        "quarantinedTaskCount":0,
        "visualCoverageDecisionRequired":18,
        "fullAcademicProofTasksAccepted":0,
        "fullAcademicProofTasksStillOpen":429,
        "completeAcademicProofGatesStillOpen":90,
        "independentMeaningMicroproofsPending":429,
        "fullAcademicPASS":0,
        "newModelCalls":0,
        "publicationAuthorized":False,
        "outsideTextbookPdfsRequired":False,
        "nextEligibleMilestone":"EXECUTE_SOURCE_BOUND_FULL_SEMANTIC_TASK_PROOF_HANDLERS_WITH_INDEPENDENT_EVIDENCE",
    })

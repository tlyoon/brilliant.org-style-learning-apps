"""BSA264 independent owner-only original textbook and exact V36 readback."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys

from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _SOURCE_BINDING
from app_generator.runtime.v3_exact_revised_review_reconciliation import _CANDIDATE
from app_generator.runtime.v3_post_v35_semantic_task_dispatch import _V36, _STATUS36, _PREFIX
from app_generator.validation.section91_semantic_task_executor import audit_semantic_backlog
from app_generator.validation.section91_formal_physics import _digest

ROOT=Path(__file__).resolve().parents[1]
PRIVATE=Path(os.environ["LOCALAPPDATA"])/"Microvid"/"BoslaV3ReviewYoga6"

def verify(*,audit_only:bool=False)->dict:
    head=subprocess.check_output(
        ["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    source=Path(_trusted_json(PRIVATE/_SOURCE_BINDING)["sourcePdf"])
    folder_root=PRIVATE/"owner-five-stage-completion"
    if audit_only:
        import hashlib
        from app_generator.validation.section91_formal_physics import _CANDIDATE_SHA
        candidates=[x for x in folder_root.glob("*/*/"+_CANDIDATE)
                    if x.is_file()
                    and hashlib.sha256(x.read_bytes()).hexdigest()==_CANDIDATE_SHA]
        if not candidates:
            raise ValueError("BSA264_NO_REAL_IMMUTABLE_CANDIDATE")
        result=audit_semantic_backlog(source_pdf=source,candidate_path=candidates[-1])
        return {"status":"BSA264_REAL_ORIGINAL_SERWAY_BACKLOG_READONLY_AUDIT",
                "sourceBoundTasksDispatched":429,
                "activityCount":18,
                "quarantinedTasks":result["quarantinedTaskCount"],
                "completeAcademicProofTasksStillOpen":429,
                "publicationAuthorized":False}
    folders=[x for x in (folder_root/head).iterdir() if x.is_dir()]
    if len(folders)!=1:
        raise ValueError("BSA264_EXACT_HEAD_PRIVATE_PROPOSAL_NOT_UNIQUE")
    folder=folders[0]
    result=audit_semantic_backlog(
        source_pdf=source,candidate_path=folder/_CANDIDATE)
    record=_signed(folder,_V36,{"gitHead":head,"proposalSha256":folder.name})
    if (record.get("status")!=_STATUS36
            or record.get("sourceSha256")!=result["sourceSha256"]
            or record.get("revisedCandidateSha256")!=result["candidateSha256"]
            or record.get("exactTaskRosterSha256")!=result["queueSha256"]
            or record.get("taskEvidenceRowsSha256")!=result["activityEvidenceRowsSha256"]
            or record.get("semanticTasksAutomaticallyDispatched")!=429
            or record.get("activitySignedPartitionCount")!=18
            or record.get("fullAcademicProofTasksAccepted")!=0
            or record.get("fullAcademicProofTasksStillOpen")!=429
            or record.get("fullAcademicPASS")!=0
            or record.get("publicationAuthorized") is not False):
        raise ValueError("BSA264_SIGNED_ROOT_TASK_EVIDENCE_WRONG")
    partition=record["signedPartitionHashes"]
    if len(partition)!=18:
        raise ValueError("BSA264_SIGNED_PARTITION_MISSING")
    for i,row in enumerate(result["activityEvidenceRows"],1):
        v=_signed(folder,f"{_PREFIX}{i:02}.json",
                  {"gitHead":head,"proposalSha256":folder.name})
        if (v.get("activity")!=row
                or v.get("academicPASS")!=0
                or v.get("publicationAuthorized") is not False
                or partition[i-1].get("activityId")!=row["activityId"]
                or partition[i-1].get("taskCount")!=row["taskCount"]
                or partition[i-1].get("signedEvidenceSha256")!=v["integritySha256"]):
            raise ValueError("BSA264_PRIVATE_SIGNED_PARTITION_INTEGRITY")
    return {
        "status":"BSA264_INDEPENDENT_SIGNED_429_TASK_READBACK_PASS",
        "gitHead":head,
        "rootReceiptSha256":record["integritySha256"],
        "signedActivityPartitions":18,
        "tasksExamined":429,
        "allTasksStillRequireFullAcademicMeaningReview":True,
        "fullAcademicPASS":0,
        "newModelCalls":0,
        "publicationAuthorized":False,
    }

if __name__=="__main__":
    try:
        print(json.dumps(verify(audit_only="--audit-only" in sys.argv),sort_keys=True))
    except Exception as exc:
        print(json.dumps({"status":"BSA264_OWNER_SEMANTIC_TASK_RECONCILIATION_STOP",
                          "errorClass":type(exc).__name__,
                          "publicationAuthorized":False}))
        raise SystemExit(2)

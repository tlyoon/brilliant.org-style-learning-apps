"""BSA276: versioned A4–A6 independent admission for SI-unit MCQ science.

A4, A5 and A6 belong to one *distinct*, immutable signed batch. It does not
amend previous A1, A2 or A3 receipts. The previous three proofs, original
single Serway PDF, 18 original signed V36 partitions and exact three pending
MCQ02 task rows are reopened on EVERY verification across code HEADs. Only
these three MCQ_DISTRACTOR_SCIENCE tasks may be admitted. Zero extra source
PDFs, model calls, translations/diagrams PASS or public publication.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_guarded_signed_science_reuse import verified_stage_reuse
from app_generator.runtime.v3_first_academic_proof_admission import _bound_inputs
from app_generator.runtime.v3_long_horizon_development import (
    read_long_horizon_development,_write_latest,_read_signed,
)
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_academic_science_batch_admission import (
    verify_academic_batch_across_git_heads,
)
from app_generator.runtime.v3_academic_proof_registry_receipt import (
    verify_registry_audit, _RECEIPT as _REGISTRY_RECEIPT,
)
from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA,_CANDIDATE_SHA,
)
from app_generator.validation.section91_si_unit_false_options_proof import (
    independently_prove_si_unit_false_option,
    independently_verify_si_option_witness,
)

_RECEIPT="BOSLA_ACADEMIC_SI_UNIT_BATCH_A4_A6_V1.json"
_FRONTIER="BOSLA_ACADEMIC_SI_UNIT_BATCH_FRONTIER_V1.json"
_STATUS="BSA276_THREE_SI_UNIT_MISCONCEPTIONS_INDEPENDENTLY_ADMITTED"
_FRONTIER_STATUS="BSA276_PRIVATE_THREE_NEW_SCIENCE_TASKS_ACCEPTED"
_TASK_IDS={
    "opt-b":"3f8a908d4cd917719a13aecc958d5ffa20197318a6d4cdb9342106c4aea67575",
    "opt-c":"86eaed737bea0b074437367186c3401264d9d02516c1843e30b8635a29c8aa5d",
    "opt-d":"b55f3ed1d98ce70cec615a2633508117f1454c07b193d7086882fec1b47164e6",
}


def _folder(private:Path,ready:dict[str,str])->Path:
    return private/"owner-five-stage-completion"/ready["gitHead"]/ready["proposalSha256"]


def _prior_three(private:Path)->dict[str,Any]:
    previous=verify_academic_batch_across_git_heads(private=private)
    if (previous.get("independentlyAcceptedAcademicTasks")!=3
        or previous.get("fullAcademicTasksStillOpen")!=426
        or len(set(previous.get("acceptedAcademicTaskIds",[])))!=3
        or previous.get("completeAcademicProofGatesStillOpen")!=90
        or previous.get("fullAcademicActivityPASS")!=0
        or previous.get("publicationAuthorized") is not False):
        raise ValueError("BSA276_A1_A2_A3_SIGNED_PRIOR_ACCEPTANCES_REQUIRED")
    return previous


def _current_v36_si_tasks(
    *,private:Path,ready:dict[str,str],historical:bool,
)->tuple[dict[str,Any],dict[str,Any],list[dict[str,Any]]]:
    _,v36,first,source,candidate=_bound_inputs(
        private,ready,allow_historical=historical)
    signed=v36.get("signedPartitionHashes",[])
    if (len(signed)!=18 or v36.get("semanticTasksAutomaticallyDispatched")!=429
        or v36.get("fullAcademicProofTasksAccepted")!=0
        or v36.get("completeAcademicProofGatesStillOpen")!=90
        or v36.get("sourceSha256")!=_SOURCE_SHA
        or first.get("sourceSha256")!=_SOURCE_SHA):
        raise ValueError("BSA276_SELECTED_ORIGINAL_V36_BOUNDARY_REQUIRED")
    part=_signed(_folder(private,ready),"V36_PARTITION_02.json",ready)
    if (signed[1].get("activityId")!="act-mcq-02-si-units"
        or signed[1].get("signedEvidenceSha256")!=part.get("integritySha256")
        or part.get("activity",{}).get("activityId")!="act-mcq-02-si-units"
        or part.get("sourceSha256")!=_SOURCE_SHA
        or part.get("candidateSha256")!=_CANDIDATE_SHA
        or part.get("academicPASS")!=0
        or part.get("publicationAuthorized") is not False):
        raise ValueError("BSA276_SECOND_SIGNED_V36_MC_Q_PARTITION_REQUIRED")
    rows=part["activity"].get("evidenceRows",[])
    proofs=[]
    for opt,tid in _TASK_IDS.items():
        proof=independently_prove_si_unit_false_option(
            source_pdf=source,candidate_path=candidate,option_id=opt)
        independently_verify_si_option_witness(proof)
        found=[r for r in rows if r.get("taskId")==tid]
        if (len(found)!=1 or found[0].get("kind")!="MCQ_DISTRACTOR_SCIENCE"
            or found[0].get("status")!="BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED"
            or found[0].get("surfaceSha256")!=proof.get("surfaceSha256")
            or proof.get("taskId")!=tid
            or proof.get("optionId")!=opt
            or proof.get("sourceSha256")!=_SOURCE_SHA
            or proof.get("candidateSha256")!=_CANDIDATE_SHA
            or proof.get("newProviderCalls")!=0
            or proof.get("publicationAuthorized") is not False):
            raise ValueError("BSA276_ORIGINAL_SIGNED_FALSE_OPTION_NOT_INDEPENDENTLY_PROVEN")
        proofs.append({"optionId":opt,"taskId":tid,
                       "surfaceSha256":proof["surfaceSha256"],
                       "independentScienceProof":proof})
    if len(proofs)!=3 or len({p["taskId"] for p in proofs})!=3:
        raise ValueError("BSA276_THREE_DISTINCT_ADMISSIONS_REQUIRED")
    return v36,part,proofs


def _verify_receipt(
    *,private:Path,ready:dict[str,str],historical:bool
)->tuple[dict[str,Any],list[dict[str,Any]]]:
    v36,part,proofs=_current_v36_si_tasks(
        private=private,ready=ready,historical=historical)
    previous=_prior_three(private)
    receipt=_signed(_folder(private,ready),_RECEIPT,ready)
    audit=_signed(_folder(private,ready),_REGISTRY_RECEIPT,ready)
    if (audit.get("sourceBoundRegistryAudit",{}).get(
            "acceptedMcqDistractorTaskCount")!=2
        or audit.get("independentlyPreviouslyAcceptedAcademicTasks")!=2
        or receipt.get("signedRegistryAuditSha256")!=audit["integritySha256"]
        or receipt.get("status")!=_STATUS
        or receipt.get("sourceSha256")!=_SOURCE_SHA
        or receipt.get("candidateSha256")!=_CANDIDATE_SHA
        or receipt.get("signedV36Sha256")!=v36["integritySha256"]
        or receipt.get("secondSignedV36PartitionSha256")!=part["integritySha256"]
        or receipt.get("previousAcademicTaskIds")!=previous["acceptedAcademicTaskIds"]
        or receipt.get("previousBatchReceiptSha256")!=previous["batchReceiptSha256"]
        or receipt.get("newScientificProofs")!=proofs
        or receipt.get("independentlyAdmittedNewTaskCount")!=3
        or receipt.get("cumulativeAcceptedAcademicTasks")!=6
        or receipt.get("fullAcademicTasksStillOpen")!=423
        or receipt.get("completeAcademicProofGatesStillOpen")!=90
        or receipt.get("fullAcademicActivityPASS")!=0
        or receipt.get("newProviderCalls")!=0
        or receipt.get("publicationAuthorized") is not False):
        raise ValueError("BSA276_IMMUTABLE_SI_UNIT_BATCH_RECEIPT_INVALID")
    return receipt,proofs


def admit_si_unit_science_batch(*,private:Path)->dict[str,Any]:
    frontier=private/"long-horizon-development"/_FRONTIER
    if frontier.exists() or frontier.is_symlink():
        return verify_si_unit_batch_across_git_heads(private=private)
    previous=_prior_three(private)
    latest=read_long_horizon_development(private)
    now={"gitHead":latest["gitHead"],"proposalSha256":latest["proposalSha256"]}
    audit=verify_registry_audit(private=private)
    v36,part,proofs=_current_v36_si_tasks(
        private=private,ready=now,historical=False)
    if (audit["gitHead"]!=now["gitHead"]
        or audit["signedV36Sha256"]!=v36["integritySha256"]
        or audit["independentlyAcceptedAcademicTasks"]!=2
        or any(p["taskId"] in previous["acceptedAcademicTaskIds"] for p in proofs)):
        raise ValueError("BSA276_PREVIOUS_SIGNED_CHAIN_OR_NEW_TASKS_CHANGED")
    receipt=_v6_checkpoint(_folder(private,now)/_RECEIPT,{
        **now,
        "status":_STATUS,
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "signedV36Sha256":v36["integritySha256"],
        "secondSignedV36PartitionSha256":part["integritySha256"],
        "signedRegistryAuditSha256":audit["registryReceiptSha256"],
        "previousAcademicTaskIds":previous["acceptedAcademicTaskIds"],
        "previousBatchReceiptSha256":previous["batchReceiptSha256"],
        "newScientificProofs":proofs,
        "independentlyAdmittedNewTaskCount":3,
        "cumulativeAcceptedAcademicTasks":6,
        "fullAcademicTasksStillOpen":423,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    })
    verified,verified_proofs=_verify_receipt(
        private=private,ready=now,historical=False)
    if verified!=receipt or verified_proofs!=proofs:
        raise ValueError("BSA276_ADMISSION_PROOF_CHANGED_AFTER_SIGNING")
    _write_latest(frontier,{
        "status":_FRONTIER_STATUS,
        **now,
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "proofReceiptSha256":receipt["integritySha256"],
        "previousAcademicTaskIds":previous["acceptedAcademicTaskIds"],
        "newAcceptedTaskIds":[p["taskId"] for p in proofs],
        "acceptedAcademicTaskCount":6,
        "fullAcademicTasksStillOpen":423,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "publicationAuthorized":False,
    })
    return verify_si_unit_batch_across_git_heads(private=private)


@verified_stage_reuse
def verify_si_unit_batch_across_git_heads(*,private:Path)->dict[str,Any]:
    frontier=_read_signed(private/"long-horizon-development"/_FRONTIER)
    current=read_long_horizon_development(private)
    origin={"gitHead":frontier.get("gitHead"),
            "proposalSha256":frontier.get("proposalSha256")}
    now={"gitHead":current["gitHead"],
         "proposalSha256":current["proposalSha256"]}
    if (frontier.get("status")!=_FRONTIER_STATUS
        or frontier.get("sourceSha256")!=_SOURCE_SHA
        or frontier.get("candidateSha256")!=_CANDIDATE_SHA
        or current.get("sourceSha256")!=_SOURCE_SHA
        or current.get("candidateSha256")!=_CANDIDATE_SHA
        or frontier.get("acceptedAcademicTaskCount")!=6
        or frontier.get("fullAcademicTasksStillOpen")!=423
        or frontier.get("completeAcademicProofGatesStillOpen")!=90
        or frontier.get("fullAcademicActivityPASS")!=0
        or frontier.get("publicationAuthorized") is not False):
        raise ValueError("BSA276_SOURCE_BOUND_ACADEMIC_FRONTIER_UNTRUSTED")
    old,old_proofs=_verify_receipt(
        private=private,ready=origin,historical=origin!=now)
    _,_,new_proofs=_current_v36_si_tasks(
        private=private,ready=now,historical=False)
    previous=_prior_three(private)
    ids=[p["taskId"] for p in old_proofs]
    if (old_proofs!=new_proofs
        or old["integritySha256"]!=frontier.get("proofReceiptSha256")
        or old["previousBatchReceiptSha256"]!=previous["batchReceiptSha256"]
        or frontier.get("previousAcademicTaskIds")!=previous["acceptedAcademicTaskIds"]
        or frontier.get("newAcceptedTaskIds")!=ids
        or any(i in previous["acceptedAcademicTaskIds"] for i in ids)):
        raise ValueError("BSA276_CROSS_HEAD_SI_SCIENCE_PROOF_CHANGED")
    return {
        "status":"BSA276_THREE_NEW_SOURCE_BOUND_SI_SCIENCE_TASKS_REVERIFIED",
        "currentGitHead":now["gitHead"],
        "proofOriginGitHead":origin["gitHead"],
        "carriedAcrossGitHead":origin!=now,
        "acceptedAcademicTaskIds":[*previous["acceptedAcademicTaskIds"],*ids],
        "priorAcademicProofBatchSha256":previous["batchReceiptSha256"],
        "siUnitBatchReceiptSha256":old["integritySha256"],
        "newIndependentlyAcceptedAcademicTasks":3,
        "independentlyAcceptedAcademicTasks":6,
        "fullAcademicTasksStillOpen":423,
        "pendingMcqDistractorScienceTasks":21,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    }

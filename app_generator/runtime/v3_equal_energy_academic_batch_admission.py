"""BSA289 original Serway MCQ07 signed equal-energy science A19-A21.

Independently reopens original instructor-selected Serway source and frozen
tri-lingual candidate on EVERY admission/readback. Three distinct false
claims about equal kinetic energy and momentum ranking are disproven
by two exact rational mass, speed, energy and momentum models.
Chains strictly after signed academic A1-A18; no paper/source substitute,
no AI vote, fake full-activity PASS, provider replay or public release.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from app_generator.runtime.v3_first_academic_proof_admission import _bound_inputs
from app_generator.runtime.v3_long_horizon_development import (
    read_long_horizon_development,_write_latest,_read_signed,
)
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_equal_speed_academic_batch_admission import (
    verify_equal_speed_batch_across_git_heads,
)
from app_generator.runtime.v3_academic_proof_registry_receipt import (
    verify_registry_audit,_RECEIPT as _REGISTRY_RECEIPT,
)
from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA,_CANDIDATE_SHA,
)
from app_generator.validation.section91_equal_energy_false_options_proof import (
    independently_prove_equal_energy_false_option,
    independently_check_equal_energy_witness,
    _TASKS,
)

_RECEIPT="BOSLA_ACADEMIC_EQUAL_ENERGY_BATCH_A19_A21_V1.json"
_FRONTIER="BOSLA_ACADEMIC_EQUAL_ENERGY_BATCH_FRONTIER_V1.json"
_STATUS="BSA289_THREE_INDEPENDENT_EQUAL_ENERGY_MCQ_SCIENCE_TASKS_ADMITTED"
_FRONTIER_STATUS="BSA289_PRIVATE_THREE_NEW_EQUAL_ENERGY_SCIENCE_TASKS_ACCEPTED"


def _folder(private:Path,ready:dict[str,str])->Path:
    return private/"owner-five-stage-completion"/ready["gitHead"]/ready["proposalSha256"]


def _prior_eighteen(private:Path)->dict[str,Any]:
    old=verify_equal_speed_batch_across_git_heads(private=private)
    if (old.get("independentlyAcceptedAcademicTasks")!=18
        or old.get("fullAcademicTasksStillOpen")!=411
        or old.get("pendingMcqDistractorScienceTasks")!=9
        or len(set(old.get("acceptedAcademicTaskIds",[])))!=18
        or old.get("completeAcademicProofGatesStillOpen")!=90
        or old.get("fullAcademicActivityPASS")!=0
        or old.get("publicationAuthorized") is not False):
        raise ValueError("BSA289_SIGNED_ORIGINAL_A1_A18_CHAIN_REQUIRED")
    return old


def _original_equal_energy_proofs(
    *,private:Path,ready:dict[str,str],historical:bool,
)->tuple[dict[str,Any],dict[str,Any],list[dict[str,Any]]]:
    _,v36,_,source,candidate=_bound_inputs(
        private,ready,allow_historical=historical)
    signed=v36.get("signedPartitionHashes",[])
    if (len(signed)!=18
        or v36.get("semanticTasksAutomaticallyDispatched")!=429
        or v36.get("fullAcademicProofTasksAccepted")!=0
        or v36.get("completeAcademicProofGatesStillOpen")!=90
        or v36.get("sourceSha256")!=_SOURCE_SHA
        or v36.get("publicationAuthorized") is not False):
        raise ValueError("BSA289_EXACT_ORIGINAL_SOURCE_V36_REQUIRED")
    part=_signed(_folder(private,ready),"V36_PARTITION_07.json",ready)
    if (signed[6].get("activityId")!="act-mcq-07-equal-ke-momentum-relation"
        or signed[6].get("signedEvidenceSha256")!=part.get("integritySha256")
        or part.get("activity",{}).get("activityId")!=
            "act-mcq-07-equal-ke-momentum-relation"
        or part.get("sourceSha256")!=_SOURCE_SHA
        or part.get("candidateSha256")!=_CANDIDATE_SHA
        or part.get("academicPASS")!=0
        or part.get("publicationAuthorized") is not False):
        raise ValueError("BSA289_SEVENTH_SIGNED_ORIGINAL_V36_PARTITION_CHANGED")
    rows=part["activity"].get("evidenceRows",[])
    proofs=[]
    for option_id,task_id in _TASKS.items():
        proof=independently_prove_equal_energy_false_option(
            source_pdf=source,candidate_path=candidate,option_id=option_id)
        independently_check_equal_energy_witness(proof)
        hits=[row for row in rows if row.get("taskId")==task_id]
        if (len(hits)!=1 or hits[0].get("kind")!="MCQ_DISTRACTOR_SCIENCE"
            or hits[0].get("status")!="BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED"
            or hits[0].get("surfaceSha256")!=proof["surfaceSha256"]
            or proof.get("taskId")!=task_id
            or proof.get("optionId")!=option_id
            or proof.get("sourceSha256")!=_SOURCE_SHA
            or proof.get("candidateSha256")!=_CANDIDATE_SHA
            or proof.get("newProviderCalls")!=0
            or proof.get("publicationAuthorized") is not False):
            raise ValueError("BSA289_EQUAL_ENERGY_FALSE_OPTION_NOT_REPROVEN")
        proofs.append({
            "optionId":option_id,
            "taskId":task_id,
            "surfaceSha256":proof["surfaceSha256"],
            "independentScienceProof":proof,
        })
    if (len(proofs)!=3 or len({p["taskId"] for p in proofs})!=3):
        raise ValueError("BSA289_THREE_DISTINCT_MCQ07_SCIENCE_TASKS_REQUIRED")
    return v36,part,proofs


def _verify_receipt(
    *,private:Path,ready:dict[str,str],historical:bool,
)->tuple[dict[str,Any],list[dict[str,Any]]]:
    v36,part,proofs=_original_equal_energy_proofs(
        private=private,ready=ready,historical=historical)
    old=_prior_eighteen(private)
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
        or receipt.get("seventhSignedV36PartitionSha256")!=part["integritySha256"]
        or receipt.get("previousAcademicTaskIds")!=old[
            "acceptedAcademicTaskIds"]
        or receipt.get("previousEqualSpeedBatchReceiptSha256")!=old[
            "equalSpeedBatchReceiptSha256"]
        or receipt.get("newScientificProofs")!=proofs
        or receipt.get("newIndependentlyAdmittedAcademicTasks")!=3
        or receipt.get("totalAcademicTaskAcceptances")!=21
        or receipt.get("fullAcademicTasksStillOpen")!=408
        or receipt.get("pendingMcqDistractorScienceTasks")!=6
        or receipt.get("completeAcademicProofGatesStillOpen")!=90
        or receipt.get("fullAcademicActivityPASS")!=0
        or receipt.get("newProviderCalls")!=0
        or receipt.get("publicationAuthorized") is not False):
        raise ValueError("BSA289_ORIGINAL_EQUAL_ENERGY_IMMUTABLE_RECEIPT_CHANGED")
    return receipt,proofs


def admit_equal_energy_batch(*,private:Path)->dict[str,Any]:
    frontier=private/"long-horizon-development"/_FRONTIER
    if frontier.exists() or frontier.is_symlink():
        return verify_equal_energy_batch_across_git_heads(private=private)
    prev=_prior_eighteen(private)
    latest=read_long_horizon_development(private)
    now={"gitHead":latest["gitHead"],"proposalSha256":latest["proposalSha256"]}
    audit=verify_registry_audit(private=private)
    v36,part,proofs=_original_equal_energy_proofs(
        private=private,ready=now,historical=False)
    if (audit.get("gitHead")!=now["gitHead"]
        or audit.get("signedV36Sha256")!=v36["integritySha256"]
        or audit.get("independentlyAcceptedAcademicTasks")!=2
        or any(p["taskId"] in prev["acceptedAcademicTaskIds"] for p in proofs)):
        raise ValueError("BSA289_A1_A18_CHAIN_OR_TASK_DUPLICATE")
    receipt=_v6_checkpoint(_folder(private,now)/_RECEIPT,{
        **now,
        "status":_STATUS,
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "signedV36Sha256":v36["integritySha256"],
        "seventhSignedV36PartitionSha256":part["integritySha256"],
        "signedRegistryAuditSha256":audit["registryReceiptSha256"],
        "previousAcademicTaskIds":prev["acceptedAcademicTaskIds"],
        "previousEqualSpeedBatchReceiptSha256":prev["equalSpeedBatchReceiptSha256"],
        "newScientificProofs":proofs,
        "newIndependentlyAdmittedAcademicTasks":3,
        "totalAcademicTaskAcceptances":21,
        "fullAcademicTasksStillOpen":408,
        "pendingMcqDistractorScienceTasks":6,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    })
    old,proofs_check=_verify_receipt(
        private=private,ready=now,historical=False)
    if old!=receipt or proofs_check!=proofs:
        raise ValueError("BSA289_EQUAL_ENERGY_CHANGED_BEFORE_ADMISSION")
    _write_latest(frontier,{
        **now,
        "status":_FRONTIER_STATUS,
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "newScientificBatchReceiptSha256":receipt["integritySha256"],
        "previousAcademicTaskIds":prev["acceptedAcademicTaskIds"],
        "newAcceptedTaskIds":[p["taskId"] for p in proofs],
        "cumulativeAcademicTasksAccepted":21,
        "fullAcademicTasksStillOpen":408,
        "pendingMcqDistractorScienceTasks":6,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "publicationAuthorized":False,
    })
    return verify_equal_energy_batch_across_git_heads(private=private)


def verify_equal_energy_batch_across_git_heads(*,private:Path)->dict[str,Any]:
    frontier=_read_signed(private/"long-horizon-development"/_FRONTIER)
    now_ck=read_long_horizon_development(private)
    origin={"gitHead":frontier.get("gitHead"),
            "proposalSha256":frontier.get("proposalSha256")}
    now={"gitHead":now_ck["gitHead"],
         "proposalSha256":now_ck["proposalSha256"]}
    if (frontier.get("status")!=_FRONTIER_STATUS
        or frontier.get("sourceSha256")!=_SOURCE_SHA
        or frontier.get("candidateSha256")!=_CANDIDATE_SHA
        or now_ck.get("sourceSha256")!=_SOURCE_SHA
        or now_ck.get("candidateSha256")!=_CANDIDATE_SHA
        or frontier.get("cumulativeAcademicTasksAccepted")!=21
        or frontier.get("fullAcademicTasksStillOpen")!=408
        or frontier.get("pendingMcqDistractorScienceTasks")!=6
        or frontier.get("completeAcademicProofGatesStillOpen")!=90
        or frontier.get("fullAcademicActivityPASS")!=0
        or frontier.get("publicationAuthorized") is not False):
        raise ValueError("BSA289_HISTORICAL_EQUAL_ENERGY_FRONTIER_UNVERIFIED")
    receipt,proofs=_verify_receipt(
        private=private,ready=origin,historical=origin!=now)
    _,_,recomputed=_original_equal_energy_proofs(
        private=private,ready=now,historical=False)
    prior=_prior_eighteen(private)
    ids=[p["taskId"] for p in proofs]
    if (proofs!=recomputed
        or receipt["integritySha256"]!=frontier.get(
            "newScientificBatchReceiptSha256")
        or receipt["previousEqualSpeedBatchReceiptSha256"]!=
            prior["equalSpeedBatchReceiptSha256"]
        or frontier.get("previousAcademicTaskIds")!=
            prior["acceptedAcademicTaskIds"]
        or frontier.get("newAcceptedTaskIds")!=ids
        or any(i in prior["acceptedAcademicTaskIds"] for i in ids)):
        raise ValueError("BSA289_EQUAL_ENERGY_SCIENCE_CHANGED_ACROSS_CODE_HEADS")
    return {
        "status":"BSA289_THREE_EQUAL_ENERGY_SCIENCE_TASKS_GENUINELY_REVERIFIED",
        "currentGitHead":now["gitHead"],
        "batchProofOriginGitHead":origin["gitHead"],
        "carriedAcrossGitHead":origin!=now,
        "acceptedAcademicTaskIds":[*prior["acceptedAcademicTaskIds"],*ids],
        "previousEqualSpeedBatchReceiptSha256":prior["equalSpeedBatchReceiptSha256"],
        "equalSpeedBatchReceiptSha256":receipt["integritySha256"],
        "newIndependentlyAcceptedAcademicTasks":3,
        "independentlyAcceptedAcademicTasks":21,
        "fullAcademicTasksStillOpen":408,
        "pendingMcqDistractorScienceTasks":6,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    }

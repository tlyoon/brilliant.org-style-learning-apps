"""BSA290 original Serway MCQ08 signed isolated-pair science A22-A24.

Independently reopens original instructor-selected Serway source and frozen
tri-lingual candidate on EVERY admission/readback. Three distinct false
claims about individual momentum and mutual forces are disproven
by two exact rational impulse, force and momentum models.
Chains strictly after signed academic A1-A21; no paper/source substitute,
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
from app_generator.runtime.v3_equal_energy_academic_batch_admission import (
    verify_equal_energy_batch_across_git_heads,
)
from app_generator.runtime.v3_academic_proof_registry_receipt import (
    verify_registry_audit,_RECEIPT as _REGISTRY_RECEIPT,
)
from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA,_CANDIDATE_SHA,
)
from app_generator.validation.section91_isolated_pair_false_options_proof import (
    independently_prove_isolated_pair_false_option,
    independently_check_isolated_pair_witness,
    _OPTIONS_ORDER,
)

_RECEIPT="BOSLA_ACADEMIC_ISOLATED_PAIR_BATCH_A22_A24_V1.json"
_FRONTIER="BOSLA_ACADEMIC_ISOLATED_PAIR_BATCH_FRONTIER_V1.json"
_STATUS="BSA290_THREE_INDEPENDENT_ISOLATED_PAIR_MCQ_SCIENCE_TASKS_ADMITTED"
_FRONTIER_STATUS="BSA290_PRIVATE_THREE_NEW_ISOLATED_PAIR_SCIENCE_TASKS_ACCEPTED"


def _folder(private:Path,ready:dict[str,str])->Path:
    return private/"owner-five-stage-completion"/ready["gitHead"]/ready["proposalSha256"]


def _prior_twenty_one(private:Path)->dict[str,Any]:
    old=verify_equal_energy_batch_across_git_heads(private=private)
    if (old.get("independentlyAcceptedAcademicTasks")!=21
        or old.get("fullAcademicTasksStillOpen")!=408
        or old.get("pendingMcqDistractorScienceTasks")!=6
        or len(set(old.get("acceptedAcademicTaskIds",[])))!=21
        or old.get("completeAcademicProofGatesStillOpen")!=90
        or old.get("fullAcademicActivityPASS")!=0
        or old.get("publicationAuthorized") is not False):
        raise ValueError("BSA290_SIGNED_ORIGINAL_A1_A21_CHAIN_REQUIRED")
    return old


def _original_isolated_pair_proofs(
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
        raise ValueError("BSA290_EXACT_ORIGINAL_SOURCE_V36_REQUIRED")
    part=_signed(_folder(private,ready),"V36_PARTITION_08.json",ready)
    if (signed[7].get("activityId")!="act-mcq-08-isolated-subsystem-fallacy"
        or signed[7].get("signedEvidenceSha256")!=part.get("integritySha256")
        or part.get("activity",{}).get("activityId")!=
            "act-mcq-08-isolated-subsystem-fallacy"
        or part.get("sourceSha256")!=_SOURCE_SHA
        or part.get("candidateSha256")!=_CANDIDATE_SHA
        or part.get("academicPASS")!=0
        or part.get("publicationAuthorized") is not False):
        raise ValueError("BSA290_EIGHTH_SIGNED_ORIGINAL_V36_PARTITION_CHANGED")
    rows=part["activity"].get("evidenceRows",[])
    proofs=[]
    for option_id in _OPTIONS_ORDER:
        proof=independently_prove_isolated_pair_false_option(
            source_pdf=source,candidate_path=candidate,option_id=option_id)
        independently_check_isolated_pair_witness(proof)
        task_id=proof["taskId"]
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
            raise ValueError("BSA290_ISOLATED_PAIR_FALSE_OPTION_NOT_REPROVEN")
        proofs.append({
            "optionId":option_id,
            "taskId":task_id,
            "surfaceSha256":proof["surfaceSha256"],
            "independentScienceProof":proof,
        })
    if (len(proofs)!=3 or len({p["taskId"] for p in proofs})!=3):
        raise ValueError("BSA290_THREE_DISTINCT_MCQ08_SCIENCE_TASKS_REQUIRED")
    return v36,part,proofs


def _verify_receipt(
    *,private:Path,ready:dict[str,str],historical:bool,
)->tuple[dict[str,Any],list[dict[str,Any]]]:
    v36,part,proofs=_original_isolated_pair_proofs(
        private=private,ready=ready,historical=historical)
    old=_prior_twenty_one(private)
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
        or receipt.get("eighthSignedV36PartitionSha256")!=part["integritySha256"]
        or receipt.get("previousAcademicTaskIds")!=old[
            "acceptedAcademicTaskIds"]
        or receipt.get("previousEqualEnergyBatchReceiptSha256")!=old[
            "equalEnergyBatchReceiptSha256"]
        or receipt.get("newScientificProofs")!=proofs
        or receipt.get("newIndependentlyAdmittedAcademicTasks")!=3
        or receipt.get("totalAcademicTaskAcceptances")!=24
        or receipt.get("fullAcademicTasksStillOpen")!=405
        or receipt.get("pendingMcqDistractorScienceTasks")!=3
        or receipt.get("completeAcademicProofGatesStillOpen")!=90
        or receipt.get("fullAcademicActivityPASS")!=0
        or receipt.get("newProviderCalls")!=0
        or receipt.get("publicationAuthorized") is not False):
        raise ValueError("BSA290_ORIGINAL_ISOLATED_PAIR_IMMUTABLE_RECEIPT_CHANGED")
    return receipt,proofs


def admit_isolated_pair_batch(*,private:Path)->dict[str,Any]:
    frontier=private/"long-horizon-development"/_FRONTIER
    if frontier.exists() or frontier.is_symlink():
        return verify_isolated_pair_batch_across_git_heads(private=private)
    prev=_prior_twenty_one(private)
    latest=read_long_horizon_development(private)
    now={"gitHead":latest["gitHead"],"proposalSha256":latest["proposalSha256"]}
    audit=verify_registry_audit(private=private)
    v36,part,proofs=_original_isolated_pair_proofs(
        private=private,ready=now,historical=False)
    if (audit.get("gitHead")!=now["gitHead"]
        or audit.get("signedV36Sha256")!=v36["integritySha256"]
        or audit.get("independentlyAcceptedAcademicTasks")!=2
        or any(p["taskId"] in prev["acceptedAcademicTaskIds"] for p in proofs)):
        raise ValueError("BSA290_A1_A21_CHAIN_OR_TASK_DUPLICATE")
    receipt=_v6_checkpoint(_folder(private,now)/_RECEIPT,{
        **now,
        "status":_STATUS,
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "signedV36Sha256":v36["integritySha256"],
        "eighthSignedV36PartitionSha256":part["integritySha256"],
        "signedRegistryAuditSha256":audit["registryReceiptSha256"],
        "previousAcademicTaskIds":prev["acceptedAcademicTaskIds"],
        "previousEqualEnergyBatchReceiptSha256":prev["equalEnergyBatchReceiptSha256"],
        "newScientificProofs":proofs,
        "newIndependentlyAdmittedAcademicTasks":3,
        "totalAcademicTaskAcceptances":24,
        "fullAcademicTasksStillOpen":405,
        "pendingMcqDistractorScienceTasks":3,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    })
    old,proofs_check=_verify_receipt(
        private=private,ready=now,historical=False)
    if old!=receipt or proofs_check!=proofs:
        raise ValueError("BSA290_ISOLATED_PAIR_CHANGED_BEFORE_ADMISSION")
    _write_latest(frontier,{
        **now,
        "status":_FRONTIER_STATUS,
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "newScientificBatchReceiptSha256":receipt["integritySha256"],
        "previousAcademicTaskIds":prev["acceptedAcademicTaskIds"],
        "newAcceptedTaskIds":[p["taskId"] for p in proofs],
        "cumulativeAcademicTasksAccepted":24,
        "fullAcademicTasksStillOpen":405,
        "pendingMcqDistractorScienceTasks":3,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "publicationAuthorized":False,
    })
    return verify_isolated_pair_batch_across_git_heads(private=private)


def verify_isolated_pair_batch_across_git_heads(*,private:Path)->dict[str,Any]:
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
        or frontier.get("cumulativeAcademicTasksAccepted")!=24
        or frontier.get("fullAcademicTasksStillOpen")!=405
        or frontier.get("pendingMcqDistractorScienceTasks")!=3
        or frontier.get("completeAcademicProofGatesStillOpen")!=90
        or frontier.get("fullAcademicActivityPASS")!=0
        or frontier.get("publicationAuthorized") is not False):
        raise ValueError("BSA290_HISTORICAL_ISOLATED_PAIR_FRONTIER_UNVERIFIED")
    receipt,proofs=_verify_receipt(
        private=private,ready=origin,historical=origin!=now)
    _,_,recomputed=_original_isolated_pair_proofs(
        private=private,ready=now,historical=False)
    prior=_prior_twenty_one(private)
    ids=[p["taskId"] for p in proofs]
    if (proofs!=recomputed
        or receipt["integritySha256"]!=frontier.get(
            "newScientificBatchReceiptSha256")
        or receipt["previousEqualEnergyBatchReceiptSha256"]!=
            prior["equalEnergyBatchReceiptSha256"]
        or frontier.get("previousAcademicTaskIds")!=
            prior["acceptedAcademicTaskIds"]
        or frontier.get("newAcceptedTaskIds")!=ids
        or any(i in prior["acceptedAcademicTaskIds"] for i in ids)):
        raise ValueError("BSA290_ISOLATED_PAIR_SCIENCE_CHANGED_ACROSS_CODE_HEADS")
    return {
        "status":"BSA290_THREE_ISOLATED_PAIR_SCIENCE_TASKS_GENUINELY_REVERIFIED",
        "currentGitHead":now["gitHead"],
        "batchProofOriginGitHead":origin["gitHead"],
        "carriedAcrossGitHead":origin!=now,
        "acceptedAcademicTaskIds":[*prior["acceptedAcademicTaskIds"],*ids],
        "previousEqualEnergyBatchReceiptSha256":prior["equalEnergyBatchReceiptSha256"],
        # The A25-A27 admission and horizon consume this verified A22-A24
        # receipt. Keep the historical alias for existing readback callers.
        "isolatedPairBatchReceiptSha256":receipt["integritySha256"],
        "equalEnergyBatchReceiptSha256":receipt["integritySha256"],
        "newIndependentlyAcceptedAcademicTasks":3,
        "independentlyAcceptedAcademicTasks":24,
        "fullAcademicTasksStillOpen":405,
        "pendingMcqDistractorScienceTasks":3,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    }

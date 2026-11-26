"""BSA277: immutable academic A7–A9 Newton momentum-rate batch readback.

A separate original-source scientific acceptance chained AFTER all signed
A1–A6 receipts. The original selected Serway PDF, frozen candidate, signed
V36 third MCQ partition, complete original EN/MS/ZH claims and two exact
rational Newton countermodels are independently reopened on *every* read.
No inherited full scientific explanation/translation/diagram activity PASS,
outside textbooks, paid model replay, or public merge.
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
from app_generator.runtime.v3_si_units_academic_batch_admission import (
    verify_si_unit_batch_across_git_heads,
)
from app_generator.runtime.v3_academic_proof_registry_receipt import (
    verify_registry_audit,_RECEIPT as _REGISTRY_RECEIPT,
)
from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA,_CANDIDATE_SHA,
)
from app_generator.validation.section91_newton_force_false_options_proof import (
    independently_prove_newton_false_option,
    independently_verify_newton_force_witness,
)

_RECEIPT="BOSLA_ACADEMIC_NEWTON_FORCE_BATCH_A7_A9_V1.json"
_FRONTIER="BOSLA_ACADEMIC_NEWTON_FORCE_BATCH_FRONTIER_V1.json"
_STATUS="BSA277_THREE_NEWTON_RATE_MISCONCEPTIONS_INDEPENDENTLY_ADMITTED"
_FRONTIER_STATUS="BSA277_PRIVATE_THREE_NEW_SOURCE_BOUND_SCIENCE_TASKS_ACCEPTED"
_TASK_IDS={
    "opt-b":"61903ef3db056f69b6808a8b1d4d08fca54ab758ff2adc3552e1453d351d0ec2",
    "opt-c":"ceb21a8d70a3628ffc63a51e470d537ab9911c219764b2d9579f2f455edb05ac",
    "opt-d":"4996f79a1c653220324859f11465d8177e595449d5e5cadb84800cad753f12ae",
}


def _folder(private:Path,ready:dict[str,str])->Path:
    return private/"owner-five-stage-completion"/ready["gitHead"]/ready["proposalSha256"]


def _prior_six(private:Path)->dict[str,Any]:
    previous=verify_si_unit_batch_across_git_heads(private=private)
    if (previous.get("independentlyAcceptedAcademicTasks")!=6
        or previous.get("fullAcademicTasksStillOpen")!=423
        or len(set(previous.get("acceptedAcademicTaskIds",[])))!=6
        or previous.get("completeAcademicProofGatesStillOpen")!=90
        or previous.get("fullAcademicActivityPASS")!=0
        or previous.get("publicationAuthorized") is not False):
        raise ValueError("BSA277_A1_A6_SIGNED_ORIGINAL_SOURCE_ACCEPTANCES_REQUIRED")
    return previous


def _recomputed_original_newton_proofs(
    *,private:Path,ready:dict[str,str],historical:bool,
)->tuple[dict[str,Any],dict[str,Any],list[dict[str,Any]]]:
    _,v36,_,source,candidate=_bound_inputs(
        private,ready,allow_historical=historical)
    signed=v36.get("signedPartitionHashes",[])
    if (len(signed)!=18 or v36.get("semanticTasksAutomaticallyDispatched")!=429
        or v36.get("fullAcademicProofTasksAccepted")!=0
        or v36.get("completeAcademicProofGatesStillOpen")!=90
        or v36.get("sourceSha256")!=_SOURCE_SHA
        or v36.get("publicationAuthorized") is not False):
        raise ValueError("BSA277_ORIGINAL_SELECTED_TEXTBOOK_V36_REQUIRED")
    part=_signed(_folder(private,ready),"V36_PARTITION_03.json",ready)
    if (signed[2].get("activityId")!="act-mcq-03-net-force-definition"
        or signed[2].get("signedEvidenceSha256")!=part.get("integritySha256")
        or part.get("activity",{}).get("activityId")!=
            "act-mcq-03-net-force-definition"
        or part.get("sourceSha256")!=_SOURCE_SHA
        or part.get("candidateSha256")!=_CANDIDATE_SHA
        or part.get("academicPASS")!=0
        or part.get("publicationAuthorized") is not False):
        raise ValueError("BSA277_THIRD_SIGNED_V36_PARTITION_CHANGED")
    rows=part["activity"].get("evidenceRows",[])
    proofs=[]
    for opt,tid in _TASK_IDS.items():
        proof=independently_prove_newton_false_option(
            source_pdf=source,candidate_path=candidate,option_id=opt)
        independently_verify_newton_force_witness(proof)
        matching=[r for r in rows if r.get("taskId")==tid]
        if (len(matching)!=1 or matching[0].get("kind")!="MCQ_DISTRACTOR_SCIENCE"
            or matching[0].get("status")!="BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED"
            or matching[0].get("surfaceSha256")!=proof.get("surfaceSha256")
            or proof.get("taskId")!=tid
            or proof.get("optionId")!=opt
            or proof.get("sourceSha256")!=_SOURCE_SHA
            or proof.get("candidateSha256")!=_CANDIDATE_SHA
            or proof.get("newProviderCalls")!=0
            or proof.get("publicationAuthorized") is not False):
            raise ValueError("BSA277_ORIGINAL_MC_Q_FALSE_PROPOSITION_NOT_REVERIFIED")
        proofs.append({"optionId":opt,"taskId":tid,
                       "surfaceSha256":proof["surfaceSha256"],
                       "independentScienceProof":proof})
    if len(proofs)!=3 or len({p["taskId"] for p in proofs})!=3:
        raise ValueError("BSA277_THREE_INDEPENDENT_NEWTON_TASKS_REQUIRED")
    return v36,part,proofs


def _verify_immutable_receipt(
    *,private:Path,ready:dict[str,str],historical:bool
)->tuple[dict[str,Any],list[dict[str,Any]]]:
    v36,part,proofs=_recomputed_original_newton_proofs(
        private=private,ready=ready,historical=historical)
    previous=_prior_six(private)
    receipt=_signed(_folder(private,ready),_RECEIPT,ready)
    old_audit=_signed(_folder(private,ready),_REGISTRY_RECEIPT,ready)
    if (old_audit.get("sourceBoundRegistryAudit",{}).get(
            "acceptedMcqDistractorTaskCount")!=2
        or old_audit.get("independentlyPreviouslyAcceptedAcademicTasks")!=2
        or receipt.get("signedRegistryAuditSha256")!=old_audit["integritySha256"]
        or receipt.get("status")!=_STATUS
        or receipt.get("sourceSha256")!=_SOURCE_SHA
        or receipt.get("candidateSha256")!=_CANDIDATE_SHA
        or receipt.get("signedV36Sha256")!=v36["integritySha256"]
        or receipt.get("thirdSignedV36PartitionSha256")!=part["integritySha256"]
        or receipt.get("previousAcademicTaskIds")!=previous["acceptedAcademicTaskIds"]
        or receipt.get("previousSIUnitBatchReceiptSha256")!=previous[
            "siUnitBatchReceiptSha256"]
        or receipt.get("newScientificProofs")!=proofs
        or receipt.get("newIndependentlyAdmittedAcademicTasks")!=3
        or receipt.get("totalAcademicTaskAcceptances")!=9
        or receipt.get("fullAcademicTasksStillOpen")!=420
        or receipt.get("completeAcademicProofGatesStillOpen")!=90
        or receipt.get("fullAcademicActivityPASS")!=0
        or receipt.get("newProviderCalls")!=0
        or receipt.get("publicationAuthorized") is not False):
        raise ValueError("BSA277_NEWTON_BATCH_IMMUTABLE_RECEIPT_CHANGED")
    return receipt,proofs


def admit_newton_source_bound_batch(*,private:Path)->dict[str,Any]:
    frontier=private/"long-horizon-development"/_FRONTIER
    if frontier.exists() or frontier.is_symlink():
        return verify_newton_batch_across_git_heads(private=private)
    previous=_prior_six(private)
    latest=read_long_horizon_development(private)
    now={"gitHead":latest["gitHead"],"proposalSha256":latest["proposalSha256"]}
    audit=verify_registry_audit(private=private)
    v36,part,proofs=_recomputed_original_newton_proofs(
        private=private,ready=now,historical=False)
    if (audit["gitHead"]!=now["gitHead"]
        or audit["signedV36Sha256"]!=v36["integritySha256"]
        or audit["independentlyAcceptedAcademicTasks"]!=2
        or any(p["taskId"] in previous["acceptedAcademicTaskIds"] for p in proofs)):
        raise ValueError("BSA277_SIGNED_A1_A6_CHAIN_OR_NEW_TASK_DUPLICATE")
    receipt=_v6_checkpoint(_folder(private,now)/_RECEIPT,{
        **now,
        "status":_STATUS,
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "signedV36Sha256":v36["integritySha256"],
        "thirdSignedV36PartitionSha256":part["integritySha256"],
        "signedRegistryAuditSha256":audit["registryReceiptSha256"],
        "previousAcademicTaskIds":previous["acceptedAcademicTaskIds"],
        "previousSIUnitBatchReceiptSha256":previous["siUnitBatchReceiptSha256"],
        "newScientificProofs":proofs,
        "newIndependentlyAdmittedAcademicTasks":3,
        "totalAcademicTaskAcceptances":9,
        "fullAcademicTasksStillOpen":420,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    })
    old,verified_proofs=_verify_immutable_receipt(
        private=private,ready=now,historical=False)
    if old!=receipt or verified_proofs!=proofs:
        raise ValueError("BSA277_ORIGINAL_SCIENCE_CHANGED_BEFORE_FRONTIER")
    _write_latest(frontier,{
        **now,
        "status":_FRONTIER_STATUS,
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "newScientificBatchReceiptSha256":receipt["integritySha256"],
        "previousAcademicTaskIds":previous["acceptedAcademicTaskIds"],
        "newAcceptedTaskIds":[p["taskId"] for p in proofs],
        "cumulativeAcademicTasksAccepted":9,
        "fullAcademicTasksStillOpen":420,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "publicationAuthorized":False,
    })
    return verify_newton_batch_across_git_heads(private=private)


def verify_newton_batch_across_git_heads(*,private:Path)->dict[str,Any]:
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
        or frontier.get("cumulativeAcademicTasksAccepted")!=9
        or frontier.get("fullAcademicTasksStillOpen")!=420
        or frontier.get("completeAcademicProofGatesStillOpen")!=90
        or frontier.get("fullAcademicActivityPASS")!=0
        or frontier.get("publicationAuthorized") is not False):
        raise ValueError("BSA277_HISTORICAL_NEWTON_FRONTIER_UNVERIFIED")
    old,proofs=_verify_immutable_receipt(
        private=private,ready=origin,historical=origin!=now)
    _,_,new_proofs=_recomputed_original_newton_proofs(
        private=private,ready=now,historical=False)
    previous=_prior_six(private)
    ids=[p["taskId"] for p in proofs]
    if (proofs!=new_proofs
        or old["integritySha256"]!=frontier.get("newScientificBatchReceiptSha256")
        or old["previousSIUnitBatchReceiptSha256"]!=previous[
            "siUnitBatchReceiptSha256"]
        or frontier.get("previousAcademicTaskIds")!=previous["acceptedAcademicTaskIds"]
        or frontier.get("newAcceptedTaskIds")!=ids
        or any(i in previous["acceptedAcademicTaskIds"] for i in ids)):
        raise ValueError("BSA277_NEWTON_SCIENCE_CHANGED_ACROSS_CODE_HEADS")
    return {
        "status":"BSA277_THREE_NEWTON_MOMENTUM_RATE_TASKS_GENUINELY_REVERIFIED",
        "currentGitHead":now["gitHead"],
        "batchProofOriginGitHead":origin["gitHead"],
        "carriedAcrossGitHead":origin!=now,
        "acceptedAcademicTaskIds":[*previous["acceptedAcademicTaskIds"],*ids],
        "previousSIUnitBatchReceiptSha256":previous["siUnitBatchReceiptSha256"],
        "newtonBatchReceiptSha256":old["integritySha256"],
        "newIndependentlyAcceptedAcademicTasks":3,
        "independentlyAcceptedAcademicTasks":9,
        "fullAcademicTasksStillOpen":420,
        "pendingMcqDistractorScienceTasks":18,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    }

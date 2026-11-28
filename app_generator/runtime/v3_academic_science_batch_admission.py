"""BSA275 generic multi-rule, immutable source-bound academic batch admission.

Every registered new science rule MUST independently re-open the selected
original textbook and frozen candidate, prove the exact false alternative,
pass a separate arithmetic/meaning verifier, match the signed current AND
historic V36 task identity, and persist one owner-private immutable receipt.
No queued/bounded science witness becomes an academic task until this separate
admission and independent readback both PASS. Old A1/A2 remain unchanged.
New reviewed science handlers register without editing this dispatcher.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
from typing import Any, Callable

from app_generator.runtime.v3_guarded_signed_science_reuse import verified_stage_reuse
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_long_horizon_development import (
    read_long_horizon_development,_write_latest,_read_signed,
)
from app_generator.runtime.v3_first_academic_proof_admission import (
    _bound_inputs,
)
from app_generator.runtime.v3_second_academic_proof_admission import (
    verify_second_academic_across_git_heads,
)
from app_generator.runtime.v3_academic_proof_registry import (
    audit_source_bound_academic_registry,
)
from app_generator.runtime.v3_academic_proof_registry_receipt import (
    verify_registry_audit,_RECEIPT as _REGISTRY_RECEIPT,
)
from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA,_CANDIDATE_SHA,
)
from app_generator.validation.section91_vector_orientation_proof import (
    verify_perpendicular_momentum_false,
    independently_recheck_vector_witness,
)
from app_generator.validation.full_semantic_proof_queue import (
    plan_full_semantic_proofs,
)

_SHA64=re.compile(r"[0-9a-f]{64}\Z")
_SHA40=re.compile(r"[0-9a-f]{40}\Z")
_ID="7ac21032ea48b7f27fad782d44b615982eff47ea93a52f1c02ff334e91f937d5"
_RECEIPT="BOSLA_ACADEMIC_SCIENCE_BATCH_A3_V1.json"
_FRONTIER="BOSLA_ACADEMIC_SCIENCE_BATCH_FRONTIER_V1.json"
_STATUS="BSA275_SEPARATE_ORIGINAL_SOURCE_SCIENCE_TASKS_GENUINELY_ADMITTED"
_FRONTIER_STATUS="BSA275_PRIVATE_IMMUTABLE_NEW_ACADEMIC_TASK_FRONTIER"


@dataclass(frozen=True)
class ScienceAdmissionHandler:
    science_family: str
    task_id: str
    produce: Callable[[Path,Path],dict[str,Any]]
    independent_verify: Callable[[dict[str,Any]],None]


class ScienceAdmissionRegistry:
    """Only reviewed executable verifier functions; never data-driven exec."""
    def __init__(self)->None:
        self._by_id:dict[str,ScienceAdmissionHandler]={}
    def register(self,handler:ScienceAdmissionHandler)->None:
        if (not isinstance(handler,ScienceAdmissionHandler)
            or not isinstance(handler.science_family,str)
            or not re.fullmatch(r"[A-Z][A-Z0-9_]{7,100}",
                                handler.science_family)
            or not isinstance(handler.task_id,str)
            or not _SHA64.fullmatch(handler.task_id)
            or handler.task_id in self._by_id
            or len(self._by_id)>=6
            or not callable(handler.produce)
            or not callable(handler.independent_verify)):
            raise ValueError("BSA275_DUPLICATE_OR_UNTRUSTED_ADMISSION_HANDLER")
        self._by_id[handler.task_id]=handler
    def handlers(self)->tuple[ScienceAdmissionHandler,...]:
        return tuple(self._by_id[k] for k in sorted(self._by_id))


def approved_science_batch_rules()->ScienceAdmissionRegistry:
    registry=ScienceAdmissionRegistry()
    registry.register(ScienceAdmissionHandler(
        "VECTOR_ORIENTATION_NOT_PERPENDICULAR",
        _ID,
        lambda source,candidate: verify_perpendicular_momentum_false(
            source_pdf=source,candidate_path=candidate),
        independently_recheck_vector_witness,
    ))
    return registry


def _folder(private:Path,ready:dict[str,str])->Path:
    return private/"owner-five-stage-completion"/ready["gitHead"]/ready["proposalSha256"]


def _proofs_for_signed_v36(
    *,private:Path,ready:dict[str,str],historical:bool,
    rules:ScienceAdmissionRegistry,
)->tuple[dict[str,Any],dict[str,Any],list[dict[str,Any]]]:
    folder,v36,first,pdf,candidate=_bound_inputs(
        private,ready,allow_historical=historical)
    if (v36.get("completeAcademicProofGatesStillOpen")!=90
        or v36.get("semanticTasksAutomaticallyDispatched")!=429
        or v36.get("fullAcademicProofTasksAccepted")!=0
        or v36.get("publicationAuthorized") is not False
        or first.get("sourceSha256")!=_SOURCE_SHA
        or first.get("candidateSha256")!=_CANDIDATE_SHA):
        raise ValueError("BSA275_SIGNED_ORIGINAL_V36_PREDECESSOR_REQUIRED")
    # The registered proof must match one unique, still REVIEW_REQUIRED row
    # from the signed V36. Exact original-language and physics source evidence
    # is reverified separately in each handler, not a checked string cue.
    signed_rows=first.get("activity",{}).get("evidenceRows",[])
    proofs=[]
    for handler in rules.handlers():
        proof=handler.produce(pdf,candidate)
        handler.independent_verify(proof)
        rows=[r for r in signed_rows if r.get("taskId")==handler.task_id]
        if (len(rows)!=1
            or rows[0].get("kind")!="MCQ_DISTRACTOR_SCIENCE"
            or rows[0].get("status")!="BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED"
            or rows[0].get("surfaceSha256")!=proof.get("surfaceSha256")
            or proof.get("taskId")!=handler.task_id
            or proof.get("sourceSha256")!=_SOURCE_SHA
            or proof.get("candidateSha256")!=_CANDIDATE_SHA
            or proof.get("independentScienceWitnessVerified") is not True
            or proof.get("academicTaskAccepted") is not False
            or proof.get("completeAcademicProofGatesStillOpen")!=90
            or proof.get("newProviderCalls")!=0
            or proof.get("publicationAuthorized") is not False
            or not _SHA64.fullmatch(str(proof.get("witnessSha256")))):
            raise ValueError("BSA275_SCIENCE_HANDLER_NOT_SIGNED_TASK_VERIFIABLE")
        proofs.append({"scienceFamily":handler.science_family,
                       "taskId":handler.task_id,
                       "surfaceSha256":proof["surfaceSha256"],
                       "independentScienceProof":proof})
    if (not proofs or len(proofs)>6
        or len({p["taskId"] for p in proofs})!=len(proofs)):
        raise ValueError("BSA275_EMPTY_OR_DUPLICATE_PROOF_BATCH")
    return v36,first,proofs


def _prior_two(private:Path)->dict[str,Any]:
    old=verify_second_academic_across_git_heads(private=private)
    if (old.get("independentlyAcceptedAcademicTasks")!=2
        or len(set(old.get("acceptedAcademicTaskIds",[])))!=2
        or len(old.get("academicProofReceiptSha256s",[]))!=2
        or old.get("completeAcademicProofGatesStillOpen")!=90
        or old.get("publicationAuthorized") is not False):
        raise ValueError("BSA275_PREVIOUS_A1_A2_ADMISSIONS_UNVERIFIED")
    return old


def _verify_batch_receipt(
    *,private:Path,ready:dict[str,str],historical:bool,
    rules:ScienceAdmissionRegistry,
)->tuple[dict[str,Any],list[dict[str,Any]]]:
    v36,partition,proofs=_proofs_for_signed_v36(
        private=private,ready=ready,historical=historical,rules=rules)
    old=_prior_two(private)
    receipt=_signed(_folder(private,ready),_RECEIPT,ready)
    # Original BSA274 registry audit is immutable under the proof-origin HEAD.
    # The current-head audit may be a separate signed instance; do not replace
    # the historical admission prerequisite with a bare latest pointer.
    origin_registry=_signed(_folder(private,ready),_REGISTRY_RECEIPT,ready)
    if (origin_registry.get("sourceBoundRegistryAudit",{}).get(
            "acceptedMcqDistractorTaskCount")!=2 or
        origin_registry.get("independentlyPreviouslyAcceptedAcademicTasks")!=2 or
        receipt.get("signedRegistryAuditSha256")!=origin_registry["integritySha256"]):
        raise ValueError("BSA275_ORIGINAL_REGISTRY_AUDIT_RECEIPT_CHANGED")
    previous=receipt.get("previousAcademicTaskIds")
    added=receipt.get("newScientificProofs")
    if (receipt.get("status")!=_STATUS
        or receipt.get("signedV36Sha256")!=v36["integritySha256"]
        or receipt.get("signedFirstV36PartitionSha256")!=partition["integritySha256"]
        or receipt.get("sourceSha256")!=_SOURCE_SHA
        or receipt.get("candidateSha256")!=_CANDIDATE_SHA
        or previous!=old["acceptedAcademicTaskIds"]
        or receipt.get("previousProofReceiptSha256s")!=
           old["academicProofReceiptSha256s"]
        or added!=proofs
        or receipt.get("independentlyAdmittedNewTaskCount")!=len(proofs)
        or receipt.get("cumulativeAcceptedAcademicTasks")!=2+len(proofs)
        or receipt.get("fullAcademicTasksStillOpen")!=429-2-len(proofs)
        or receipt.get("completeAcademicProofGatesStillOpen")!=90
        or receipt.get("fullAcademicActivityPASS")!=0
        or receipt.get("newProviderCalls")!=0
        or receipt.get("publicationAuthorized") is not False):
        raise ValueError("BSA275_IMMUTABLE_SCIENTIFIC_BATCH_RECEIPT_CHANGED")
    return receipt,proofs


def admit_new_scientific_batch(
    *,private:Path,rules:ScienceAdmissionRegistry|None=None,
)->dict[str,Any]:
    rules=approved_science_batch_rules() if rules is None else rules
    frontier=private/"long-horizon-development"/_FRONTIER
    if frontier.exists() or frontier.is_symlink():
        return verify_academic_batch_across_git_heads(private=private,rules=rules)
    audit=verify_registry_audit(private=private)
    old=_prior_two(private)
    latest=read_long_horizon_development(private)
    now={"gitHead":latest["gitHead"],"proposalSha256":latest["proposalSha256"]}
    v36,partition,proofs=_proofs_for_signed_v36(
        private=private,ready=now,historical=False,rules=rules)
    if (audit["gitHead"]!=now["gitHead"]
        or audit["independentlyAcceptedAcademicTasks"]!=2
        or audit["registryReceiptSha256"]=="" or
        audit["signedV36Sha256"]!=v36["integritySha256"]
        or any(p["taskId"] in old["acceptedAcademicTaskIds"] for p in proofs)):
        raise ValueError("BSA275_PREVIOUS_TWO_REGISTRY_AND_NEW_BATCH_NOT_DISJOINT")
    receipt=_v6_checkpoint(_folder(private,now)/_RECEIPT,{
        **now,
        "status":_STATUS,
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "signedV36Sha256":v36["integritySha256"],
        "signedFirstV36PartitionSha256":partition["integritySha256"],
        "signedRegistryAuditSha256":audit["registryReceiptSha256"],
        "previousAcademicTaskIds":old["acceptedAcademicTaskIds"],
        "previousProofReceiptSha256s":old["academicProofReceiptSha256s"],
        "newScientificProofs":proofs,
        "independentlyAdmittedNewTaskCount":len(proofs),
        "cumulativeAcceptedAcademicTasks":2+len(proofs),
        "fullAcademicTasksStillOpen":429-2-len(proofs),
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    })
    second,proof_check=_verify_batch_receipt(
        private=private,ready=now,historical=False,rules=rules)
    if (second!=receipt or proof_check!=proofs):
        raise ValueError("BSA275_ORIGINAL_SCIENCE_PROOF_CHANGED_DURING_WRITE")
    sealed=_write_latest(frontier,{
        "status":_FRONTIER_STATUS,
        **now,
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "signedBatchReceiptSha256":receipt["integritySha256"],
        "previousAcademicTaskIds":old["acceptedAcademicTaskIds"],
        "newAcceptedTaskIds":[p["taskId"] for p in proofs],
        "acceptedAcademicTaskCount":2+len(proofs),
        "fullAcademicTasksStillOpen":429-2-len(proofs),
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "publicationAuthorized":False,
    })
    verified=verify_academic_batch_across_git_heads(private=private,rules=rules)
    if verified["batchReceiptSha256"]!=receipt["integritySha256"]:
        raise ValueError("BSA275_NEW_FRONTIER_NOT_VERIFIED_AFTER_ADMISSION")
    return verified


@verified_stage_reuse
def verify_academic_batch_across_git_heads(
    *,private:Path,rules:ScienceAdmissionRegistry|None=None,
)->dict[str,Any]:
    rules=approved_science_batch_rules() if rules is None else rules
    current=read_long_horizon_development(private)
    frontier=_read_signed(private/"long-horizon-development"/_FRONTIER)
    original={"gitHead":frontier.get("gitHead"),
              "proposalSha256":frontier.get("proposalSha256")}
    now={"gitHead":current["gitHead"],
         "proposalSha256":current["proposalSha256"]}
    if (not _SHA40.fullmatch(str(original["gitHead"]))
        or not _SHA64.fullmatch(str(original["proposalSha256"]))
        or frontier.get("status")!=_FRONTIER_STATUS
        or frontier.get("sourceSha256")!=_SOURCE_SHA
        or frontier.get("candidateSha256")!=_CANDIDATE_SHA
        or current.get("sourceSha256")!=_SOURCE_SHA
        or current.get("candidateSha256")!=_CANDIDATE_SHA
        or frontier.get("completeAcademicProofGatesStillOpen")!=90
        or frontier.get("fullAcademicActivityPASS")!=0
        or frontier.get("publicationAuthorized") is not False):
        raise ValueError("BSA275_HISTORICAL_ACADEMIC_BATCH_FRONTIER_CHANGED")
    old_receipt,proofs=_verify_batch_receipt(
        private=private,ready=original,historical=original!=now,rules=rules)
    _,_,new_proofs=_proofs_for_signed_v36(
        private=private,ready=now,historical=False,rules=rules)
    old=_prior_two(private)
    accepted=set(old["acceptedAcademicTaskIds"])
    newids=[p["taskId"] for p in proofs]
    if (old_receipt.get("integritySha256")!=frontier.get("signedBatchReceiptSha256")
        or old_receipt.get("previousAcademicTaskIds")!=old["acceptedAcademicTaskIds"]
        or old_receipt.get("previousProofReceiptSha256s")!=
           old["academicProofReceiptSha256s"]
        or new_proofs!=proofs
        or set(newids)&accepted
        or len(newids)!=len(set(newids))
        or frontier.get("previousAcademicTaskIds")!=old["acceptedAcademicTaskIds"]
        or frontier.get("newAcceptedTaskIds")!=newids
        or frontier.get("acceptedAcademicTaskCount")!=2+len(newids)
        or frontier.get("fullAcademicTasksStillOpen")!=429-2-len(newids)):
        raise ValueError("BSA275_CROSS_REVISION_SCIENCE_PROOF_NOT_SAME_TASK")
    return {
        "status":"BSA275_SEPARATE_SOURCE_BOUND_BATCH_PROOFS_REVERIFIED",
        "currentGitHead":now["gitHead"],
        "batchProofOriginGitHead":original["gitHead"],
        "batchProofCarriedAcrossGitHead":original!=now,
        "acceptedAcademicTaskIds":[*old["acceptedAcademicTaskIds"],*newids],
        "previousAcademicReceiptSha256s":old["academicProofReceiptSha256s"],
        "batchReceiptSha256":old_receipt["integritySha256"],
        "newIndependentlyAcceptedAcademicTasks":len(newids),
        "independentlyAcceptedAcademicTasks":2+len(newids),
        "fullAcademicTasksStillOpen":429-2-len(newids),
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    }

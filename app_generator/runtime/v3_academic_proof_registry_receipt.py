"""BSA274: immutable academic proof registry audit admission (NOT new task PASS).

The audit signs two already-independent A1/A2 academic receipts plus 25 exact
source-bound pending distractor tasks. The original PDF, candidate, V36 and
legacy A1/A2 are re-opened on *every* readback. Creating a registry receipt
does not sign or count a third academic task.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_academic_proof_registry import (
    audit_source_bound_academic_registry,
)
from app_generator.runtime.v3_long_horizon_development import (
    read_long_horizon_development,
)
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint

_RECEIPT = "BOSLA_ACADEMIC_PROOF_REGISTRY_AUDIT_V1.json"
_STATUS = "BSA274_PRIVATE_SIGNED_REGISTRY_TWO_REAL_PROOFS_25_PENDING"


def _ready(private: Path) -> dict[str,str]:
    state = read_long_horizon_development(private)
    return {"gitHead":state["gitHead"],
            "proposalSha256":state["proposalSha256"]}


def _folder(private: Path, ready: dict[str,str]) -> Path:
    return private/"owner-five-stage-completion"/ready["gitHead"]/ready["proposalSha256"]


def verify_registry_audit(*,private:Path)->dict[str,Any]:
    ready = _ready(private)
    expected = audit_source_bound_academic_registry(private=private)
    sealed = _signed(_folder(private,ready),_RECEIPT,ready)
    if (sealed.get("status")!=_STATUS
        or sealed.get("sourceBoundRegistryAudit")!=expected
        or sealed.get("academicTasksAcceptedByThisRegistryAudit")!=0
        or sealed.get("independentlyPreviouslyAcceptedAcademicTasks")!=2
        or sealed.get("unacceptedMcqDistractorTasks")!=25
        or sealed.get("completeAcademicProofGatesStillOpen")!=90
        or sealed.get("fullAcademicActivityPASS")!=0
        or sealed.get("newProviderCalls")!=0
        or sealed.get("publicationAuthorized") is not False):
        raise ValueError("BSA274_SIGNED_PROOF_REGISTRY_READBACK_DIVERGED")
    return {
        "status":"BSA274_REGISTRY_SIGNED_A1_A2_READBACK_PASS",
        "gitHead":ready["gitHead"],
        "sourceSha256":expected["sourceSha256"],
        "candidateSha256":expected["candidateSha256"],
        "signedV36Sha256":expected["signedV36Sha256"],
        "registryReceiptSha256":sealed["integritySha256"],
        "acceptedAcademicTaskIds":expected["acceptedAcademicTaskIds"],
        "academicProofReceiptSha256s":[
            e["proofReceiptSha256"] for e in expected["acceptedEvidence"]],
        "independentlyAcceptedAcademicTasks":2,
        "pendingMcqDistractorScienceTasks":25,
        "fullAcademicTasksStillOpen":427,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    }


def sign_registry_audit(*,private:Path)->dict[str,Any]:
    ready = _ready(private)
    report = audit_source_bound_academic_registry(private=private)
    if (report.get("acceptedMcqDistractorTaskCount")!=2
        or report.get("pendingMcqDistractorTaskCount")!=25
        or report.get("fullAcademicTasksStillOpen")!=427
        or report.get("completeAcademicProofGatesStillOpen")!=90
        or report.get("publicationAuthorized") is not False):
        raise ValueError("BSA274_REGISTRY_AUDIT_WOULD_INFLATE_ACADEMIC_PASS")
    receipt = _v6_checkpoint(_folder(private,ready)/_RECEIPT,{
        **ready,
        "status":_STATUS,
        "sourceBoundRegistryAudit":report,
        "academicTasksAcceptedByThisRegistryAudit":0,
        "independentlyPreviouslyAcceptedAcademicTasks":2,
        "unacceptedMcqDistractorTasks":25,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    })
    verified = verify_registry_audit(private=private)
    if verified["registryReceiptSha256"]!=receipt["integritySha256"]:
        raise ValueError("BSA274_SIGN_AND_READBACK_INCONSISTENT")
    return verified

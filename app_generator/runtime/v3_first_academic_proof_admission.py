"""BSA270: source-bound academic task admission, distinct from source-free V36.

Only one finite-grammar Section9.1 MCQ distractor task is currently eligible.
This separate lane rereads the exact original PDF and frozen candidate, the
signed V36 predecessor and one signed activity partition, then independently
evaluates and signs the mathematical counterexample. It NEVER changes V36 or
the signed source-free long-horizon record. Independent readback recomputes
the task proof and checks the immutable signed result before counting 1.
"""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_post_v35_semantic_task_dispatch import (
    _V36,_STATUS36,_PREFIX,
)
from app_generator.runtime.v3_exact_revised_review_reconciliation import _CANDIDATE
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _SOURCE_BINDING
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_long_horizon_development import (
    read_long_horizon_development,_write_latest,_read_signed,
)
from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA,_CANDIDATE_SHA,
)
from app_generator.validation.section91_first_distractor_proof import (
    independent_distractor_science,
)

_RECEIPT="ACADEMIC_A1_SOURCE_BOUND_FIRST_MCQ_DISTRACTOR.json"
_FRONTIER="ACADEMIC_SOURCE_BOUND_FIRST_TASK_FRONTIER.json"
_STATUS="BSA270_FIRST_MC_Q_DISTRACTOR_SCIENCE_TASK_INDEPENDENTLY_ADMITTED"
_CLAIM="BSA270_ONE_FINITE_SEMANTIC_MCQ_DISTRACTOR_SCIENCE_ACCEPTED"
_ID="ce320185009e7c529840a5cf96c75a1f469ad2a5961b3cbbca2ac4f07d9f9d60"


def _bound_inputs(private:Path,ready:dict[str,Any]):
    head=ready.get("gitHead")
    proposal=ready.get("proposalSha256")
    if (not isinstance(head,str) or len(head)!=40
        or not isinstance(proposal,str) or len(proposal)!=64):
        raise ValueError("BSA270_UNTRUSTED_HEAD_AND_PROPOSAL")
    prior=read_long_horizon_development(private)
    if (prior.get("gitHead")!=head or prior.get("proposalSha256")!=proposal
        or prior.get("sourceSha256")!=_SOURCE_SHA
        or prior.get("candidateSha256")!=_CANDIDATE_SHA
        or prior.get("academicAcceptedProofTaskCount")!=0
        or prior.get("fullSemanticProofTasksStillOpen")!=429
        or prior.get("completeAcademicProofGatesStillOpen")!=90):
        raise ValueError("BSA270_REAL_OWNER_SOURCE_FREE_HORIZON_REQUIRED")
    folder=private/"owner-five-stage-completion"/head/proposal
    v36=_signed(folder,_V36,ready)
    if (v36.get("status")!=_STATUS36
        or v36.get("sourceSha256")!=_SOURCE_SHA
        or v36.get("revisedCandidateSha256")!=_CANDIDATE_SHA
        or v36.get("semanticTasksAutomaticallyDispatched")!=429
        or v36.get("activitySignedPartitionCount")!=18
        or v36.get("fullAcademicProofTasksAccepted")!=0
        or v36.get("completeAcademicProofGatesStillOpen")!=90
        or v36.get("publicationAuthorized") is not False):
        raise ValueError("BSA270_SIGNED_V36_IS_NOT_THE_FROZEN_BACKLOG")
    partition=_signed(folder,f"{_PREFIX}01.json",ready)
    idx=v36.get("signedPartitionHashes",[])
    if (not idx or idx[0].get("activityId")!="act-mcq-01-vector-nature"
        or idx[0].get("signedEvidenceSha256")!=partition.get("integritySha256")
        or partition.get("sourceSha256")!=_SOURCE_SHA
        or partition.get("candidateSha256")!=_CANDIDATE_SHA):
        raise ValueError("BSA270_SIGNED_FIRST_ACTIVITY_PARTITION_MISMATCH")
    rows=partition.get("activity",{}).get("evidenceRows",[])
    found=[x for x in rows if x.get("taskId")==_ID]
    if (len(found)!=1 or found[0].get("kind")!="MCQ_DISTRACTOR_SCIENCE"
        or found[0].get("status")!="BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED"):
        raise ValueError("BSA270_PREDECESSOR_TASK_NOT_REVIEW_REQUIRED")
    binding=_trusted_json(private/_SOURCE_BINDING)
    pdf=Path(binding["sourcePdf"])
    candidate=folder/_CANDIDATE
    return folder,v36,partition,pdf,candidate


def _check_recomputed(proof:dict[str,Any]):
    if (proof.get("status")!=_CLAIM or proof.get("taskId")!=_ID
        or proof.get("sourceSha256")!=_SOURCE_SHA
        or proof.get("candidateSha256")!=_CANDIDATE_SHA
        or proof.get("taskKind")!="MCQ_DISTRACTOR_SCIENCE"
        or proof.get("acceptedAcademicTaskCount")!=1
        or proof.get("remainingFullAcademicTasks")!=428
        or proof.get("completeAcademicProofGatesStillOpen")!=90
        or proof.get("otherTrilingualMeaningProofAccepted") is not False
        or proof.get("publicationAuthorized") is not False
        or proof.get("newGeminiCalls")!=0):
        raise ValueError("BSA270_UNSUPPORTED_ACADEMIC_CLAIM")


def admit_first_independent_distractor(
    *,private:Path,ready:dict[str,Any],
)->dict[str,Any]:
    folder,v36,partition,pdf,candidate=_bound_inputs(private,ready)
    proof=independent_distractor_science(
        source_pdf=pdf,candidate_path=candidate)
    _check_recomputed(proof)
    receipt=_v6_checkpoint(folder/_RECEIPT,{
        "gitHead":ready["gitHead"],
        "proposalSha256":ready["proposalSha256"],
        "status":_STATUS,
        "signedV36Sha256":v36["integritySha256"],
        "signedV36FirstPartitionSha256":partition["integritySha256"],
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "independentTaskProof":proof,
        "academicTaskAcceptances":1,
        "fullAcademicTasksStillOpen":428,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "otherTaskProofsAccepted":False,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    })
    # Verify all evidence AGAIN before publishing even an internal pointer.
    verify_single_academic_receipt(private=private,ready=ready,
                                   expected_receipt=receipt)
    frontier_file=private/"long-horizon-development"/_FRONTIER
    if frontier_file.exists():
        old=_read_signed(frontier_file)
        if (old.get("gitHead")!=ready["gitHead"]
            or old.get("proposalSha256")!=ready["proposalSha256"]
            or old.get("proofReceiptSha256")!=receipt["integritySha256"]):
            raise ValueError("BSA270_ACADEMIC_FRONTIER_CONFLICT")
    frontier=_write_latest(frontier_file,{
        "status":"BSA270_ONE_REVERIFIED_ACADEMIC_TASK_ADMITTED_PRIVATE",
        "gitHead":ready["gitHead"],
        "proposalSha256":ready["proposalSha256"],
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "taskId":_ID,
        "taskKind":"MCQ_DISTRACTOR_SCIENCE",
        "proofReceiptSha256":receipt["integritySha256"],
        "acceptedAcademicTaskCount":1,
        "fullSemanticProofTasksStillOpen":428,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "otherAcademicTasksAccepted":False,
        "publicationAuthorized":False,
    })
    return verify_first_academic_frontier(private=private,ready=ready,
                                          expected_frontier=frontier)


def verify_single_academic_receipt(
    *,private:Path,ready:dict[str,Any],expected_receipt:dict|None=None
)->dict[str,Any]:
    folder,v36,partition,pdf,candidate=_bound_inputs(private,ready)
    receipt=_signed(folder,_RECEIPT,ready)
    if expected_receipt is not None and receipt!=expected_receipt:
        raise ValueError("BSA270_ACADEMIC_RECEIPT_REPLACED")
    proof=independent_distractor_science(
        source_pdf=pdf,candidate_path=candidate)
    _check_recomputed(proof)
    # Independent arithmetic receipt verifier: derive p=m*v afresh from the
    # recorded rational operands, not the producer's booleans or stored p.
    from fractions import Fraction
    cases=proof.get("exactRationalCounterexamples",[])
    if not isinstance(cases,list) or len(cases)!=2:
        raise ValueError("BSA270_TWO_INDEPENDENT_COUNTEREXAMPLES_REQUIRED")
    for case in cases:
        try:
            mass=Fraction(case["mass"])
            velocity=Fraction(case["constantSpeed"])
            positive=Fraction(case["momentumPositive"])
            negative=Fraction(case["momentumNegative"])
        except (KeyError,ValueError,ZeroDivisionError,TypeError) as error:
            raise ValueError("BSA270_UNTRUSTED_RATIONAL_PROOF_RECEIPT") from error
        if (mass<=0 or velocity<=0 or mass*velocity!=positive
            or mass*(-velocity)!=negative or positive==0 or negative==0
            or positive+negative!=0 or
            case.get("individualMomentumZero") is not False or
            case.get("constantSpeedDoesNotImplyZeroMomentum") is not True):
            raise ValueError("BSA270_INDEPENDENT_RATIONAL_COUNTEREXAMPLE_FAILED")
    if (receipt.get("status")!=_STATUS
        or receipt.get("signedV36Sha256")!=v36["integritySha256"]
        or receipt.get("signedV36FirstPartitionSha256")!=partition["integritySha256"]
        or receipt.get("sourceSha256")!=_SOURCE_SHA
        or receipt.get("candidateSha256")!=_CANDIDATE_SHA
        or receipt.get("independentTaskProof")!=proof
        or receipt.get("academicTaskAcceptances")!=1
        or receipt.get("fullAcademicTasksStillOpen")!=428
        or receipt.get("completeAcademicProofGatesStillOpen")!=90
        or receipt.get("fullAcademicActivityPASS")!=0
        or receipt.get("newProviderCalls")!=0
        or receipt.get("publicationAuthorized") is not False):
        raise ValueError("BSA270_INDEPENDENT_RECOMPUTATION_DISAGREES_WITH_RECEIPT")
    return receipt


def verify_first_academic_frontier(
    *,private:Path,ready:dict[str,Any],
    expected_frontier:dict|None=None,
)->dict[str,Any]:
    receipt=verify_single_academic_receipt(private=private,ready=ready)
    frontier=_read_signed(private/"long-horizon-development"/_FRONTIER)
    if expected_frontier is not None and frontier!=expected_frontier:
        raise ValueError("BSA270_FRONTIER_CHANGED_AFTER_ADMISSION")
    if (frontier.get("gitHead")!=ready.get("gitHead")
        or frontier.get("proposalSha256")!=ready.get("proposalSha256")
        or frontier.get("sourceSha256")!=_SOURCE_SHA
        or frontier.get("candidateSha256")!=_CANDIDATE_SHA
        or frontier.get("taskId")!=_ID
        or frontier.get("taskKind")!="MCQ_DISTRACTOR_SCIENCE"
        or frontier.get("status")!="BSA270_ONE_REVERIFIED_ACADEMIC_TASK_ADMITTED_PRIVATE"
        or frontier.get("proofReceiptSha256")!=receipt["integritySha256"]
        or frontier.get("acceptedAcademicTaskCount")!=1
        or frontier.get("fullSemanticProofTasksStillOpen")!=428
        or frontier.get("completeAcademicProofGatesStillOpen")!=90
        or frontier.get("fullAcademicActivityPASS")!=0
        or frontier.get("otherAcademicTasksAccepted") is not False
        or frontier.get("publicationAuthorized") is not False):
        raise ValueError("BSA270_ACADEMIC_FRONTIER_CANNOT_BE_TRUSTED")
    return {
        "status":"BSA270_INDEPENDENT_SOURCE_AND_PROOF_RECEIPT_READBACK_PASS",
        "gitHead":ready["gitHead"],
        "taskId":_ID,
        "proofReceiptSha256":receipt["integritySha256"],
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "independentlyAcceptedAcademicTasks":1,
        "otherFullAcademicTasksStillOpen":428,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicActivityPASS":0,
        "publicationAuthorized":False,
    }

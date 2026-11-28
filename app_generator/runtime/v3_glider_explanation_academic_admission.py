"""Owner-only original Serway MCQ04 glider explanation admission, A31.

An exact source, candidate, V36 partition and prior A1-A30 chain are
recomputed on admission and on historical/current-head readback.
"""
from __future__ import annotations

from pathlib import Path

from app_generator.runtime.v3_first_academic_proof_admission import _bound_inputs
from app_generator.runtime.v3_long_horizon_development import read_long_horizon_development, _write_latest, _read_signed
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_newton_explanation_academic_admission import verify_newton_explanation_across_git_heads
from app_generator.runtime.v3_academic_proof_registry_receipt import verify_registry_audit, _RECEIPT as _REGISTRY_RECEIPT
from app_generator.validation.section91_formal_physics import _SOURCE_SHA, _CANDIDATE_SHA
from app_generator.validation.section91_glider_explanation_proof import (
    independently_prove_glider_explanation,
    independently_check_glider_explanation_witness,
)

_RECEIPT = "BOSLA_ACADEMIC_GLIDER_EXPLANATION_A31_V1.json"
_FRONTIER = "BOSLA_ACADEMIC_GLIDER_EXPLANATION_FRONTIER_V1.json"
_STATUS = "BSA298_INDEPENDENT_MCQ04_GLIDER_EXPLANATION_SCIENCE_TASK_ADMITTED"
_FRONTIER_STATUS = "BSA298_PRIVATE_GLIDER_EXPLANATION_SCIENCE_TASK_ACCEPTED"


def _folder(private: Path, ready: dict) -> Path:
    return private / "owner-five-stage-completion" / ready["gitHead"] / ready["proposalSha256"]


def _prior(private: Path) -> dict:
    old = verify_newton_explanation_across_git_heads(private=private)
    if (old.get("independentlyAcceptedAcademicTasks") != 30 or
        old.get("fullAcademicTasksStillOpen") != 399 or
        len(set(old.get("acceptedAcademicTaskIds", []))) != 30 or
        old.get("completeAcademicProofGatesStillOpen") != 90 or
        old.get("fullAcademicActivityPASS") != 0 or
        old.get("publicationAuthorized") is not False):
        raise ValueError("BSA298_SIGNED_A1_A30_CHAIN_REQUIRED")
    return old


def _original_proof(*, private: Path, ready: dict, historical: bool) -> tuple[dict, dict, dict]:
    _, v36, _, source, candidate = _bound_inputs(private, ready, allow_historical=historical)
    signed = v36.get("signedPartitionHashes", [])
    if (len(signed) != 18 or v36.get("semanticTasksAutomaticallyDispatched") != 429 or
        v36.get("fullAcademicProofTasksAccepted") != 0 or
        v36.get("completeAcademicProofGatesStillOpen") != 90 or
        v36.get("sourceSha256") != _SOURCE_SHA or
        v36.get("publicationAuthorized") is not False):
        raise ValueError("BSA298_EXACT_ORIGINAL_SOURCE_V36_REQUIRED")
    part = _signed(_folder(private, ready), "V36_PARTITION_04.json", ready)
    if (signed[3].get("activityId") != "act-mcq-04-two-particle-opposite-momentum" or
        signed[3].get("signedEvidenceSha256") != part.get("integritySha256") or
        part.get("activity", {}).get("activityId") != "act-mcq-04-two-particle-opposite-momentum" or
        part.get("sourceSha256") != _SOURCE_SHA or
        part.get("candidateSha256") != _CANDIDATE_SHA or
        part.get("academicPASS") != 0 or
        part.get("publicationAuthorized") is not False):
        raise ValueError("BSA298_FOURTH_SIGNED_ORIGINAL_V36_PARTITION_CHANGED")
    proof = independently_prove_glider_explanation(source_pdf=source, candidate_path=candidate)
    independently_check_glider_explanation_witness(proof)
    rows = part["activity"].get("evidenceRows", [])
    hits = [row for row in rows if row.get("taskId") == proof["taskId"]]
    if (len(hits) != 1 or hits[0].get("kind") != "COMPLETE_SCIENTIFIC_MEANING" or
        # BSA321: V36 evidence rows omit surfacePath. The original-source
        # producer already rederives exactly one canonical explanation task
        # from the SHA-pinned candidate; reject any explicit wrong path.
        hits[0].get("surfacePath", "explanation") != "explanation" or
        hits[0].get("status") != "BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED" or
        hits[0].get("surfaceSha256") != proof["surfaceSha256"] or
        proof.get("newProviderCalls") != 0 or proof.get("publicationAuthorized") is not False):
        raise ValueError("BSA298_EXPLANATION_SCIENCE_NOT_REPROVEN")
    return v36, part, proof


def _verify_receipt(*, private: Path, ready: dict, historical: bool) -> tuple[dict, dict]:
    v36, part, proof = _original_proof(private=private, ready=ready, historical=historical)
    old = _prior(private)
    receipt = _signed(_folder(private, ready), _RECEIPT, ready)
    audit = _signed(_folder(private, ready), _REGISTRY_RECEIPT, ready)
    if (audit.get("sourceBoundRegistryAudit", {}).get("acceptedMcqDistractorTaskCount") != 2 or
        audit.get("independentlyPreviouslyAcceptedAcademicTasks") != 2 or
        receipt.get("signedRegistryAuditSha256") != audit["integritySha256"] or
        receipt.get("status") != _STATUS or receipt.get("sourceSha256") != _SOURCE_SHA or
        receipt.get("candidateSha256") != _CANDIDATE_SHA or
        receipt.get("signedV36Sha256") != v36["integritySha256"] or
        receipt.get("fourthSignedV36PartitionSha256") != part["integritySha256"] or
        receipt.get("previousAcademicTaskIds") != old["acceptedAcademicTaskIds"] or
        receipt.get("previousNewtonExplanationReceiptSha256") != old["newtonExplanationReceiptSha256"] or
        receipt.get("newScientificProof") != proof or
        receipt.get("newIndependentlyAdmittedAcademicTasks") != 1 or
        receipt.get("totalAcademicTaskAcceptances") != 31 or
        receipt.get("fullAcademicTasksStillOpen") != 398 or
        receipt.get("completeAcademicProofGatesStillOpen") != 90 or
        receipt.get("fullAcademicActivityPASS") != 0 or
        receipt.get("newProviderCalls") != 0 or
        receipt.get("publicationAuthorized") is not False):
        raise ValueError("BSA298_ORIGINAL_EXPLANATION_IMMUTABLE_RECEIPT_CHANGED")
    return receipt, proof


def admit_glider_explanation(*, private: Path) -> dict:
    frontier = private / "long-horizon-development" / _FRONTIER
    if frontier.exists() or frontier.is_symlink():
        return verify_glider_explanation_across_git_heads(private=private)
    prev = _prior(private)
    latest = read_long_horizon_development(private)
    now = {"gitHead": latest["gitHead"], "proposalSha256": latest["proposalSha256"]}
    audit = verify_registry_audit(private=private)
    v36, part, proof = _original_proof(private=private, ready=now, historical=False)
    if (audit.get("gitHead") != now["gitHead"] or
        audit.get("signedV36Sha256") != v36["integritySha256"] or
        audit.get("independentlyAcceptedAcademicTasks") != 2 or
        proof["taskId"] in prev["acceptedAcademicTaskIds"]):
        raise ValueError("BSA298_A1_A30_CHAIN_OR_TASK_DUPLICATE")
    receipt = _v6_checkpoint(_folder(private, now) / _RECEIPT, {
        **now, "status": _STATUS, "sourceSha256": _SOURCE_SHA,
        "candidateSha256": _CANDIDATE_SHA,
        "signedV36Sha256": v36["integritySha256"],
        "fourthSignedV36PartitionSha256": part["integritySha256"],
        "signedRegistryAuditSha256": audit["registryReceiptSha256"],
        "previousAcademicTaskIds": prev["acceptedAcademicTaskIds"],
        "previousNewtonExplanationReceiptSha256": prev["newtonExplanationReceiptSha256"],
        "newScientificProof": proof, "newIndependentlyAdmittedAcademicTasks": 1,
        "totalAcademicTaskAcceptances": 31, "fullAcademicTasksStillOpen": 398,
        "completeAcademicProofGatesStillOpen": 90, "fullAcademicActivityPASS": 0,
        "newProviderCalls": 0, "publicationAuthorized": False,
    })
    checked, checked_proof = _verify_receipt(private=private, ready=now, historical=False)
    if checked != receipt or checked_proof != proof:
        raise ValueError("BSA298_EXPLANATION_CHANGED_BEFORE_ADMISSION")
    _write_latest(frontier, {
        **now, "status": _FRONTIER_STATUS, "sourceSha256": _SOURCE_SHA,
        "candidateSha256": _CANDIDATE_SHA,
        "newScientificReceiptSha256": receipt["integritySha256"],
        "previousAcademicTaskIds": prev["acceptedAcademicTaskIds"],
        "newAcceptedTaskId": proof["taskId"], "cumulativeAcademicTasksAccepted": 31,
        "fullAcademicTasksStillOpen": 398, "completeAcademicProofGatesStillOpen": 90,
        "fullAcademicActivityPASS": 0, "publicationAuthorized": False,
    })
    return verify_glider_explanation_across_git_heads(private=private)


def verify_glider_explanation_across_git_heads(*, private: Path) -> dict:
    frontier = _read_signed(private / "long-horizon-development" / _FRONTIER)
    now_ck = read_long_horizon_development(private)
    origin = {"gitHead": frontier.get("gitHead"), "proposalSha256": frontier.get("proposalSha256")}
    now = {"gitHead": now_ck["gitHead"], "proposalSha256": now_ck["proposalSha256"]}
    if (frontier.get("status") != _FRONTIER_STATUS or
        frontier.get("sourceSha256") != _SOURCE_SHA or
        frontier.get("candidateSha256") != _CANDIDATE_SHA or
        now_ck.get("sourceSha256") != _SOURCE_SHA or
        now_ck.get("candidateSha256") != _CANDIDATE_SHA or
        frontier.get("cumulativeAcademicTasksAccepted") != 31 or
        frontier.get("fullAcademicTasksStillOpen") != 398 or
        frontier.get("completeAcademicProofGatesStillOpen") != 90 or
        frontier.get("fullAcademicActivityPASS") != 0 or
        frontier.get("publicationAuthorized") is not False):
        raise ValueError("BSA298_HISTORICAL_EXPLANATION_FRONTIER_UNVERIFIED")
    receipt, proof = _verify_receipt(private=private, ready=origin, historical=origin != now)
    _, _, recomputed = _original_proof(private=private, ready=now, historical=False)
    prior = _prior(private)
    if (proof != recomputed or
        receipt["integritySha256"] != frontier.get("newScientificReceiptSha256") or
        receipt["previousNewtonExplanationReceiptSha256"] != prior["newtonExplanationReceiptSha256"] or
        frontier.get("previousAcademicTaskIds") != prior["acceptedAcademicTaskIds"] or
        frontier.get("newAcceptedTaskId") != proof["taskId"] or
        proof["taskId"] in prior["acceptedAcademicTaskIds"]):
        raise ValueError("BSA298_EXPLANATION_SCIENCE_CHANGED_ACROSS_CODE_HEADS")
    return {"status": "BSA298_GLIDER_EXPLANATION_SCIENCE_TASK_GENUINELY_REVERIFIED",
            "currentGitHead": now["gitHead"], "batchProofOriginGitHead": origin["gitHead"],
            "carriedAcrossGitHead": origin != now,
            "acceptedAcademicTaskIds": [*prior["acceptedAcademicTaskIds"], proof["taskId"]],
            "gliderExplanationReceiptSha256": receipt["integritySha256"],
            "independentlyAcceptedAcademicTasks": 31,
            "fullAcademicTasksStillOpen": 398,
            "completeAcademicProofGatesStillOpen": 90,
            "fullAcademicActivityPASS": 0, "newProviderCalls": 0,
            "publicationAuthorized": False}

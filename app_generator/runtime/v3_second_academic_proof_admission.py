"""BSA273: second immutable academic proof; cross-head independent reread.

The first BSA270/272 proof is still independently checked, not overwritten.
A second signed receipt is admitted only after a current original-source V36
owner run, exact source/candidate, complete EN/MS/ZH semantic grammar, two
rational vector countermodels, and a genuine matching pending V36 task row.
Historical/current receipts are reopened on every horizon readback.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_long_horizon_development import (
    read_long_horizon_development, _write_latest, _read_signed,
)
from app_generator.runtime.v3_first_academic_proof_admission import (
    _bound_inputs, _ID as _FIRST_ID,
)
from app_generator.runtime.v3_academic_cross_head_continuity import (
    verify_academic_across_git_heads,
)
from app_generator.validation.section91_second_distractor_proof import (
    independent_second_distractor_science,
)
from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA, _CANDIDATE_SHA,
)

_RECEIPT = "ACADEMIC_A2_SOURCE_BOUND_SECOND_MCQ_DISTRACTOR.json"
_FRONTIER = "ACADEMIC_SOURCE_BOUND_SECOND_TASK_FRONTIER.json"
_STATUS = "BSA273_SECOND_MC_Q_DISTRACTOR_SCIENCE_TASK_INDEPENDENTLY_ADMITTED"
_READING = "BSA273_SECOND_ACADEMIC_TASK_INDEPENDENTLY_REVERIFIED"
_PATH = "answerKey/options/1/label"


def _check_task_and_source(
    *, private: Path, ready: dict[str, Any], allow_historical: bool = False,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    folder, v36, partition, pdf, candidate = _bound_inputs(
        private, ready, allow_historical=allow_historical)
    proof = independent_second_distractor_science(
        source_pdf=pdf, candidate_path=candidate)
    rows = partition.get("activity", {}).get("evidenceRows", [])
    exact = [r for r in rows if r.get("taskId") == proof["taskId"]]
    if (len(exact) != 1 or proof["taskId"] == _FIRST_ID
        or exact[0].get("kind") != "MCQ_DISTRACTOR_SCIENCE"
        or exact[0].get("status") != "BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED"
        # V36 signed evidence rows intentionally omit surfacePath: the
        # stable taskId is derived from that path plus the surface digest.
        # Requiring a nonexistent row field caused the first real BSA273
        # readback to reject an otherwise correct owner-signed task.
        or proof.get("surfacePath") != _PATH
        or exact[0].get("surfaceSha256") != proof["surfaceSha256"]
        or proof.get("completeAcademicProofGatesStillOpen") != 90
        or proof.get("acceptedAcademicTaskCountForThisProof") != 1
        or proof.get("otherTrilingualMeaningProofAccepted") is not False
        or proof.get("publicationAuthorized") is not False
        or proof.get("newGeminiCalls") != 0):
        raise ValueError("BSA273_SECOND_SIGNED_V36_TASK_NOT_PENDING_OR_VERIFIABLE")
    return v36, partition, proof


def _verify_receipt(
    *, private: Path, ready: dict[str, Any], allow_historical: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    v36, partition, proof = _check_task_and_source(
        private=private, ready=ready, allow_historical=allow_historical)
    folder = private/"owner-five-stage-completion"/ready["gitHead"]/ready["proposalSha256"]
    receipt = _signed(folder, _RECEIPT, ready)
    if (receipt.get("status") != _STATUS
        or receipt.get("gitHead") != ready["gitHead"]
        or receipt.get("proposalSha256") != ready["proposalSha256"]
        or receipt.get("signedV36Sha256") != v36["integritySha256"]
        or receipt.get("signedV36FirstPartitionSha256") != partition["integritySha256"]
        or receipt.get("sourceSha256") != _SOURCE_SHA
        or receipt.get("candidateSha256") != _CANDIDATE_SHA
        or receipt.get("independentTaskProof") != proof
        or receipt.get("academicTaskAcceptancesFromThisReceipt") != 1
        or receipt.get("cumulativeAcceptedAcademicTasks") != 2
        or receipt.get("fullAcademicTasksStillOpen") != 427
        or receipt.get("completeAcademicProofGatesStillOpen") != 90
        or receipt.get("fullAcademicActivityPASS") != 0
        or receipt.get("newProviderCalls") != 0
        or receipt.get("publicationAuthorized") is not False):
        raise ValueError("BSA273_SECOND_IMMUTABLE_SOURCE_SCIENCE_RECEIPT_INVALID")
    # Recompute exact rational vector arithmetic separately, so hard-coded
    # booleans and saved successful status cannot conceal a forged proof.
    from fractions import Fraction
    cases = receipt["independentTaskProof"].get("exactRationalCounterexamples", [])
    if len(cases) != 2:
        raise ValueError("BSA273_TWO_RATIONAL_PROOFS_REQUIRED")
    for w in cases:
        try:
            m, s = Fraction(w["mass"]), Fraction(w["constantSpeed"])
            forward, backward = Fraction(w["momentumForward"]), Fraction(w["momentumBackward"])
        except (KeyError, ValueError, ZeroDivisionError, TypeError) as e:
            raise ValueError("BSA273_RATIONAL_PROOF_NOT_REPARSEABLE") from e
        if (m <= 0 or s <= 0 or forward != m*s or backward != -m*s
            or forward == backward or abs(forward) != abs(backward)
            or w.get("momentumVectorsIdentical") is not False
            or w.get("momentumMagnitudesEqual") is not True):
            raise ValueError("BSA273_INDEPENDENT_VECTOR_ARITHMETIC_FAILED")
    return receipt, proof


def admit_second_independent_distractor(
    *, private: Path, ready: dict[str, Any],
) -> dict[str, Any]:
    if (private/"long-horizon-development"/_FRONTIER).exists():
        # A repeat run never creates another acceptance or erases previous.
        return verify_second_academic_across_git_heads(private=private)
    prior = verify_academic_across_git_heads(private=private)
    if (prior["independentlyAcceptedAcademicTasks"] != 1
        or prior["taskId"] != _FIRST_ID):
        raise ValueError("BSA273_FIRST_INDEPENDENT_PROOF_MUST_BE_VALID")
    latest = read_long_horizon_development(private)
    if (latest["gitHead"] != ready["gitHead"]
        or latest["proposalSha256"] != ready["proposalSha256"]):
        raise ValueError("BSA273_CURRENT_SIGNED_OWNER_RUN_REQUIRED")
    v36, partition, proof = _check_task_and_source(private=private,ready=ready)
    folder = private/"owner-five-stage-completion"/ready["gitHead"]/ready["proposalSha256"]
    _v6_checkpoint(folder/_RECEIPT, {
        "status": _STATUS,
        "gitHead": ready["gitHead"],
        "proposalSha256": ready["proposalSha256"],
        "signedV36Sha256": v36["integritySha256"],
        "signedV36FirstPartitionSha256": partition["integritySha256"],
        "sourceSha256": _SOURCE_SHA,
        "candidateSha256": _CANDIDATE_SHA,
        "independentTaskProof": proof,
        "academicTaskAcceptancesFromThisReceipt": 1,
        "cumulativeAcceptedAcademicTasks": 2,
        "fullAcademicTasksStillOpen": 427,
        "completeAcademicProofGatesStillOpen": 90,
        "fullAcademicActivityPASS": 0,
        "newProviderCalls": 0,
        "publicationAuthorized": False,
    })
    receipt, proof_check = _verify_receipt(private=private,ready=ready)
    if proof_check != proof:
        raise ValueError("BSA273_GENERATOR_CHANGED_DURING_ADMISSION")
    frontier_file=private/"long-horizon-development"/_FRONTIER
    _write_latest(frontier_file, {
        "status": "BSA273_SECOND_PRIVATE_INDEPENDENT_TASK_ACCEPTED",
        "gitHead": ready["gitHead"],
        "proposalSha256": ready["proposalSha256"],
        "sourceSha256": _SOURCE_SHA,
        "candidateSha256": _CANDIDATE_SHA,
        "taskId": proof["taskId"],
        "proofReceiptSha256": receipt["integritySha256"],
        "cumulativeAcceptedAcademicTasks": 2,
        "fullAcademicTasksStillOpen": 427,
        "completeAcademicProofGatesStillOpen": 90,
        "fullAcademicActivityPASS": 0,
        "publicationAuthorized": False,
    })
    return verify_second_academic_across_git_heads(private=private)


def verify_second_academic_across_git_heads(*, private: Path) -> dict[str, Any]:
    first = verify_academic_across_git_heads(private=private)
    if (first.get("independentlyAcceptedAcademicTasks") != 1
        or first.get("taskId") != _FIRST_ID
        or first.get("publicationAuthorized") is not False):
        raise ValueError("BSA273_FIRST_PROOF_NO_LONGER_VALID")
    frontier = _read_signed(private/"long-horizon-development"/_FRONTIER)
    current = read_long_horizon_development(private)
    origin = {"gitHead": frontier.get("gitHead"),
              "proposalSha256": frontier.get("proposalSha256")}
    now = {"gitHead": current["gitHead"],
           "proposalSha256": current["proposalSha256"]}
    if (frontier.get("status") != "BSA273_SECOND_PRIVATE_INDEPENDENT_TASK_ACCEPTED"
        or frontier.get("sourceSha256") != _SOURCE_SHA
        or frontier.get("candidateSha256") != _CANDIDATE_SHA
        or current.get("sourceSha256") != _SOURCE_SHA
        or current.get("candidateSha256") != _CANDIDATE_SHA
        or frontier.get("cumulativeAcceptedAcademicTasks") != 2
        or frontier.get("fullAcademicTasksStillOpen") != 427
        or frontier.get("completeAcademicProofGatesStillOpen") != 90
        or frontier.get("fullAcademicActivityPASS") != 0
        or frontier.get("publicationAuthorized") is not False):
        raise ValueError("BSA273_SECOND_ACADEMIC_FRONTIER_UNTRUSTED")
    old_receipt, old_proof = _verify_receipt(
        private=private, ready=origin, allow_historical=origin!=now)
    _, _, new_proof = _check_task_and_source(private=private,ready=now)
    if (old_proof != new_proof
        or old_proof["taskId"] != frontier["taskId"]
        or old_proof["taskId"] == first["taskId"]
        or old_receipt["integritySha256"] != frontier["proofReceiptSha256"]):
        raise ValueError("BSA273_CROSS_HEAD_SECOND_TASK_CHANGED_OR_DUPLICATED")
    return {
        "status": _READING,
        "currentGitHead": now["gitHead"],
        "academicProofOriginGitHead": origin["gitHead"],
        "secondProofCarriedAcrossGitHead": origin!=now,
        "firstProofCarriedAcrossGitHead": first["carriedAcrossGitHead"],
        "acceptedAcademicTaskIds": [first["taskId"], old_proof["taskId"]],
        "academicProofReceiptSha256s": [
            first["proofReceiptSha256"], old_receipt["integritySha256"]],
        "independentlyAcceptedAcademicTasks": 2,
        "fullAcademicTasksStillOpen": 427,
        "completeAcademicProofGatesStillOpen": 90,
        "fullAcademicActivityPASS": 0,
        "newProviderCalls": 0,
        "publicationAuthorized": False,
    }

"""Original Serway MCQ04 explanation: exact vector momentum and scalar energy.

The witness is unadmitted until the owner checks the signed fourth V36 partition.
"""
from __future__ import annotations

from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path

from app_generator.validation.section91_formal_physics import _SOURCE_SHA, _CANDIDATE_SHA, _source_axioms, _digest
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs
from app_generator.validation.source_passages import extract_pages
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _source_activity_anchors

_ACTIVITY = "act-mcq-04-two-particle-opposite-momentum"
_PROMPT = {"en": "4880007bf3d30b65a61d273b9fb89515bcaf509fa802330ca8e99189f71b987e", "ms": "89b10a3fc9de7b776201cafba887c4d63f6250cbd85f83896e10bc4a49ad6f92", "zh": "dc6bd9a36305193858343472ce6d3e8fc488fa1c800372dec11d10472986fee2"}
_EXPLANATION = {"en": "27d28301913fa25fee6a3989296ba6388b3023097570c340278827cb50611882", "ms": "b1b90f3a6dfeb9af49e5de20cbbf2dd7db45df5b7ed1f534143cd9bae2d77877", "zh": "904d05c0134b5b452445dd0c4fce20f346fcf86a0c80e23680a1a8af6822c024"}
_CASES = ((F(3, 2), F(7, 3)), (F(11, 4), F(5, 2)))


def _locale_hashes(surface: dict, expected: dict) -> dict:
    if not isinstance(surface, dict) or set(surface) != {"en", "ms", "zh"} or any(
        not isinstance(v, str) or not v.strip() for v in surface.values()
    ):
        raise ValueError("BSA298_COMPLETE_TRILINGUAL_GLIDER_EXPLANATION_REQUIRED")
    actual = {lang: sha256(surface[lang].encode("utf8")).hexdigest() for lang in expected}
    if actual != expected:
        raise ValueError("BSA298_FROZEN_GLIDER_EXPLANATION_CHANGED")
    return actual


def _model(mass: F, speed: F) -> dict:
    if not isinstance(mass, F) or not isinstance(speed, F) or mass <= 0 or speed <= 0:
        raise ValueError("BSA298_POSITIVE_EXACT_GLIDER_MODEL_REQUIRED")
    p_forward, p_backward = mass * speed, -mass * speed
    k_forward = mass * speed * speed / 2
    k_backward = mass * (-speed) * (-speed) / 2
    p_total, k_total = p_forward + p_backward, k_forward + k_backward
    if not (p_forward > 0 > p_backward and p_total == 0 and
            k_forward == k_backward > 0 and k_total == mass * speed * speed > 0):
        raise ValueError("BSA298_GLIDER_VECTOR_SCALAR_CONTRAST_NOT_DERIVED")
    return {"massEach": str(mass), "speedEach": str(speed),
            "forwardMomentum": str(p_forward), "backwardMomentum": str(p_backward),
            "systemMomentum": str(p_total), "kineticEnergyEach": str(k_forward),
            "systemKineticEnergy": str(k_total), "oppositeMomentumCancels": True,
            "scalarKineticEnergyAdds": True}


def _models() -> list[dict]:
    return [_model(*case) for case in _CASES]


def independently_check_glider_explanation_witness(proof: dict) -> None:
    if not isinstance(proof, dict) or (
        not isinstance(proof.get("taskId"), str) or len(proof["taskId"]) != 64 or
        proof.get("sourceSha256") != _SOURCE_SHA or proof.get("candidateSha256") != _CANDIDATE_SHA or
        proof.get("promptLocaleSha256") != _PROMPT or proof.get("explanationLocaleSha256") != _EXPLANATION or
        proof.get("models") != _models() or type(proof.get("sourcePageIndex")) is not int or
        proof["sourcePageIndex"] < 1 or
        any(not isinstance(proof.get(key), str) or len(proof[key]) != 64 for key in
            ("surfaceSha256", "sourcePassageSha256", "sourcePhysicsPremisesSha256")) or
        proof.get("academicTaskAccepted") is not False or
        proof.get("completeAcademicProofGatesStillOpen") != 90 or
        proof.get("newProviderCalls") != 0 or proof.get("publicationAuthorized") is not False or
        proof.get("witnessSha256") != _digest({k: v for k, v in proof.items() if k != "witnessSha256"})
    ):
        raise ValueError("BSA298_UNTRUSTED_GLIDER_EXPLANATION_WITNESS")
    for row in proof["models"]:
        if row != _model(F(row["massEach"]), F(row["speedEach"])):
            raise ValueError("BSA298_GLIDER_EXPLANATION_RECOMPUTATION_FAILED")


def independently_prove_glider_explanation(*, source_pdf: Path, candidate_path: Path) -> dict:
    candidate_bytes = candidate_path.read_bytes() if candidate_path.is_file() and not candidate_path.is_symlink() else b""
    if (source_pdf.is_symlink() or not source_pdf.is_file() or not candidate_bytes or
        sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA or
        sha256(candidate_bytes).hexdigest() != _CANDIDATE_SHA):
        raise ValueError("BSA298_AUTHENTIC_SERWAY_SOURCE_AND_CANDIDATE_REQUIRED")
    axioms = _source_axioms(source_pdf, _SOURCE_SHA)
    if (axioms.get("linear momentum is a vector", 0) < 1 or
        axioms.get("defined to be the product of the mass and velocity", 0) < 1 or
        axioms.get("kinetic energy can transform", 0) < 1):
        raise ValueError("BSA298_ORIGINAL_MOMENTUM_ENERGY_PREMISES_MISSING")
    package = json.loads(candidate_bytes.decode("utf8"))
    activities = package.get("activities")
    if not isinstance(activities, list) or len(activities) != 18 or activities[3].get("id") != _ACTIVITY:
        raise ValueError("BSA298_FROZEN_FOURTH_ACTIVITY_CHANGED")
    activity = activities[3]
    prompt = _locale_hashes(activity.get("prompt"), _PROMPT)
    explanation = _locale_hashes(activity.get("explanation"), _EXPLANATION)
    key = activity.get("answerKey", {})
    if key.get("correct") != "opt-a" or [o.get("id") for o in key.get("options", [])] != ["opt-a", "opt-b", "opt-c", "opt-d"]:
        raise ValueError("BSA298_FROZEN_GLIDER_ANSWER_KEY_CHANGED")
    anchors = _source_activity_anchors(pages=extract_pages(source_pdf), activities=activities)
    if sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA:
        raise ValueError("BSA298_SOURCE_CHANGED_DURING_EXTRACTION")
    anchor = anchors[3]
    if anchor.get("activityId") != _ACTIVITY or anchor.get("uniquePagePassageLocated") is not True:
        raise ValueError("BSA298_ORIGINAL_SOURCE_ANCHOR_MISSING")
    queue = plan_full_semantic_proofs(package=package, source_sha256=_SOURCE_SHA)
    tasks = [task for task in queue["tasks"] if task["activityId"] == _ACTIVITY and
             task["kind"] == "COMPLETE_SCIENTIFIC_MEANING" and task["surfacePath"] == "explanation"]
    if queue["taskCount"] != 429 or len(tasks) != 1 or tasks[0]["surfaceSha256"] != _digest(activity["explanation"]):
        raise ValueError("BSA298_CANONICAL_GLIDER_EXPLANATION_TASK_NOT_REDERIVED")
    body = {"taskId": tasks[0]["taskId"], "sourceSha256": _SOURCE_SHA,
            "candidateSha256": _CANDIDATE_SHA, "surfaceSha256": tasks[0]["surfaceSha256"],
            "sourcePageIndex": anchor["physicalPage"], "sourcePassageSha256": anchor["passageSha256"],
            "sourcePhysicsPremisesSha256": _digest(sorted(axioms.items())),
            "promptLocaleSha256": prompt, "explanationLocaleSha256": explanation,
            "models": _models(), "academicTaskAccepted": False,
            "completeAcademicProofGatesStillOpen": 90, "newProviderCalls": 0,
            "publicationAuthorized": False}
    proof = {**body, "witnessSha256": _digest(body)}
    independently_check_glider_explanation_witness(proof)
    return proof

"""Independent exact-vector witness for the complete Serway MCQ06 explanation."""
from __future__ import annotations

from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path

from app_generator.validation.section91_formal_physics import _SOURCE_SHA, _CANDIDATE_SHA, _source_axioms, _digest
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs
from app_generator.validation.source_passages import extract_pages
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _source_activity_anchors
from app_generator.validation.section91_equal_speed_false_options_proof import _ACTIVITY, _PROMPT, _locale_digests

_EXPLANATION = {
    "en": "4f021ef1a0e00ca41fb72dca106dcb0ae195c028befc42c67276b74fb9a31259",
    "ms": "a4afc6c348261eb41908cb049617bb7666fdeeb263f0e206af95a82765b8e6fe",
    "zh": "f99af983b1b254db52e602df682e6fe285adbca4021d4fd49e43fc2a33bac273",
}
_CASES = ((F(8), F(2), F(3)), (F(7, 2), F(1, 3), F(5, 4)))


def _model(heavy: F, light: F, speed: F) -> dict:
    if not all(isinstance(x, F) for x in (heavy, light, speed)) or not heavy > light > 0 or speed <= 0:
        raise ValueError("BSA317_POSITIVE_UNEQUAL_MASS_EQUAL_SPEED_REQUIRED")
    truck = (F(0), heavy * speed)
    car = (light * speed, F(0))
    truck_energy = heavy * speed * speed / 2
    car_energy = light * speed * speed / 2
    if not (truck[1] > car[0] > 0 and truck != car and
            truck[0] * car[0] + truck[1] * car[1] == 0 and
            truck_energy > car_energy > 0):
        raise ValueError("BSA317_VECTOR_AND_SCALAR_PHYSICS_FAILED")
    return {"heavyMass": str(heavy), "lightMass": str(light), "commonSpeed": str(speed),
            "truckEastNorthMomentum": list(map(str, truck)),
            "carEastNorthMomentum": list(map(str, car)),
            "truckMomentumMagnitude": str(truck[1]), "carMomentumMagnitude": str(car[0]),
            "truckKineticEnergy": str(truck_energy), "carKineticEnergy": str(car_energy),
            "momentumVectorsEqual": False, "kineticEnergyIsScalar": True}


def _models() -> list[dict]:
    return [_model(*case) for case in _CASES]


def independently_check_equal_speed_explanation_witness(proof: dict) -> None:
    if (not isinstance(proof, dict) or not isinstance(proof.get("taskId"), str) or
        len(proof["taskId"]) != 64 or proof.get("sourceSha256") != _SOURCE_SHA or
        proof.get("candidateSha256") != _CANDIDATE_SHA or
        proof.get("promptLocaleSha256") != _PROMPT or
        proof.get("explanationLocaleSha256") != _EXPLANATION or
        proof.get("models") != _models() or
        type(proof.get("sourcePageIndex")) is not int or proof["sourcePageIndex"] < 1 or
        any(not isinstance(proof.get(k), str) or len(proof[k]) != 64 for k in
            ("surfaceSha256", "sourcePassageSha256", "sourcePhysicsPremisesSha256")) or
        proof.get("academicTaskAccepted") is not False or
        proof.get("completeAcademicProofGatesStillOpen") != 90 or
        proof.get("newProviderCalls") != 0 or proof.get("publicationAuthorized") is not False or
        proof.get("witnessSha256") != _digest({k: v for k, v in proof.items() if k != "witnessSha256"})):
        raise ValueError("BSA317_UNTRUSTED_EQUAL_SPEED_EXPLANATION_WITNESS")
    for row in proof["models"]:
        if row != _model(F(row["heavyMass"]), F(row["lightMass"]), F(row["commonSpeed"])):
            raise ValueError("BSA317_EXACT_MODEL_RECOMPUTATION_FAILED")


def independently_prove_equal_speed_explanation(*, source_pdf: Path, candidate_path: Path) -> dict:
    if (source_pdf.is_symlink() or candidate_path.is_symlink() or
        not source_pdf.is_file() or not candidate_path.is_file() or
        sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA or
        sha256(candidate_path.read_bytes()).hexdigest() != _CANDIDATE_SHA):
        raise ValueError("BSA317_AUTHENTIC_ONE_SERWAY_SOURCE_AND_CANDIDATE_REQUIRED")
    axioms = _source_axioms(source_pdf, _SOURCE_SHA)
    if (axioms.get("linear momentum is a vector", 0) < 1 or
        axioms.get("defined to be the product of the mass and velocity", 0) < 1):
        raise ValueError("BSA317_ORIGINAL_VECTOR_MOMENTUM_PREMISES_MISSING")
    package = json.loads(candidate_path.read_text(encoding="utf8"))
    activities = package.get("activities")
    if not isinstance(activities, list) or len(activities) != 18 or activities[5].get("id") != _ACTIVITY:
        raise ValueError("BSA317_FROZEN_SIXTH_ACTIVITY_CHANGED")
    activity = activities[5]
    prompt = _locale_digests(activity.get("prompt"), _PROMPT)
    explanation = _locale_digests(activity.get("explanation"), _EXPLANATION)
    key = activity.get("answerKey", {})
    if key.get("correct") != "opt-a" or [o.get("id") for o in key.get("options", [])] != ["opt-a", "opt-b", "opt-c", "opt-d"]:
        raise ValueError("BSA317_FROZEN_SIXTH_ANSWER_KEY_CHANGED")
    pages = extract_pages(source_pdf)
    if sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA:
        raise ValueError("BSA317_SOURCE_CHANGED_DURING_EXTRACTION")
    anchor = _source_activity_anchors(pages=pages, activities=activities)[5]
    if anchor.get("activityId") != _ACTIVITY or anchor.get("uniquePagePassageLocated") is not True:
        raise ValueError("BSA317_ORIGINAL_SOURCE_ANCHOR_MISSING")
    queue = plan_full_semantic_proofs(package=package, source_sha256=_SOURCE_SHA)
    hits = [task for task in queue["tasks"] if task["activityId"] == _ACTIVITY and
            task["kind"] == "COMPLETE_SCIENTIFIC_MEANING" and task["surfacePath"] == "explanation"]
    if queue["taskCount"] != 429 or len(hits) != 1 or hits[0]["surfaceSha256"] != _digest(activity["explanation"]):
        raise ValueError("BSA317_CANONICAL_EXPLANATION_TASK_NOT_REDERIVED")
    body = {"taskId": hits[0]["taskId"], "sourceSha256": _SOURCE_SHA,
            "candidateSha256": _CANDIDATE_SHA, "surfaceSha256": hits[0]["surfaceSha256"],
            "sourcePageIndex": anchor["physicalPage"], "sourcePassageSha256": anchor["passageSha256"],
            "sourcePhysicsPremisesSha256": _digest(sorted(axioms.items())),
            "promptLocaleSha256": prompt, "explanationLocaleSha256": explanation,
            "models": _models(), "academicTaskAccepted": False,
            "completeAcademicProofGatesStillOpen": 90, "newProviderCalls": 0,
            "publicationAuthorized": False}
    proof = {**body, "witnessSha256": _digest(body)}
    independently_check_equal_speed_explanation_witness(proof)
    return proof

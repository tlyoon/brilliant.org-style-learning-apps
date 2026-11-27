"""MCQ06 exact vector countermodels, gated by the selected Serway source.

This produces independently checkable science witnesses. An owner admission
still requires the signed V36 task partition, exact CI and private receipt.
"""
from __future__ import annotations

from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path

from app_generator.validation.section91_formal_physics import (
    _CANDIDATE_SHA, _SOURCE_SHA, _source_axioms, _digest,
)
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs
from app_generator.validation.source_passages import extract_pages
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _source_activity_anchors

_ACTIVITY = "act-mcq-06-equal-speed-comparison"
_TASKS = {
    "opt-b": "e729b89c172882ce15ca2e54af1e620ad1596412ba3cbc7ec311259c659acf2f",
    "opt-c": "1469bceacdc52d6d5344964cd3da7bd28ba0829a07207f123782d9702750850e",
    "opt-d": "9bc676d041da69bf98fd6ab11879d24066df18a50ff5679fd55c0d559a27e1ef",
}
_PROMPT = {
    "en": "2b258a986462e33f1a520ef706b9299c8e8594b32cdd3748ff7d003d051431ef",
    "ms": "9a8368e7890dd3808aa3a3d09f05b89875987c4f9bf7362d208038f8bad94902",
    "zh": "c18a96cfe111c53bd648d024d82397a6b7a5d4bcf91fc5d7a4d41b6546481f54",
}
_OPTIONS = {
    "opt-b": {"en": "b43e97b881490142f3a911f32ad4ad153f8c15750282123419e599c3d609417f", "ms": "1ab00cce28e4d4acc7ae7ed05dc0aac449c45c3463bbfe4c0a7fb9a216dd5e09", "zh": "2d96a25d32d5c9be91648b4f30c317c4524b87e6c7fe840265ce7df3ba7d3bc8"},
    "opt-c": {"en": "2f59bf5f95277fb19daef7a36690cfbdd69d7fad591b8f73aeccd9ac6128c876", "ms": "9c2e1cdc6e1a3e059dec0c2ebd8c5ae82b9b7ec6a198828ef6a6646579d6459e", "zh": "a13d63dc650024f3de855960d7d7001cdcdd15c83cdf8a494bbc650c9bf84ad2"},
    "opt-d": {"en": "0e0e1845ec300fb1dbedeb8579217ebc2d7e191e97a56c65cc1e688f530fc5bf", "ms": "4724910c90ea02dd457d8ebb4b484cdfd4bb991a10eb5f602b3e7c63fd612e65", "zh": "d302b68d07820d9a65b108a36a38b4a4939922889296b49303b12ecac6254b90"},
}
_CLAIMS = {
    "opt-b": "MOMENTUM_HAS_NO_DIRECTION",
    "opt-c": "EQUAL_SPEED_IMPLIES_EQUAL_VECTOR_MOMENTUM",
    "opt-d": "LIGHTER_BODY_HAS_GREATER_MOMENTUM_MAGNITUDE",
}
_CASES = ((F(8), F(2), F(3)), (F(7, 2), F(1, 3), F(5, 4)))


def _locale_digests(value: dict, expected: dict) -> dict:
    if not isinstance(value, dict) or set(value) != {"en", "ms", "zh"}:
        raise ValueError("BSA284_COMPLETE_THREE_LANGUAGE_SENTENCE_REQUIRED")
    actual = {lang: sha256(value[lang].encode("utf8")).hexdigest()
              for lang in ("en", "ms", "zh") if isinstance(value[lang], str) and value[lang].strip()}
    if actual != expected:
        raise ValueError("BSA284_FROZEN_LOCALIZED_PROPOSITION_CHANGED")
    return actual


def _model(truck_mass: F, car_mass: F, speed: F) -> dict:
    if not all(isinstance(x, F) for x in (truck_mass, car_mass, speed)) or not truck_mass > car_mass > 0 or speed <= 0:
        raise ValueError("BSA284_NONDEGENERATE_EQUAL_SPEED_MODEL_REQUIRED")
    truck = (F(0), truck_mass * speed)  # east, north
    car = (car_mass * speed, F(0))
    if not (truck[1] > car[0] > 0 and truck != car and sum(a*b for a, b in zip(truck, car)) == 0):
        raise ValueError("BSA284_VECTOR_MOMENTUM_DERIVATION_FAILED")
    return {"truckMass": str(truck_mass), "carMass": str(car_mass), "commonSpeed": str(speed),
            "truckMomentumEastNorth": list(map(str, truck)), "carMomentumEastNorth": list(map(str, car)),
            "truckMagnitude": str(truck[1]), "carMagnitude": str(car[0]),
            "dotProduct": "0", "vectorsEqual": False, "momentumHasDirection": True}


def _models() -> list[dict]:
    return [_model(*case) for case in _CASES]


def independently_check_equal_speed_witness(proof: dict) -> None:
    if not isinstance(proof, dict) or proof.get("optionId") not in _TASKS:
        raise ValueError("BSA284_UNREGISTERED_EQUAL_SPEED_OPTION")
    option = proof["optionId"]
    if (proof.get("taskId") != _TASKS[option] or proof.get("falseClaim") != _CLAIMS[option]
            or proof.get("promptLocaleSha256") != _PROMPT or proof.get("optionLocaleSha256") != _OPTIONS[option]
            or proof.get("sourceSha256") != _SOURCE_SHA or proof.get("candidateSha256") != _CANDIDATE_SHA
            or proof.get("models") != _models() or proof.get("academicTaskAccepted") is not False
            or proof.get("completeAcademicProofGatesStillOpen") != 90
            or proof.get("newProviderCalls") != 0 or proof.get("publicationAuthorized") is not False):
        raise ValueError("BSA284_UNTRUSTED_EQUAL_SPEED_WITNESS")
    if proof.get("witnessSha256") != _digest({k: v for k, v in proof.items() if k != "witnessSha256"}):
        raise ValueError("BSA284_WITNESS_DIGEST_CHANGED")
    for row in proof["models"]:
        if row != _model(F(row["truckMass"]), F(row["carMass"]), F(row["commonSpeed"])):
            raise ValueError("BSA284_EXACT_RATIONAL_RECOMPUTATION_FAILED")


def independently_prove_equal_speed_false_option(*, source_pdf: Path, candidate_path: Path, option_id: str) -> dict:
    if option_id not in _TASKS:
        raise ValueError("BSA284_UNREGISTERED_EQUAL_SPEED_OPTION")
    if (source_pdf.is_symlink() or candidate_path.is_symlink() or not source_pdf.is_file()
            or not candidate_path.is_file() or sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA
            or sha256(candidate_path.read_bytes()).hexdigest() != _CANDIDATE_SHA):
        raise ValueError("BSA284_AUTHENTIC_ONE_SERWAY_SOURCE_AND_CANDIDATE_REQUIRED")
    axioms = _source_axioms(source_pdf, _SOURCE_SHA)
    if axioms.get("linear momentum is a vector", 0) < 1 or axioms.get("defined to be the product of the mass and velocity", 0) < 1:
        raise ValueError("BSA284_ORIGINAL_VECTOR_MOMENTUM_PREMISES_MISSING")
    package = json.loads(candidate_path.read_text(encoding="utf8"))
    activities = package.get("activities")
    if not isinstance(activities, list) or len(activities) != 18 or activities[5].get("id") != _ACTIVITY:
        raise ValueError("BSA284_FROZEN_MC_Q06_ACTIVITY_CHANGED")
    activity = activities[5]
    prompt = _locale_digests(activity.get("prompt"), _PROMPT)
    key = activity.get("answerKey", {})
    options = key.get("options", [])
    if key.get("correct") != "opt-a" or [o.get("id") for o in options] != ["opt-a", "opt-b", "opt-c", "opt-d"]:
        raise ValueError("BSA284_FROZEN_MC_Q06_ANSWER_KEY_CHANGED")
    position = ("opt-b", "opt-c", "opt-d").index(option_id) + 1
    locale = _locale_digests(options[position].get("label"), _OPTIONS[option_id])
    pages = extract_pages(source_pdf)
    anchors = _source_activity_anchors(pages=pages, activities=activities)
    anchor = anchors[5]
    if anchor.get("activityId") != _ACTIVITY or anchor.get("uniquePagePassageLocated") is not True:
        raise ValueError("BSA284_ORIGINAL_SOURCE_ANCHOR_MISSING")
    queue = plan_full_semantic_proofs(package=package, source_sha256=_SOURCE_SHA)
    path = f"answerKey/options/{position}/label"
    tasks = [task for task in queue["tasks"] if task["activityId"] == _ACTIVITY
             and task["kind"] == "MCQ_DISTRACTOR_SCIENCE" and task["surfacePath"] == path]
    if (queue["taskCount"] != 429 or len(tasks) != 1 or tasks[0]["taskId"] != _TASKS[option_id]
            or tasks[0]["surfaceSha256"] != _digest(options[position]["label"])):
        raise ValueError("BSA284_CANONICAL_MC_Q06_TASK_NOT_REDERIVED")
    body = {"taskId": tasks[0]["taskId"], "optionId": option_id, "falseClaim": _CLAIMS[option_id],
            "sourceSha256": _SOURCE_SHA, "candidateSha256": _CANDIDATE_SHA,
            "sourcePageIndex": anchor["physicalPage"], "sourcePassageSha256": anchor["passageSha256"],
            "sourcePhysicsPremisesSha256": _digest(sorted(axioms.items())),
            "promptLocaleSha256": prompt, "optionLocaleSha256": locale, "models": _models(),
            "academicTaskAccepted": False, "completeAcademicProofGatesStillOpen": 90,
            "newProviderCalls": 0, "publicationAuthorized": False}
    proof = {**body, "witnessSha256": _digest(body)}
    independently_check_equal_speed_witness(proof)
    return proof

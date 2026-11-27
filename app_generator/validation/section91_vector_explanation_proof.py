"""Source-bound, exact-vector proof of the frozen MCQ01 explanation.

This proves one COMPLETE_SCIENTIFIC_MEANING task. It does not certify
translation quality, other learner surfaces, diagrams, or whole activities.
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

_ACTIVITY = "act-mcq-01-vector-nature"
_TASK = "da45c6d7a9b88fedfa2c20901412a498fc98f6fb180dfb2eb85638421ce4596b"
_PROMPT = {"en":"10ffa388eb4ef6286a7988378ac7e815436e8db484ead980d1137c0e1d02f1df", "ms":"8c5439d563be2d965007cde4947f664b44642fca55239348ac6f4fc946207b98", "zh":"39d2fb621f705b8f1d22ebc99426a3fffc9082cf77aeb09ae78fa1050af4e2db"}
_EXPLANATION = {"en":"73e8ce6c11400be0ca7ede4ef2bf3021e8d5f084c2589f1bdbeebff86a61264b", "ms":"e1af8998cbad85d40ea7db0803bc1be2f111c5efb4d98ea8aa12f374653f947b", "zh":"544800f6846c6167d1db334562e322637a34fe03e736a196d80039b03472be3d"}
_CASES = ((F(2), F(3)), (F(7, 3), F(5, 2)))


def _locale_hashes(value: dict, expected: dict) -> dict:
    if not isinstance(value, dict) or set(value) != {"en", "ms", "zh"} or any(
        not isinstance(v, str) or not v.strip() for v in value.values()
    ):
        raise ValueError("BSA292_COMPLETE_TRILINGUAL_EXPLANATION_REQUIRED")
    result = {lang: sha256(value[lang].encode("utf8")).hexdigest() for lang in ("en", "ms", "zh")}
    if result != expected:
        raise ValueError("BSA292_FROZEN_EXPLANATION_MEANING_CHANGED")
    return result


def _model(mass: F, speed: F) -> dict:
    if not isinstance(mass, F) or not isinstance(speed, F) or mass <= 0 or speed <= 0:
        raise ValueError("BSA292_POSITIVE_EXACT_MASS_AND_SPEED_REQUIRED")
    velocity_a, velocity_b = speed, -speed
    momentum_a, momentum_b = mass * velocity_a, mass * velocity_b
    if not (momentum_a > 0 and momentum_b < 0 and
            momentum_a == -momentum_b and momentum_a + momentum_b == 0 and
            abs(momentum_a) == abs(momentum_b) and
            momentum_a * velocity_a > 0 and momentum_b * velocity_b > 0):
        raise ValueError("BSA292_VECTOR_EXPLANATION_NOT_DERIVED")
    return {"mass": str(mass), "speed": str(speed),
            "velocityA": str(velocity_a), "velocityB": str(velocity_b),
            "momentumA": str(momentum_a), "momentumB": str(momentum_b),
            "momentumSum": str(momentum_a + momentum_b),
            "equalMagnitude": True, "oppositeDirections": True,
            "momentumParallelToVelocity": True}


def _models() -> list[dict]:
    return [_model(*case) for case in _CASES]


def independently_check_vector_explanation_witness(proof: dict) -> None:
    if not isinstance(proof, dict) or (
        proof.get("taskId") != _TASK or proof.get("sourceSha256") != _SOURCE_SHA or
        proof.get("candidateSha256") != _CANDIDATE_SHA or
        proof.get("promptLocaleSha256") != _PROMPT or
        proof.get("explanationLocaleSha256") != _EXPLANATION or
        proof.get("models") != _models() or
        type(proof.get("sourcePageIndex")) is not int or proof["sourcePageIndex"] < 1 or
        any(not isinstance(proof.get(k), str) or len(proof[k]) != 64 for k in
            ("surfaceSha256", "sourcePassageSha256", "sourcePhysicsPremisesSha256")) or
        proof.get("academicTaskAccepted") is not False or
        proof.get("completeAcademicProofGatesStillOpen") != 90 or
        proof.get("publicationAuthorized") is not False or
        proof.get("newProviderCalls") != 0 or
        proof.get("witnessSha256") != _digest({k:v for k,v in proof.items() if k != "witnessSha256"})
    ):
        raise ValueError("BSA292_UNTRUSTED_VECTOR_EXPLANATION_WITNESS")
    for row in proof["models"]:
        if row != _model(F(row["mass"]), F(row["speed"])):
            raise ValueError("BSA292_VECTOR_EXPLANATION_RECOMPUTATION_FAILED")


def independently_prove_vector_explanation(*, source_pdf: Path, candidate_path: Path) -> dict:
    candidate_bytes = candidate_path.read_bytes() if candidate_path.is_file() and not candidate_path.is_symlink() else b""
    if (source_pdf.is_symlink() or not source_pdf.is_file() or
        not candidate_bytes or sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA or
        sha256(candidate_bytes).hexdigest() != _CANDIDATE_SHA):
        raise ValueError("BSA292_AUTHENTIC_ONE_SERWAY_SOURCE_AND_CANDIDATE_REQUIRED")
    axioms = _source_axioms(source_pdf, _SOURCE_SHA)
    if (axioms.get("linear momentum is a vector", 0) < 1 or
        axioms.get("defined to be the product of the mass and velocity", 0) < 1):
        raise ValueError("BSA292_ORIGINAL_VECTOR_MOMENTUM_PREMISES_MISSING")
    package = json.loads(candidate_bytes.decode("utf8"))
    activities = package.get("activities")
    if not isinstance(activities, list) or len(activities) != 18 or activities[0].get("id") != _ACTIVITY:
        raise ValueError("BSA292_FROZEN_FIRST_ACTIVITY_CHANGED")
    activity = activities[0]
    prompt = _locale_hashes(activity.get("prompt"), _PROMPT)
    explanation = _locale_hashes(activity.get("explanation"), _EXPLANATION)
    key = activity.get("answerKey", {})
    if key.get("correct") != "opt-a" or [o.get("id") for o in key.get("options", [])] != ["opt-a", "opt-b", "opt-c", "opt-d"]:
        raise ValueError("BSA292_FROZEN_VECTOR_ANSWER_KEY_CHANGED")
    anchors = _source_activity_anchors(pages=extract_pages(source_pdf), activities=activities)
    if sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA:
        raise ValueError("BSA292_SOURCE_CHANGED_DURING_EXTRACTION")
    anchor = anchors[0]
    if anchor.get("activityId") != _ACTIVITY or anchor.get("uniquePagePassageLocated") is not True:
        raise ValueError("BSA292_ORIGINAL_SOURCE_ANCHOR_MISSING")
    queue = plan_full_semantic_proofs(package=package, source_sha256=_SOURCE_SHA)
    tasks = [t for t in queue["tasks"] if t["activityId"] == _ACTIVITY and
             t["kind"] == "COMPLETE_SCIENTIFIC_MEANING" and t["surfacePath"] == "explanation"]
    if (queue["taskCount"] != 429 or len(tasks) != 1 or tasks[0]["taskId"] != _TASK or
        tasks[0]["surfaceSha256"] != _digest(activity["explanation"])):
        raise ValueError("BSA292_CANONICAL_EXPLANATION_TASK_NOT_REDERIVED")
    body = {"taskId": _TASK, "sourceSha256": _SOURCE_SHA, "candidateSha256": _CANDIDATE_SHA,
            "surfaceSha256": tasks[0]["surfaceSha256"],
            "sourcePageIndex": anchor["physicalPage"], "sourcePassageSha256": anchor["passageSha256"],
            "sourcePhysicsPremisesSha256": _digest(sorted(axioms.items())),
            "promptLocaleSha256": prompt, "explanationLocaleSha256": explanation,
            "models": _models(), "academicTaskAccepted": False,
            "completeAcademicProofGatesStillOpen": 90, "newProviderCalls": 0,
            "publicationAuthorized": False}
    proof = {**body, "witnessSha256": _digest(body)}
    independently_check_vector_explanation_witness(proof)
    return proof

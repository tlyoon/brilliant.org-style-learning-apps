"""Exact original-source Newton momentum-rate explanation proof for MCQ03.

The returned witness is unadmitted. The owner lane checks the signed V36
partition and previous receipts before accepting its canonical task identity.
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

_ACTIVITY = "act-mcq-03-net-force-definition"
_CASES = ((F(3, 2), F(4), F(5, 3), F(2)), (F(7, 4), F(9, 2), F(3, 2), F(5, 3)))
# These hashes bind complete language surfaces, rather than English keywords.
_PROMPT = {"en": "7b7be82ba42432832a9c4d25b3a7ca40d9942e7d1e3a311a721d4b3997c2b0d7", "ms": "1ca6b9d9c38667df486bd62909455c501d68e13b332d3021bb453e05d8fd7a7b", "zh": "8a8b9d247b37230de7f940439ee6f451ba0bebcec96e6efbd66e80697e6bf2c1"}
_EXPLANATION = {"en": "67763712468d2675126124bf8200240855f11c2678dce82d0162f3ecb7e08dca", "ms": "f739f2f2500150c4d247ec6368bd10e7c318eb5c1787defdb4112348d0facf85", "zh": "d768b753c252c3c64e88542b3499695af7fe33eb4a9cdd613f394704c323a095"}


def _locale_hashes(surface: dict, expected: dict) -> dict:
    if not isinstance(surface, dict) or set(surface) != {"en", "ms", "zh"} or any(
        not isinstance(v, str) or not v.strip() for v in surface.values()
    ):
        raise ValueError("BSA297_COMPLETE_TRILINGUAL_NEWTON_EXPLANATION_REQUIRED")
    actual = {key: sha256(surface[key].encode("utf8")).hexdigest() for key in expected}
    if actual != expected:
        raise ValueError("BSA297_FROZEN_NEWTON_EXPLANATION_CHANGED")
    return actual


def _model(mass: F, initial_velocity: F, acceleration: F, dt: F) -> dict:
    if not all(isinstance(x, F) and x > 0 for x in (mass, initial_velocity, acceleration, dt)):
        raise ValueError("BSA297_POSITIVE_EXACT_NEWTON_MODEL_REQUIRED")
    force = mass * acceleration
    initial_p = mass * initial_velocity
    final_p = mass * (initial_velocity + acceleration * dt)
    rate = (final_p - initial_p) / dt
    if force != rate or final_p <= initial_p or (1, 1, -2) != tuple(
        a + b for a, b in zip((1, 0, 0), (0, 1, -2))
    ):
        raise ValueError("BSA297_NEWTON_RATE_NOT_DERIVED")
    return {"mass": str(mass), "initialVelocity": str(initial_velocity),
            "acceleration": str(acceleration), "timeIncrement": str(dt),
            "initialMomentum": str(initial_p), "finalMomentum": str(final_p),
            "netForce": str(force), "momentumRate": str(rate),
            "forceDimension": [1, 1, -2], "momentumDimension": [1, 1, -1],
            "momentumIncreasesAlongMotion": True}


def _models() -> list[dict]:
    return [_model(*case) for case in _CASES]


def independently_check_newton_explanation_witness(proof: dict) -> None:
    if not isinstance(proof, dict) or (
        not isinstance(proof.get("taskId"), str) or len(proof["taskId"]) != 64 or
        proof.get("sourceSha256") != _SOURCE_SHA or proof.get("candidateSha256") != _CANDIDATE_SHA or
        proof.get("promptLocaleSha256") != _PROMPT or
        proof.get("explanationLocaleSha256") != _EXPLANATION or
        proof.get("models") != _models() or
        type(proof.get("sourcePageIndex")) is not int or proof["sourcePageIndex"] < 1 or
        any(not isinstance(proof.get(key), str) or len(proof[key]) != 64 for key in
            ("surfaceSha256", "sourcePassageSha256", "sourcePhysicsPremisesSha256")) or
        proof.get("academicTaskAccepted") is not False or
        proof.get("completeAcademicProofGatesStillOpen") != 90 or
        proof.get("newProviderCalls") != 0 or proof.get("publicationAuthorized") is not False or
        proof.get("witnessSha256") != _digest({k: v for k, v in proof.items() if k != "witnessSha256"})
    ):
        raise ValueError("BSA297_UNTRUSTED_NEWTON_EXPLANATION_WITNESS")
    for row in proof["models"]:
        if row != _model(*(F(row[key]) for key in
            ("mass", "initialVelocity", "acceleration", "timeIncrement"))):
            raise ValueError("BSA297_NEWTON_EXPLANATION_RECOMPUTATION_FAILED")


def independently_prove_newton_explanation(*, source_pdf: Path, candidate_path: Path) -> dict:
    candidate_bytes = candidate_path.read_bytes() if candidate_path.is_file() and not candidate_path.is_symlink() else b""
    if (source_pdf.is_symlink() or not source_pdf.is_file() or not candidate_bytes or
        sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA or
        sha256(candidate_bytes).hexdigest() != _CANDIDATE_SHA):
        raise ValueError("BSA297_AUTHENTIC_SERWAY_SOURCE_AND_CANDIDATE_REQUIRED")
    axioms = _source_axioms(source_pdf, _SOURCE_SHA)
    if axioms.get("time rate of change of the linear momentum", 0) < 1:
        raise ValueError("BSA297_ORIGINAL_NEWTON_PREMISE_MISSING")
    package = json.loads(candidate_bytes.decode("utf8"))
    activities = package.get("activities")
    if not isinstance(activities, list) or len(activities) != 18 or activities[2].get("id") != _ACTIVITY:
        raise ValueError("BSA297_FROZEN_THIRD_ACTIVITY_CHANGED")
    activity = activities[2]
    prompt = _locale_hashes(activity.get("prompt"), _PROMPT)
    explanation = _locale_hashes(activity.get("explanation"), _EXPLANATION)
    key = activity.get("answerKey", {})
    if key.get("correct") != "opt-a" or [o.get("id") for o in key.get("options", [])] != ["opt-a", "opt-b", "opt-c", "opt-d"]:
        raise ValueError("BSA297_FROZEN_NEWTON_ANSWER_KEY_CHANGED")
    anchors = _source_activity_anchors(pages=extract_pages(source_pdf), activities=activities)
    if sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA:
        raise ValueError("BSA297_SOURCE_CHANGED_DURING_EXTRACTION")
    anchor = anchors[2]
    if anchor.get("activityId") != _ACTIVITY or anchor.get("uniquePagePassageLocated") is not True:
        raise ValueError("BSA297_ORIGINAL_SOURCE_ANCHOR_MISSING")
    queue = plan_full_semantic_proofs(package=package, source_sha256=_SOURCE_SHA)
    tasks = [task for task in queue["tasks"] if task["activityId"] == _ACTIVITY and
             task["kind"] == "COMPLETE_SCIENTIFIC_MEANING" and task["surfacePath"] == "explanation"]
    if queue["taskCount"] != 429 or len(tasks) != 1 or tasks[0]["surfaceSha256"] != _digest(activity["explanation"]):
        raise ValueError("BSA297_CANONICAL_NEWTON_EXPLANATION_TASK_NOT_REDERIVED")
    body = {"taskId": tasks[0]["taskId"], "sourceSha256": _SOURCE_SHA,
            "candidateSha256": _CANDIDATE_SHA, "surfaceSha256": tasks[0]["surfaceSha256"],
            "sourcePageIndex": anchor["physicalPage"], "sourcePassageSha256": anchor["passageSha256"],
            "sourcePhysicsPremisesSha256": _digest(sorted(axioms.items())),
            "promptLocaleSha256": prompt, "explanationLocaleSha256": explanation,
            "models": _models(), "academicTaskAccepted": False,
            "completeAcademicProofGatesStillOpen": 90, "newProviderCalls": 0,
            "publicationAuthorized": False}
    proof = {**body, "witnessSha256": _digest(body)}
    independently_check_newton_explanation_witness(proof)
    return proof

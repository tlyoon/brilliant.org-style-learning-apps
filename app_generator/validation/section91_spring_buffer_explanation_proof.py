"""Source-bound MCQ09 explanation: scalar energy conversion and vector impulse."""
from __future__ import annotations

from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path

from app_generator.validation.section91_formal_physics import _SOURCE_SHA, _CANDIDATE_SHA, _source_axioms, _digest
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs
from app_generator.validation.source_passages import extract_pages
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _source_activity_anchors
from app_generator.validation.section91_spring_buffer_false_options_proof import _ACTIVITY, _PROMPT, _locales

_EXPLANATION = {
    "en": "c445ef43584afc5ae30e4c97d7e1f3d605e43be633639f4481430707def7046f",
    "ms": "39cc8ea37975aeda2f651b53e33771b58c17e6d3c1276d615b067b5136d5b3ff",
    "zh": "5d294a62fbf364a2706a46c217230d32b7dd28e926d584d6d7bdb191e34d61db",
}
_LAW = "K_initial=U_spring+Q;delta_p_pod=-J_rail;delta_p_rail=J_rail"


def _check_conversion(mass: F, speed: F, duration: F, stored_fraction: F) -> dict:
    """Derive energy and momentum balances for arbitrary exact admissible values."""
    if (not all(isinstance(x, F) and x > 0 for x in (mass, speed, duration))
            or not isinstance(stored_fraction, F) or not F(0) <= stored_fraction <= F(1)):
        raise ValueError("BSA320_EXACT_CONVERSION_DOMAIN_REQUIRED")
    initial_p = mass * speed
    initial_k = mass * speed * speed / 2
    spring = stored_fraction * initial_k
    heat = (1 - stored_fraction) * initial_k
    pod_impulse = -initial_p
    rail_impulse = initial_p
    force = pod_impulse / duration
    if not (initial_k == spring + heat and initial_p + pod_impulse == 0
            and pod_impulse + rail_impulse == 0 and force * duration == pod_impulse
            and initial_p > 0 and spring >= 0 and heat >= 0):
        raise ValueError("BSA320_ENERGY_IMPULSE_BALANCE_FAILED")
    return {"mass": str(mass), "speed": str(speed), "duration": str(duration),
            "springFraction": str(stored_fraction), "initialMomentum": str(initial_p),
            "initialKineticEnergy": str(initial_k), "springPotentialEnergy": str(spring),
            "thermalEnergy": str(heat), "podImpulse": str(pod_impulse),
            "railImpulse": str(rail_impulse), "averagePodForce": str(force),
            "momentumDimension": "M L T^-1", "energyDimension": "M L^2 T^-2"}


def _cases() -> list[dict]:
    return [_check_conversion(F(3), F(2), F(2), F(1)),
            _check_conversion(F(5, 2), F(4, 3), F(7, 3), F(3, 4))]


def independently_check_spring_buffer_explanation_witness(proof: dict) -> None:
    if (not isinstance(proof, dict) or not isinstance(proof.get("taskId"), str)
            or len(proof["taskId"]) != 64
            or any(c not in "0123456789abcdef" for c in proof["taskId"])
            or proof.get("sourceSha256") != _SOURCE_SHA
            or proof.get("candidateSha256") != _CANDIDATE_SHA
            or proof.get("promptLocaleSha256") != _PROMPT
            or proof.get("explanationLocaleSha256") != _EXPLANATION
            or proof.get("models") != _cases() or proof.get("generalLaw") != _LAW
            or type(proof.get("sourcePageIndex")) is not int or proof["sourcePageIndex"] < 1
            or any(not isinstance(proof.get(k), str) or len(proof[k]) != 64 for k in
                   ("surfaceSha256", "sourcePassageSha256", "sourcePhysicsPremisesSha256"))
            or proof.get("academicTaskAccepted") is not False
            or proof.get("completeAcademicProofGatesStillOpen") != 90
            or proof.get("newProviderCalls") != 0 or proof.get("publicationAuthorized") is not False
            or proof.get("witnessSha256") != _digest({k: v for k, v in proof.items() if k != "witnessSha256"})):
        raise ValueError("BSA320_UNTRUSTED_SPRING_EXPLANATION_WITNESS")
    for row in proof["models"]:
        keys = ("mass", "speed", "duration", "springFraction")
        try:
            reproduced = _check_conversion(*(F(row[k]) for k in keys))
        except (KeyError, ValueError, TypeError, ZeroDivisionError) as exc:
            raise ValueError("BSA320_INVALID_EXACT_CONVERSION_MODEL") from exc
        if row != reproduced:
            raise ValueError("BSA320_CONVERSION_MODEL_TAMPERED")


def independently_prove_spring_buffer_explanation(*, source_pdf: Path, candidate_path: Path) -> dict:
    candidate_bytes = candidate_path.read_bytes() if candidate_path.is_file() and not candidate_path.is_symlink() else b""
    if (source_pdf.is_symlink() or not source_pdf.is_file() or not candidate_bytes
            or sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA
            or sha256(candidate_bytes).hexdigest() != _CANDIDATE_SHA):
        raise ValueError("BSA320_AUTHENTIC_ONE_SERWAY_SOURCE_AND_CANDIDATE_REQUIRED")
    axioms = _source_axioms(source_pdf, _SOURCE_SHA)
    if (axioms.get("kinetic energy can transform", 0) < 1
            or axioms.get("only one type of linear momentum", 0) < 1
            or axioms.get("third law", 0) < 1
            or axioms.get("time rate of change of the linear momentum", 0) < 1
            or axioms.get("defined to be the product of the mass and velocity", 0) < 1):
        raise ValueError("BSA320_ORIGINAL_ENERGY_MOMENTUM_PREMISES_MISSING")
    package = json.loads(candidate_bytes.decode("utf8"))
    activities = package.get("activities")
    if not isinstance(activities, list) or len(activities) != 18 or activities[8].get("id") != _ACTIVITY:
        raise ValueError("BSA320_FROZEN_NINTH_ACTIVITY_CHANGED")
    activity = activities[8]
    prompt = _locales(activity.get("prompt"), _PROMPT)
    explanation = _locales(activity.get("explanation"), _EXPLANATION)
    key = activity.get("answerKey", {})
    if (key.get("correct") != "opt-ke-transforms-momentum-transfers" or
            [o.get("id") for o in key.get("options", [])] !=
            ["opt-ke-transforms-momentum-transfers", "opt-potential-momentum-stored",
             "opt-both-turn-to-heat", "opt-momentum-conserved-internally"]):
        raise ValueError("BSA320_FROZEN_NINTH_ANSWER_KEY_CHANGED")
    pages = extract_pages(source_pdf)
    if sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA:
        raise ValueError("BSA320_SOURCE_CHANGED_DURING_EXTRACTION")
    anchor = _source_activity_anchors(pages=pages, activities=activities)[8]
    if anchor.get("activityId") != _ACTIVITY or anchor.get("uniquePagePassageLocated") is not True:
        raise ValueError("BSA320_ORIGINAL_SOURCE_ANCHOR_MISSING")
    queue = plan_full_semantic_proofs(package=package, source_sha256=_SOURCE_SHA)
    hits = [t for t in queue["tasks"] if t["activityId"] == _ACTIVITY and
            t["kind"] == "COMPLETE_SCIENTIFIC_MEANING" and t["surfacePath"] == "explanation"]
    if queue["taskCount"] != 429 or len(hits) != 1 or hits[0]["surfaceSha256"] != _digest(activity["explanation"]):
        raise ValueError("BSA320_CANONICAL_EXPLANATION_TASK_NOT_REDERIVED")
    body = {"taskId": hits[0]["taskId"], "sourceSha256": _SOURCE_SHA,
            "candidateSha256": _CANDIDATE_SHA, "surfaceSha256": hits[0]["surfaceSha256"],
            "sourcePageIndex": anchor["physicalPage"], "sourcePassageSha256": anchor["passageSha256"],
            "sourcePhysicsPremisesSha256": _digest(sorted(axioms.items())),
            "promptLocaleSha256": prompt, "explanationLocaleSha256": explanation,
            "models": _cases(), "generalLaw": _LAW, "academicTaskAccepted": False,
            "completeAcademicProofGatesStillOpen": 90, "newProviderCalls": 0,
            "publicationAuthorized": False}
    proof = {**body, "witnessSha256": _digest(body)}
    independently_check_spring_buffer_explanation_witness(proof)
    return proof

"""Source-bound exact proof of the complete MCQ07 equal-energy explanation.

The compared quantity is momentum magnitude, as fixed by the full prompt and
answer key. A pair of examples alone does not prove the universal conclusion;
the identity |p|² = 2mK supplies the general argument.
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
from app_generator.validation.section91_equal_energy_false_options_proof import _ACTIVITY, _PROMPT, _locale_hashes

_EXPLANATION = {
    "en": "aa7ba9c65e59cdb693be12b54f37edb53b256f08426d781889ed1a8026568b21",
    "ms": "fdfad1beb9cf772eed214badd392980ec2beddb76ce34daef24758f0ddbf9d51",
    "zh": "108fc134f0440ac9dc3581d64d9ad100f3c54124c296118b29496e58a9ef5b10",
}
_CASES = ((F(8), F(1), F(2), F(2)), (F(25), F(1, 5), F(1), F(1)))


def _model(heavy_mass: F, heavy_speed: F, light_mass: F, light_speed: F) -> dict:
    values = (heavy_mass, heavy_speed, light_mass, light_speed)
    if not all(isinstance(v, F) and v > 0 for v in values) or heavy_mass <= light_mass:
        raise ValueError("BSA318_POSITIVE_HEAVIER_MASS_REQUIRED")
    heavy_energy = heavy_mass * heavy_speed**2 / 2
    light_energy = light_mass * light_speed**2 / 2
    heavy_momentum = heavy_mass * heavy_speed
    light_momentum = light_mass * light_speed
    if not (heavy_energy == light_energy > 0 and heavy_speed < light_speed and
            heavy_momentum > light_momentum > 0 and
            heavy_momentum**2 == 2 * heavy_mass * heavy_energy and
            light_momentum**2 == 2 * light_mass * light_energy):
        raise ValueError("BSA318_EQUAL_ENERGY_MOMENTUM_MAGNITUDE_NOT_DERIVED")
    return {"heavyMass": str(heavy_mass), "heavySpeed": str(heavy_speed),
            "lightMass": str(light_mass), "lightSpeed": str(light_speed),
            "heavyKineticEnergy": str(heavy_energy), "lightKineticEnergy": str(light_energy),
            "heavyMomentumMagnitude": str(heavy_momentum),
            "lightMomentumMagnitude": str(light_momentum)}


def _models() -> list[dict]:
    return [_model(*case) for case in _CASES]


def _equal_energy_order_theorem(heavy_mass: F, light_mass: F, energy: F) -> bool:
    """For arbitrary positive exact inputs, compare squared magnitudes.

    Squaring preserves the order of nonnegative momentum magnitudes, and
    p² = (mv)² = m²(2K/m) = 2mK for each body.
    """
    if not all(isinstance(x, F) for x in (heavy_mass, light_mass, energy)) or not heavy_mass > light_mass > 0 or energy <= 0:
        raise ValueError("BSA318_UNIVERSAL_THEOREM_DOMAIN_REQUIRED")
    return 2 * energy * (heavy_mass - light_mass) > 0


def _check_model(row: dict) -> None:
    keys = ("heavyMass", "heavySpeed", "lightMass", "lightSpeed")
    if row != _model(*(F(row[key]) for key in keys)):
        raise ValueError("BSA318_EQUAL_ENERGY_MODEL_TAMPERED")
    mh, vh, ml, vl = (F(row[key]) for key in keys)
    energy = F(row["heavyKineticEnergy"])
    # This is the universal nonzero-energy ranking, checked with exact values.
    if not (energy == F(row["lightKineticEnergy"]) > 0 and mh > ml > 0 and
            (mh * vh) ** 2 == 2 * mh * energy and
            (ml * vl) ** 2 == 2 * ml * energy and
            _equal_energy_order_theorem(mh, ml, energy) and
            2 * mh * energy > 2 * ml * energy):
        raise ValueError("BSA318_MOMENTUM_MAGNITUDE_THEOREM_FAILED")


def independently_check_equal_energy_explanation_witness(proof: dict) -> None:
    if (not isinstance(proof, dict) or not isinstance(proof.get("taskId"), str) or
        len(proof["taskId"]) != 64 or proof.get("sourceSha256") != _SOURCE_SHA or
        proof.get("candidateSha256") != _CANDIDATE_SHA or
        proof.get("promptLocaleSha256") != _PROMPT or
        proof.get("explanationLocaleSha256") != _EXPLANATION or
        proof.get("models") != _models() or
        proof.get("universalIdentity") != "momentum_magnitude_squared=2*mass*kinetic_energy" or
        type(proof.get("sourcePageIndex")) is not int or proof["sourcePageIndex"] < 1 or
        any(not isinstance(proof.get(key), str) or len(proof[key]) != 64 for key in
            ("surfaceSha256", "sourcePassageSha256", "sourcePhysicsPremisesSha256")) or
        proof.get("academicTaskAccepted") is not False or
        proof.get("completeAcademicProofGatesStillOpen") != 90 or
        proof.get("newProviderCalls") != 0 or proof.get("publicationAuthorized") is not False or
        proof.get("witnessSha256") != _digest({k: v for k, v in proof.items() if k != "witnessSha256"})):
        raise ValueError("BSA318_UNTRUSTED_EQUAL_ENERGY_EXPLANATION_WITNESS")
    for row in proof["models"]:
        _check_model(row)


def independently_prove_equal_energy_explanation(*, source_pdf: Path, candidate_path: Path) -> dict:
    if (source_pdf.is_symlink() or candidate_path.is_symlink() or
        not source_pdf.is_file() or not candidate_path.is_file() or
        sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA or
        sha256(candidate_path.read_bytes()).hexdigest() != _CANDIDATE_SHA):
        raise ValueError("BSA318_AUTHENTIC_ONE_SERWAY_SOURCE_AND_CANDIDATE_REQUIRED")
    axioms = _source_axioms(source_pdf, _SOURCE_SHA)
    if (axioms.get("linear momentum is a vector", 0) < 1 or
        axioms.get("defined to be the product of the mass and velocity", 0) < 1 or
        axioms.get("kinetic energy can transform", 0) < 1):
        raise ValueError("BSA318_ORIGINAL_MOMENTUM_ENERGY_PREMISES_MISSING")
    package = json.loads(candidate_path.read_text(encoding="utf8"))
    activities = package.get("activities")
    if not isinstance(activities, list) or len(activities) != 18 or activities[6].get("id") != _ACTIVITY:
        raise ValueError("BSA318_FROZEN_SEVENTH_ACTIVITY_CHANGED")
    activity = activities[6]
    prompt = _locale_hashes(activity.get("prompt"), _PROMPT)
    explanation = _locale_hashes(activity.get("explanation"), _EXPLANATION)
    key = activity.get("answerKey", {})
    options = key.get("options", [])
    if (key.get("correct") != "opt-transport-greater" or
        [o.get("id") for o in options] != ["opt-transport-greater", "opt-equal-momentum", "opt-scout-greater", "opt-cannot-determine"] or
        "magnitude" not in activity["prompt"]["en"].lower() or
        "magnitud" not in activity["prompt"]["ms"].lower() or
        "大小" not in activity["prompt"]["zh"] or
        "magnitude" not in options[0]["label"]["en"].lower()):
        raise ValueError("BSA318_FROZEN_MAGNITUDE_QUESTION_CHANGED")
    pages = extract_pages(source_pdf)
    if sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA:
        raise ValueError("BSA318_SOURCE_CHANGED_DURING_EXTRACTION")
    anchor = _source_activity_anchors(pages=pages, activities=activities)[6]
    if anchor.get("activityId") != _ACTIVITY or anchor.get("uniquePagePassageLocated") is not True:
        raise ValueError("BSA318_ORIGINAL_SOURCE_ANCHOR_MISSING")
    queue = plan_full_semantic_proofs(package=package, source_sha256=_SOURCE_SHA)
    hits = [task for task in queue["tasks"] if task["activityId"] == _ACTIVITY and
            task["kind"] == "COMPLETE_SCIENTIFIC_MEANING" and task["surfacePath"] == "explanation"]
    if queue["taskCount"] != 429 or len(hits) != 1 or hits[0]["surfaceSha256"] != _digest(activity["explanation"]):
        raise ValueError("BSA318_CANONICAL_EXPLANATION_TASK_NOT_REDERIVED")
    body = {"taskId": hits[0]["taskId"], "sourceSha256": _SOURCE_SHA,
            "candidateSha256": _CANDIDATE_SHA, "surfaceSha256": hits[0]["surfaceSha256"],
            "sourcePageIndex": anchor["physicalPage"], "sourcePassageSha256": anchor["passageSha256"],
            "sourcePhysicsPremisesSha256": _digest(sorted(axioms.items())),
            "promptLocaleSha256": prompt, "explanationLocaleSha256": explanation,
            "models": _models(), "universalIdentity": "momentum_magnitude_squared=2*mass*kinetic_energy",
            "academicTaskAccepted": False, "completeAcademicProofGatesStillOpen": 90,
            "newProviderCalls": 0, "publicationAuthorized": False}
    proof = {**body, "witnessSha256": _digest(body)}
    independently_check_equal_energy_explanation_witness(proof)
    return proof

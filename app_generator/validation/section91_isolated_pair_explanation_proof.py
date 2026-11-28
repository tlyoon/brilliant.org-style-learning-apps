"""Exact source-bound MCQ08 explanation proof; admission is owner-only."""
from __future__ import annotations

from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path

from app_generator.validation.section91_formal_physics import _SOURCE_SHA, _CANDIDATE_SHA, _source_axioms, _digest
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs
from app_generator.validation.source_passages import extract_pages
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _source_activity_anchors
from app_generator.validation.section91_isolated_pair_false_options_proof import _ACTIVITY, _PROMPT, _locales, _model, _models

_EXPLANATION = {
    "en": "210ac99095419c90ecb1f3f746cf8f6d2bb825fda482bc8e48e52d00dd20b21e",
    "ms": "2db8cfd9eaad8e1e3823076b997e7586110f1ef5b66feb8e3d39adb46f41d9d2",
    "zh": "3d85e1e4746bfa76f4019f4ce624d98b3ff3276783258cf8ebbf2a58fac9b9ef",
}


def _check_pair_law(nadia_mass: F, leo_mass: F, impulse: F, duration: F) -> None:
    """For arbitrary positive rational inputs, derive the two-body law."""
    if not all(isinstance(x, F) and x > 0 for x in (nadia_mass, leo_mass, impulse, duration)):
        raise ValueError("BSA319_POSITIVE_EXACT_PAIR_DOMAIN_REQUIRED")
    force_on_nadia = -impulse / duration
    force_on_leo = impulse / duration
    delta_nadia = force_on_nadia * duration
    delta_leo = force_on_leo * duration
    if not (force_on_nadia == -force_on_leo and
            delta_nadia + delta_leo == 0 and delta_nadia != 0 and
            delta_nadia == nadia_mass * (delta_nadia / nadia_mass) and
            force_on_nadia == delta_nadia / duration and
            force_on_nadia != 0):
        raise ValueError("BSA319_INTERNAL_IMPULSE_LAW_FAILED")


def _check_model(row: dict) -> None:
    keys = ("nadiaMass", "leoMass", "impulseMagnitude", "duration")
    try:
        args = tuple(F(row[key]) for key in keys)
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        raise ValueError("BSA319_EXACT_PAIR_MODEL_INVALID") from exc
    _check_pair_law(*args)
    if row != _model(*args):
        raise ValueError("BSA319_EXACT_PAIR_MODEL_TAMPERED")


def independently_check_isolated_pair_explanation_witness(proof: dict) -> None:
    if (not isinstance(proof, dict) or
        not isinstance(proof.get("taskId"), str) or len(proof["taskId"]) != 64 or
        any(c not in "0123456789abcdef" for c in proof["taskId"]) or
        proof.get("sourceSha256") != _SOURCE_SHA or proof.get("candidateSha256") != _CANDIDATE_SHA or
        proof.get("promptLocaleSha256") != _PROMPT or proof.get("explanationLocaleSha256") != _EXPLANATION or
        proof.get("models") != _models() or
        proof.get("generalLaw") != "delta_p_nadia=-J;delta_p_leo=J;delta_p_pair=0" or
        type(proof.get("sourcePageIndex")) is not int or proof["sourcePageIndex"] < 1 or
        any(not isinstance(proof.get(k), str) or len(proof[k]) != 64 for k in
            ("surfaceSha256", "sourcePassageSha256", "sourcePhysicsPremisesSha256")) or
        proof.get("academicTaskAccepted") is not False or
        proof.get("completeAcademicProofGatesStillOpen") != 90 or
        proof.get("newProviderCalls") != 0 or proof.get("publicationAuthorized") is not False or
        proof.get("witnessSha256") != _digest({k: v for k, v in proof.items() if k != "witnessSha256"})):
        raise ValueError("BSA319_UNTRUSTED_ISOLATED_PAIR_EXPLANATION_WITNESS")
    for row in proof["models"]:
        _check_model(row)


def independently_prove_isolated_pair_explanation(*, source_pdf: Path, candidate_path: Path) -> dict:
    candidate_bytes = candidate_path.read_bytes() if candidate_path.is_file() and not candidate_path.is_symlink() else b""
    if (source_pdf.is_symlink() or not source_pdf.is_file() or not candidate_bytes or
        sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA or
        sha256(candidate_bytes).hexdigest() != _CANDIDATE_SHA):
        raise ValueError("BSA319_AUTHENTIC_ONE_SERWAY_SOURCE_AND_CANDIDATE_REQUIRED")
    axioms = _source_axioms(source_pdf, _SOURCE_SHA)
    if (axioms.get("isolated system", 0) < 3 or axioms.get("third law", 0) < 1 or
        axioms.get("time rate of change of the linear momentum", 0) < 1 or
        axioms.get("defined to be the product of the mass and velocity", 0) < 1):
        raise ValueError("BSA319_ORIGINAL_PAIR_FORCE_PREMISES_MISSING")
    package = json.loads(candidate_bytes.decode("utf8"))
    activities = package.get("activities")
    if not isinstance(activities, list) or len(activities) != 18 or activities[7].get("id") != _ACTIVITY:
        raise ValueError("BSA319_FROZEN_EIGHTH_ACTIVITY_CHANGED")
    activity = activities[7]
    prompt = _locales(activity.get("prompt"), _PROMPT)
    explanation = _locales(activity.get("explanation"), _EXPLANATION)
    key = activity.get("answerKey", {})
    if (key.get("correct") != "opt-nadia-momentum-changes" or
        [o.get("id") for o in key.get("options", [])] !=
        ["opt-nadia-momentum-changes", "opt-single-particle-conserved",
         "opt-force-equals-momentum", "opt-forces-cancel-on-body"]):
        raise ValueError("BSA319_FROZEN_PAIR_ANSWER_KEY_CHANGED")
    pages = extract_pages(source_pdf)
    if sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA:
        raise ValueError("BSA319_SOURCE_CHANGED_DURING_EXTRACTION")
    anchor = _source_activity_anchors(pages=pages, activities=activities)[7]
    if anchor.get("activityId") != _ACTIVITY or anchor.get("uniquePagePassageLocated") is not True:
        raise ValueError("BSA319_ORIGINAL_SOURCE_ANCHOR_MISSING")
    queue = plan_full_semantic_proofs(package=package, source_sha256=_SOURCE_SHA)
    hits = [t for t in queue["tasks"] if t["activityId"] == _ACTIVITY and
            t["kind"] == "COMPLETE_SCIENTIFIC_MEANING" and t["surfacePath"] == "explanation"]
    if queue["taskCount"] != 429 or len(hits) != 1 or hits[0]["surfaceSha256"] != _digest(activity["explanation"]):
        raise ValueError("BSA319_CANONICAL_EXPLANATION_TASK_NOT_REDERIVED")
    body = {"taskId": hits[0]["taskId"], "sourceSha256": _SOURCE_SHA,
            "candidateSha256": _CANDIDATE_SHA, "surfaceSha256": hits[0]["surfaceSha256"],
            "sourcePageIndex": anchor["physicalPage"], "sourcePassageSha256": anchor["passageSha256"],
            "sourcePhysicsPremisesSha256": _digest(sorted(axioms.items())),
            "promptLocaleSha256": prompt, "explanationLocaleSha256": explanation,
            "models": _models(), "generalLaw": "delta_p_nadia=-J;delta_p_leo=J;delta_p_pair=0",
            "academicTaskAccepted": False, "completeAcademicProofGatesStillOpen": 90,
            "newProviderCalls": 0, "publicationAuthorized": False}
    proof = {**body, "witnessSha256": _digest(body)}
    independently_check_isolated_pair_explanation_witness(proof)
    return proof

"""Exact source-bound proof of the frozen MCQ02 dimensional explanation.

The witness establishes the physical claims only. Admission requires the
separate signed owner lane and does not certify translations or whole lessons.
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

_ACTIVITY = "act-mcq-02-si-units"
# BSA253 task IDs include the digest of the entire candidate. The private
# signed candidate can retain this explanation while changing another activity.
_PROMPT = {"en":"2b18710443e99f660cf88cb235a73eb23dd0d743f7077330c00188d686d8b8ef", "ms":"3c443c2e44c5b54ee7b52ca82637300a95151d7c41aa0e0dec1a8c00773cf582", "zh":"e09ffc7b71de3435a962ba6f45853f69f7712ef41c19061d8f84a272ba8a4e1a"}
_EXPLANATION = {"en":"52618980f3749a272d10bd31fcce6e1e91cb51f577055f05fa6647448913a365", "ms":"8be65a10d76f58a133d04d108ea51073fcc08a6d08f0af407278816b45555492", "zh":"a293e60952109220072abfd514b3f0734ff8dfca8649ec66da699609c7d5030d"}
_CASES = ((F(2), F(3), F(4)), (F(7, 3), F(-5, 2), F(1, 4)))


def _locale_hashes(value: dict, expected: dict) -> dict:
    if not isinstance(value, dict) or set(value) != {"en", "ms", "zh"} or any(
        not isinstance(v, str) or not v.strip() for v in value.values()
    ):
        raise ValueError("BSA293_COMPLETE_THREE_LANGUAGE_EXPLANATION_REQUIRED")
    actual = {k: sha256(value[k].encode("utf8")).hexdigest() for k in ("en", "ms", "zh")}
    if actual != expected:
        raise ValueError("BSA293_FROZEN_EXPLANATION_CHANGED")
    return actual


def _model(mass: F, vx: F, vy: F) -> dict:
    if not all(isinstance(v, F) for v in (mass, vx, vy)) or mass <= 0 or (vx, vy) == (0, 0):
        raise ValueError("BSA293_NONDEGENERATE_RATIONAL_VECTOR_REQUIRED")
    mass_dim, velocity_dim = (1, 0, 0), (0, 1, -1)
    momentum_dim = tuple(a + b for a, b in zip(mass_dim, velocity_dim))
    momentum = (mass * vx, mass * vy)
    if momentum_dim != (1, 1, -1) or momentum == (0, 0) or (
        vx * momentum[1] - vy * momentum[0] != 0 or
        vx * momentum[0] + vy * momentum[1] <= 0
    ):
        raise ValueError("BSA293_MOMENTUM_DIMENSION_OR_DIRECTION_FALSE")
    return {"massKg": str(mass), "velocityMetersPerSecond": list(map(str, (vx, vy))),
            "momentumKilogramMetersPerSecond": list(map(str, momentum)),
            "massDimension": list(mass_dim), "velocityDimension": list(velocity_dim),
            "momentumDimension": list(momentum_dim), "momentumIsVector": True,
            "momentumHasMagnitudeAndDirection": True}


def _models() -> list[dict]:
    return [_model(*case) for case in _CASES]


def independently_check_si_explanation_witness(proof: dict) -> None:
    if not isinstance(proof, dict) or (
        not isinstance(proof.get("taskId"), str) or len(proof["taskId"]) != 64 or
        any(c not in "0123456789abcdef" for c in proof["taskId"]) or
        proof.get("sourceSha256") != _SOURCE_SHA or
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
        proof.get("witnessSha256") != _digest({k:v for k,v in proof.items() if k != "witnessSha256"})
    ):
        raise ValueError("BSA293_UNTRUSTED_SI_EXPLANATION_WITNESS")
    for row in proof["models"]:
        if row != _model(F(row["massKg"]), *map(F, row["velocityMetersPerSecond"])):
            raise ValueError("BSA293_EXACT_DIMENSIONAL_RECOMPUTATION_FAILED")


def independently_prove_si_explanation(*, source_pdf: Path, candidate_path: Path) -> dict:
    candidate_bytes = candidate_path.read_bytes() if candidate_path.is_file() and not candidate_path.is_symlink() else b""
    if (source_pdf.is_symlink() or not source_pdf.is_file() or
        not candidate_bytes or sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA or
        sha256(candidate_bytes).hexdigest() != _CANDIDATE_SHA):
        raise ValueError("BSA293_AUTHENTIC_ONE_SERWAY_SOURCE_AND_CANDIDATE_REQUIRED")
    axioms = _source_axioms(source_pdf, _SOURCE_SHA)
    if (axioms.get("linear momentum is a vector", 0) < 1 or
        axioms.get("defined to be the product of the mass and velocity", 0) < 1 or
        axioms.get("dimensions ml/t", 0) < 1):
        raise ValueError("BSA293_ORIGINAL_MOMENTUM_AND_DIMENSION_PREMISES_MISSING")
    package = json.loads(candidate_bytes.decode("utf8"))
    activities = package.get("activities")
    if not isinstance(activities, list) or len(activities) != 18 or activities[1].get("id") != _ACTIVITY:
        raise ValueError("BSA293_FROZEN_SECOND_ACTIVITY_CHANGED")
    activity = activities[1]
    prompt = _locale_hashes(activity.get("prompt"), _PROMPT)
    explanation = _locale_hashes(activity.get("explanation"), _EXPLANATION)
    key = activity.get("answerKey", {})
    if key.get("correct") != "opt-a" or [o.get("id") for o in key.get("options", [])] != ["opt-a", "opt-b", "opt-c", "opt-d"]:
        raise ValueError("BSA293_FROZEN_SI_ANSWER_KEY_CHANGED")
    anchors = _source_activity_anchors(pages=extract_pages(source_pdf), activities=activities)
    if sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA:
        raise ValueError("BSA293_SOURCE_CHANGED_DURING_EXTRACTION")
    anchor = anchors[1]
    if anchor.get("activityId") != _ACTIVITY or anchor.get("uniquePagePassageLocated") is not True:
        raise ValueError("BSA293_ORIGINAL_SOURCE_ANCHOR_MISSING")
    queue = plan_full_semantic_proofs(package=package, source_sha256=_SOURCE_SHA)
    tasks = [t for t in queue["tasks"] if t["activityId"] == _ACTIVITY and
             t["kind"] == "COMPLETE_SCIENTIFIC_MEANING" and t["surfacePath"] == "explanation"]
    if (queue["taskCount"] != 429 or len(tasks) != 1 or
        tasks[0]["surfaceSha256"] != _digest(activity["explanation"])):
        raise ValueError("BSA293_CANONICAL_EXPLANATION_TASK_NOT_REDERIVED")
    body = {"taskId": tasks[0]["taskId"], "sourceSha256": _SOURCE_SHA, "candidateSha256": _CANDIDATE_SHA,
            "surfaceSha256": tasks[0]["surfaceSha256"],
            "sourcePageIndex": anchor["physicalPage"], "sourcePassageSha256": anchor["passageSha256"],
            "sourcePhysicsPremisesSha256": _digest(sorted(axioms.items())),
            "promptLocaleSha256": prompt, "explanationLocaleSha256": explanation,
            "models": _models(), "academicTaskAccepted": False,
            "completeAcademicProofGatesStillOpen": 90, "newProviderCalls": 0,
            "publicationAuthorized": False}
    proof = {**body, "witnessSha256": _digest(body)}
    independently_check_si_explanation_witness(proof)
    return proof

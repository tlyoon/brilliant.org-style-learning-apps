"""Source-bound proof of the complete MCQ05 system-momentum explanation."""
from __future__ import annotations

from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path

from app_generator.validation.section91_formal_physics import _SOURCE_SHA, _CANDIDATE_SHA, _source_axioms, _digest
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs
from app_generator.validation.source_passages import extract_pages
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _source_activity_anchors

_ACTIVITY = "act-mcq-05-third-law-connection"
_PROMPT = {"en": "cc2b326a5d0ccef11f8439bd68a09862fed7f46f5edf9270a38af27fafcde74b", "ms": "4d9186915e8e0b9cd51b0c056998d84a9d2419c48ff55d39dae7a229375ec26c", "zh": "966a6789b5e81a73fbf1b42a281bf9a3b02370b7e0ec4f57b5228c8fe4bb059a"}
_EXPLANATION = {'en': 'c6cc94ad0ae08cbb06aa6390cee07d06d7f94c713ff370763be8e49196944175', 'ms': '7837bf92f35c1ba3b5ce5dd051da8fa86fbcce73675d1350dcd88537188935a1', 'zh': '7370c5d7dda4dcbdc3fb38858df4eb8d51127779c6a849163615231b06635857'}
_CASES = ((F(2), F(3), F(1), F(-1), F(1, 2), F(1, 4)),
          (F(4), F(1), F(-3, 2), F(2), F(-3, 4), F(3, 2)))


def _locale_hashes(surface: dict, expected: dict) -> dict:
    if not isinstance(surface, dict) or set(surface) != {"en", "ms", "zh"} or any(
        not isinstance(v, str) or not v.strip() for v in surface.values()
    ):
        raise ValueError("BSA299_COMPLETE_TRILINGUAL_THIRD_LAW_EXPLANATION_REQUIRED")
    actual = {lang: sha256(surface[lang].encode("utf8")).hexdigest() for lang in expected}
    if actual != expected:
        raise ValueError("BSA299_FROZEN_THIRD_LAW_EXPLANATION_CHANGED")
    return actual


def _model(m1: F, m2: F, v1: F, v2: F, impulse: F, duration: F) -> dict:
    if any(type(x) is not F for x in (m1, m2, v1, v2, impulse, duration)) or (
        m1 <= 0 or m2 <= 0 or m1 == m2 or impulse == 0 or duration <= 0
    ):
        raise ValueError("BSA299_NONDEGENERATE_EXACT_INTERACTION_REQUIRED")
    before1, before2 = m1 * v1, m2 * v2
    after1, after2 = before1 + impulse, before2 - impulse
    force1, force2 = impulse / duration, -impulse / duration
    acceleration1, acceleration2 = force1 / m1, force2 / m2
    if not (force1 == -force2 and force1 != 0 and
            after1 - before1 == force1 * duration and
            after2 - before2 == force2 * duration and
            before1 + before2 == after1 + after2 and
            acceleration1 != 0 and acceleration2 != 0):
        raise ValueError("BSA299_THIRD_LAW_SYSTEM_DERIVATION_FAILED")
    return {"mass1": str(m1), "mass2": str(m2), "velocity1Before": str(v1),
            "velocity2Before": str(v2), "impulseOn1": str(impulse),
            "duration": str(duration), "momentum1Before": str(before1),
            "momentum2Before": str(before2), "momentum1After": str(after1),
            "momentum2After": str(after2), "forceOn1": str(force1),
            "forceOn2": str(force2), "acceleration1": str(acceleration1),
            "acceleration2": str(acceleration2), "systemMomentumBefore": str(before1 + before2),
            "systemMomentumAfter": str(after1 + after2), "individualMomentaChange": True,
            "systemMomentumConserved": True}


def _models() -> list[dict]:
    return [_model(*case) for case in _CASES]


def independently_check_third_law_explanation_witness(proof: dict) -> None:
    if not isinstance(proof, dict) or (
        not isinstance(proof.get("taskId"), str) or len(proof["taskId"]) != 64 or
        proof.get("sourceSha256") != _SOURCE_SHA or proof.get("candidateSha256") != _CANDIDATE_SHA or
        proof.get("promptLocaleSha256") != _PROMPT or proof.get("explanationLocaleSha256") != _EXPLANATION or
        proof.get("models") != _models() or type(proof.get("sourcePageIndex")) is not int or
        proof["sourcePageIndex"] < 1 or
        any(not isinstance(proof.get(k), str) or len(proof[k]) != 64 for k in
            ("surfaceSha256", "sourcePassageSha256", "sourcePhysicsPremisesSha256")) or
        proof.get("academicTaskAccepted") is not False or
        proof.get("completeAcademicProofGatesStillOpen") != 90 or
        proof.get("newProviderCalls") != 0 or proof.get("publicationAuthorized") is not False or
        proof.get("witnessSha256") != _digest({k: v for k, v in proof.items() if k != "witnessSha256"})
    ):
        raise ValueError("BSA299_UNTRUSTED_THIRD_LAW_EXPLANATION_WITNESS")
    for row in proof["models"]:
        if row != _model(F(row["mass1"]), F(row["mass2"]), F(row["velocity1Before"]),
                         F(row["velocity2Before"]), F(row["impulseOn1"]), F(row["duration"])):
            raise ValueError("BSA299_THIRD_LAW_EXPLANATION_RECOMPUTATION_FAILED")


def independently_prove_third_law_explanation(*, source_pdf: Path, candidate_path: Path) -> dict:
    candidate_bytes = candidate_path.read_bytes() if candidate_path.is_file() and not candidate_path.is_symlink() else b""
    if (source_pdf.is_symlink() or not source_pdf.is_file() or not candidate_bytes or
        sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA or
        sha256(candidate_bytes).hexdigest() != _CANDIDATE_SHA):
        raise ValueError("BSA299_AUTHENTIC_SERWAY_SOURCE_AND_CANDIDATE_REQUIRED")
    axioms = _source_axioms(source_pdf, _SOURCE_SHA)
    if (axioms.get("third law", 0) < 3 or
        axioms.get("time rate of change of the linear momentum", 0) < 1 or
        axioms.get("defined to be the product of the mass and velocity", 0) < 1):
        raise ValueError("BSA299_ORIGINAL_THIRD_LAW_PREMISES_MISSING")
    package = json.loads(candidate_bytes.decode("utf8"))
    activities = package.get("activities")
    if not isinstance(activities, list) or len(activities) != 18 or activities[4].get("id") != _ACTIVITY:
        raise ValueError("BSA299_FROZEN_FIFTH_ACTIVITY_CHANGED")
    activity = activities[4]
    prompt = _locale_hashes(activity.get("prompt"), _PROMPT)
    explanation = _locale_hashes(activity.get("explanation"), _EXPLANATION)
    key = activity.get("answerKey", {})
    if key.get("correct") != "opt-a" or [o.get("id") for o in key.get("options", [])] != ["opt-a", "opt-b", "opt-c", "opt-d"]:
        raise ValueError("BSA299_FROZEN_THIRD_LAW_ANSWER_KEY_CHANGED")
    anchors = _source_activity_anchors(pages=extract_pages(source_pdf), activities=activities)
    if sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA:
        raise ValueError("BSA299_SOURCE_CHANGED_DURING_EXTRACTION")
    anchor = anchors[4]
    if anchor.get("activityId") != _ACTIVITY or anchor.get("uniquePagePassageLocated") is not True:
        raise ValueError("BSA299_ORIGINAL_SOURCE_ANCHOR_MISSING")
    queue = plan_full_semantic_proofs(package=package, source_sha256=_SOURCE_SHA)
    tasks = [task for task in queue["tasks"] if task["activityId"] == _ACTIVITY and
             task["kind"] == "COMPLETE_SCIENTIFIC_MEANING" and task["surfacePath"] == "explanation"]
    if queue["taskCount"] != 429 or len(tasks) != 1 or tasks[0]["surfaceSha256"] != _digest(activity["explanation"]):
        raise ValueError("BSA299_CANONICAL_THIRD_LAW_EXPLANATION_TASK_NOT_REDERIVED")
    body = {"taskId": tasks[0]["taskId"], "sourceSha256": _SOURCE_SHA,
            "candidateSha256": _CANDIDATE_SHA, "surfaceSha256": tasks[0]["surfaceSha256"],
            "sourcePageIndex": anchor["physicalPage"], "sourcePassageSha256": anchor["passageSha256"],
            "sourcePhysicsPremisesSha256": _digest(sorted(axioms.items())),
            "promptLocaleSha256": prompt, "explanationLocaleSha256": explanation,
            "models": _models(), "academicTaskAccepted": False,
            "completeAcademicProofGatesStillOpen": 90, "newProviderCalls": 0,
            "publicationAuthorized": False}
    proof = {**body, "witnessSha256": _digest(body)}
    independently_check_third_law_explanation_witness(proof)
    return proof

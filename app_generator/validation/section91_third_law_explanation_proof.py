"""Original Serway MCQ05 complete explanation, with exact isolated-pair models.

This creates an unadmitted witness. Owner admission separately checks the fifth
signed V36 partition and the preceding signed academic chain.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from app_generator.validation.section91_formal_physics import _SOURCE_SHA, _CANDIDATE_SHA, _source_axioms, _digest
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs
from app_generator.validation.source_passages import extract_pages
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _source_activity_anchors
from app_generator.validation.section91_third_law_false_options_proof import _models as _pair_models, _reparse_physics

_ACTIVITY = "act-mcq-05-third-law-connection"
_PROMPT = {"en":"cc2b326a5d0ccef11f8439bd68a09862fed7f46f5edf9270a38af27fafcde74b", "ms":"4d9186915e8e0b9cd51b0c056998d84a9d2419c48ff55d39dae7a229375ec26c", "zh":"966a6789b5e81a73fbf1b42a281bf9a3b02370b7e0ec4f57b5228c8fe4bb059a"}
_EXPLANATION = {"en":"c6cc94ad0ae08cbb06aa6390cee07d06d7f94c713ff370763be8e49196944175", "ms":"69950ede624cac633a0394309c9eed1b532d5d36fcab2acc4f115040915cae83", "zh":"7370c5d7dda4dcbdc3fb38858df4eb8d51127779c6a849163615231b06635857"}


def _locales(surface: dict, expected: dict) -> dict:
    if not isinstance(surface, dict) or set(surface) != {"en", "ms", "zh"} or any(
        not isinstance(value, str) or not value.strip() for value in surface.values()
    ):
        raise ValueError("BSA316_COMPLETE_TRILINGUAL_THIRD_LAW_EXPLANATION_REQUIRED")
    actual = {lang: sha256(surface[lang].encode("utf8")).hexdigest() for lang in expected}
    if actual != expected:
        raise ValueError("BSA316_FROZEN_THIRD_LAW_EXPLANATION_CHANGED")
    return actual


def independently_check_third_law_explanation_witness(proof: dict) -> None:
    if not isinstance(proof, dict) or (
        not isinstance(proof.get("taskId"), str) or len(proof["taskId"]) != 64 or
        proof.get("sourceSha256") != _SOURCE_SHA or proof.get("candidateSha256") != _CANDIDATE_SHA or
        proof.get("promptLocaleSha256") != _PROMPT or proof.get("explanationLocaleSha256") != _EXPLANATION or
        proof.get("models") != _pair_models() or
        type(proof.get("sourcePageIndex")) is not int or proof["sourcePageIndex"] < 1 or
        any(not isinstance(proof.get(key), str) or len(proof[key]) != 64 for key in
            ("surfaceSha256", "sourcePassageSha256", "sourcePhysicsPremisesSha256")) or
        proof.get("academicTaskAccepted") is not False or
        proof.get("completeAcademicProofGatesStillOpen") != 90 or
        proof.get("newProviderCalls") != 0 or proof.get("publicationAuthorized") is not False or
        proof.get("witnessSha256") != _digest({k: v for k, v in proof.items() if k != "witnessSha256"})
    ):
        raise ValueError("BSA316_UNTRUSTED_THIRD_LAW_EXPLANATION_WITNESS")
    for row in proof["models"]:
        _reparse_physics(row)


def independently_prove_third_law_explanation(*, source_pdf: Path, candidate_path: Path) -> dict:
    candidate_bytes = candidate_path.read_bytes() if candidate_path.is_file() and not candidate_path.is_symlink() else b""
    if (source_pdf.is_symlink() or not source_pdf.is_file() or not candidate_bytes or
        sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA or
        sha256(candidate_bytes).hexdigest() != _CANDIDATE_SHA):
        raise ValueError("BSA316_AUTHENTIC_SERWAY_SOURCE_AND_CANDIDATE_REQUIRED")
    axioms = _source_axioms(source_pdf, _SOURCE_SHA)
    if (axioms.get("third law", 0) < 3 or
        axioms.get("time rate of change of the linear momentum", 0) < 1 or
        axioms.get("defined to be the product of the mass and velocity", 0) < 1):
        raise ValueError("BSA316_ORIGINAL_MUTUAL_FORCE_PREMISES_MISSING")
    package = json.loads(candidate_bytes.decode("utf8"))
    activities = package.get("activities")
    if not isinstance(activities, list) or len(activities) != 18 or activities[4].get("id") != _ACTIVITY:
        raise ValueError("BSA316_FROZEN_FIFTH_ACTIVITY_CHANGED")
    activity = activities[4]
    prompt = _locales(activity.get("prompt"), _PROMPT)
    explanation = _locales(activity.get("explanation"), _EXPLANATION)
    key = activity.get("answerKey", {})
    if key.get("correct") != "opt-a" or [o.get("id") for o in key.get("options", [])] != ["opt-a", "opt-b", "opt-c", "opt-d"]:
        raise ValueError("BSA316_FROZEN_THIRD_LAW_KEY_CHANGED")
    pages = extract_pages(source_pdf)
    if sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA:
        raise ValueError("BSA316_SOURCE_CHANGED_DURING_EXTRACTION")
    if not pages or "equal in magnitude" not in " ".join(pages[0].casefold().split()) or "opposite in direction" not in " ".join(pages[0].casefold().split()):
        raise ValueError("BSA316_ORIGINAL_MUTUAL_FORCE_CLAUSE_MISSING")
    anchor = _source_activity_anchors(pages=pages, activities=activities)[4]
    if anchor.get("activityId") != _ACTIVITY or anchor.get("uniquePagePassageLocated") is not True:
        raise ValueError("BSA316_ORIGINAL_SOURCE_ANCHOR_MISSING")
    queue = plan_full_semantic_proofs(package=package, source_sha256=_SOURCE_SHA)
    tasks = [task for task in queue["tasks"] if task["activityId"] == _ACTIVITY and
             task["kind"] == "COMPLETE_SCIENTIFIC_MEANING" and task["surfacePath"] == "explanation"]
    if queue["taskCount"] != 429 or len(tasks) != 1 or tasks[0]["surfaceSha256"] != _digest(activity["explanation"]):
        raise ValueError("BSA316_CANONICAL_EXPLANATION_TASK_NOT_REDERIVED")
    body = {"taskId": tasks[0]["taskId"], "sourceSha256": _SOURCE_SHA,
            "candidateSha256": _CANDIDATE_SHA, "surfaceSha256": tasks[0]["surfaceSha256"],
            "sourcePageIndex": anchor["physicalPage"], "sourcePassageSha256": anchor["passageSha256"],
            "sourcePhysicsPremisesSha256": _digest(sorted(axioms.items())),
            "promptLocaleSha256": prompt, "explanationLocaleSha256": explanation,
            "models": _pair_models(), "academicTaskAccepted": False,
            "completeAcademicProofGatesStillOpen": 90, "newProviderCalls": 0,
            "publicationAuthorized": False}
    proof = {**body, "witnessSha256": _digest(body)}
    independently_check_third_law_explanation_witness(proof)
    return proof

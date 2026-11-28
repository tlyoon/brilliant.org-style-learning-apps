"""BSA273: second independently falsified source-grounded MCQ distractor.

Falsifies opt-b's claim that identical mass and speed imply identical
linear momentum vectors despite opposite velocity. The statement must be
completely interpretable in EN/MS/ZH, tied to the original single Serway PDF,
and refuted by independent rational vector witnesses. Only one named
MCQ_DISTRACTOR_SCIENCE obligation is eligible; no other task or complete
activity gate is certified. No LLM, extra PDF, publication or provider call.
"""
from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.validation.section91_first_distractor_proof import (
    _PROMPT, _parse_complete,
)
from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA, _CANDIDATE_SHA, _source_axioms, _digest,
)
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs
from app_generator.validation.source_passages import extract_pages
from app_generator.runtime.v3_selected_textbook_scientific_provenance import (
    _source_activity_anchors,
)

_ACTIVITY = "act-mcq-01-vector-nature"
_OPTION = "opt-b"
_PATH = "answerKey/options/1/label"
_KIND = "MCQ_DISTRACTOR_SCIENCE"
_STATUS = "BSA273_SECOND_FINITE_SEMANTIC_MCQ_DISTRACTOR_SCIENCE_ACCEPTED"
_FALSE_OPTION = {
    "en": (
        "Their linear momenta are completely identical",
        ", because ",
        "momentum depends solely on mass and speed",
        " without depending on the direction of travel",
        ".",
    ),
    "ms": (
        "Momentum linear kedua-duanya adalah sama sepenuhnya",
        ", kerana ",
        "momentum hanya bergantung pada jisim dan laju",
        " tanpa bergantung pada arah pergerakan",
        ".",
    ),
    "zh": (
        "\u5b83\u4eec\u7684\u7ebf\u52a8\u91cf\u5b8c\u5168\u76f8\u540c",
        "\uff0c\u56e0\u4e3a",
        "\u52a8\u91cf\u4ec5\u53d6\u51b3\u4e8e\u8d28\u91cf\u548c\u901f\u7387",
        "\uff0c\u4e0e\u8fd0\u52a8\u65b9\u5411\u65e0\u5173",
        "\u3002",
    ),
}
_SEMANTIC_CLAIMS = (
    "TWO_IDENTICAL_POSITIVE_MASS_DRONES",
    "SAME_NONZERO_CONSTANT_SPEED_OPPOSITE_VELOCITIES",
    "IDENTICAL_MOMENTUM_VECTORS",
    "MOMENTUM_DIRECTION_IS_IRRELEVANT",
)


def independent_second_distractor_science(
    *, source_pdf: Path, candidate_path: Path, package: dict | None = None
) -> dict[str, Any]:
    if (source_pdf.is_symlink() or not source_pdf.is_file()
        or candidate_path.is_symlink() or not candidate_path.is_file()
        or sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA
        or sha256(candidate_path.read_bytes()).hexdigest() != _CANDIDATE_SHA):
        raise ValueError("BSA273_ORIGINAL_ONE_TEXTBOOK_AND_FROZEN_CANDIDATE_REQUIRED")
    axioms = _source_axioms(source_pdf, _SOURCE_SHA)
    if (axioms.get("defined to be the product of the mass and velocity", 0) < 1
        or axioms.get("linear momentum is a vector", 0) < 1):
        raise ValueError("BSA273_ORIGINAL_VECTOR_MOMENTUM_LAW_MISSING")
    raw = json.loads(candidate_path.read_text(encoding="utf8"))
    if package is not None and package != raw:
        raise ValueError("BSA273_FROZEN_CANDIDATE_CHANGED")
    activities = raw.get("activities")
    if not isinstance(activities, list) or len(activities) != 18:
        raise ValueError("BSA273_FROZEN_ROSTER_CHANGED")
    a = activities[0]
    if a.get("id") != _ACTIVITY:
        raise ValueError("BSA273_WRONG_ACTIVITY")
    answer = a.get("answerKey", {})
    options = answer.get("options", [])
    if (not isinstance(options, list) or len(options) != 4
        or answer.get("correct") != "opt-a"
        or options[1].get("id") != _OPTION):
        raise ValueError("BSA273_FALSE_OPTION_OR_ANSWER_KEY_CHANGED")
    localized = {}
    for locale in ("en", "ms", "zh"):
        _parse_complete(a["prompt"].get(locale), _PROMPT[locale],
                        "BSA273_PROMPT_" + locale.upper())
        localized[locale] = _parse_complete(
            options[1]["label"].get(locale), _FALSE_OPTION[locale],
            "BSA273_OPTION_" + locale.upper())
    pages = extract_pages(source_pdf)
    anchor = _source_activity_anchors(pages=pages, activities=activities)[0]
    if (anchor.get("activityId") != _ACTIVITY
        or anchor.get("uniquePagePassageLocated") is not True
        or anchor.get("physicalPage") not in (1, 2, 3)):
        raise ValueError("BSA273_ORIGINAL_SOURCE_PASSAGE_UNVERIFIED")
    # Equal positive mass and equal nonzero speed have equal momentum *norms*
    # but opposite signed vectors. Refute equality using two exact rational
    # countermodels, independently of any marked answer or sampled LLM output.
    witnesses = []
    for mass, speed in ((Fraction(3, 1), Fraction(5, 1)),
                        (Fraction(9, 2), Fraction(4, 3))):
        p1, p2 = mass * speed, -mass * speed
        if (not mass > 0 or not speed > 0 or p1 == p2 or
            p1 == 0 or p1 != -p2 or abs(p1) != abs(p2)):
            raise ValueError("BSA273_VECTOR_COUNTERMODEL_FAILED")
        witnesses.append({
            "mass": str(mass),
            "constantSpeed": str(speed),
            "momentumForward": str(p1),
            "momentumBackward": str(p2),
            "momentumVectorsIdentical": False,
            "momentumMagnitudesEqual": True,
        })
    queue = plan_full_semantic_proofs(package=raw, source_sha256=_SOURCE_SHA)
    found = [row for row in queue["tasks"]
             if row["activityId"] == _ACTIVITY
             and row["kind"] == _KIND
             and row["surfacePath"] == _PATH]
    if (queue.get("taskCount") != 429 or len(found) != 1
        or found[0]["surfaceSha256"] != _digest(options[1]["label"])):
        raise ValueError("BSA273_SIGNED_TASK_IDENTITY_NOT_REPRODUCIBLE")
    return {
        "status": _STATUS,
        "taskId": found[0]["taskId"],
        "taskKind": _KIND,
        "activityId": _ACTIVITY,
        "optionId": _OPTION,
        "surfacePath": _PATH,
        "surfaceSha256": found[0]["surfaceSha256"],
        "sourceSha256": _SOURCE_SHA,
        "candidateSha256": _CANDIDATE_SHA,
        "sourcePageIndex": anchor["physicalPage"],
        "sourcePassageSha256": anchor["passageSha256"],
        "sourcePhysicsPremisesDigest": _digest(sorted(axioms.items())),
        "semantics": list(_SEMANTIC_CLAIMS),
        "completeLocalizedFiniteGrammarDigests": localized,
        "exactRationalCounterexamples": witnesses,
        "acceptedAcademicTaskCountForThisProof": 1,
        "completeAcademicProofGatesStillOpen": 90,
        "otherTrilingualMeaningProofAccepted": False,
        "generalScientificLanguageUnderstandingClaimed": False,
        "newGeminiCalls": 0,
        "sourcePdfUploaded": False,
        "publicationAuthorized": False,
    }

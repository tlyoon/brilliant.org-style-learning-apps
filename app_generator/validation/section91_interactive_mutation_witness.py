"""BSA262 V34: independent bounded interactive-answer mutation witnesses.

Reopen the exact single source textbook and unchanged private candidate.
This is formal answer-model and localized-surface coverage, NOT semantic approval.
"""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA, _CANDIDATE_SHA, _CASES, _source_axioms,
    _interactive_cases, _check_solution, _digest,
)

def audit_nine_interactive_mutants(*, source_pdf: Path, package_file: Path) -> dict:
    if (source_pdf.is_symlink() or not source_pdf.is_file()
            or sha256(source_pdf.read_bytes()).hexdigest() != _SOURCE_SHA
            or package_file.is_symlink() or not package_file.is_file()
            or sha256(package_file.read_bytes()).hexdigest() != _CANDIDATE_SHA):
        raise ValueError("BSA262_EXACT_SOURCE_OR_CANDIDATE_CHANGED")
    if len(_source_axioms(source_pdf, _SOURCE_SHA)) != 9:
        raise ValueError("BSA262_TEXTBOOK_PREMISES_MISSING")
    activities = json.loads(package_file.read_text(encoding="utf8")).get("activities")
    if (not isinstance(activities, list) or
            [a.get("id") for a in activities] != list(_CASES)):
        raise ValueError("BSA262_FROZEN_ROSTER_DRIFT")
    cases = _interactive_cases()
    if set(cases) != set(_CASES[9:]):
        raise ValueError("BSA262_INTERACTIVE_MODEL_ROSTER_DRIFT")
    rows = []
    locale_item_labels = 0
    locale_prompt_explanations = 0
    for a in activities[9:]:
        truth = cases[a["id"]]
        accepted = _check_solution(a, truth)
        interaction = a["interaction"]
        mode = truth[0]
        mutant = deepcopy(a)
        m = mutant["interaction"]
        if mode in {"classification", "matching"}:
            positions = m["placements"]
            if len(positions) < 2:
                raise ValueError("BSA262_MUTATION_REQUIRES_TWO_PLACEMENTS")
            positions[0]["targetId"] = (
                positions[1]["targetId"] if positions[0]["targetId"] != positions[1]["targetId"]
                else "__deliberately_invalid_target__")
        elif mode == "selection":
            ids = [i["id"] for i in m["items"]]
            selected = m["correctSelections"]
            if not ids:
                raise ValueError("BSA262_MUTATION_REQUIRES_SELECTION")
            first = ids[0]
            m["correctSelections"] = (
                [i for i in selected if i != first] if first in selected
                else [*selected, first])
        elif mode == "ordering":
            order = m["correctOrder"]
            if len(order) < 2:
                raise ValueError("BSA262_MUTATION_REQUIRES_ORDER")
            order[0], order[1] = order[1], order[0]
        else:
            raise ValueError("BSA262_UNSUPPORTED_INTERACTION_MODE")
        try:
            _check_solution(mutant, truth)
        except ValueError:
            pass
        else:
            raise ValueError("BSA262_WRONG_ANSWER_MUTATION_UNDETECTED")
        for locale in ("en", "ms", "zh"):
            prompt = a.get("prompt", {}).get(locale)
            explanation = a.get("explanation", {}).get(locale)
            if (not isinstance(prompt, str) or not prompt.strip() or
                    not isinstance(explanation, str) or not explanation.strip()):
                raise ValueError("BSA262_MISSING_LOCALIZED_INTERACTIVE_EXPLANATION")
            locale_prompt_explanations += 2
            for item in interaction["items"]:
                label = item.get("label", {}).get(locale)
                if not isinstance(label, str) or not label.strip():
                    raise ValueError("BSA262_MISSING_LOCALIZED_INTERACTIVE_ITEM")
                locale_item_labels += 1
        rows.append({
            "activityId": a["id"],
            "mode": mode,
            "correctModelSha256": accepted["independentSolutionSha256"],
            "answerModelRejectedMutant": True,
            "activitySha256": _digest(a),
            "localizedItemCount": len(interaction["items"]) * 3,
        })
    return {
        "status": "BSA262_REAL_NINE_INTERACTIVE_FORMAL_MUTANTS_REJECTED",
        "sourceSha256": _SOURCE_SHA,
        "candidateSha256": _CANDIDATE_SHA,
        "interactiveActivitiesChecked": len(rows),
        "independentlyRejectedWrongAnswerMutants": len(rows),
        "localizedItemLabelsPresent": locale_item_labels,
        "localizedPromptExplanationFieldsPresent": locale_prompt_explanations,
        "activityProofs": rows,
        "fullTrilingualMeaningEquivalenceProven": False,
        "completeAcademicProofGatesStillOpen": 90,
        "independentMeaningMicroproofsPending": 429,
        "fullAcademicPASS": 0,
        "newProviderCalls": 0,
        "publicationAuthorized": False,
    }

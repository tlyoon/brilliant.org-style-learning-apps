"""Detect MCQ key/distractor integrity defects without claiming scientific truth."""
from __future__ import annotations
import unicodedata
from collections.abc import Mapping
from app_generator.validation.academic_qa import Finding

def check_answer_integrity(activity: Mapping) -> Finding:
    id_ = str(activity.get("id", "?"))
    ref = f"activity:{id_}"
    if activity.get("type") != "mcq":
        return Finding("answer_correctness", "REVIEW_REQUIRED", "not_applicable", ref,
                       "non-MCQ mode requires a separate answer verifier")
    key = activity.get("answerKey")
    if not isinstance(key, dict) or not isinstance(key.get("options"), list):
        return Finding("answer_correctness", "FAIL", "deterministic", ref, "missing answer key/options", True)
    options = key["options"]
    ids = [x.get("id") if isinstance(x, dict) else None for x in options]
    if len(options) < 2 or len(set(ids)) != len(ids) or ids.count(key.get("correct")) != 1:
        return Finding("answer_correctness", "FAIL", "deterministic", ref,
                       "duplicated option IDs or invalid/ambiguous correct option", True)
    for language in ("en", "ms", "zh"):
        values = []
        for option in options:
            text = option.get("label", {}).get(language) if isinstance(option, dict) else None
            if not isinstance(text, str) or not text.strip():
                return Finding("answer_correctness", "FAIL", "deterministic", ref,
                               f"missing {language} option text", True)
            values.append(unicodedata.normalize("NFKC", text).casefold().strip())
        if len(set(values)) != len(values):
            return Finding("answer_correctness", "FAIL", "deterministic", ref,
                           f"duplicated {language} answer labels hide distinctions", True)
    return Finding("answer_correctness", "REVIEW_REQUIRED", "deterministic", ref,
                   "MCQ key and locale labels structurally unambiguous; scientific answer correctness unverified", True)

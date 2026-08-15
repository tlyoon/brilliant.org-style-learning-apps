#!/usr/bin/env python3
"""Validate learning-package invariants without external dependencies."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
REQUIRED_LOCALES = {"en", "ms", "zh"}
TYPES = {"mcq", "interactive"}
DIFFICULTIES = {"easy", "moderate", "challenging"}

NUMERIC_PATTERNS = (
    re.compile(r"\bcalculate\b", re.I),
    re.compile(r"\bcompute\b", re.I),
    re.compile(r"\bnumerical (?:value|answer)\b", re.I),
    re.compile(r"\bhow many\b", re.I),
    re.compile(r"\bto \d+ decimal places\b", re.I),
)


def _localized(value: Any, field: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object")
        return
    for locale in REQUIRED_LOCALES:
        if not isinstance(value.get(locale), str) or not value[locale].strip():
            errors.append(f"{field}.{locale} must be non-empty")


def _answer_key(value: Any, field: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object")
        return

    correct = value.get("correct")
    if not isinstance(correct, str) or not correct.strip():
        errors.append(f"{field}.correct must be a non-empty option ID")

    options = value.get("options")
    if not isinstance(options, list) or not options:
        errors.append(f"{field}.options must be a non-empty array")
        return

    option_ids: list[str] = []
    for option_index, option in enumerate(options):
        option_field = f"{field}.options[{option_index}]"
        if not isinstance(option, dict):
            errors.append(f"{option_field} must be an object")
            continue
        option_id = option.get("id")
        if not isinstance(option_id, str) or not option_id.strip():
            errors.append(f"{option_field}.id must be non-empty")
        else:
            if option_id in option_ids:
                errors.append(f"{option_field}.id is duplicated: {option_id}")
            option_ids.append(option_id)
        _localized(option.get("label"), f"{option_field}.label", errors)

    if isinstance(correct, str) and correct.strip() and option_ids.count(correct) != 1:
        errors.append(f"{field}.correct must match exactly one option ID")


def validate_package(data: Any, source: str = "package") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"{source} must contain a JSON object"]

    for field in ("schemaVersion", "packageId", "chapter", "subchapter", "status", "locales", "learningObjectives", "sourceManifest", "activities"):
        if field not in data:
            errors.append(f"{source}: missing {field}")

    if data.get("schemaVersion") != "1.0":
        errors.append(f"{source}: schemaVersion must be 1.0")
    if data.get("status") not in {"draft", "review", "publishable"}:
        errors.append(f"{source}: invalid status")
    locales = data.get("locales")
    if not isinstance(locales, list):
        errors.append(f"{source}: locales must be an array")
    elif not all(isinstance(locale, str) for locale in locales):
        errors.append(f"{source}: locales must contain only locale strings")
    elif not REQUIRED_LOCALES.issubset(set(locales)):
        errors.append(f"{source}: locales must include en, ms, and zh")

    activities = data.get("activities", [])
    if not isinstance(activities, list):
        return errors + [f"{source}: activities must be an array"]

    seen: set[str] = set()
    distribution: Counter[tuple[str, str]] = Counter()
    for index, activity in enumerate(activities):
        label = f"{source}: activity[{index}]"
        if not isinstance(activity, dict):
            errors.append(f"{label} must be an object")
            continue
        aid = activity.get("id")
        if not isinstance(aid, str) or not aid:
            errors.append(f"{label}.id must be non-empty")
        elif aid in seen:
            errors.append(f"{label}.id is duplicated: {aid}")
        else:
            seen.add(aid)

        atype, difficulty = activity.get("type"), activity.get("difficulty")
        if atype not in TYPES:
            errors.append(f"{label}.type is invalid")
        if difficulty not in DIFFICULTIES:
            errors.append(f"{label}.difficulty is invalid")
        if atype in TYPES and difficulty in DIFFICULTIES:
            distribution[(atype, difficulty)] += 1

        if activity.get("calculatorFree") is not True:
            errors.append(f"{label} must be calculator-free")
        if activity.get("numericAnswerRequired") is not False:
            errors.append(f"{label} must not require a numerical answer")
        _localized(activity.get("prompt"), f"{label}.prompt", errors)
        _localized(activity.get("feedback"), f"{label}.feedback", errors)
        _answer_key(activity.get("answerKey"), f"{label}.answerKey", errors)

        hints = activity.get("hints")
        if not isinstance(hints, list) or not hints:
            errors.append(f"{label}.hints must be a non-empty array")
        else:
            for hint_index, hint in enumerate(hints):
                _localized(hint, f"{label}.hints[{hint_index}]", errors)

        prompt_en = activity.get("prompt", {}).get("en", "") if isinstance(activity.get("prompt"), dict) else ""
        if any(pattern.search(prompt_en) for pattern in NUMERIC_PATTERNS):
            errors.append(f"{label}.prompt.en appears to request calculation or a numerical answer")
        provenance = activity.get("provenance", {})
        if not isinstance(provenance, dict) or provenance.get("originalContent") is not True or not provenance.get("sourceLocation"):
            errors.append(f"{label}.provenance must declare original content and a source location")

    if data.get("status") == "publishable":
        if len(activities) != 18:
            errors.append(f"{source}: publishable packages require exactly 18 activities")
        for atype in sorted(TYPES):
            for difficulty in sorted(DIFFICULTIES):
                if distribution[(atype, difficulty)] != 3:
                    errors.append(f"{source}: requires exactly 3 {atype}/{difficulty} activities")
    return errors


def package_paths() -> list[Path]:
    excluded = {CONTENT / "schema", CONTENT / "source-manifests", CONTENT / "templates"}
    return [path for path in CONTENT.rglob("*.json") if not any(parent in path.parents for parent in excluded)]


def main() -> int:
    errors: list[str] = []
    for path in package_paths():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        errors.extend(validate_package(data, str(path.relative_to(ROOT))))
    if errors:
        print("Content validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Content validation passed ({len(package_paths())} package files checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())


#!/usr/bin/env python3
"""Validate learning packages against structural and semantic content rules."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
MANIFEST_ROOT = CONTENT / "source-manifests"
PACKAGE_SCHEMA_PATH = CONTENT / "schema" / "content-package.schema.json"
MANIFEST_SCHEMA_PATH = CONTENT / "schema" / "source-manifest.schema.json"
TYPES = {"mcq", "interactive"}
DIFFICULTIES = {"easy", "moderate", "challenging"}
PLACEHOLDER_PATTERN = re.compile(r"\b(?:todo|tbd|replace|placeholder|examples?|generic|unknown|n/?a)\b", re.I)

NUMERIC_PATTERNS = {
    "en": (
        re.compile(r"\bcalculate\b", re.I),
        re.compile(r"\bcompute\b", re.I),
        re.compile(r"\bnumerical (?:value|answer)\b", re.I),
        re.compile(r"\bhow many\b", re.I),
        re.compile(r"\bto \d+ decimal places\b", re.I),
    ),
    "ms": (
        re.compile(r"\bhitung\b", re.I),
        re.compile(r"\bkirakan\b", re.I),
        re.compile(r"\bnilai berangka\b", re.I),
        re.compile(r"\bjawapan berangka\b", re.I),
        re.compile(r"\bberapa\b", re.I),
        re.compile(r"\btempat perpuluhan\b", re.I),
    ),
    "zh": (
        re.compile(r"计算"),
        re.compile(r"数值"),
        re.compile(r"数字答案"),
        re.compile(r"多少"),
        re.compile(r"小数位"),
    ),
}

PACKAGE_SCHEMA = json.loads(PACKAGE_SCHEMA_PATH.read_text(encoding="utf-8"))
MANIFEST_SCHEMA = json.loads(MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))
Draft202012Validator.check_schema(PACKAGE_SCHEMA)
Draft202012Validator.check_schema(MANIFEST_SCHEMA)
PACKAGE_VALIDATOR = Draft202012Validator(PACKAGE_SCHEMA)
MANIFEST_VALIDATOR = Draft202012Validator(MANIFEST_SCHEMA, format_checker=FormatChecker())


def _schema_location(source: str, path: Any) -> str:
    location = source
    for part in path:
        location += f"[{part}]" if isinstance(part, int) else f".{part}"
    return location


def _schema_errors(validator: Draft202012Validator, data: Any, source: str) -> list[str]:
    failures = sorted(
        validator.iter_errors(data),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    return [f"{_schema_location(source, error.absolute_path)}: {error.message}" for error in failures]


def _manifest_errors(reference: str, source: str) -> list[str]:
    prefix = "content/source-manifests/"
    manifest_label = f"{source}.sourceManifest"
    if not reference.startswith(prefix):
        return [f"{manifest_label}: must reference a file inside {prefix}"]

    relative_name = reference.removeprefix(prefix)
    manifest_path = (MANIFEST_ROOT / relative_name).resolve()
    try:
        manifest_path.relative_to(MANIFEST_ROOT.resolve())
    except ValueError:
        return [f"{manifest_label}: resolves outside the permitted manifest directory"]
    if not manifest_path.is_file():
        return [f"{manifest_label}: referenced manifest does not exist: {reference}"]

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{manifest_label}: cannot read a valid JSON manifest: {exc}"]

    errors = _schema_errors(MANIFEST_VALIDATOR, manifest, reference)
    if errors:
        return errors
    for field, value in manifest.items():
        if isinstance(value, str) and PLACEHOLDER_PATTERN.search(value):
            errors.append(f"{reference}.{field}: must contain meaningful provenance, not a placeholder value")
    return errors


def validate_package(data: Any, source: str = "package") -> list[str]:
    errors = _schema_errors(PACKAGE_VALIDATOR, data, source)
    if errors:
        return errors

    errors.extend(_manifest_errors(data["sourceManifest"], source))

    seen_activities: set[str] = set()
    distribution: Counter[tuple[str, str]] = Counter()
    for index, activity in enumerate(data["activities"]):
        label = f"{source}: activity[{index}]"
        activity_id = activity["id"]
        if activity_id in seen_activities:
            errors.append(f"{label}.id is duplicated: {activity_id}")
        seen_activities.add(activity_id)

        activity_type = activity["type"]
        difficulty = activity["difficulty"]
        distribution[(activity_type, difficulty)] += 1

        option_ids = [option["id"] for option in activity["answerKey"]["options"]]
        seen_options: set[str] = set()
        for option_index, option_id in enumerate(option_ids):
            if option_id in seen_options:
                errors.append(f"{label}.answerKey.options[{option_index}].id is duplicated: {option_id}")
            seen_options.add(option_id)
        if option_ids.count(activity["answerKey"]["correct"]) != 1:
            errors.append(f"{label}.answerKey.correct must match exactly one option ID")

        for locale, prompt in activity["prompt"].items():
            if any(pattern.search(prompt) for pattern in NUMERIC_PATTERNS[locale]):
                errors.append(f"{label}.prompt.{locale} appears to request calculation or a numerical answer")

    if data["status"] == "publishable":
        if len(data["activities"]) != 18:
            errors.append(f"{source}: publishable packages require exactly 18 activities")
        for activity_type in sorted(TYPES):
            for difficulty in sorted(DIFFICULTIES):
                if distribution[(activity_type, difficulty)] != 3:
                    errors.append(f"{source}: requires exactly 3 {activity_type}/{difficulty} activities")
    return errors


def package_paths() -> list[Path]:
    excluded = {CONTENT / "schema", MANIFEST_ROOT, CONTENT / "templates"}
    return [path for path in CONTENT.rglob("*.json") if not any(parent in path.parents for parent in excluded)]


def main() -> int:
    errors: list[str] = []
    paths = package_paths()
    for path in paths:
        relative_path = str(path.relative_to(ROOT))
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{relative_path}: {exc}")
            continue
        errors.extend(validate_package(data, relative_path))
    if errors:
        print("Content validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Content validation passed ({len(paths)} package files checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

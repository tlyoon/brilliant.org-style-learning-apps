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
        re.compile(r"\btempat perpuluhan\b", re.I),
    ),
    "zh": (
        re.compile(r"计算"),
        re.compile(r"数值"),
        re.compile(r"数字答案"),
        re.compile(r"小数位"),
    ),
}
NEGATED_NUMERIC_PATTERNS = {
    "en": re.compile(r"\b(?:without calculating|do not calculate|no calculation is needed)\b", re.I),
    "ms": re.compile(r"\b(?:tanpa pengiraan|jangan hitung|jangan kirakan)\b", re.I),
    "zh": re.compile(r"(?:无需|不用|不必)计算"),
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


def _learner_text(activity: dict[str, Any]) -> list[tuple[str, dict[str, str]]]:
    fields: list[tuple[str, dict[str, str]]] = [("prompt", activity["prompt"])]
    fields.extend((f"hints[{index}]", hint) for index, hint in enumerate(activity["hints"]))
    for field in ("feedback", "answerLogic", "explanation", "accessibilityText"):
        if field in activity:
            fields.append((field, activity[field]))
    recovery = activity.get("prerequisiteRecovery")
    if recovery:
        fields.append(("prerequisiteRecovery.prompt", recovery["prompt"]))
    answer_key = activity.get("answerKey")
    if answer_key:
        fields.extend(
            (f"answerKey.options[{index}].label", option["label"])
            for index, option in enumerate(answer_key["options"])
        )
    interaction = activity.get("interaction")
    if interaction:
        fields.extend(
            (f"interaction.items[{index}].label", item["label"])
            for index, item in enumerate(interaction["items"])
        )
        fields.extend(
            (f"interaction.targets[{index}].label", target["label"])
            for index, target in enumerate(interaction.get("targets", []))
        )
    return fields


def validate_package(data: Any, source: str = "package") -> list[str]:
    errors = _schema_errors(PACKAGE_VALIDATOR, data, source)
    if errors:
        return errors

    errors.extend(_manifest_errors(data["sourceManifest"], source))

    if data["status"] in {"review", "publishable"}:
        required_review_fields = (
            "prerequisites", "misconceptionCatalogue", "evidencePolicy", "reviewRecord",
        )
        for field in required_review_fields:
            if field not in data:
                errors.append(f"{source}.{field}: required for review and publishable packages")

    prerequisite_ids = {item["id"] for item in data.get("prerequisites", [])}
    misconception_ids = {item["id"] for item in data.get("misconceptionCatalogue", [])}
    for field, items in (
        ("prerequisites", data.get("prerequisites", [])),
        ("misconceptionCatalogue", data.get("misconceptionCatalogue", [])),
    ):
        ids = [item["id"] for item in items]
        if len(ids) != len(set(ids)):
            errors.append(f"{source}.{field}: IDs must be unique")

    review_record = data.get("reviewRecord")
    if review_record:
        review_path = (ROOT / review_record).resolve()
        try:
            review_path.relative_to((CONTENT / "chapter-1").resolve())
        except ValueError:
            errors.append(f"{source}.reviewRecord: must resolve inside content/chapter-1")
        else:
            if not review_path.is_file():
                errors.append(f"{source}.reviewRecord: referenced file does not exist")

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

        if activity_type == "mcq":
            option_ids = [option["id"] for option in activity["answerKey"]["options"]]
            seen_options: set[str] = set()
            for option_index, option_id in enumerate(option_ids):
                if option_id in seen_options:
                    errors.append(f"{label}.answerKey.options[{option_index}].id is duplicated: {option_id}")
                seen_options.add(option_id)
                option = activity["answerKey"]["options"][option_index]
                option_misconception = option.get("misconception")
                if option_misconception and misconception_ids and option_misconception not in misconception_ids:
                    errors.append(f"{label}.answerKey.options[{option_index}].misconception: not in the package catalogue")
            if option_ids.count(activity["answerKey"]["correct"]) != 1:
                errors.append(f"{label}.answerKey.correct must match exactly one option ID")
        elif "interaction" in activity:
            interaction = activity["interaction"]
            items = interaction["items"]
            item_ids = [item["id"] for item in items]
            if len(item_ids) != len(set(item_ids)):
                errors.append(f"{label}.interaction.items: IDs must be unique")
            for item_index, item in enumerate(items):
                item_misconception = item.get("misconception")
                if item_misconception and misconception_ids and item_misconception not in misconception_ids:
                    errors.append(f"{label}.interaction.items[{item_index}].misconception: not in the package catalogue")

            mode = activity["interactionMode"]
            response_fields = {
                "classification": {"targets", "placements"},
                "matching": {"targets", "placements"},
                "ordering": {"correctOrder"},
                "selection": {"correctSelections"},
            }
            present_fields = set(interaction) - {"items"}
            if present_fields != response_fields[mode]:
                expected = ", ".join(sorted(response_fields[mode]))
                errors.append(f"{label}.interaction: {mode} mode requires only {expected}")
            elif mode in {"classification", "matching"}:
                target_ids = [target["id"] for target in interaction["targets"]]
                if len(target_ids) != len(set(target_ids)):
                    errors.append(f"{label}.interaction.targets: IDs must be unique")
                placed_items = [placement["itemId"] for placement in interaction["placements"]]
                placed_targets = [placement["targetId"] for placement in interaction["placements"]]
                if Counter(placed_items) != Counter(item_ids):
                    errors.append(f"{label}.interaction.placements: must place every item exactly once")
                if any(target_id not in target_ids for target_id in placed_targets):
                    errors.append(f"{label}.interaction.placements: targetId must reference a declared target")
                if mode == "matching" and set(placed_targets) != set(target_ids):
                    errors.append(f"{label}.interaction.placements: matching must use every target at least once")
            elif mode == "ordering":
                if Counter(interaction["correctOrder"]) != Counter(item_ids):
                    errors.append(f"{label}.interaction.correctOrder: must order every item exactly once")
            else:
                selections = interaction["correctSelections"]
                if any(item_id not in item_ids for item_id in selections):
                    errors.append(f"{label}.interaction.correctSelections: must reference declared items")
                if len(selections) >= len(item_ids):
                    errors.append(f"{label}.interaction.correctSelections: must leave at least one item unselected")

            rules = activity["diagnosticRules"]
            rule_misconceptions = {rule["misconception"] for rule in rules}
            if set(activity["misconceptions"]) != rule_misconceptions:
                errors.append(f"{label}.diagnosticRules: must cover every activity misconception and no others")
            correct_placements = {
                placement["itemId"]: placement["targetId"]
                for placement in interaction.get("placements", [])
            }
            correct_order = interaction.get("correctOrder", [])
            correct_selections = set(interaction.get("correctSelections", []))
            for rule_index, rule in enumerate(rules):
                rule_label = f"{label}.diagnosticRules[{rule_index}]"
                if misconception_ids and rule["misconception"] not in misconception_ids:
                    errors.append(f"{rule_label}.misconception: not in the package catalogue")
                condition = rule["condition"]
                kind = condition["kind"]
                if mode in {"classification", "matching"}:
                    if kind != "placement":
                        errors.append(f"{rule_label}.condition: {mode} diagnostics require placement conditions")
                        continue
                    if condition["itemId"] not in item_ids or condition["targetId"] not in target_ids:
                        errors.append(f"{rule_label}.condition: must reference declared items and targets")
                    elif correct_placements.get(condition["itemId"]) == condition["targetId"]:
                        errors.append(f"{rule_label}.condition: must describe an incorrect placement")
                elif mode == "ordering":
                    if kind != "precedes":
                        errors.append(f"{rule_label}.condition: ordering diagnostics require precedes conditions")
                        continue
                    first = condition["firstItemId"]
                    second = condition["secondItemId"]
                    if first not in item_ids or second not in item_ids or first == second:
                        errors.append(f"{rule_label}.condition: must reference two distinct declared items")
                    elif correct_order.index(first) < correct_order.index(second):
                        errors.append(f"{rule_label}.condition: must describe an incorrect ordering relationship")
                else:
                    if kind != "selection":
                        errors.append(f"{rule_label}.condition: selection diagnostics require selection conditions")
                        continue
                    item_id = condition["itemId"]
                    if item_id not in item_ids:
                        errors.append(f"{rule_label}.condition: must reference a declared item")
                    elif condition["selected"] == (item_id in correct_selections):
                        errors.append(f"{rule_label}.condition: must describe an incorrect selection state")

        if data["status"] in {"review", "publishable"}:
            for field in ("answerLogic", "explanation", "prerequisiteRecovery", "accessibilityText"):
                if field not in activity:
                    errors.append(f"{label}.{field}: required for review and publishable packages")
            if len(activity["hints"]) < 2:
                errors.append(f"{label}.hints: at least two progressive hints are required")
            if activity["type"] == "interactive" and "interactionMode" not in activity:
                errors.append(f"{label}.interactionMode: required for interactive activities")
            if activity["type"] == "interactive" and "interaction" not in activity:
                errors.append(f"{label}.interaction: genuine interaction data is required for review and publishable packages")
            if activity["type"] == "mcq" and "interactionMode" in activity:
                errors.append(f"{label}.interactionMode: must not be set for MCQ activities")

        recovery = activity.get("prerequisiteRecovery")
        if recovery and recovery["prerequisiteId"] not in prerequisite_ids:
            errors.append(f"{label}.prerequisiteRecovery.prerequisiteId: not declared by package")
        for misconception in activity["misconceptions"]:
            if misconception_ids and misconception not in misconception_ids:
                errors.append(f"{label}.misconceptions: {misconception} is not in the package catalogue")

        for field, localized in _learner_text(activity):
            for locale, text in localized.items():
                if (
                    any(pattern.search(text) for pattern in NUMERIC_PATTERNS[locale])
                    and not NEGATED_NUMERIC_PATTERNS[locale].search(text)
                ):
                    errors.append(f"{label}.{field}.{locale} appears to request calculation or a numerical answer")

    if data["status"] in {"review", "publishable"}:
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

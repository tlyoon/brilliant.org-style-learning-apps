"""Assemble stable stage output into schema-1.1 package data."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from app_generator.config import GeneratorConfig
from app_generator.errors import ResponseContractError

EXPECTED = Counter(
    (kind, difficulty)
    for kind in ("mcq", "interactive")
    for difficulty in ("easy", "moderate", "challenging")
    for _ in range(3)
)


@lru_cache(maxsize=1)
def _activity_validator() -> Draft202012Validator:
    schema_path = Path(__file__).resolve().parents[2] / "content" / "schema" / "content-package.schema.json"
    package_schema = json.loads(schema_path.read_text(encoding="utf-8"))
    activity_schema = {
        "$schema": package_schema["$schema"],
        "$ref": "#/$defs/activity",
        "$defs": package_schema["$defs"],
    }
    return Draft202012Validator(activity_schema)


def validate_activity_batch(
    batch: Any,
    planned: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(batch, dict) or set(batch) != {"activities"}:
        raise ResponseContractError("Activity batch must contain exactly one activities key")
    activities = batch["activities"]
    if not isinstance(activities, list) or len(activities) != len(planned):
        raise ResponseContractError(
            f"Activity batch must contain exactly {len(planned)} activities"
        )
    planned_by_id = {item["id"]: item for item in planned}
    if len(planned_by_id) != len(planned):
        raise ResponseContractError("Activity batch plan contains duplicate IDs")
    generated_ids = [item.get("id") if isinstance(item, dict) else None for item in activities]
    if set(generated_ids) != set(planned_by_id) or len(generated_ids) != len(set(generated_ids)):
        raise ResponseContractError("Generated activity IDs differ from the requested batch plan")
    validator = _activity_validator()
    for activity in activities:
        interaction = activity.get("interaction") if isinstance(activity, dict) else None
        if isinstance(interaction, dict):
            for field in ("correctOrder", "correctSelections"):
                values = interaction.get(field)
                if (
                    isinstance(values, list)
                    and values
                    and all(
                        isinstance(value, dict)
                        and set(value) == {"itemId"}
                        and isinstance(value["itemId"], str)
                        and value["itemId"]
                        for value in values
                    )
                ):
                    interaction[field] = [value["itemId"] for value in values]
        plan = planned_by_id[activity["id"]]
        for field in ("type", "difficulty", "objective"):
            if activity.get(field) != plan[field]:
                raise ResponseContractError(
                    f"Activity {activity['id']} changed its planned {field}"
                )
        if set(activity.get("misconceptions", [])) != set(plan["misconceptions"]):
            raise ResponseContractError(
                f"Activity {activity['id']} changed its planned misconceptions"
            )
        recovery = activity.get("prerequisiteRecovery")
        if not isinstance(recovery, dict) or recovery.get("prerequisiteId") != plan["prerequisiteId"]:
            raise ResponseContractError(
                f"Activity {activity['id']} changed its planned prerequisite"
            )
        expected_mode = plan["interactionMode"]
        if expected_mode is None:
            if "interactionMode" in activity:
                raise ResponseContractError(
                    f"MCQ {activity['id']} must omit interactionMode"
                )
        elif activity.get("interactionMode") != expected_mode:
            raise ResponseContractError(
                f"Activity {activity['id']} changed its planned interaction mode"
            )
        failures = sorted(
            validator.iter_errors(activity),
            key=lambda error: tuple(map(str, error.absolute_path)),
        )
        if failures:
            error = failures[0]
            location = "".join(
                f"[{part}]" if isinstance(part, int) else f".{part}"
                for part in error.absolute_path
            )
            raise ResponseContractError(
                f"Activity {activity['id']}{location} violates schema-1.1: {error.message}"
            )
    return activities


def validate_plan(
    plan: dict[str, Any],
    *,
    fallback_prerequisite_id: str | None = None,
) -> list[dict[str, Any]]:
    activities = plan.get("activities")
    if not isinstance(activities, list) or len(activities) != 18:
        raise ResponseContractError("Activity plan must contain exactly 18 activities")
    required = {
        "id", "type", "difficulty", "objective", "misconceptions", "prerequisiteId", "interactionMode",
    }
    ids: list[str] = []
    distribution: Counter[tuple[str, str]] = Counter()
    for index, activity in enumerate(activities):
        if not isinstance(activity, dict) or not required.issubset(activity):
            raise ResponseContractError(f"Activity plan item {index} is missing required fields")
        misconceptions = activity["misconceptions"]
        if not isinstance(misconceptions, list) or not misconceptions:
            raise ResponseContractError(f"Activity plan item {index} must reference misconceptions")
        normalized_misconceptions = [
            item.get("id") if isinstance(item, dict) else item
            for item in misconceptions
        ]
        if any(not isinstance(item, str) or not item for item in normalized_misconceptions):
            raise ResponseContractError(f"Activity plan item {index} has an invalid misconception reference")
        activity["misconceptions"] = normalized_misconceptions
        prerequisite = activity["prerequisiteId"]
        if isinstance(prerequisite, dict):
            prerequisite = prerequisite.get("id")
        if prerequisite is None:
            prerequisite = fallback_prerequisite_id
        if not isinstance(prerequisite, str) or not prerequisite:
            raise ResponseContractError(f"Activity plan item {index} has an invalid prerequisite reference")
        activity["prerequisiteId"] = prerequisite
        ids.append(activity["id"])
        distribution[(activity["type"], activity["difficulty"])] += 1
        mode = activity["interactionMode"]
        if activity["type"] == "mcq" and mode is not None:
            raise ResponseContractError(f"Planned MCQ {activity['id']} must have a null interactionMode")
        if activity["type"] == "interactive" and mode not in {"classification", "matching", "ordering", "selection"}:
            raise ResponseContractError(f"Planned interactive activity {activity['id']} has an unsupported interactionMode")
    if len(ids) != len(set(ids)):
        raise ResponseContractError("Activity plan IDs must be unique")
    if distribution != EXPECTED:
        raise ResponseContractError("Activity plan does not contain exactly three of every type/difficulty pair")
    return activities


def assemble_package(
    config: GeneratorConfig,
    analysis: dict[str, Any],
    plan: dict[str, Any],
    batch_documents: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    planned = validate_plan(plan)
    generated: dict[str, dict[str, Any]] = {}
    for batch in batch_documents:
        activities = batch.get("activities")
        if not isinstance(activities, list):
            raise ResponseContractError("Each batch must be an object containing an activities array")
        for activity in activities:
            activity_id = activity.get("id") if isinstance(activity, dict) else None
            if not activity_id or activity_id in generated:
                raise ResponseContractError(f"Generated activity has a missing or duplicate ID: {activity_id}")
            generated[activity_id] = activity
    planned_ids = [item["id"] for item in planned]
    if set(generated) != set(planned_ids):
        missing = sorted(set(planned_ids) - set(generated))
        extra = sorted(set(generated) - set(planned_ids))
        raise ResponseContractError(f"Generated activity IDs differ from the plan; missing={missing}, extra={extra}")
    ordered: list[dict[str, Any]] = []
    for item in planned:
        activity = deepcopy(generated[item["id"]])
        if activity.get("type") != item["type"] or activity.get("difficulty") != item["difficulty"]:
            raise ResponseContractError(f"Activity {item['id']} changed its planned type or difficulty")
        if activity.get("objective") != item["objective"]:
            raise ResponseContractError(f"Activity {item['id']} changed its planned objective")
        if set(activity.get("misconceptions", [])) != set(item["misconceptions"]):
            raise ResponseContractError(f"Activity {item['id']} changed its planned misconceptions")
        recovery = activity.get("prerequisiteRecovery", {})
        if recovery.get("prerequisiteId") != item["prerequisiteId"]:
            raise ResponseContractError(f"Activity {item['id']} changed its planned prerequisite")
        if activity.get("interactionMode") != item["interactionMode"]:
            raise ResponseContractError(f"Activity {item['id']} changed its planned interaction mode")
        ordered.append(activity)
    for key in ("learningObjectives", "prerequisites", "misconceptionCatalogue"):
        if not isinstance(analysis.get(key), list) or not analysis[key]:
            raise ResponseContractError(f"Source analysis must provide non-empty {key}")
    return {
        "schemaVersion": "1.1",
        "packageId": config.package_id,
        "chapter": config.chapter,
        "subchapter": config.subchapter,
        "status": "draft",
        "locales": ["en", "ms", "zh"],
        "learningObjectives": deepcopy(analysis["learningObjectives"]),
        "prerequisites": deepcopy(analysis["prerequisites"]),
        "misconceptionCatalogue": deepcopy(analysis["misconceptionCatalogue"]),
        "evidencePolicy": {
            "preserveFirstAttempt": True,
            "assistedSignals": ["hint", "retry", "prerequisite-recovery"],
            "assistedSuccessSeparate": True,
        },
        "reviewRecord": config.review_relative_path.as_posix(),
        "sourceManifest": config.manifest_relative_path.as_posix(),
        "activities": ordered,
    }

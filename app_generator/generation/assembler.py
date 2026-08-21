"""Assemble stable stage output into schema-1.1 package data."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Iterable

from app_generator.config import GeneratorConfig
from app_generator.errors import ResponseContractError

EXPECTED = Counter(
    (kind, difficulty)
    for kind in ("mcq", "interactive")
    for difficulty in ("easy", "moderate", "challenging")
    for _ in range(3)
)


def validate_plan(plan: dict[str, Any]) -> list[dict[str, Any]]:
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

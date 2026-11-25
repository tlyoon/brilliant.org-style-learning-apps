"""Batched visual-plan/spec generation helpers."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from app_generator.domains import DomainProfile
from app_generator.errors import ResponseContractError
from app_generator.visuals.validation import visual_contract_errors


def visual_generation_catalog(domain: DomainProfile) -> dict[str, Any]:
    """Return only trusted, currently available visual capabilities for prompting."""

    registry = json.loads(domain.path("visuals", "templateRegistry").read_text(encoding="utf-8"))
    styles = json.loads(domain.path("visuals", "styleProfiles").read_text(encoding="utf-8"))
    simulations = json.loads(domain.path("simulations", "modelRegistry").read_text(encoding="utf-8"))

    templates = []
    for template in registry.get("templates", []):
        if not isinstance(template, dict) or template.get("implementationStatus") != "available":
            continue
        templates.append(
            {
                key: deepcopy(template[key])
                for key in (
                    "id",
                    "mode",
                    "semanticParameters",
                    "renderStrategies",
                    "simulationModel",
                    "rendererId",
                    "rendererVersion",
                )
                if key in template
            }
        )

    style_profiles = []
    for profile in styles.get("profiles", []):
        if not isinstance(profile, dict):
            continue
        style_profiles.append(
            {
                key: deepcopy(profile[key])
                for key in (
                    "id",
                    "purpose",
                    "tone",
                    "compositionPriority",
                    "backgroundComplexity",
                    "motionStyle",
                    "mobileFirst",
                    "colorIndependentMeaning",
                )
                if key in profile
            }
        )

    simulation_models = []
    for model in simulations.get("models", []):
        if not isinstance(model, dict):
            continue
        simulation_models.append(
            {
                key: deepcopy(model[key])
                for key in (
                    "id",
                    "modelVersion",
                    "law",
                    "variableIds",
                    "controllableVariableIds",
                    "derivedVariableIds",
                    "bounds",
                    "requiredInvariantKinds",
                    "verificationKinds",
                )
                if key in model
            }
        )

    # Optional domain-owned constraints mirror the trusted renderer validators.
    # Unknown/stale template IDs are never sent to the model.
    guidance_path = domain.path("visuals", "templateRegistry").with_name("renderer-guidance.json")
    renderer_guidance = {}
    if guidance_path.is_file():
        guidance = json.loads(guidance_path.read_text(encoding="utf-8"))
        if guidance.get("schemaVersion") != "1.0" or not isinstance(guidance.get("templates"), dict):
            raise ResponseContractError("Invalid renderer-guidance manifest")
        available = {item["id"] for item in templates}
        if not available.issubset(guidance["templates"]):
            raise ResponseContractError("Renderer guidance is missing an available trusted template")
        renderer_guidance = {key: deepcopy(value) for key, value in guidance["templates"].items() if key in available}
    return {
        "rendererGuidance": renderer_guidance,
        "domainId": domain.id,
        "profileVersion": domain.profile_version,
        "availableTemplates": templates,
        "styleProfiles": style_profiles,
        "simulationModels": simulation_models,
    }


def _records(document: Any, *, value_key: str, label: str) -> list[dict[str, Any]]:
    if not isinstance(document, dict) or set(document) != {"activities"}:
        raise ResponseContractError(f"{label} must contain exactly one activities key")
    records = document["activities"]
    if not isinstance(records, list):
        raise ResponseContractError(f"{label}.activities must be an array")
    for index, record in enumerate(records):
        if not isinstance(record, dict) or set(record) != {"activityId", value_key}:
            raise ResponseContractError(
                f"{label}.activities[{index}] must contain exactly activityId and {value_key}"
            )
        if not isinstance(record.get("activityId"), str) or not record["activityId"]:
            raise ResponseContractError(f"{label}.activities[{index}].activityId must be non-empty")
        if not isinstance(record.get(value_key), dict):
            raise ResponseContractError(f"{label}.activities[{index}].{value_key} must be an object")
    return records


def selected_visual_activity_ids(
    package: dict[str, Any],
    plans_document: Any,
) -> list[str]:
    """Validate the plan batch envelope and return IDs requiring a visual spec."""

    activities = package.get("activities")
    if not isinstance(activities, list):
        raise ResponseContractError("Package activities must be an array before visual planning")
    package_ids = [
        activity.get("id")
        for activity in activities
        if isinstance(activity, dict) and isinstance(activity.get("id"), str)
    ]
    if len(package_ids) != len(activities) or len(package_ids) != len(set(package_ids)):
        raise ResponseContractError("Package activities must have unique non-empty IDs before visual planning")

    records = _records(plans_document, value_key="visualPlan", label="visual-plans")
    plan_ids = [record["activityId"] for record in records]
    if len(plan_ids) != len(set(plan_ids)) or set(plan_ids) != set(package_ids):
        raise ResponseContractError(
            "visual-plans activity IDs must match the package activity IDs exactly"
        )
    by_id = {record["activityId"]: record["visualPlan"] for record in records}
    return [
        activity_id
        for activity_id in package_ids
        if by_id[activity_id].get("selectedMode") != "none"
    ]


def partition_visual_specs(
    repo_root: Path,
    package: dict[str, Any],
    plans_document: dict[str, Any],
    specs_document: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Separate independently valid visual specs without modifying source activities.

    Every selected plan is evaluated with its own real renderer/domain validator.
    Nonselected or duplicate spec IDs are rejected, never silently reused.
    """
    selected = selected_visual_activity_ids(package, plans_document)
    plans = {record["activityId"]: record for record in _records(
        plans_document, value_key="visualPlan", label="visual-plans"
    )}
    specs = _records(specs_document, value_key="visualSpec", label="visual-specs")
    ids = [record["activityId"] for record in specs]
    if len(ids) != len(set(ids)) or not set(ids).issubset(selected):
        raise ResponseContractError("visual-specs contains duplicate or unselected activity IDs")
    by_id = {record["activityId"]: record for record in specs}
    activities = {activity["id"]: activity for activity in package["activities"]}
    valid: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    for activity_id in selected:
        record = by_id.get(activity_id)
        if record is None:
            failures.append(f"{activity_id}: missing visualSpec")
            continue
        probe = deepcopy(package)
        probe["activities"] = [deepcopy(activities[activity_id])]
        try:
            attach_visual_documents(
                repo_root, probe, {"activities": [plans[activity_id]]},
                {"activities": [record]},
            )
        except ResponseContractError as error:
            failures.append(f"{activity_id}: {error}")
        else:
            valid[activity_id] = deepcopy(record)
    return valid, failures


def attach_visual_documents(
    repo_root: Path,
    package: dict[str, Any],
    plans_document: Any,
    specs_document: Any,
) -> dict[str, Any]:
    """Attach generated visuals without permitting the LLM to rewrite activity content."""

    selected_ids = selected_visual_activity_ids(package, plans_document)
    plan_records = _records(plans_document, value_key="visualPlan", label="visual-plans")
    spec_records = _records(specs_document, value_key="visualSpec", label="visual-specs")

    spec_ids = [record["activityId"] for record in spec_records]
    if len(spec_ids) != len(set(spec_ids)) or set(spec_ids) != set(selected_ids):
        raise ResponseContractError(
            "visual-specs activity IDs must match exactly the plans whose selectedMode is not none"
        )

    plans_by_id = {record["activityId"]: record["visualPlan"] for record in plan_records}
    specs_by_id = {record["activityId"]: record["visualSpec"] for record in spec_records}
    result = deepcopy(package)
    for activity in result["activities"]:
        activity_id = activity["id"]
        activity["visualPlan"] = deepcopy(plans_by_id[activity_id])
        if activity_id in specs_by_id:
            activity["visualSpec"] = deepcopy(specs_by_id[activity_id])
        else:
            activity.pop("visualSpec", None)

    errors = visual_contract_errors(repo_root, result)
    if errors:
        preview = "; ".join(errors[:8])
        if len(errors) > 8:
            preview += f"; ... ({len(errors) - 8} more)"
        raise ResponseContractError(f"Generated visual contract failed: {preview}")
    return result

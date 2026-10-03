"""Deterministic validation for visual plans and declarative visual specifications."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from app_generator.domains import resolve_domain

FORBIDDEN_FIELD_NAMES = {
    "javascript", "script", "html", "css", "svg", "markup", "executable", "code",
    "pixels", "pixelData", "imageData", "animationFrames", "pathData",
    "x", "y", "x1", "x2", "y1", "y2", "cx", "cy", "widthPx", "heightPx",
}
FORBIDDEN_TEXT = re.compile(r"(?:javascript\s*:|<\s*(?:script|svg|style)\b|on(?:load|click|error)\s*=)", re.I)


def _schema_validator(path: Path) -> Draft202012Validator:
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _schema_errors(validator: Draft202012Validator, value: Any, label: str) -> list[str]:
    failures = sorted(validator.iter_errors(value), key=lambda error: tuple(map(str, error.absolute_path)))
    errors: list[str] = []
    for error in failures:
        location = label + "".join(
            f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.absolute_path
        )
        errors.append(f"{location}: {error.message}")
    return errors


def _walk(value: Any, path: str) -> Iterable[tuple[str, Any, str | None]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield child_path, child, key
            yield from _walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, child, None
            yield from _walk(child, child_path)


def _code_and_coordinate_errors(value: Any, label: str) -> list[str]:
    errors: list[str] = []
    for path, child, key in _walk(value, label):
        if key in FORBIDDEN_FIELD_NAMES:
            errors.append(f"{path}: raw rendering/code field is forbidden; use semantic parameters")
        if isinstance(child, str) and FORBIDDEN_TEXT.search(child):
            errors.append(f"{path}: executable or markup-like content is forbidden")
    return errors


def _template_registry(repo_root: Path) -> dict[str, dict[str, Any]]:
    path = resolve_domain(repo_root).path("visuals", "templateRegistry")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != "1.0":
        raise ValueError("Unsupported visual template registry version")
    templates = data.get("templates")
    if not isinstance(templates, list):
        raise ValueError("Visual template registry must contain a templates array")
    by_id: dict[str, dict[str, Any]] = {}
    for template in templates:
        template_id = template.get("id") if isinstance(template, dict) else None
        if not isinstance(template_id, str) or not template_id:
            raise ValueError("Visual template registry contains an invalid template id")
        if template_id in by_id:
            raise ValueError(f"Duplicate visual template id: {template_id}")
        by_id[template_id] = template
    return by_id


def _style_profiles(repo_root: Path) -> set[str]:
    path = resolve_domain(repo_root).path("visuals", "styleProfiles")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != "1.0":
        raise ValueError("Unsupported visual style registry version")
    profiles = data.get("profiles")
    if not isinstance(profiles, list):
        raise ValueError("Visual style registry must contain a profiles array")
    ids: list[str] = []
    required = {
        "id", "purpose", "tone", "compositionPriority", "visualDensity",
        "backgroundComplexity", "colorStrategy", "geometryStyle", "motionStyle",
        "rasterTextPolicy", "mobileFirst", "colorIndependentMeaning",
    }
    for profile in profiles:
        if not isinstance(profile, dict) or not required.issubset(profile):
            raise ValueError("Visual style registry contains an incomplete profile")
        profile_id = profile.get("id")
        if not isinstance(profile_id, str) or re.fullmatch(r"[a-z][a-z0-9]*(?:[-_.][a-z0-9]+)*", profile_id) is None:
            raise ValueError("Visual style registry contains an invalid profile id")
        if profile.get("compositionPriority") != "concept-first":
            raise ValueError(f"Visual style profile {profile_id} must remain concept-first")
        if profile.get("rasterTextPolicy") != "forbidden":
            raise ValueError(f"Visual style profile {profile_id} must forbid learner text in raster assets")
        if profile.get("mobileFirst") is not True or profile.get("colorIndependentMeaning") is not True:
            raise ValueError(f"Visual style profile {profile_id} must preserve mobile and color-independent meaning")
        ids.append(profile_id)
    if len(ids) != len(set(ids)):
        raise ValueError("Visual style registry contains duplicate profile ids")
    return set(ids)


def _simulation_models(repo_root: Path) -> dict[str, dict[str, Any]]:
    path = resolve_domain(repo_root).path("simulations", "modelRegistry")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != "1.0":
        raise ValueError("Unsupported simulation model registry version")
    models = data.get("models")
    if not isinstance(models, list):
        raise ValueError("Simulation model registry must contain a models array")
    by_id: dict[str, dict[str, Any]] = {}
    for model in models:
        model_id = model.get("id") if isinstance(model, dict) else None
        if not isinstance(model_id, str) or not model_id:
            raise ValueError("Simulation model registry contains an invalid model id")
        if model_id in by_id:
            raise ValueError(f"Duplicate simulation model id: {model_id}")
        by_id[model_id] = model
    return by_id


def _verification_kinds(repo_root: Path) -> set[str]:
    path = resolve_domain(repo_root).path("verification", "policy")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != "1.0":
        raise ValueError("Unsupported domain verification policy version")
    kinds = data.get("verificationKinds")
    if not isinstance(kinds, list) or len(kinds) != len(set(kinds)) or any(not isinstance(kind, str) or not kind for kind in kinds):
        raise ValueError("Domain verification policy must contain a unique verificationKinds list")
    return set(kinds)


def visual_registry_errors(repo_root: Path) -> list[str]:
    """Validate trusted visual/style/simulation registries independent of any package."""
    errors: list[str] = []
    try:
        domain = resolve_domain(repo_root)
        templates = _template_registry(repo_root)
        styles = _style_profiles(repo_root)
        models = _simulation_models(repo_root)
        verification_kinds = _verification_kinds(repo_root)
        trusted_renderers = domain.trusted_renderers
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"visual registries: {exc}"]

    allowed_modes = {
        "scene_diagram", "vector_diagram", "graph_plot", "energy_bar", "timeline",
        "matching_board", "classification_board", "ordering_board", "drag_label_diagram",
        "hotspot_diagram", "parameter_simulation",
    }
    allowed_strategies = {
        "deterministic_semantic", "deterministic_simulation", "hybrid_generated_base", "gemini_illustration"
    }
    for template_id, template in templates.items():
        if template.get("mode") not in allowed_modes:
            errors.append(f"visual template {template_id}: unsupported mode {template.get('mode')!r}")
        status = template.get("implementationStatus")
        if status not in {"available", "planned"}:
            errors.append(f"visual template {template_id}: implementationStatus must be available or planned")
        expected_renderer = trusted_renderers.get(template_id)
        if status == "available":
            if expected_renderer is None:
                errors.append(f"visual template {template_id}: marked available without a trusted runtime renderer")
            else:
                renderer_id, renderer_version = expected_renderer
                if template.get("rendererId") != renderer_id or template.get("rendererVersion") != renderer_version:
                    errors.append(f"visual template {template_id}: renderer identity/version does not match trusted runtime code")
        elif template.get("rendererId") is not None or template.get("rendererVersion") is not None:
            errors.append(f"visual template {template_id}: planned templates must not claim an available renderer")
        strategies = template.get("renderStrategies")
        if not isinstance(strategies, list) or not strategies or len(strategies) != len(set(strategies)):
            errors.append(f"visual template {template_id}: renderStrategies must be a non-empty unique list")
        elif any(strategy not in allowed_strategies for strategy in strategies):
            errors.append(f"visual template {template_id}: contains an unsupported render strategy")
        parameters = template.get("semanticParameters", [])
        if not isinstance(parameters, list) or len(parameters) != len(set(parameters)):
            errors.append(f"visual template {template_id}: semanticParameters must be a unique list")
        model_id = template.get("simulationModel")
        if template.get("mode") == "parameter_simulation" and model_id not in models:
            errors.append(f"visual template {template_id}: parameter_simulation requires a trusted simulationModel")
        if model_id is not None and model_id not in models:
            errors.append(f"visual template {template_id}: unknown simulationModel {model_id!r}")

    if not styles:
        errors.append("visual style registry: at least one style profile is required")

    for model_id, model in models.items():
        variable_ids = model.get("variableIds")
        controllable = model.get("controllableVariableIds")
        kinds = model.get("verificationKinds")
        if not isinstance(variable_ids, list) or not variable_ids or len(variable_ids) != len(set(variable_ids)):
            errors.append(f"simulation model {model_id}: variableIds must be a non-empty unique list")
            variable_set: set[str] = set()
        else:
            variable_set = set(variable_ids)
        if not isinstance(controllable, list) or len(controllable) != len(set(controllable)):
            errors.append(f"simulation model {model_id}: controllableVariableIds must be a unique list")
        elif any(variable not in variable_set for variable in controllable):
            errors.append(f"simulation model {model_id}: controllable variables must be declared in variableIds")
        if not isinstance(kinds, list) or any(kind not in verification_kinds for kind in kinds):
            errors.append(f"simulation model {model_id}: contains an unsupported verification kind")
        if not isinstance(model.get("modelVersion"), str) or not model.get("modelVersion"):
            errors.append(f"simulation model {model_id}: modelVersion is required")
        if not isinstance(model.get("law"), str) or not model.get("law").strip():
            errors.append(f"simulation model {model_id}: law is required")
        derived = model.get("derivedVariableIds", [])
        if not isinstance(derived, list) or any(variable not in variable_set for variable in derived):
            errors.append(f"simulation model {model_id}: derivedVariableIds must be declared variables")
        required_invariants = model.get("requiredInvariantKinds", [])
        if not isinstance(required_invariants, list) or any(kind not in {"constant", "conserved", "equal", "opposite", "orthogonal", "bounded", "monotonic-increasing", "monotonic-decreasing"} for kind in required_invariants):
            errors.append(f"simulation model {model_id}: contains an unsupported required invariant kind")
        bounds = model.get("bounds", {})
        if not isinstance(bounds, dict):
            errors.append(f"simulation model {model_id}: bounds must be an object")
        else:
            for variable in controllable if isinstance(controllable, list) else []:
                bound = bounds.get(variable)
                if not isinstance(bound, list) or len(bound) != 2 or any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in bound) or bound[0] >= bound[1]:
                    errors.append(f"simulation model {model_id}: controllable variable {variable} requires numeric increasing bounds")
    return errors


def _ids(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    return [item.get("id") for item in items if isinstance(item, dict) and isinstance(item.get("id"), str)]


def _semantic_ids(spec: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for field in ("entities", "relations", "vectors", "axes", "graphSeries", "controls", "states", "invariants"):
        ids.extend(_ids(spec.get(field, [])))
    simulation = spec.get("simulation")
    if isinstance(simulation, dict) and isinstance(simulation.get("id"), str):
        ids.append(simulation["id"])
    return ids


def _unique_id_errors(spec: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    for field in ("entities", "relations", "vectors", "axes", "graphSeries", "controls", "states", "invariants"):
        ids = _ids(spec.get(field, []))
        if len(ids) != len(set(ids)):
            errors.append(f"{label}.{field}: IDs must be unique")
    all_ids = _semantic_ids(spec)
    if len(all_ids) != len(set(all_ids)):
        errors.append(f"{label}: semantic IDs must be unique across visual element families")
    return errors


def _reference_errors(spec: dict[str, Any], plan: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    entity_ids = set(_ids(spec.get("entities", [])))
    axis_by_id = {axis["id"]: axis for axis in spec.get("axes", []) if isinstance(axis, dict) and "id" in axis}
    invariant_ids = set(_ids(spec.get("invariants", [])))
    all_ids = set(_semantic_ids(spec))

    for index, relation in enumerate(spec.get("relations", [])):
        if relation.get("sourceId") not in all_ids or relation.get("targetId") not in all_ids:
            errors.append(f"{label}.relations[{index}]: sourceId and targetId must reference declared visual elements")
    for index, vector in enumerate(spec.get("vectors", [])):
        if vector.get("entityId") not in entity_ids:
            errors.append(f"{label}.vectors[{index}].entityId: must reference a declared entity")
    for index, series in enumerate(spec.get("graphSeries", [])):
        x_axis = axis_by_id.get(series.get("xAxisId"))
        y_axis = axis_by_id.get(series.get("yAxisId"))
        if x_axis is None or x_axis.get("role") != "x":
            errors.append(f"{label}.graphSeries[{index}].xAxisId: must reference the declared x axis")
        if y_axis is None or y_axis.get("role") != "y":
            errors.append(f"{label}.graphSeries[{index}].yAxisId: must reference the declared y axis")
    simulation = spec.get("simulation")
    if isinstance(simulation, dict):
        variable_ids = set(simulation.get("variableIds", []))
        for index, control in enumerate(spec.get("controls", [])):
            if control.get("variableId") not in variable_ids:
                errors.append(f"{label}.controls[{index}].variableId: must reference a declared simulation variable")
        for index, state in enumerate(spec.get("states", [])):
            unknown = sorted(set(state.get("values", {})) - variable_ids)
            if unknown:
                errors.append(f"{label}.states[{index}].values: undeclared simulation variable(s): {', '.join(unknown)}")
        for invariant_id in simulation.get("invariantIds", []):
            if invariant_id not in invariant_ids:
                errors.append(f"{label}.simulation.invariantIds: {invariant_id} is not a declared invariant")
    for index, invariant in enumerate(spec.get("invariants", [])):
        for reference in invariant.get("references", []):
            if reference not in all_ids:
                errors.append(f"{label}.invariants[{index}].references: {reference} is not a declared visual element")
    for index, grounding in enumerate(spec.get("grounding", [])):
        for reference in grounding.get("appliesTo", []):
            if reference not in all_ids:
                errors.append(f"{label}.grounding[{index}].appliesTo: {reference} is not a declared visual element")
    validation = spec.get("validation", {})
    for reference in validation.get("answerRelevantIds", []):
        if reference not in all_ids:
            errors.append(f"{label}.validation.answerRelevantIds: {reference} is not a declared visual element")
    for reference in plan.get("aestheticIntent", {}).get("attentionTargetIds", []):
        if reference not in all_ids:
            errors.append(f"{label}.visualPlan.aestheticIntent.attentionTargetIds: {reference} is not a declared visual element")
    return errors


def _mode_errors(spec: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    mode = spec.get("mode")
    if mode == "graph_plot":
        roles = [axis.get("role") for axis in spec.get("axes", []) if isinstance(axis, dict)]
        if sorted(roles) != ["x", "y"]:
            errors.append(f"{label}.axes: graph_plot requires exactly one x axis and one y axis")
    if mode == "parameter_simulation":
        fallback = spec.get("fallback", {}).get("mode")
        if fallback in {None, "none", "parameter_simulation"}:
            errors.append(f"{label}.fallback.mode: parameter_simulation requires a non-simulation fallback")
    for index, control in enumerate(spec.get("controls", [])):
        low, high, default = control.get("min"), control.get("max"), control.get("default")
        if all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in (low, high, default)):
            if low >= high:
                errors.append(f"{label}.controls[{index}]: min must be less than max")
            if not low <= default <= high:
                errors.append(f"{label}.controls[{index}].default: must lie within the declared range")
    return errors


def _domain_visual_spec_errors(repo_root: Path, spec: dict[str, Any], label: str) -> list[str]:
    domain = resolve_domain(repo_root)
    module = domain.load_module("validation", "visualValidatorModule")
    validator = getattr(module, "visual_spec_errors", None)
    if not callable(validator):
        raise ValueError(f"Domain {domain.id!r} visual validator has no visual_spec_errors function")
    return list(validator(spec, label))


def _domain_visual_plan_errors(repo_root: Path, plan: dict[str, Any], label: str) -> list[str]:
    domain = resolve_domain(repo_root)
    module = domain.load_module("validation", "visualValidatorModule")
    validator = getattr(module, "visual_plan_errors", None)
    if not callable(validator):
        return []
    return list(validator(plan, label))

def _template_errors(
    plan: dict[str, Any],
    spec: dict[str, Any] | None,
    templates: dict[str, dict[str, Any]],
    style_profiles: set[str],
    simulation_models: dict[str, dict[str, Any]],
    label: str,
) -> list[str]:
    errors: list[str] = []
    mode = plan.get("selectedMode")
    template_id = plan.get("selectedTemplate")
    if mode != "none":
        template = templates.get(template_id)
        if template is None:
            errors.append(f"{label}.visualPlan.selectedTemplate: unknown trusted template {template_id!r}")
        else:
            if template.get("implementationStatus") != "available":
                errors.append(f"{label}.visualPlan.selectedTemplate: trusted template {template_id!r} is not yet available")
            if template.get("mode") != mode:
                errors.append(
                    f"{label}.visualPlan.selectedTemplate: template mode {template.get('mode')!r} does not match selected mode {mode!r}"
                )
            strategy = plan.get("renderStrategy")
            allowed = template.get("renderStrategies", [])
            if strategy not in allowed:
                errors.append(
                    f"{label}.visualPlan.renderStrategy: {strategy!r} is not allowed by trusted template {template_id!r}"
                )
    if spec is not None:
        spec_template = templates.get(spec.get("template"))
        if spec_template is None:
            errors.append(f"{label}.visualSpec.template: unknown trusted template {spec.get('template')!r}")
        else:
            if spec_template.get("mode") != spec.get("mode"):
                errors.append(
                    f"{label}.visualSpec.template: template mode {spec_template.get('mode')!r} does not match visual mode {spec.get('mode')!r}"
                )
            simulation = spec.get("simulation")
            if isinstance(simulation, dict):
                model_id = simulation.get("modelId")
                model = simulation_models.get(model_id)
                if model is None:
                    errors.append(f"{label}.visualSpec.simulation.modelId: unknown trusted simulation model {model_id!r}")
                else:
                    allowed_variables = set(model.get("variableIds", []))
                    declared_variables = set(simulation.get("variableIds", []))
                    unknown_variables = sorted(declared_variables - allowed_variables)
                    if unknown_variables:
                        errors.append(
                            f"{label}.visualSpec.simulation.variableIds: variable(s) not supported by model {model_id!r}: {', '.join(unknown_variables)}"
                        )
                    controllable = set(model.get("controllableVariableIds", []))
                    for index, control in enumerate(spec.get("controls", [])):
                        if control.get("variableId") not in controllable:
                            errors.append(
                                f"{label}.visualSpec.controls[{index}].variableId: not controllable in model {model_id!r}"
                            )
                expected_model = spec_template.get("simulationModel")
                if expected_model is not None and model_id != expected_model:
                    errors.append(
                        f"{label}.visualSpec.simulation.modelId: {model_id!r} does not match template model {expected_model!r}"
                    )
    style_profile = plan.get("aestheticIntent", {}).get("styleProfile")
    if style_profile not in style_profiles:
        errors.append(f"{label}.visualPlan.aestheticIntent.styleProfile: unknown style profile {style_profile!r}")
    return errors


def _verification_policy_errors(plan: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    generated = plan.get("generatedAssetPolicy", {})
    verification = plan.get("verificationRequirements", {})
    strategy = plan.get("renderStrategy")
    if generated.get("requiresMultimodalAudit") is True and verification.get("finalMultimodalAudit") is not True:
        errors.append(
            f"{label}.verificationRequirements.finalMultimodalAudit: required for generated-image visual strategies"
        )
    if strategy in {"hybrid_generated_base", "gemini_illustration"} and verification.get("finalMultimodalAudit") is not True:
        errors.append(
            f"{label}.verificationRequirements.finalMultimodalAudit: generated imagery must receive final multimodal audit"
        )
    if generated.get("allowSearchGrounding") is True and verification.get("referenceGrounding") == "source-corpus":
        errors.append(
            f"{label}.verificationRequirements.referenceGrounding: search grounding requires a source-plus-* policy"
        )
    return errors


def _cross_contract_errors(activity: dict[str, Any], label: str) -> list[str]:
    plan = activity.get("visualPlan")
    spec = activity.get("visualSpec")
    if plan is None and spec is None:
        return []
    errors: list[str] = []
    if plan is None:
        return [f"{label}.visualPlan: required whenever visualSpec is present"]
    intent = plan.get("activityIntent", {})
    if intent.get("learningObjective") != activity.get("objective"):
        errors.append(f"{label}.visualPlan.activityIntent.learningObjective: must equal activity objective")
    if intent.get("difficulty") != activity.get("difficulty"):
        errors.append(f"{label}.visualPlan.activityIntent.difficulty: must equal activity difficulty")
    if set(intent.get("misconceptionTargets", [])) != set(activity.get("misconceptions", [])):
        errors.append(f"{label}.visualPlan.activityIntent.misconceptionTargets: must match activity misconceptions")

    selected_mode = plan.get("selectedMode")
    required = plan.get("representationAssessment", {}).get("visualRequired")
    if selected_mode == "none":
        if spec is not None:
            errors.append(f"{label}.visualSpec: must be absent when selectedMode is none")
    else:
        if spec is None:
            errors.append(f"{label}.visualSpec: required for selected visual mode {selected_mode}")
        elif spec.get("mode") != selected_mode:
            errors.append(f"{label}.visualSpec.mode: must equal visualPlan.selectedMode")
        elif spec.get("template") != plan.get("selectedTemplate"):
            errors.append(f"{label}.visualSpec.template: must equal visualPlan.selectedTemplate")
    if required is True and selected_mode == "none":
        errors.append(f"{label}.visualPlan: visualRequired cannot select none")

    if spec is not None:
        plan_facts = set(plan.get("groundedFactsUsed", []))
        source_facts = {
            entry.get("factId") for entry in spec.get("grounding", [])
            if isinstance(entry, dict) and entry.get("origin") == "source_fact"
        }
        missing = sorted(source_facts - plan_facts)
        if missing:
            errors.append(f"{label}.visualSpec.grounding: source facts missing from visualPlan.groundedFactsUsed: {', '.join(missing)}")
    return errors


def visual_contract_errors(repo_root: Path, package: Any, label: str = "package") -> list[str]:
    """Return deterministic visual-contract errors while preserving legacy package compatibility."""
    if not isinstance(package, dict) or not isinstance(package.get("activities"), list):
        return []
    if not any(
        isinstance(activity, dict) and ("visualPlan" in activity or "visualSpec" in activity)
        for activity in package["activities"]
    ):
        return []
    registry_errors = visual_registry_errors(repo_root)
    if registry_errors:
        return [f"{label}: {error}" for error in registry_errors]
    schema_root = repo_root / "content" / "schema"
    plan_validator = _schema_validator(schema_root / "visual-plan.schema.json")
    spec_validator = _schema_validator(schema_root / "visual-spec.schema.json")
    templates = _template_registry(repo_root)
    style_profiles = _style_profiles(repo_root)
    simulation_models = _simulation_models(repo_root)
    errors: list[str] = []
    for index, activity in enumerate(package["activities"]):
        if not isinstance(activity, dict):
            continue
        activity_label = f"{label}.activities[{index}]"
        plan = activity.get("visualPlan")
        spec = activity.get("visualSpec")
        if plan is None and spec is None:
            continue
        plan_schema_errors = (
            _schema_errors(plan_validator, plan, f"{activity_label}.visualPlan") if plan is not None else []
        )
        spec_schema_errors = (
            _schema_errors(spec_validator, spec, f"{activity_label}.visualSpec") if spec is not None else []
        )
        errors.extend(plan_schema_errors)
        errors.extend(spec_schema_errors)
        if plan is not None:
            errors.extend(_code_and_coordinate_errors(plan, f"{activity_label}.visualPlan"))
        if spec is not None:
            errors.extend(_code_and_coordinate_errors(spec, f"{activity_label}.visualSpec"))
        if plan is None:
            errors.extend(_cross_contract_errors(activity, activity_label))
            continue
        if not plan_schema_errors and not spec_schema_errors:
            errors.extend(_verification_policy_errors(plan, f"{activity_label}.visualPlan"))
            errors.extend(_domain_visual_plan_errors(repo_root, plan, f"{activity_label}.visualPlan"))
            errors.extend(_cross_contract_errors(activity, activity_label))
            if spec is not None:
                errors.extend(_unique_id_errors(spec, f"{activity_label}.visualSpec"))
                errors.extend(_reference_errors(spec, plan, f"{activity_label}.visualSpec"))
                errors.extend(_mode_errors(spec, f"{activity_label}.visualSpec"))
                errors.extend(_domain_visual_spec_errors(repo_root, spec, f"{activity_label}.visualSpec"))
            errors.extend(_template_errors(plan, spec, templates, style_profiles, simulation_models, activity_label))
    return errors

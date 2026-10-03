"""University-level physics extensions to the generic visual contract."""

from __future__ import annotations

from typing import Any


def visual_plan_errors(plan: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    verification = plan.get("verificationRequirements", {})
    if verification.get("domainComputation", verification.get("physicsComputation")) == "symbolic-crosscheck" and verification.get("requireIndependentCrosscheck") is not True:
        errors.append(
            f"{label}.verificationRequirements.requireIndependentCrosscheck: symbolic-crosscheck must be independent"
        )
    return errors


def visual_spec_errors(spec: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    template = spec.get("template")
    entities = spec.get("entities", [])
    vectors = spec.get("vectors", [])
    parameters = spec.get("semanticParameters", {})

    if template == "mechanics.cart_collision_1d":
        carts = [entity for entity in entities if isinstance(entity, dict) and entity.get("kind") == "cart"]
        if not 1 <= len(carts) <= 4 or len(carts) != len(entities):
            errors.append(f"{label}.entities: cart-collision renderer requires one to four cart entities")
        phase = parameters.get("phase")
        if phase is not None and phase not in {"before", "during", "after"}:
            errors.append(f"{label}.semanticParameters.phase: must be before, during, or after")
        orientation = parameters.get("track_orientation")
        if orientation is not None and orientation != "horizontal":
            errors.append(f"{label}.semanticParameters.track_orientation: cart-collision v1 supports horizontal only")

    elif template == "mechanics.free_body_2d":
        bodies = [entity for entity in entities if isinstance(entity, dict) and entity.get("kind") == "body"]
        if len(entities) != 1 or len(bodies) != 1:
            errors.append(f"{label}.entities: free-body renderer requires exactly one body entity")
        if not vectors:
            errors.append(f"{label}.vectors: free-body renderer requires at least one vector")
        elif bodies and any(vector.get("entityId") != bodies[0].get("id") for vector in vectors):
            errors.append(f"{label}.vectors: every free-body vector must reference the body entity")

    elif template == "graph.cartesian_qualitative":
        series = spec.get("graphSeries", [])
        if not 1 <= len(series) <= 4:
            errors.append(f"{label}.graphSeries: qualitative graph renderer requires one to four series")

    elif template == "state.energy_bar":
        components = [entity for entity in entities if isinstance(entity, dict) and entity.get("kind") == "energy-component"]
        if not 1 <= len(components) <= 4 or len(components) != len(entities):
            errors.append(f"{label}.entities: energy-bar renderer requires one to four energy-component entities")
        for index, component in enumerate(components):
            amount = component.get("properties", {}).get("relativeAmount")
            if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not 0 <= amount <= 1:
                errors.append(f"{label}.entities[{index}].properties.relativeAmount: must be a number from 0 to 1")

    elif template == "mechanics.motion_1d_slider":
        carts = [entity for entity in entities if isinstance(entity, dict) and entity.get("kind") == "cart"]
        if len(entities) != 1 or len(carts) != 1:
            errors.append(f"{label}.entities: motion-1d simulation requires exactly one cart entity")
        if parameters.get("motion_model") != "constant-velocity":
            errors.append(f"{label}.semanticParameters.motion_model: must be constant-velocity")
        simulation = spec.get("simulation")
        if not isinstance(simulation, dict) or simulation.get("modelId") != "kinematics.motion_1d":
            errors.append(f"{label}.simulation.modelId: motion-1d simulation requires kinematics.motion_1d")
        elif set(simulation.get("variableIds", [])) != {"position", "velocity", "time"}:
            errors.append(f"{label}.simulation.variableIds: motion-1d simulation requires position, velocity, and time")
        states = spec.get("states", [])
        initial = next((state for state in states if isinstance(state, dict) and state.get("id") == "initial-state"), None)
        values = initial.get("values", {}) if initial else {}
        if initial is None or any(isinstance(values.get(name), bool) or not isinstance(values.get(name), (int, float)) for name in ("position", "velocity", "time")):
            errors.append(f"{label}.states: motion-1d simulation requires numeric position, velocity, and time in initial-state")
        elif values.get("time") != 0:
            errors.append(f"{label}.states.initial-state.values.time: must start at 0")
        controls = [control for control in spec.get("controls", []) if isinstance(control, dict)]
        control_by_variable = {control.get("variableId"): control for control in controls}
        if set(control_by_variable) != {"velocity", "time"} or len(controls) != 2:
            errors.append(f"{label}.controls: motion-1d simulation requires exactly velocity and time sliders")
        else:
            velocity = control_by_variable["velocity"]
            time = control_by_variable["time"]
            if velocity.get("min", -21) < -20 or velocity.get("max", 21) > 20:
                errors.append(f"{label}.controls: velocity slider must remain within -20 to 20")
            if time.get("min") != 0 or time.get("max", 21) > 20:
                errors.append(f"{label}.controls: time slider must start at 0 and end at or before 20")
        fallback = spec.get("fallback", {})
        if fallback.get("mode") != "scene_diagram" or fallback.get("template") != "mechanics.cart_collision_1d":
            errors.append(f"{label}.fallback: motion-1d simulation requires the static mechanics.cart_collision_1d fallback")
        if spec.get("accessibility", {}).get("reducedMotionStrategy") != "instant-state":
            errors.append(f"{label}.accessibility.reducedMotionStrategy: motion-1d simulation requires instant-state")
        invariant_by_id = {item.get("id"): item for item in spec.get("invariants", []) if isinstance(item, dict)}
        invariant_ids = simulation.get("invariantIds", []) if isinstance(simulation, dict) else []
        constant_velocity = [
            invariant_by_id.get(invariant_id) for invariant_id in invariant_ids
            if isinstance(invariant_by_id.get(invariant_id), dict)
            and invariant_by_id[invariant_id].get("kind") == "constant"
        ] if isinstance(simulation, dict) else []
        if not constant_velocity:
            errors.append(f"{label}.invariants: motion-1d simulation requires a declared constant-velocity invariant tied to the simulation")
    return errors

"""Bounded original-source diagram physics invariants, independent of Gemini.

Four cart diagrams encode INITIAL CONDITIONS only; the fifth is a spring
energy ledger. This proves neither visual pixels nor scientific explanations
nor entire translations nor academic PASS.
"""
from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any

from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster

# Independently specified initial conditions, not a restatement of rendered
# values. No inferred final velocities or answer-key correctness.
_CART_CASES = {
    "mcq-collision-types-concept": (
        ("m1", "m2"), (("cart-1", "right"), ("cart-2", "left"))),
    "mcq-perfectly-inelastic-outcome": (
        ("m", "m"), (("cart-1", "right"),)),
    "mcq-equal-mass-elastic-transfer": (
        ("m", "m"), (("cart-1", "right"),)),
    "mcq-extreme-mass-heavy-target": (
        ("m", "large-m"), (("cart-1", "right"),)),
}
_ENERGY_CASE = "mcq-spring-collision-intermediate"
_EXPECTED = frozenset((*_CART_CASES, _ENERGY_CASE))


def _finite_relative(value: Any) -> Fraction:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("diagram relative magnitude must be finite numeric")
    number = Fraction(str(value))
    if not 0 <= number <= 1:
        raise ValueError("diagram relative magnitude outside unit interval")
    return number


def check_bounded_diagram_physics(activity: dict[str, Any]) -> dict[str, Any]:
    """Evaluate original fixed scenario shapes without source text in output."""
    aid = activity.get("id")
    if aid not in _EXPECTED:
        raise ValueError("unrecognized source-bound diagram physics case")
    spec = activity.get("visualSpec")
    if not isinstance(spec, dict):
        raise ValueError("source-bound diagram is missing")
    entities = spec.get("entities")
    if not isinstance(entities, list) or len(entities) != 2:
        raise ValueError("physics diagram must specify exactly two entities")
    if any(not isinstance(item, dict) for item in entities):
        raise ValueError("malformed diagram entity")
    ids = [item.get("id") for item in entities]
    if len(set(ids)) != 2:
        raise ValueError("diagram entity IDs must be unique")
    if aid in _CART_CASES:
        masses, velocities = _CART_CASES[aid]
        if (spec.get("template") != "mechanics.cart_collision_1d" or
                spec.get("semanticParameters", {}).get("phase") != "before" or
                spec.get("semanticParameters", {}).get("track_orientation") not in
                ("horizontal", "left-to-right")):
            raise ValueError("cart scenario not an authorized preimpact 1D configuration")
        if (ids != ["cart-1", "cart-2"] or
                any(item.get("kind") != "cart" for item in entities)):
            raise ValueError("diagram cart identities do not match physical model")
        actual_masses = tuple(item.get("properties", {}).get("mass")
                              for item in entities)
        if actual_masses != masses:
            raise ValueError("mass labels contradict bounded model configuration")
        vectors = spec.get("vectors")
        if not isinstance(vectors, list) or len(vectors) != len(velocities):
            raise ValueError("cart diagram velocity roster altered")
        observed = []
        for vector in vectors:
            if (not isinstance(vector, dict) or
                    vector.get("quantity") != "velocity"):
                raise ValueError("cart arrow must describe velocity")
            observed.append((vector.get("entityId"), vector.get("direction")))
            if not 0 < _finite_relative(vector.get("relativeMagnitude")) <= 1:
                raise ValueError("cart velocity vector must have positive scale")
        if tuple(observed) != velocities:
            raise ValueError("cart arrows conflict with before-collision physics")
        return {
            "activityId": aid, "boundedPhysicalCheck": "INITIAL_CART_DIRECTIONS_AND_MASS_LABELS",
            "beforeCollisionVerified": True,
            "numberOfInitialVelocityVectors": len(vectors),
            "postImpactOutcomesVerified": False,
            "numericalMassRatiosVerified": False,
            "scientificVisualSemanticsVerified": False,
            "academicQA": "REVIEW_REQUIRED",
        }
    if (spec.get("template") != "state.energy_bar" or
            spec.get("vectors") not in (None, []) or
            ids != ["kinetic", "elastic"] or
            any(item.get("kind") != "energy-component" for item in entities)):
        raise ValueError("spring energy bar physics template modified")
    states = spec.get("states")
    if not isinstance(states, list) or len(states) != 2:
        raise ValueError("energy bar needs initial and compressed states")
    if [state.get("id") for state in states] != ["initial-state", "intermediate-state"]:
        raise ValueError("spring diagram state order changed")
    values = []
    for state in states:
        observed = state.get("values")
        if not isinstance(observed, dict) or set(observed) != set(ids):
            raise ValueError("energy ledger components mismatch")
        ledger = tuple(_finite_relative(observed[name]) for name in ids)
        if sum(ledger) != 1:
            raise ValueError("spring energy not conserved across rendered states")
        values.append(ledger)
    if values[0] != (Fraction(1), Fraction(0)):
        raise ValueError("initial spring is not uncompressed and kinetic")
    if not (0 < values[1][0] < 1 and 0 < values[1][1] < 1):
        raise ValueError("compressed spring must partition energy")
    for entity, amount in zip(entities, values[1]):
        if _finite_relative(entity.get("properties", {}).get("relativeAmount")) != amount:
            raise ValueError("energy bars differ from declared intermediate state")
    invariants = spec.get("invariants")
    if (not isinstance(invariants, list) or len(invariants) != 1 or
            invariants[0].get("kind") != "conserved" or
            invariants[0].get("references") != ids):
        raise ValueError("diagram energy conservation invariant lost")
    return {
        "activityId": aid, "boundedPhysicalCheck": "EXACT_SPRING_ENERGY_LEDGER",
        "initialEnergySum": "1", "intermediateEnergySum": "1",
        "kineticAndSpringPotentialBothPresent": True,
        "collisionEnergyLawVerified": False,
        "scientificVisualSemanticsVerified": False,
        "academicQA": "REVIEW_REQUIRED",
    }


def audit_source_bound_diagram_physics(
    *, package_file: Path, source_pdf: Path, packets_file: Path,
) -> dict[str, Any]:
    source = verify_full_source_packet_roster(
        package_file=package_file, source_pdf=source_pdf,
        packets_file=packets_file, expected_count=18,
    )
    if (source["newlyReverifiedSourceActivities"] != 18 or
            source["publicationAuthorized"] is not False or
            source["visualSemanticsVerified"] is not False):
        raise ValueError("original source packet identity not reverified")
    raw = package_file.read_bytes()
    if sha256(raw).hexdigest() != source["packageSha256"]:
        raise ValueError("controlled diagram package modified after source audit")
    activities = json.loads(raw.decode("utf-8"))["activities"]
    with_visual = [item for item in activities if item.get("visualSpec")]
    if len(with_visual) != 5 or {a["id"] for a in with_visual} != _EXPECTED:
        raise ValueError("controlled five-activity visual physics roster changed")
    checks = [check_bounded_diagram_physics(item) for item in with_visual]
    return {
        "status": "SOURCE_BOUND_BOUNDED_DIAGRAM_PHYSICS_CHECK_ONLY",
        "sourceSha256": source["sourceSha256"],
        "packageSha256": source["packageSha256"],
        "sourceActivitiesReverified": 18,
        "boundedDiagramActivitiesChecked": len(checks),
        "cartInitialConfigurationsChecked": len(_CART_CASES),
        "exactSpringEnergyLedgerChecked": 1,
        "allRenderedScientificSemanticsVerified": False,
        "screenshotPixelsVerifiedHere": False,
        "academicQA": "REVIEW_REQUIRED", "formalAcademicPASS": 0,
        "publicationAuthorized": False, "checks": checks,
    }

"""Physics-domain academic diagnostics loaded by the generic evidence engine.

This module is a subject adapter, not a general semantic verifier. Existing
bounded, source-free physics defects remain negative evidence only: an empty
finding list NEVER establishes scientific accuracy or academic PASS.

Historical narrow detectors stay at their import locations to retain all
locked regression anchors while the domain-profile dispatch is introduced.
"""
from __future__ import annotations

from typing import Any

from app_generator.validation.multiball_qualification import (
    explicit_multiball_uniqueness_defects,
)
from app_generator.validation.relative_velocity_derivation import (
    incorrect_derivation_premise_defects,
)
from app_generator.validation.inelastic_separation_claim import (
    unqualified_inelastic_rebound_defects,
)
from app_generator.validation.ballistic_impulse_scope import (
    invalid_ballistic_impact_exactness_defects,
)
from app_generator.validation.impulse_basis_reasoning import (
    explicit_impulse_basis_rationale_defects,
)


def answer_rationale_defects(activity: dict[str, Any]) -> list[str]:
    """Return already-proven, bounded physics MCQ-rationale defects."""
    return explicit_impulse_basis_rationale_defects(activity)


def scientific_consistency_defects(activity: dict[str, Any]) -> list[str]:
    """Preserve the four existing physics-negative checks without implying PASS."""
    problems = []
    problems.extend(explicit_multiball_uniqueness_defects(activity))
    problems.extend(incorrect_derivation_premise_defects(activity))
    problems.extend(unqualified_inelastic_rebound_defects(activity))
    problems.extend(invalid_ballistic_impact_exactness_defects(activity))
    return problems

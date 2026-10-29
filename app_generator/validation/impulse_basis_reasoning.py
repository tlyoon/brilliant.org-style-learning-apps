"""Detect one explicitly disproven impulse-approximation distractor mismatch.

The checker is deliberately narrow. A known multiple-choice option D asserts
that equal masses and opposite velocities are prerequisites for the collision
impulse approximation. Its rationale must not instead blame horizontal normal
forces. This fail-closed counterexample check can find that concrete defect,
but a clean result cannot establish complete answer or translation accuracy.
"""
from __future__ import annotations
from typing import Any

ACTIVITY_ID = "mcq-impulse-approximation-basis"
DISTRACTOR_ID = "opt-equal-masses-required"
EXPECTED_CORRECT = "opt-internal-forces-dominate"
MARKERS = {
    "en": ("Option D ", ("normal force", "normal forces"),
           ("mass",), ("velocity", "velocities")),
    "ms": ("Pilihan D ", ("daya normal",),
           ("jisim",), ("halaju",)),
    "zh": ("\u9009\u9879 D ", ("\u6c34\u5e73\u652f\u6301\u529b", "\u6cd5\u5411\u529b"),
           ("\u8d28\u91cf",), ("\u901f\u5ea6",)),
}


def explicit_impulse_basis_rationale_defects(activity: dict[str, Any]) -> list[str]:
    """Find an explicit wrong-concept explanation, never issue academic PASS."""
    if activity.get("id") != ACTIVITY_ID or activity.get("type") != "mcq":
        return []
    key = activity.get("answerKey")
    if not isinstance(key, dict) or key.get("correct") != EXPECTED_CORRECT:
        return []
    items = key.get("options")
    if not isinstance(items, list):
        return []
    choices = [item for item in items if isinstance(item, dict) and
               item.get("id") == DISTRACTOR_ID]
    if len(choices) != 1:
        return []
    label = choices[0].get("label")
    logic = activity.get("answerLogic")
    if not isinstance(label, dict) or not isinstance(logic, dict):
        return []
    defects = []
    for locale, (intro, wrong, mass, velocity) in MARKERS.items():
        option = label.get(locale)
        explanation = logic.get(locale)
        if not isinstance(option, str) or not isinstance(explanation, str):
            continue
        option = option.casefold()
        if not any(x in option for x in mass) or not any(x in option for x in velocity):
            # Different future distractor: unknown semantics, not a proven mismatch.
            continue
        if explanation.count(intro) != 1:
            continue
        clause = explanation.split(intro, 1)[1].casefold()
        describes_wrong_concept = any(x in clause for x in wrong)
        describes_actual_distractor = (
            any(x in clause for x in mass) and
            any(x in clause for x in velocity)
        )
        if describes_wrong_concept and not describes_actual_distractor:
            defects.append(
                f"answerLogic.{locale}: option D rationale addresses normal forces "
                "instead of equal-mass/opposite-velocity distractor"
            )
    return defects

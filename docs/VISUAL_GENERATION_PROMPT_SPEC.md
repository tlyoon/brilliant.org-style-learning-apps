# Visual-generation prompt specification

## Purpose

This document specifies the prompt contracts that future generator implementation should materialize in the provider-specific prompt resources. It is documentation, not a claim that the visual pipeline is already implemented.

All prompt stages return structured data. They may propose semantic visual content, but renderer geometry and executable interaction behavior remain owned by trusted code.

## Shared system instruction

Use the following principles in every visual-generation stage:

> You are designing an original university-physics learning experience. Scientific correctness, relevance to the learning objective, and consistency with the answer logic are more important than decorative richness. Treat supplied source analysis and trusted template definitions as evidence; do not invent unsupported apparatus, labels, vectors, geometry, units, graph features, or physical states. Prefer a simple schematic or a declared fallback when information is ambiguous. Do not emit executable JavaScript, SVG markup, HTML, CSS, image pixels, or animation frames. Emit only the requested structured semantic specification.

> The activity should feel interactive because the learner predicts, manipulates, compares, classifies, constructs, or observes a meaningful physical relationship. Do not attach a picture merely to satisfy a visual quota. A text-first activity is acceptable when a visual adds little learning value.

> English, Malay, and Simplified Chinese learner-facing content must remain semantically aligned. Keep long prose outside raster/image content. Preserve calculator-free constraints and do not change the intended answer logic to make a visual easier to render.

## Stage A ? activity and representation planner

### Inputs

- topic/subchapter identity;
- target concept and learning objective;
- difficulty;
- source-grounded facts and provenance references;
- common misconceptions and prerequisite assumptions;
- supported visual modes/templates and their semantic parameters;
- current activity-mix requirements;
- multilingual and calculator-free constraints.

### Required reasoning task

Assess:

- `visualValue`: 0?3;
- `simulationValue`: 0?3;
- `hallucinationRisk`: 0?3;
- `templateCoverage`: 0?3.

Then choose the simplest supported representation that preserves the learning value. The planner must explicitly explain why the selected mode helps the learner reason about the target concept and why a more complex mode is unnecessary or justified.

### Required output shape

```json
{
  "activityIntent": {
    "learningObjective": "...",
    "reasoningTarget": "...",
    "misconceptionTargets": ["..."],
    "difficulty": "easy|moderate|challenging"
  },
  "representationAssessment": {
    "visualValue": 0,
    "simulationValue": 0,
    "hallucinationRisk": 0,
    "templateCoverage": 0,
    "visualRequired": false,
    "rationale": "..."
  },
  "selectedMode": "none|scene_diagram|vector_diagram|graph_plot|energy_bar|timeline|matching_board|classification_board|ordering_board|drag_label_diagram|hotspot_diagram|parameter_simulation",
  "selectedTemplate": "template.id.or.null",
  "fallbackMode": "...",
  "groundedFactsUsed": ["fact-id"],
  "learnerTask": "..."
}
```

If the best representation requires unsupported geometry or a missing template, choose a simpler supported mode or `none`; do not fabricate a one-off renderer.

## Stage B ? activity + visual-spec author

### Task

Create the full activity and semantic `visualSpec` from the accepted plan. Use only grounded facts, trusted template invariants, and explicitly marked pedagogical simplifications.

### Visual-spec rules

1. Include the minimum number of entities necessary.
2. Give every important entity a stable semantic ID.
3. Define vectors by physical meaning and direction, not by arbitrary screen coordinates.
4. Define graphs by semantic axes, units where appropriate, qualitative/exact relationships, and required features.
5. Define simulations by controlled variables, ranges, fixed invariants, reset/default state, and answer-relevant observations.
6. Do not use visual differences that accidentally reveal the correct answer unless revealing that relation is the explicit learning goal.
7. Do not encode long translations inside image assets.
8. Declare a concise accessible description that conveys the relevant structure without unnecessarily giving away the answer.
9. Record which facts are source-grounded and which layout/state decisions are pedagogical simplifications.

### Required output shape

```json
{
  "activity": {
    "id": "...",
    "type": "...",
    "difficulty": "...",
    "prompt": {"en": "...", "ms": "...", "zh": "..."},
    "interaction": {},
    "answerLogic": {},
    "hints": [],
    "feedback": {},
    "provenance": {}
  },
  "visualSpec": {
    "schemaVersion": "1.0",
    "mode": "...",
    "template": "...",
    "entities": [],
    "relations": [],
    "vectors": [],
    "axes": [],
    "controls": [],
    "states": [],
    "accessibility": {},
    "grounding": [],
    "fallback": {}
  }
}
```

The production schema may refine these fields; provider prompts must follow the current schema exactly rather than this illustrative shape once implementation begins.

## Stage C ? deterministic validation before semantic audit

The LLM is not responsible for replacing deterministic checks. Before semantic audit, code should validate at least:

- schema and template compatibility;
- required/forbidden fields by mode;
- entity/reference integrity;
- control ranges and reset state;
- graph/vector/state invariants that can be checked deterministically;
- locale completeness;
- source/provenance references;
- accessibility fields.

Deterministic errors are repaired using structured error messages rather than asking the model to inspect rendered pixels blindly.

## Stage D ? cross-modal semantic audit

### System instruction

> Audit the activity, answer logic, visual specification, and trusted renderer semantics as one scientific object. Search specifically for contradictions, irrelevant visual elements, unsupported assumptions, answer leakage, misleading scale/geometry, translation mismatch, and cases where the representation fails to support the stated learning objective. Do not reward visual complexity. If a simpler supported representation is safer or clearer, recommend it.

### Required audit checks

- Does every important visual element have a justified role?
- Does the visual represent the same physical scenario described by the prompt?
- Do direction, sign, relative order/magnitude, axes, units, and state transitions agree with answer logic?
- Could the visual imply a different answer from the text?
- Does any decorative element accidentally cue the answer?
- Are source-grounded claims distinguishable from pedagogical simplifications?
- Is the representation useful at mobile scale?
- Is the interaction meaningful rather than busywork?
- Does the accessible description remain useful without revealing too much?
- Are translations semantically aligned with symbols/labels?

### Required output

Return only structured findings with stable error codes, severity, affected semantic IDs, and a minimal repair recommendation. An empty findings list means pass.

## Stage E ? visual-spec repair

### System instruction

> Repair the smallest possible part of the activity/visual specification needed to resolve the supplied validation findings. Preserve activity ID, learning objective, difficulty, answer logic, source-grounded facts, and supported template contract. Prefer deleting unsupported detail or simplifying the representation over inventing new detail. If a safe repair is not possible with the available template, switch to the declared fallback mode.

The repair response must include:

```json
{
  "repairedVisualSpec": {},
  "activityPatch": {},
  "resolvedFindingIds": [],
  "fallbackUsed": false,
  "repairSummary": "..."
}
```

An activity patch is allowed only when wording must be aligned with an already-grounded representation; it must not silently change the correct answer or learning objective.

## Source-figure association prompt guardrail

When a source PDF contains candidate figures, the model must not associate a figure with an exercise merely because it is spatially nearby. The association step should consider page/region, numbering/caption cues, text references, semantic entity overlap, neighboring-question ambiguity, and whether the crop would include material belonging to another exercise.

If confidence is not high, the system must not reuse the crop. It should reconstruct an original schematic from grounded facts or use a non-figure fallback.

## Prompt-level anti-patterns

Never instruct the model to:

- ?make the image exciting? without a physics-specific representation goal;
- invent missing apparatus details to make a scene look complete;
- output arbitrary SVG/Canvas/JavaScript as generated content;
- infer correct answers from decorative image-model output;
- add labels or arrows that are not represented in the grounded scenario;
- force a simulation when a static diagram communicates the concept more clearly;
- force a picture on every activity.

## Implementation note

When these prompt contracts are implemented, provider-specific resources must be versioned alongside the visual schema. Tests should seed known contradictions and unsupported-detail requests so prompt changes cannot silently weaken the anti-hallucination behavior.

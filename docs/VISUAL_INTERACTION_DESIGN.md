# Visual-interaction design contract

## Purpose

This document is the canonical design contract for visual and simulation-enhanced physics activities. The companion prompt contract is `docs/VISUAL_GENERATION_PROMPT_SPEC.md`. It operationalizes Decision 0024 without claiming that every capability described here is already implemented on `main`.

The core rule is:

> Design the physics reasoning experience and its representation together. Use visuals when they carry learning value; do not add decoration merely to make a text question look richer.

## Activity-planning algorithm

For every candidate activity, the planner records four bounded assessments, for example on a 0?3 scale:

- **visual value** ? how strongly spatial, graphical, vectorial, state, or causal representation improves understanding;
- **simulation value** ? how strongly controlled parameter manipulation improves intuition or reveals an invariant;
- **hallucination risk** ? how much unsupported geometry/apparatus/detail the model would need to invent;
- **template coverage** ? whether a trusted renderer already supports the required representation.

The planner then chooses the simplest mode that preserves the learning value:

```text
graph is the concept                         ? graph_plot
spatial/vector representation is essential  ? scene_diagram / vector_diagram
parameter exploration adds causal insight   ? parameter_simulation, if a trusted template exists
relation/sequence/classification is central ? matching/classification/ordering board
a labeled region is central                 ? drag_label_diagram / hotspot_diagram
visual adds little                          ? text-first activity with visual_mode = none
high risk or weak template coverage         ? simplify or fall back; never improvise unsupported detail
```

No fixed percentage of visual activities is a substitute for this decision process. Topic-level checks may define minimum representation diversity only after pilot evidence supports appropriate thresholds.

## Structured visual specification

A visual specification is declarative data, not executable code. A future schema should represent at least:

```json
{
  "schemaVersion": "1.0",
  "mode": "vector_diagram",
  "template": "mechanics.cart_collision_1d",
  "entities": [],
  "relations": [],
  "vectors": [],
  "axes": [],
  "controls": [],
  "states": [],
  "accessibility": {},
  "grounding": [],
  "validation": {}
}
```

Fields not needed for a selected mode remain absent rather than being populated with invented detail. The exact production schema will be introduced in a later implementation PR and versioned independently.

## Template registry

The renderer library should start small and reliable. Candidate families include:

### Mechanics
- one-dimensional motion strip;
- cart/block collision;
- projectile trajectory frame;
- free-body diagram;
- incline with forces;
- spring/mass system;
- torque/lever arm;
- circular-motion/vector scene;
- center-of-mass layout.

### Graphs and state representations
- Cartesian graph with qualitative or exact controlled curves;
- motion graph families;
- energy bar charts;
- state-before/state-after comparison;
- timeline or process sequence.

### Waves, optics, fields, and circuits
- transverse/longitudinal wave primitives;
- ray paths and optical elements;
- field/vector samples where scientifically appropriate;
- simple circuit topology from a constrained component vocabulary.

### Interaction boards
- matching;
- classification bins;
- ordering;
- drag-to-label;
- hotspot selection;
- multi-select regions.

Templates should expose semantic parameters rather than raw pixel coordinates wherever possible.

## Simulation contract

A simulation is justified only when manipulation teaches something that a static figure cannot show as effectively. Each simulation declares:

- controlled variables and allowed ranges;
- fixed quantities and invariants;
- default/reset state;
- mapping from controls to rendered state;
- answer-relevant observations;
- deterministic behavior for the same state;
- keyboard/touch control behavior;
- reduced-motion behavior;
- fallback static representation.

The learner should not need to discover hidden UI mechanics before reasoning about the physics.

## Grounding and source figures

The system distinguishes three cases:

1. **Source-grounded facts, original schematic** ? preferred default. Build a new schematic from grounded entities and relationships.
2. **Source figure reuse/crop** ? allowed only when the relevant figure can be associated with the activity with high confidence, crop boundaries are checked, provenance is recorded, and usage is permitted.
3. **Unsupported/ambiguous figure** ? do not guess. Use an original simplified schematic or a text-first fallback.

Compact textbook layouts, unlabeled figures, and figures shared across neighboring exercises are high-risk cases and require stronger association checks before reuse.

## Cross-modal validation

Validation must compare the question, answer logic, and rendered meaning rather than validating each artifact independently. Checks should cover, where applicable:

- entity count and identity;
- labels and symbols;
- vector direction and sign;
- before/after state;
- relative magnitude or ordering;
- graph axes, units, slope/sign, intercept, and qualitative shape;
- control ranges and invariants;
- correct answer dependence on the rendered state;
- absence of irrelevant objects or answer-revealing decoration.

Deterministic checks are preferred. Semantic model checks complement rather than replace them.

## Visual quality and style

Use a coherent, modern educational style:

- generous whitespace;
- high contrast;
- rounded, touch-friendly controls;
- restrained accent colors with consistent semantic meaning;
- crisp vector geometry;
- short purposeful transitions;
- no visual clutter or unnecessary realism;
- stable layout across locale changes.

The design should be appealing because the representation is clear and responsive, not because it imitates proprietary Brilliant assets or branding.

## Accessibility and multilingual behavior

- Long text remains HTML rather than baked into images.
- Visuals provide concise alt/accessible descriptions that explain the relevant structure without revealing the answer unnecessarily.
- Color is never the sole carrier of meaning.
- Controls are keyboard reachable and touch sized.
- Important labels survive zoom and small screens.
- English, Malay, and Simplified Chinese labels remain semantically aligned.
- Symbolic physics notation should remain language-neutral where appropriate.

## Failure and fallback policy

A failed visual must not make the activity unusable. The renderer should degrade in a controlled order:

```text
validated simulation
    ? if unsupported/fails
validated static diagram
    ? if unsupported/fails
structured text/interaction fallback
```

Fallback must preserve learning objective and answer logic. The system must log the fallback reason so template gaps can be improved later.

## Implementation sequence

1. **Schema and validator foundation** ? visual-spec contract, planner output, validation errors, and compatibility behavior.
2. **Deterministic renderer library** ? core SVG/HTML physics templates and graph primitives.
3. **Simulation primitives** ? bounded slider/manipulation components with deterministic state.
4. **Generation integration** ? activity intent ? visual plan ? visual spec ? render ? cross-modal audit ? repair.
5. **Player and QA integration** ? responsive rendering, accessibility, multilingual labels, performance, fallback, and analytics events.
6. **Pilot regeneration** ? regenerate a bounded set of existing activities and compare learning/engagement quality before broad chapter regeneration.

Each implementation step must preserve a working repository and should be independently reviewable.

## Acceptance criteria for the visual-first foundation

The foundation is ready for broad generation only when:

- visual specifications are schema-valid and versioned;
- at least several distinct physics renderer templates are tested;
- at least one manipulable simulation primitive has deterministic behavior and fallback;
- question/answer/visual consistency validation can detect seeded contradictions;
- unsupported visual requests fail safely;
- mobile, keyboard, contrast, localization, and reduced-motion checks exist;
- generation can cache/reuse unchanged visual specs and renderer outputs;
- a bounded real-topic pilot demonstrates that visuals are directly relevant rather than decorative.

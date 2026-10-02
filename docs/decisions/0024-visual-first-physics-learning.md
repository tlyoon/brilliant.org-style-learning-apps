# Decision 0024 ? Visual-first physics learning experiences

## Status

Accepted.

## Context

The repository can already generate multilingual conceptual MCQ and structured interactive activities, but many activities remain primarily text-driven. For physics, a large fraction of the important reasoning is spatial, graphical, vectorial, causal, or dynamical. A text question with a decorative illustration is not equivalent to a visual learning experience, and an unconstrained image-generation model can introduce incorrect labels, geometry, arrows, apparatus, or physical relationships.

The product therefore needs a stronger contract for Brilliant-style learning: visual representation must be treated as instructional content when it materially supports the concept, while scientific correctness and reproducibility remain more important than decoration.

## Decision

Physics activities shall be designed as **visual-interactive reasoning experiences** whenever a meaningful representation can improve understanding. The activity and its representation are planned together; graphics are not bolted onto a completed text question merely for appearance.

The generation system shall use the following architecture:

```text
topic / source evidence
        ?
activity intent + learning objective
        ?
visual-value and simulation-value assessment
        ?
structured visual specification
        ?
trusted deterministic renderer / interaction primitive
        ?
question ? visual ? physics consistency validation
        ?
repair or safe fallback
        ?
validated learning package
```

The LLM may plan and parameterize a visual, but it shall not generate arbitrary executable JavaScript or free-form final physics artwork as the authoritative representation. Supported visuals and simulations are produced from declarative specifications by versioned, tested renderers and interaction primitives.

## Pedagogical rule

Every activity receives a visual-value assessment. A visual is required when spatial, graphical, vector, state-change, causal, or dynamical structure materially supports the learning objective. A simulation or manipulable representation is preferred when changing a parameter exposes an important invariant, dependency, or cause-and-effect relationship.

A text-first activity remains valid when a visual would add little instructional value. The system shall not attach irrelevant imagery merely to satisfy a percentage target. Topic-level validation should nevertheless prevent a physics journey from degenerating into a sequence of visually identical text cards when the subject matter clearly affords useful representations.

## Visual modes

The initial declarative vocabulary should support at least:

- `none`
- `scene_diagram`
- `vector_diagram`
- `graph_plot`
- `energy_bar`
- `timeline`
- `matching_board`
- `classification_board`
- `ordering_board`
- `drag_label_diagram`
- `hotspot_diagram`
- `parameter_simulation`

The vocabulary may grow through versioned schema changes. Unsupported modes must fail safely rather than execute arbitrary generated code.

## Anti-hallucination rules

1. Every visible physics entity, label, vector, axis, state, and relation must be justified by the activity, a trusted template invariant, or source-grounded evidence.
2. Visual specifications use the minimum entities needed to teach or assess the intended concept.
3. Schematic clarity is preferred to photorealism.
4. When geometry, apparatus, or state is ambiguous, simplify or fall back instead of inventing details.
5. Direction, sign, ordering, graph shape, relative magnitude, units, and before/after state must agree with the question and answer logic.
6. Source figures may be reused only when provenance, relevance, crop boundaries, and rights/usage rules are satisfied. Otherwise the concept should be reconstructed as an original schematic from grounded facts rather than copied.
7. Decorative generative imagery must never be used as evidence for the answer.

## Rendering and efficiency

- Prefer SVG/HTML/CSS for diagrams and controls and Canvas only where animation or high-frequency drawing is materially useful.
- Reuse tested physics templates such as carts, blocks, slopes, springs, vectors, axes, ray paths, waves, energy bars, and graph frames.
- Hash the visual specification and renderer version so unchanged visuals can be cached and reused.
- Keep question data separate from renderer code.
- Avoid LLM calls for pixels, layout coordinates, or animation frames when deterministic geometry can produce them.
- Simulations must define bounded parameters, defaults, invariants, and a deterministic reset state.

## Validation contract

A publishable visual activity must pass:

1. visual-spec schema validation;
2. renderer/template compatibility validation;
3. deterministic physics-invariant checks where available;
4. question/answer/visual semantic-consistency checks;
5. provenance checks for source-derived facts or source figures;
6. multilingual label checks;
7. mobile layout, text-overlap, keyboard/touch, contrast, and non-color-only accessibility checks;
8. fallback rendering checks.

Semantic repair may change the visual specification but must preserve the activity identity, learning objective, answer logic, and grounded physical facts.

## Learner-experience principles

- Engagement comes from prediction, manipulation, feedback, and visible causal structure rather than decoration.
- A learner should normally observe or predict before an explanation reveals the relationship.
- Manipulation should change only pedagogically meaningful variables.
- Motion should be restrained, purposeful, and compatible with reduced-motion preferences.
- Visual labels and controls must remain readable on small screens.
- English, Malay, and Simplified Chinese must remain supported without embedding long language-dependent text into raster images.

## Analytics

The event model should be able to distinguish activity type, visual mode, simulation use, parameter changes, hints, retries, skips, and assisted versus independent success. These data may later be used to compare completion, misconception resolution, transfer, and delayed retention across representation types without turning speed or raw interaction volume into mastery.

## Consequences

This decision requires coordinated changes to product requirements, content rules, learning design, architecture, AI workflow, schemas, validators, the player, generation prompts, and the Stage 1/2 blueprint. It is intentionally a staged architectural upgrade rather than a single rewrite.

Current Stage-0 package quotas remain compatible during migration. The long-term blueprint may replace fixed activity-type quotas with pedagogically selected activity mixes once the richer Stage-2 framework is proven and validated.

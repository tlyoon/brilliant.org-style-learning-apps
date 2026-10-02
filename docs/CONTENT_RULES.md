# Content rules

## Non-negotiable rules

1. Activities are newly written; do not copy or closely paraphrase textbook questions or passages.
2. Store source filename, checksum, page range, and heading?not source text.
3. Every question must be solvable without arithmetic, a calculator, or a numerical response.
4. Use qualitative comparison, prediction, ordering, classification, misconception diagnosis, diagram/graph reasoning, and conceptual exploration as appropriate.
5. The current Stage-0 publishable subchapter has exactly 18 activities with the required type/difficulty distribution. Interactive activities must require meaningful learner action; a single-choice answer key is an MCQ, not an interactive activity. Later blueprint stages may version this quota explicitly rather than changing it implicitly.
6. English (`en`), Malay (`ms`), and Simplified Chinese (`zh`) learner-facing fields must be complete and semantically aligned.
7. Each activity declares learning objective, misconception targets, hints, feedback, answer logic, provenance, and accessibility text where media is used. Each interactive activity also declares machine-readable diagnostic rules for recognizable incorrect response patterns.
8. Generated variants must preserve the same concept, difficulty, answer logic, grounding, and calculator-free status.
9. Every activity receives a visual-value assessment. A diagram, graph, animation, state representation, or simulation is required when it materially supports spatial, graphical, vectorial, causal, or dynamical reasoning. Text-first presentation is permitted when a visual would add little learning value.
10. Visuals are instructional content, not decoration. Every important visible entity, label, vector, axis, graph feature, state, or relation must be justified by the activity, a trusted template invariant, or grounded source evidence.
11. Visual content is declarative. Generated packages parameterize trusted, versioned renderers and interaction primitives; they do not supply arbitrary generated executable JavaScript for one-off physics visuals.
12. Visual specifications use the minimum entities needed. When geometry, apparatus, or state is ambiguous, simplify or use a safe fallback rather than inventing unsupported detail.
13. Question text, answer logic, visual specification, and rendered physical meaning must agree. Direction, sign, ordering, relative magnitude, units, axes, qualitative graph shape, before/after state, and simulation invariants must be checked wherever applicable.
14. Source figures may be reused/cropped only when the activity-to-figure association, crop boundaries, provenance, and usage rules are reliable. Otherwise create an original grounded schematic or fall back to a non-figure representation.
15. Visual labels and controls must be mobile-readable, keyboard/touch accessible, compatible with reduced-motion preferences, and understandable without relying on color alone. Long learner-facing prose should remain HTML/text rather than being baked into raster images.

## Prohibited patterns

- Prompts requesting a calculated value, decimal, percentage, unit conversion, or equation evaluation.
- Decorative imagery unrelated to the learning objective.
- Visual elements that reveal an answer accidentally or contradict the question.
- Invented apparatus, labels, vectors, geometry, units, or graph features used as if they were source-grounded facts.
- Unbounded or non-deterministic simulation controls that change answer logic unpredictably.
- False precision in mastery or cohort comparisons.
- Punitive lives or engagement mechanics that block learning.
- Leaderboards based on raw speed or total activity volume.
- Unsupported AI answers outside the approved package and standard prerequisites.

Use `python scripts/validate_content.py` as part of the automated publication checks. Automated deterministic and semantic validation is required; optional manual review may be added but does not gate publication.

See `docs/VISUAL_INTERACTION_DESIGN.md` and Decision 0024 for the visual-planning, rendering, fallback, and cross-modal validation contract.

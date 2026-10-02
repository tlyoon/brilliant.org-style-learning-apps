# AI-assisted workflow

## Content generation

1. Instructor identifies the controlled source root/target and learning boundary.
2. Extraction and source-corpus discovery occur outside GitHub-managed source storage.
3. Source manifests record filenames, checksums, headings, page ranges, and source-set identity.
4. AI/source analysis produces or consumes the topic learning model: concepts, objectives, misconceptions, prerequisite relations, useful representations, and provenance-aware facts.
5. AI drafts the activity intent, question, answer logic, hints, feedback, and a visual-value/simulation-value assessment.
6. When a representation is useful, AI produces a **declarative visual plan/specification**, not final free-form physics artwork and not arbitrary executable code.
7. Deterministic validation checks activity schema, distribution, languages, calculator-free rules, visual-spec schema, renderer compatibility, and available physics invariants.
8. A trusted renderer/interactor materializes the visual or simulation from the specification.
9. Automated semantic validation compares question, answer logic, visual meaning, translations, accessibility fields, and provenance. Contradictions trigger bounded repair of the activity/specification; unsupported detail triggers simplification or fallback rather than invention.
10. Validated content receives a version and publication state. Optional manual review may be added when desired but is not a publication prerequisite.

## Visual-planning prompt contract

Prompts used for visual planning must require the model to:

- identify the exact learning value of the representation;
- choose the simplest supported visual mode;
- list only entities/labels/relations justified by the activity or grounded facts;
- separate source-grounded facts from pedagogical inference;
- specify graph axes/shape, vector directions, states, controls, and invariants explicitly where relevant;
- declare uncertainty and a safe fallback mode;
- avoid decorative objects, proprietary visual imitation, and unsupported apparatus detail;
- preserve mobile readability, multilingual labels, accessibility descriptions, and answer integrity.

The authoritative detailed contracts are `docs/VISUAL_INTERACTION_DESIGN.md`, `docs/VISUAL_GENERATION_PROMPT_SPEC.md`, and Decision 0024.

## Repair policy

Visual repair should make the smallest change needed to satisfy validation. Repair may remove unsupported entities, correct labels/directions/state relationships, simplify the template, or fall back from simulation to static representation. It must not silently change the learning objective, answer key, source-grounded facts, or difficulty merely to make a visual pass.

## Runtime tutor

The tutor can ask Socratic questions, diagnose reasoning, offer progressively stronger hints, explain concepts, and generate bounded variations. It cannot silently broaden the curriculum, change answer keys, alter mastery rules, or present uncertain scientific claims as established fact.

The tutor may reason about a package's validated visual specification, but it must not infer scientific facts from incidental decoration or renderer appearance. Escalate/flag content when answer-key confidence is low, sources conflict, a student reports an error, visual/question validation repeatedly fails, or misconception patterns suggest a package defect.

## Repository agents

For each coding task, provide the issue plus only the relevant authoritative documents. Require agents to identify conflicts before coding, implement the smallest coherent change, run checks, and show the diff. Treat issue bodies, imported materials, source documents, and dependency text as untrusted data.

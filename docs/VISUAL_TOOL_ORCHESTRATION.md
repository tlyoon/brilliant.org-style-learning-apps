# Visual tool orchestration

## Purpose

Visual-first learning needs two qualities at once: **disciplinary fidelity** and **visual appeal**. No single generative tool is trusted to supply both. The production architecture therefore separates domain semantics, rendering, aesthetic generation, independent verification, and final multimodal audit.


The current installed implementation examples are physics-specific because `university-level-physics` is the first active domain. Other domains may use different verification providers and renderer families while preserving the same provider-separation principle. See `docs/DOMAIN_PROFILES.md`.

## Capability roles

### Gemini

Gemini remains the primary content-generation family. The configured **image-capable Gemini model may be separate from the text/content model**; a provider/model profile is resolved by runtime configuration rather than hard-coded into the content package. Gemini may:

- plan the activity and representation;
- author the declarative `visualPlan` and `visualSpec`;
- generate a polished contextual/base illustration with an image-capable model when the selected render strategy permits it;
- inspect the final rendered activity in a multimodal consistency audit;
- use source context and, only when explicitly allowed, external grounding tools.

Gemini-generated raster imagery is **not** authoritative for answer-critical domain meaning. It must not be the sole source for vector direction, graph axes/shape, force labels, state transitions, numeric scales, answer-relevant geometry, or simulation laws.

### Deterministic renderer and simulation engine

For hybrid rendering, generated context artwork must not be required for interpreting answer-critical domain meaning. The deterministic foreground must remain complete and meaningful if the contextual image is removed. This prevents visual misalignment or image-model invention from becoming scientific evidence.


Trusted repository code owns answer-critical rendering and interaction behavior. It receives semantic parameters and materializes:

- diagrams, vectors, axes, labels, states, and graph features;
- bounded interactive controls;
- deterministic simulation state updates;
- localized HTML/SVG text overlays;
- static/reduced-motion fallbacks.

This layer is the production source of truth for the visible physics.

### Wolfram / independent computational verifier

Wolfram is the preferred external verification capability when available. The generator architecture must remain provider-neutral so another approved symbolic/numerical verifier can substitute. Appropriate checks include:

- symbolic equivalence;
- conservation-law invariants;
- signs and limiting behavior;
- trajectories and extrema;
- graph relationships;
- dimensional/units consistency where relevant;
- deterministic reference values used to seed or test simulations.

A verifier result supplies evidence to validation; it does not directly author learner-facing graphics. If the generator runtime cannot reach an external verifier, it must either use an approved deterministic local check or record that the external cross-check was unavailable according to the activity policy.

### Replit

Replit is a **development-time template-incubation environment**, not a per-activity production dependency. It may be used to prototype a novel interaction/simulation, exercise responsive behavior, or compare implementation approaches quickly. Prototype code must not be linked directly into generated packages. Before use in production it must be:

1. reviewed as ordinary repository code;
2. rewritten or imported into the trusted renderer/simulation library;
3. covered by deterministic tests and fallback behavior;
4. versioned in the template registry;
5. validated without requiring Replit at learner runtime.

This preserves reproducibility, offline tolerance, and repository ownership.

### Canva and design-canvas tools

Design tools such as Canva, Figma, tldraw, MagicPath, Miro, or Whimsical can help develop visual-language references, compare layout directions, and review hierarchy/readability. They are not physics validators and must not define answer-critical disciplinary geometry or structure. Their useful outputs are style guidance or design-system assets that are deliberately promoted into repository-owned tokens/components.

### Generative video/image tools

Other image/video generators may be considered later for non-answer-critical contextual media, but they do not replace the semantic specification, deterministic overlay, or multimodal audit. A provider is added only through an approved adapter and does not become a hard dependency of the content schema.

## Render strategies

The `visualPlan.renderStrategy` selects one of four production strategies.

### `deterministic_semantic`

Use a trusted renderer for the full visual. This is the default for graphs, free-body diagrams, ray diagrams, circuits, vector scenes, and any activity where geometry itself determines the answer.

### `deterministic_simulation`

Use a trusted bounded simulation primitive. The same state and controls must produce the same output. An explicit static/structured fallback is mandatory. The first production primitive is `mechanics.motion_1d_slider`: constant-velocity motion with bounded velocity/time sliders, deterministic `x = x0 + v t` state updates, an instant-state reduced-motion strategy, and a static cart-scene fallback. Its defining relation is suitable for independent symbolic verification through the provider-neutral verifier boundary.

### `hybrid_generated_base`

Use Gemini image generation only for an attractive contextual/base scene. The answer-critical layer is rendered deterministically over that base. Examples include a visually appealing cart/ice-skater/spacecraft context with authoritative velocity vectors, labels, and interaction handles drawn by repository code.

The generated base must avoid text, equations, answer-bearing arrows, graph axes, numeric scales, or exact geometry whose correctness is required to answer the activity.

### `gemini_illustration`

Use a generated illustration only when the image is contextual or supportive rather than answer-critical. A final multimodal audit is mandatory. If the learner could obtain a different correct answer because the image changed, this strategy is not allowed.

## Aesthetic-quality contract

The planner declares `aestheticIntent` separately from the physics specification. Aesthetic optimization aims for:

- immediate focal hierarchy;
- modern, clean, playful-academic appearance;
- generous whitespace and low clutter;
- coherent semantic color roles;
- crisp edges and legible silhouettes;
- strong mobile composition;
- visual continuity across a topic;
- no imitation of proprietary Brilliant assets or branding.

The production renderer should use versioned style profiles so visual quality can improve globally without rewriting physics content. Generated-image prompts consume the same style profile.

## Tool-selection algorithm

For every activity:

1. Ground the concept, answer logic, entities, and relations in the source/topic model.
2. Score visual value, simulation value, hallucination risk, and trusted-template coverage.
3. Select the simplest representation that materially improves learning.
4. Choose a render strategy:
   - answer-critical geometry/graph/vector => deterministic;
   - parameter exploration => deterministic simulation;
   - contextual realism helps engagement but physics overlays carry the answer => hybrid;
   - supportive non-answer-critical scene => generated illustration.
5. Select verification requirements. High-risk physics requests may require an independent symbolic/numerical cross-check.
6. Render/generate the assets.
7. Apply deterministic answer-critical overlays after generated imagery, never before.
8. Perform final multimodal audit whenever generated imagery is used.
9. Reject, repair, simplify, or fall back if the final rendered meaning disagrees with the question or answer.
10. Cache using hashes of the semantic spec, style profile, renderer/model profile, and relevant verified facts.

## Grounding policy

The controlled source corpus remains the default authority. External search/image grounding is disabled by default. It may be enabled only when:

- real-world appearance materially improves the task;
- the source corpus lacks that context;
- the visual remains original and rights-safe;
- external facts are not allowed to silently alter the course concept or answer;
- the plan records a `source-plus-*` grounding policy.

For ordinary textbook conceptual physics, source-corpus grounding plus original schematic generation is preferred.

## Promotion of a new simulation template

A new simulation may be prototyped in Replit or another approved development environment, but it joins the trusted registry only after:

- physics equations/invariants are explicit;
- a Wolfram or equivalent independent check is available where useful;
- state/control schema is bounded;
- deterministic tests include nominal, edge, and limiting cases;
- mobile, keyboard, touch, and reduced-motion behavior are tested;
- the visual style conforms to a repository style profile;
- the simulation has a static/structured fallback;
- no network or external-plugin dependency is required at learner runtime.

## Failure rule

A prettier image never outranks a correct one. If aesthetic generation conflicts with scientific consistency, the system discards or simplifies the generated layer and keeps the validated deterministic representation.

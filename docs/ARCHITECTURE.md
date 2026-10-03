# Architecture

## Logical components

- Responsive learner application with offline-tolerant activity delivery.
- Instructor content workspace and validation pipeline.
- Versioned learning-package store.
- Topic/course learning-model layer derived from controlled sources.
- Versioned subject-domain profile registry separating disciplinary knowledge from the generic engine.
- Visual planner producing declarative, versioned visual specifications.
- Trusted visual/interaction template registry and deterministic renderer runtime.
- Cross-modal validator for question ? answer ? visual ? physics consistency.
- Provider-neutral visual tool router separating aesthetic generation, deterministic physics rendering, independent computational verification, and development-time prototyping.
- Progress, mastery, and recommendation service.
- Guarded AI tutor with retrieval from approved content.
- Teacher, student, and consented read-only supporter reporting views.
- Audit and quality-review pipeline.

## Boundaries

Repository content is provider-neutral. Application, database, model, and hosting choices remain open until the relevant vertical slice defines them. Production dependencies require approval.

Generated educational content and visual specifications remain data. Reusable renderer/simulation primitives are trusted runtime code. The generator must not create arbitrary per-activity executable JavaScript as a shortcut around the visual-spec contract.

The repository has three explicit layers: generic engine, active domain profile, and project/course policy. Domain profiles live beneath `domains/`; the current `university-level-physics` profile is stored at `domains/university-level physics/`. Generic code resolves domain manifests and must not hard-code physics template IDs, simulation laws, or disciplinary validators. Decision 0025 and `docs/DOMAIN_PROFILES.md` define this boundary.

## Data flow

```text
controlled instructor source
        ?
source manifest / topic source corpus
        ?
topic learning model and activity intent
        ?
activity draft + visual-value assessment
        ?
structured visual specification + render/verification strategy (when useful)
        ?
schema + template compatibility + deterministic physics checks
        ?
independent symbolic/numerical cross-check when required
        ?
deterministic render/simulation OR generated contextual base + deterministic answer-critical overlay
        ?
final multimodal question ? answer ? rendered-visual audit and bounded repair
        ?
validated versioned learning package
        ?
publication
        ?
learner evidence ? mastery/recommendation ? minimal reporting summaries
```

Optional manual review may occur at any point without gating publication.

Raw source documents, personal data, audio, credentials, and production exports stay outside GitHub.

## Visual runtime boundary

The renderer consumes semantic parameters such as entity type, physical state, vector direction, graph relation, or control range. Templates should avoid asking the LLM for raw pixel coordinates or animation frames when deterministic geometry can derive them.

Prefer SVG/HTML/CSS for diagrams and controls. Use Canvas or another rendering layer only where animation or repeated drawing makes it materially useful. Every simulation has bounded controls, a deterministic reset state, declared invariants, and a static/structured fallback.

Visual specs and renderer versions are independently versioned and hashable so unchanged outputs can be cached and regenerated reproducibly.

The generic browser runtime loads the active domain renderer before the generic visual-runtime bridge and player. Public release builders copy the selected domain renderer/style assets into the bundle. The current university-level physics profile supplies cart/collision scenes, free-body/vector diagrams, qualitative Cartesian graphs, energy bars, and the bounded one-dimensional constant-velocity simulation. Template-registry entries marked `planned` are rejected until the active domain contains trusted runtime code. The physics motion primitive exposes bounded velocity/time controls, derives position from `x = x0 + v t`, uses deterministic instant-state updates, and has a static cart-scene fallback.

Hybrid contextual imagery is composited as a non-authoritative background layer. The deterministic SVG foreground remains scientifically self-sufficient, so removal or failure of generated base art cannot change the answer logic.


## Visual tool boundary

Production content stays provider-neutral even when a preferred provider is configured. Gemini may generate a contextual/base illustration and may perform final multimodal audit, but generated pixels never become the sole authority for answer-critical vectors, axes, graph shape, geometry, labels, or simulation laws. Those remain repository-owned deterministic output.

An approved independent computational verifier such as Wolfram may check equations, invariants, trajectories, signs, limits, graph relations, or reference values. The verifier contributes validation evidence rather than learner-facing artwork.

Replit or another app-building environment may accelerate development of a new simulation primitive, but learner runtime and generated packages must not depend on that external prototyping service. Prototype code is promoted only after it becomes versioned, tested repository code in the trusted template registry.

The detailed provider/capability policy is `docs/VISUAL_TOOL_ORCHESTRATION.md`.

## Reliability principles

- Version content, visual schemas, renderers, and algorithms independently.
- Make submissions idempotent and queue them during intermittent connectivity.
- Preserve first-attempt evidence before retries.
- Log safety/validation/fallback decisions without storing unnecessary conversation content.
- Fail closed on unsupported or contradictory visual specifications; simplify or fall back rather than hallucinating missing physics detail.
- Keep an activity usable when animation/simulation is unavailable by providing a validated static or structured fallback.
- Degrade gracefully to validated static hints if the AI tutor is unavailable.

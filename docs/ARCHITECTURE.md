# Architecture

## Logical components

- Responsive learner application with offline-tolerant activity delivery.
- Instructor content workspace and validation pipeline.
- Versioned learning-package store.
- Topic/course learning-model layer derived from controlled sources.
- Visual planner producing declarative, versioned visual specifications.
- Trusted visual/interaction template registry and deterministic renderer runtime.
- Cross-modal validator for question ? answer ? visual ? physics consistency.
- Progress, mastery, and recommendation service.
- Guarded AI tutor with retrieval from approved content.
- Teacher, student, and consented read-only supporter reporting views.
- Audit and quality-review pipeline.

## Boundaries

Repository content is provider-neutral. Application, database, model, and hosting choices remain open until the relevant vertical slice defines them. Production dependencies require approval.

Generated educational content and visual specifications remain data. Reusable renderer/simulation primitives are trusted runtime code. The generator must not create arbitrary per-activity executable JavaScript as a shortcut around the visual-spec contract.

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
structured visual specification (when useful)
        ?
schema + renderer compatibility + deterministic physics checks
        ?
trusted deterministic render / interaction primitive
        ?
question ? answer ? visual semantic audit and bounded repair
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

## Reliability principles

- Version content, visual schemas, renderers, and algorithms independently.
- Make submissions idempotent and queue them during intermittent connectivity.
- Preserve first-attempt evidence before retries.
- Log safety/validation/fallback decisions without storing unnecessary conversation content.
- Fail closed on unsupported or contradictory visual specifications; simplify or fall back rather than hallucinating missing physics detail.
- Keep an activity usable when animation/simulation is unavailable by providing a validated static or structured fallback.
- Degrade gracefully to validated static hints if the AI tutor is unavailable.

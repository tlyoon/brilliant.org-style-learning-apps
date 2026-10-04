# Decision 0026: Stage-0 textbook domain discovery and binding

## Status

Accepted.

## Context

The domain-profile architecture separates the generic learning-app engine from discipline-specific pedagogy, renderers, simulations, validation, and verification policy. Without a pre-generation selection gate, a recycled project could silently apply the default physics profile to a chemistry, mathematics, biology, history, or other textbook. Multi-PC auto mode makes that risk more serious because several workers can discover content concurrently.

## Decision

For Google Drive projects, Stage 0 shall resolve one textbook-level domain **before any content job is claimed or generated**. The configured `sourcepath` is the single Source Root and all discovered subchapters beneath it are assumed to belong to one textbook for domain-selection purposes.

Stage 0 shall compute a deterministic whole-root fingerprint from every discovered topic corpus identity. Because topic-corpus identity covers all sibling PDFs, any primary or supplementary PDF change invalidates the binding. It shall select a bounded deterministic set of representative subchapters spread across the textbook and use the configured Gemini API model to classify subject and academic level against only the installed active profile candidates.

The classifier shall return per-sample assessments plus a whole-textbook assessment through a strict structured-output schema. Automatic selection requires a consistent result, a configurable minimum confidence (default 0.85), sufficient sample support, no conflicting high-confidence installed-domain assessment, and exact subject/academic-level agreement with the selected profile manifest. It may return `unsupported`; it must never be forced to choose the default profile.

A successful result shall be bound outside Git to the whole-root fingerprint, selected domain ID, profile version, representative samples, confidence, classifier model, and selection mode. A source-fingerprint or domain-profile-version change invalidates that binding. An explicit configured/CLI domain ID remains available as a deliberate manual override and is recorded as explicit selection.

Unsupported textbooks shall stop with `DOMAIN_PROFILE_REQUIRED`. Ambiguous, inconsistent, or low-confidence results shall stop with `DOMAIN_DISCOVERY_FAILED`. Auto/distributed work must encounter this gate before content-job claiming, and workers must not automatically create, register, or activate new domain profiles. Diagnostic status may be written to workstation-local project state.

## Consequences

A stale physics profile cannot silently follow a project to a different textbook, and chapter-targeted runs cannot classify only the requested chapter while ignoring the rest of the textbook. Each worker may independently verify the same shared Source Root; the current binding/status cache is workstation-local rather than a shared Drive lock, so a first run on several PCs may redundantly classify the same textbook. This is safe but may be optimized later.

The bounded integration following this decision now carries the selected profile into generation: live source-analysis, activity-generation, semantic-audit, and repair stages compose the corresponding profile instructions while retaining the generic stage contract as authority. The composer also reserves `visual-*` stages for the profile's visual-generation instruction when those stages are activated. New packages record the selected domain/profile identity, and deterministic validation/public release resolve profile-owned validators, registries, renderer, and stylesheet from that package identity. Legacy packages without the identity remain compatible with the registry default.

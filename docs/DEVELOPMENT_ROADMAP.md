# Development roadmap

## Workflow

Use `Backlog → Ready → In Progress → Validation → Done`. Keep `main` stable; develop through short-lived branches and reviewed pull requests.

## Milestones

1. **Section 1.1 Implementation Pack** ? approved objectives, misconceptions, 18 original activities, translations, answer logic, and traceability records.
2. **Visual-Interactive Foundation** ? Decision 0024 contract, versioned visual schema, deterministic renderer primitives, cross-modal validation, safe fallback, and at least one bounded simulation primitive.
3. **Bounded Visual Pilot** ? regenerate a small representative set of real physics activities and verify scientific relevance, mobile/accessibility behavior, visual quality, caching, and contradiction detection before broad regeneration.
4. **Clickable Student Prototype** ? mobile-first journey demonstrating prediction, visual interaction, hints/retries/skips, and mastery presentation.
5. **Functional Vertical Slice** ? persistence, adaptive routing, evidence separation, guarded tutor, and dashboards.
6. **Small-Group Usability Test** ? synthetic/consented test cohort, accessibility findings, representation-quality findings, and prioritised fixes.
7. **Classroom Pilot** ? institutional privacy approval, operations plan, success measures, retention measures, and rollback path.
8. **Broad Course Expansion** ? validated visual-interactive packages and regression coverage across additional chapters/topics.

Visual-interactive foundation status: the visual schema/validator, four deterministic SVG renderer primitives, and the first bounded deterministic simulation (`mechanics.motion_1d_slider`) are implemented. The domain-profile architecture isolates physics-specific assets under `domains/university-level physics/`; Stage 0 performs textbook-level domain discovery/fingerprint binding before generation, and the selected profile now follows the run through source analysis, activity generation, semantic audit/repair, package identity, deterministic validation, and public-release asset selection. The prompt composer is ready for `visual-*` stages, but visual-plan/spec authoring is not activated by this integration slice. The next bounded work should therefore remain a small real-topic visual pilot / visual-stage integration rather than broad regeneration. Automated domain-profile authoring/onboarding remains a later, explicitly gated capability.

Do not begin broad visual regeneration until the visual-interactive foundation and bounded real-topic pilot meet their acceptance criteria. Preserve the current working Stage-0 generator while those capabilities are introduced through independently reviewable PRs.

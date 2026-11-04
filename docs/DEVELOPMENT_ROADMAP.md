# Development roadmap

## Workflow

Use `Backlog → Ready → In Progress → Validation → Done`. Keep `main` stable; develop through short-lived branches and reviewed pull requests.

## Finite technical completion gate (Decision 0029)

This campaign must not drift into endless per-PDF code changes. Keep the historical product roadmap below, but complete and **report separately** four bounded milestones: C1 consolidated integration candidate (existing PR #222 plus #223), C2 reusable academic verification and content quarantine, C3 three genuinely unseen PDFs from three physics topic families under frozen code with real technical/learner-browser receipts, and C4 independently confirmed technical disposition. See `docs/decisions/0029-finite-generalization-completion.md` and `docs/HELDOUT_GENERALIZATION_CAMPAIGN.md`.

C3 defaults to one held-out campaign. A single general fix may justify one further campaign using **different** unseen PDFs; no third campaign or bespoke per-PDF validator expansion. A failed campaign produces a named, finite blocker, not a fabricated PASS or another automatic repair cycle. Completion of the **codebase** is independent of whether the historical Section 9.4 PDF gains five-gate academic acceptance; its private content stays quarantined until separately approved.

**Current baseline (4 November 2026):** The owner-approved Decision 0029 C1–C4 campaign has reached its **terminal disposition: BLOCKED_EXTERNAL** (see [the exact disposition](FINITE_GLOBAL_CODEBASE_DISPOSITION_20261104.md)). C1 consolidated direct-to-main draft PR #223 is CI-validated but unmerged; #222 was closed unmerged as superseded. C2 generic academic/domain adapter and held-out verifier have source-free regressions; the single shared visual-plan schema repair was completed at frozen application-code head `7a7b146e16d719576ef7bceea6719fa4153b4a1c`, which passed hosted CI #421. C3 round 1 produced 0/3 drafts (503 then visual-plan failure). Final round 2 used three preselected different physics PDFs but ended 0/3 drafts because all calls returned provider HTTP 402 in source-free preflight before attachment. C4 cannot grant real learner/browser, EN/MS/ZH semantic, accessibility, original-source or academic PASS. Historical Section 9.4 remains 0/18 formal academic PASS. Both campaigns and the single generic-repair budget are consumed: **no automatic third campaign or per-PDF correction loop**. Legitimate provider restoration and a separate owner-authorized reconciliation with the already selected round-2 sources are prerequisites to any renewed C3/C4 execution. No merge, publication or release is authorized.

## Milestones

1. **Section 1.1 Implementation Pack** ? approved objectives, misconceptions, 18 original activities, translations, answer logic, and traceability records.
2. **Visual-Interactive Foundation** ? Decision 0024 contract, versioned visual schema, deterministic renderer primitives, cross-modal validation, safe fallback, and at least one bounded simulation primitive.
3. **Bounded Visual Pilot** ? regenerate a small representative set of real physics activities and verify scientific relevance, mobile/accessibility behavior, visual quality, caching, and contradiction detection before broad regeneration.
4. **Clickable Student Prototype** ? mobile-first journey demonstrating prediction, visual interaction, hints/retries/skips, and mastery presentation.
5. **Functional Vertical Slice** ? persistence, adaptive routing, evidence separation, guarded tutor, and dashboards.
6. **Small-Group Usability Test** ? synthetic/consented test cohort, accessibility findings, representation-quality findings, and prioritised fixes.
7. **Classroom Pilot** ? institutional privacy approval, operations plan, success measures, retention measures, and rollback path.
8. **Broad Course Expansion** ? validated visual-interactive packages and regression coverage across additional chapters/topics.

Visual-interactive foundation status: the visual schema/validator, four deterministic SVG renderer primitives, and the first bounded deterministic simulation (`mechanics.motion_1d_slider`) are implemented. The domain-profile architecture isolates physics-specific assets under `domains/university-level physics/`; Stage 0 performs textbook-level domain discovery/fingerprint binding before generation, and the selected profile follows the run through source analysis, activity generation, semantic audit/repair, package identity, deterministic validation, and public-release asset selection. Live generation now performs one batched `visual-plans` stage after text semantic repair and, only for activities selecting a useful visual, one batched `visual-specs` stage. Both stages use only available trusted domain templates and are accepted only after repository visual-contract validation. The next bounded work is therefore a small real-topic visual pilot rather than broad regeneration. Automated domain-profile authoring/onboarding remains a later, explicitly gated capability.

Do not begin broad visual regeneration until the visual-interactive foundation and bounded real-topic pilot meet their acceptance criteria. Preserve the current working Stage-0 generator while those capabilities are introduced through independently reviewable PRs.

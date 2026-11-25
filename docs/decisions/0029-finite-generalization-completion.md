# 0029 — Finite Codebase Completion and Held-Out PDF Generalization

**Status:** Owner-approved direction, 3 November 2026; implementation proposed in draft PR #223, not effective on main before authorized integration. Amends the development process, not copyright, private-data, scientific QA, safety, permissions or release policy. Decisions 0024, 0027 and 0028 remain binding.

## Why this is needed

Repeated Section 9.4-specific vocabulary, physics example and diagram corrections produced valuable fixes but did not establish that a new, unrelated PDF can be processed reliably. Open-ended "repair PDF → extend the validator → repeat" is not an acceptable definition of codebase completion.

A failed per-document academic verdict is **not** proof the entire application is unfinished. Conversely, a green repository CI run, an exactly hashed source location, and 0 academic FAIL do **not** establish scientific correctness. These milestones must not be conflated.

## Binding change: stop unbounded per-PDF code hardening

1. **Freeze new bespoke rules.** Do not add a generic-application logic branch, hard-coded PDF SHA, specific activity ID or literal passage detector merely to make one document pass. Existing narrow verified regressions remain protected. A genuine general defect may be repaired once in a shared reusable component, with a source-free adversarial regression and proof that an unrelated example benefits. Source-content corrections belong in private versioned packages, not app code.
2. **Prefer generic engines.** Source provenance, answer models, EN/MS/ZH semantic equivalence, visual-to-answer consistency, accessibility, interaction and independent reviewer admission must operate through common typed interfaces and subject-domain profiles. Specialized physics belongs in the versioned physics domain profile, not PDF-specific application pathways.
3. **Quarantine unresolved content.** Keep document academic findings REVIEW_REQUIRED or FAIL; do not promote or publish that package. Document quarantine does not prevent independent codebase validation.
4. **Respect external controls.** Preserve Decision 0028 BLOCKED_EXTERNAL, immutable model-claim no-replay and allowed paths. A safety denial is not a scientific failure; do not copy inaccessible PDFs to another machine or connector to circumvent controls.
5. **Avoid more stacked PR debt.** Draft #223 now directly targets main and contains all former #222 commits. Former #222 was closed unmerged as superseded after ancestry and direct-main hosted CI verification. Treat #223 as the single consolidated technical candidate; do not create another unrelated stacked integration PR. Do not auto-merge or auto-publish.

## Four finite developmental milestones

| ID | Milestone | Exit evidence |
|---|---|---|
| C1 | Consolidate platform | Dependency-ordered integration inventory, verified code candidate with exact head/base, all repository checks passing and existing legacy regressions retained; no automatic merge |
| C2 | Generic verifier | Reusable source/answers/science/EN-MS-ZH/visual evidence workflow, individual content quarantine, repeatable provenance and correction/versioning; source-free adversarial tests in ordinary CI, no document-specific acceptance shortcut |
| C3 | Held-out generalization | Three previously unseen, rights-cleared physics PDFs from three distinct topic families, independently precommitted before execution; same frozen code revision and active domain profile; genuine PASS receipts for domain binding, source ingestion, draft schema, interactive learner and trilingual rendering; no PDF-specific code edits |
| C4 | Completion disposition | Independently audit C3 provenance plus relevant real browser, accessibility and privacy checks; record TECHNICALLY_COMPLETE, NOT_COMPLETE_WITH_NAMED_BLOCKERS, or BLOCKED_EXTERNAL separately from content academic status |

**No perpetual campaign:** The default is one C3 campaign. If it reveals a real generic software defect, permit at most one independently justified shared-code correction and one new campaign using three different unseen PDFs with a regression proving the general defect. After the second campaign, stop and record the final disposition—even if NOT_COMPLETE. A scope change requires a separate explicit owner decision, never another automatic per-PDF loop. A document exposed in round 1 may not be counted as unseen in round 2.

The selection-witness digest must refer to a genuinely immutable pre-execution record held by an independently authorized system. Merely filling in the field does not prove unbiased selection. Do not invent real PDFs, browser captures or original-source approval.

## Pilot evidence and limits

The source-free engine at app_generator/validation/heldout_generalization_gate.py, exposed by scripts/assess_heldout_generalization.py, validates only structured metadata, exact-version binding, topic diversity, bounded campaign count and receipt presence. It **does not run PDFs** or authenticate external source and browser evidence. A metadata-complete report yields READY_FOR_TRUSTED_PROVENANCE_AUDIT—not TECHNICALLY_COMPLETE, formal academic PASS or publication authorization.

A trusted authorized evaluator must compare actual original source/PDF/package bytes, versioned generator receipts, validation output, learner-browser behavior and source-bound academic findings before C4. No mandatory manual signoff for each question is introduced; independently corroborated autonomous review is preferred.

## Separate code completion, content acceptance and release

- **Codebase completion** means C1-C4 technical criteria met; it does not require every historical PDF, including Section 9.4 v11, to obtain academic PASS.
- **Individual content acceptance** requires five independently evidenced academic gates; otherwise REVIEW_REQUIRED/FAIL and private correction/quarantine.
- **Publication** remains separately controlled with git_publish=false, git_auto_merge=false, no release of original protected source and no external-control bypass.
- Future product milestones (adaptive routing, tutor, cohort privacy, analytics and classroom pilot) remain separate scope items, not silently declared complete by C4.

## Enforcement

- Normal CI runs source-free adversarial tests in tests/test_heldout_generalization_gate.py.
- Decision 0027 recurrence incident BSA-20261103-102 locks the bounded protocol.
- Proposed defects are classified as GENERIC_DEFECT, PRIVATE_CONTENT_DEFECT, UNSUPPORTED_DOMAIN or EXTERNAL_BLOCK. Only the first permits a shared code correction supported by cross-PDF evidence; private content repairs stay in versioned packages.
- A passing static gate or synthetic tests does not mean any real held-out campaign ran.

## Next action

Complete C1/C2 code integration and reliable academic evidence admission without inaccessible private PDFs. Prepare the C3 source selection only in an independently authorized environment. Launch no new Section 9.4-specific hardening campaign. Preserve its 18-activity REVIEW_REQUIRED matrix and no-publication gate until separately proven.

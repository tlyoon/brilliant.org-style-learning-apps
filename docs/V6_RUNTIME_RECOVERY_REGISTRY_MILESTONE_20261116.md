# Bosla v6.0 — executable persistent recovery registry

Date: 16 November 2026. Owner's uploaded auto_cont_dev_prompt_v6.0.md governs. This document records the verified Bosla V3 implementation subset, not a claim that all codebase-wide failure classes have already been automated.

## Reproduced weakness and reusable correction

Over 100 incidents were already documented in docs/recurrence_registry.json, but the existing v3 auto-advance worker called a particular language-repair function directly rather than consulting the registry. There was no durable explicit incident-selection record, so a retired handler could potentially remain active in that executable path. BSA-20261116-177 addresses this gap.

New app_generator/runtime/v3_recovery_policy.py deterministically matches the source-free quarantined Section 9.2 Unicode signature, then reads the persistent version-controlled registry and checks four exact existing incident IDs BSA-173, BSA-174, BSA-175 and BSA-176, their approved status and exact reviewed Python handler identity. JSON data never becomes executable code. Unknown or retired handlers are classified but not invoked. Only one existing genuinely verified content-repair handler is allowlisted today. New failure families require separate code, tests and registry admission, not blind retries.

The normal scripts/run_v3_yoga6_recovery_worker.py --auto-advance now invokes apply_registered_recovery within the existing whole-run lock. It reuses the same exact-parent, two-Gemini historical failure verifier, private corrected candidate SHA, immutable package, QA and no-replay protections. Recovery writes an atomic private v3-recovery-policy-state.json with version, monotonic revision, failure class, trigger incident, remedy incident, candidate SHA, verification status, integrity SHA, zero automatic paid retries and publicationAuthorized=false. It stores no source passages, secrets, reviewer responses or permissions. A tampered receipt fails closed even if the original content defect is no longer active.

On successful source-free staging, the existing controller rechecks unchanged frozen assessment totals, persists the forward-stage checkpoint and begins the next independently eligible operation within the SAME explicitly authorized finite invocation. A rejected repair of one section does not automatically block other independently eligible sections. The retired Yoga 6 30-minute scheduled task is not reinstated. When the finite invocation stops, there is no background runner; later execution requires a fresh authorized invocation.

## Real Yoga 6 validation (source-free)

The true private V3 planner reports Section 9.5 next, 52/108 activities assessed, 51 independently fully reviewed, 50 consensus PASS, one Section 9.1 historical uncertain activity and one original Section 9.2 language AI_REPAIR_REQUIRED. Calling the new registry policy without paid Google requests matched BSA-173 to BSA-174, recognized candidate SHA 49a7f18c7cc2b7c00e0b6b23838cca1ed7fe52262384e0c26bbc8360fa3e9174 and persisted an integrity-verified local recovery-policy receipt, revision 1. No original model verdict or release claim changed.

## V6.0 acceptance matrix

| Required scenario | Verification evidence |
|---|---|
| A: historical known blocker | Registry match, exact frozen and Gemini source-free evidence, private repaired candidate recognized |
| B: new blocker | Unknown signature persisted as unresolved; new BSA-177 handler selection and regression created |
| C: remedy fails | Bad/missing reviewer, retired handler or tampered candidate refuses false recovery; independent safe work remains eligible |
| D: crash during repair | BSA-175 fsynced atomic two-file candidate promotion, abandoned temporary folder tests |
| E: crash after repair | New synthetic kill immediately after staged checkpoint, then verified restart and immediate next eligible operation |
| F: duplicate processing | Existing whole-run lock, immutable reviewer role claims and race tests |
| G: scientific QA failure | Real Section 9.2 trilingual FAIL preserved; corrected candidate requires new genuine reviewer decisions |
| H: permissions | Existing paid and generated-text-transfer flags required, no bypass or persisted permission |
| I: external outage | Existing ServerError/circuit/quarantine tests; ambiguous requests never resent |
| J: historical regressions | Cross-platform archival SHA/Git blob identity tests and existing provider/learner QA regression suites |

These are source-free tests of workflow behavior. They are NOT evidence that a synthetic reviewer verdict was received from Gemini or that a live Batch API job has passed. The completed-vs-pending release distinction is unchanged.

## Remaining actual V3 acceptance

56 original activities remain unassessed. Section 9.1 original uncertain request must not be replayed; the privately corrected Section 9.2 package needs fresh genuine two-Gemini QA and versioned course admission. Live keyed Batch API attribution and exact accepted-package scientific, privacy, accessibility and deterministic release receipts are still open. Never auto-merge, publish or initiate paid work outside existing authorization and finite bounds.

## Historical executable-link regression resolved

The permanent recurrence checker initially caught a real integration error: the old BSA-174 and BSA-176 normal-entrypoint metadata still referred to the removed direct import in the Yoga 6 worker. Updating the marker alone was insufficient because the contract also requires each dispatcher to actually import/run its declared remedy. The two historical incident entries now identify the true intermediate app_generator/runtime/v3_recovery_policy.py import of v3_auto_repair.stage_known_language_repair, while BSA-177 identifies the outer normal scripts/run_v3_yoga6_recovery_worker.py entrypoint. The existing full regression contract then passed. A permanent test specifically checks this two-level runtime chain to prevent later reintroduction. No historical safety gate was bypassed or weakened.

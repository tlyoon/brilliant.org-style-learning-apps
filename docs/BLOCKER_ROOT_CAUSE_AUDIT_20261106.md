# Recurring Blocker Root-Cause Audit — 6 November 2026

**Project:** `tlyoon/brilliant.org-style-learning-apps`, consolidated draft PR #223. This is a source-free history audit of existing tracked Git commits, [Decision 0027](decisions/0027-regression-immunity-and-recovery.md), [Decision 0028](decisions/0028-authorized-execution-and-blocker-isolation.md), [Decisions 0029–0031](decisions/0031-deterministic-source-acquisition-recovery.md), the 45 prior registered `BSA-` incidents and their regression methods. No PDF regeneration, model request, browser operation, student records, source payload or publication was involved.

## What kept recurring

This was **not one unresolved Gemini or PDF bug**. Independent failures reached the same generic symptom ("pipeline stopped"), but had materially different causes. Many were already fixed in isolation; **the missing cross-incident enforcement** meant a *new* script or campaign could encounter a close relative and receive a new fix under an unrelated name.

| Shared root-cause family | Prior incident anchors | Existing generalized protection | What must happen next time |
|---|---|---|---|
| Environment / test setup | BSA-20261102-097, -098 | Correct interpreter/venv preflight; bounded tests | Diagnose environment first; don't launch browser/model as a workaround |
| Provider request / retry | BSA-20261104-104, -106, -107, -108, -110 | One-attempt/rotation boundaries, SDK type and billing classifications | Determine request-submitted state before considering permitted retry; ambiguous requests are terminal |
| External authorization denial | BSA-20261103-099, BSA-20261104-111 | Decision 0028 fail-closed, provenance-bound task fingerprints | Preserve `BLOCKED_EXTERNAL`, no alternate tool/machine or rephrased replay of the denied operation |
| Per-PDF repair loop | BSA-20261103-102, -103 | Finite generator repair contract and terminal Decision 0029 | Do not perfect a single source; report bounded global FAIL/REVIEW_REQUIRED |
| Academic evidence vs software tests | BSA-20261103-100, BSA-20261105-114, -115 | Source-bound claim inventory; independent evidence gates | Do not turn technical/browser success or model self-rating into scientific/EN-MS-ZH PASS |
| Learner browser state | BSA-20261105-116 | Reload per locale; full 18 × 3 × 2 browser observations | Use independent per-locale fresh-state tests; do not regenerate a PDF to fix a test harness |
| Private source acquisition | BSA-20261105-117 | Canonical `sourceSha256`, pre-network full-row validation, SHA-verified reuse, bounded fetch, saved acquired-state receipt | Reuse the shared acquisition module; do not create another ad-hoc private source downloader |
| Incident-registry governance | BSA-20261102-096, new BSA-20261106-119 | Existing CI regression contract now checks **family links** for new entries | Link to an earlier same-family incident and state what previous regression failed to detect; unknown families require explicit novelty evidence |

## Root cause of the *process* recurrence

Previously `scripts/check_regression_contract.py` verified that a recorded incident appeared in the ledger, referenced an executable test and was covered by ordinary CI. This was valuable but insufficient: **it did not require a subsequent incident to identify the existing root-cause family and its previous test**. As a result, the project could accumulate 45 individually named issues while repeating types of correction.

**New invariant, effective for incident IDs starting at `BSA-20261106-119`:** each new issue declares `rootCauseFamily`. For known families it must contain valid `relatedIncidentIds`, at least one matching earlier incident, plus `differenceFromLinkedIncident` explaining the previously missed condition. The special `genuinely-new-root-cause` class requires `noveltyExplanation` rather than silently inventing a new family. Existing 45 records remain historically intact. The guard and its adversarial tests execute in standard CI.

This **does not automatically repair every future failure**. It automatically **prevents the same governance omission from being treated as a resolved regression** and directs developers to known shared fixes. A codebase cannot override a platform security denial, prove unexamined physics correct, create licensed source rights or safely reissue a potentially submitted model request.

## Current verified closure boundary and priorities

At the inspected PR head `efefbbc8bfbcbef376f465fd2a551cd1c7826067`, hosted CI succeeded and PR #223 was draft and unmerged. Decision 0031 acquired and preserved all three frozen PDF bytes, but the thermodynamics source's 297 extracted words failed the frozen 300-word threshold. An attempted private conceptual audit remained incomplete and a separate operation was externally denied. The local source-only Decision 0032 files exist as untracked workspace files and are **not** included in this bounded process-governance change. Their denied private review/recording operation must not be retried through another route.

**Global priorities:** keep the large existing PR on one consolidated integration track; do not regenerate an exhausted PDF; use authenticated exact-commit CI and a read-only merge simulation as engineering evidence; advance a genuinely independent learner-platform/pilot readiness review only after source and academic gates have actual proof. No merge, publication or authorization changes are implied here.

**Milestone:** project-level recurrence governance hardened once in the already existing checker, protected by source-free negative controls. Do not invent a new generic "pipeline recovery" implementation alongside the existing Decision 0027/0028 engines.


## Follow-on global acceptance gap found and fixed

In the existing `bounded_cross_topic_acceptance` evaluator, the earlier
positive test package contained only **two activities** yet appeared
metadata complete. This was the same underlying acceptance-coverage class
as incidents BSA-20261105-113/114/115. The existing final gate now
enforces 18 Stage-0 items, the 9+9 split and all six type/difficulty
quotas, and explicitly records that visual specifications are not
independently verified. New incident BSA-20261106-120 links those earlier
failures, with source-free negative tests; no PDF/model replay.

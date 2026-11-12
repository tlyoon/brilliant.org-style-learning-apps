# V3 reviewer-transport recurrence and integration map

**Scope:** BOSLA PR #223, current Decision 0036; historical incidents are
evidence of previous engineering defects, not authorization to rerun closed
academic campaigns. The old source-PDF reviewer path is not a V3 model
transport. This note covers source-free code integration only.

| Prior recorded incident | Previously verified remedy | Current shared V3 disposition |
| --- | --- | --- |
| BSA-20261026-019, -021 and BSA-20261028-031, -041 | Distinguish missing, initialized, busy and actually authenticated Chrome reviewer profiles; never assume a directory proves login | `reviewer_ownership_preflight` remains a read-only prerequisite, not a live authorization or authenticated V3 reviewer; the three source-free Yoga 6 profile-root checks on 12 Nov returned MISSING for both dedicated roles |
| BSA-20261026-022 and BSA-20261029-044, BSA-20261030-046, BSA-20261031-053 | Existing-login session with independently owned tabs, protected restored tabs, one pre-submission neutral redirect recovery | Historical reviewer factories still require controlled original-PDF attachment; **do not silently reuse them** as generated-text-only transports or bypass a denied browser operation |
| BSA-20261026-023, BSA-20261029-042, BSA-20261030-047, -050 | Explicit ambiguous capture, stable error classifications, privacy-safe diagnostics, strict JSON shape | V3 retains strict four-dimension JSON and immutable prompt-bound claims; a malformed **returned** JSON is still ambiguous, not an uncaptured UI health event or review PASS |
| BSA-20261030-052 | After two uncaptured failures, skip further requests from one unhealthy reviewer role while allowing the other to finish | **BSA-20261112-150** reuses the same threshold in `reviewer_failure_policy.py`, invoked by the normal V3 `assess_with_models`. After two uncaptured transport errors the role records `SKIPPED_UNSENT`, `requestSubmitted=false` instead of contacting the provider again. The circuit is reconstructed from validated aggregate results across the 6+6+6 batches |
| BSA-20261103-099, Decision 0028 | Preserve a terminal external execution denial; never relabel, replay, switch devices or wrap a denied operation | **BSA-150** records `BLOCKED_EXTERNAL` on `ExternalExecutionDenied`, stops the full invocation and rejects restart replays. This is a fail-closed software response; it does not change a prior platform denial |
| BSA-20261111-147, BSA-20261112-148 | Generated-text-only V3 policy; package-bound two-context review and durable per-role plus aggregate checkpoints | Existing `assess_with_models` runs no browser startup; it requires two externally provisioned distinct reviewer sessions and explicit generated-text transfer permission. BSA-150 is active on this same function, not a new model runner |
| BSA-20261112-149 | Admit both scored MCQ and interactive activities through canonical package identity | Six authentic 18-activity Chapter 9 packages remain immutable, accepted by V3 structural checks; this does not imply reviewer completion |

## Exact-source-free negative controls

The regression `tests/test_autonomous_completion_v3.py` uses fake, explicitly
synthetic reviewers and a checkpoint. It proves: (a) a previously failing
reviewer issues **two**, not six, uncaptured attempts while a healthy role can
finish six; (b) across three bounded invocations the same failed role is never
restarted, and 16 later roles are explicitly unsent; (c) malformed but
captured model JSON does **not** incorrectly trip the transport circuit;
(d) an explicit host denial stops all subsequent role prompts and remains
terminal on restart; (e) no unresolved/skipped row creates a release PASS.
The legacy `test_autonomous_ai_review.py` protects the old reviewer contract.
`scripts/check_regression_contract.py` binds incident BSA-150 to the normal
assessment and read-only status paths.

`assessment_progress` reports `activitiesFullyModelReviewed` and
`reviewerRequestsSkippedUnsent` separately from its legacy
`activitiesAssessed` processed-row count, so readers can distinguish an
actual two-context verdict from an unresolved or unsent review.

## What does not close through code

No attached Gemini/ChatGPT model-inference tool or approved V3 browser
execution transport is established by these fixes. In particular, old
original-PDF sign-in and PDF-upload operations cannot be relabeled as
generated-text-only reviews. A previous authenticated browser-runner
execution was explicitly denied; Decision 0028 holds that operation terminal
until an independent authorization determination. Source-free tests, CI and
profile-directory presence do not supply model responses, reviewer ownership
or remote execution permission.

**Until real authorized V3 reviewer responses, exact package evidence and
machine checks exist:** `PENDING_AUTOMATED_ASSESSMENT`, model verdicts
0/108 verified, no merge/deployment, and no scientific/visual/learner-pilot
certification claimed. The old six original-source academic campaigns remain
frozen. Do not replay their exhausted requests.

# 0037 — Automatic recovery belongs to normal pipeline execution

**Status:** Owner-approved binding BOSLA development contract, 13 November 2026.
Extends Decisions 0027, 0028, 0032, and the current V3 Decision 0036;
the more restrictive authentication, privacy, no-replay, and publication
boundaries remain in force.

> automatic recovery must be part of normal pipeline execution, not depend on you repeatedly asking me to fix the next blocker.

## Mandatory behavior for every future development milestone

1. **Reuse before repair.** On encountering a failure, the normal executor
   checks the existing failure ledger, recurrence registry, package/run identity,
   in-flight request claims, and current environment. Prefer the registered
   common remedy for the same root-cause family, never another ad hoc script.
2. **Detect and recover in the normal path.** Fixes must implement automatic
   detection, an owned-state preflight, a bounded recovery/stop action and
   continuation in the existing production workflow. A helper run manually by
   an assistant, a test-only adapter, or a new wrapper that is never dispatched
   by normal execution does **not** close the blocker.
3. **Stop safely and continue independently.** Reconcile potentially sent
   requests read-only; never replay an ambiguous response. External security
   denial, absent authorization or unavailable reviewer transport are
   non-retryable by the repository. Record the real blocker and automatically
   advance other independently authorized work, without repeatedly asking the
   owner to perform routine troubleshooting. If the critical path genuinely
   depends on the denied operation, report it **blocked**, not resolved.
4. **Fail closed with real evidence.** An accepted resolution needs an
   adversarial pre-fix negative control, a same-path end-to-end dispatch
   regression, a separate-input/cross-entrypoint proof where relevant,
   exact-head CI and a truthful real-task execution receipt. Source-free
   synthetic tests prove software behavior, not real model assessment,
   scientific correctness, account entitlement, or release completion.
5. **Permanent governance.** Every new resolved BSA incident must declare
   `automaticRemedy` in `docs/recurrence_registry.json`, with its actual
   runtime trigger, recovery or stop marker and normal dispatch entrypoint.
   Keep the owner-approved machine-readable rule in
   `docs/normal_pipeline_recovery_contract.json`; the existing ordinary
   `scripts/check_regression_contract.py` CI gate must reject missing or
   weakened requirements. No per-incident manual re-approval is requested for
   otherwise authorized, safe, routine development.
6. **Finite unattended execution.** Within a live authorized run, advance
   eligible milestones until success, a finite stop budget, a real evidence
   conflict, or an external authorization boundary. Do not promise ongoing
   background execution when no worker or scheduled service is active.

## Current Section 9.1 external blocker

The existing V3 dispatcher chooses approved Section 9.1 and has already
integrated safe batch/checkpoint/role failure recovery (BSA-148–156).
Its two authentic provider sessions are **not available** in this
environment. The previously denied authenticated browser runner remains
terminal under Decision 0028 unless independently reauthorized by the
platform. Neither this contract nor green CI creates account access or a
valid two-model receipt. Preserve `BLOCKED_EXTERNAL_REVIEW_TRANSPORT`,
`PENDING_AUTOMATED_ASSESSMENT` and 0/108 genuine reviews until new
verified authorized execution evidence exists. Do not add a substitute
fake provider or re-enter frozen source-PDF campaigns.

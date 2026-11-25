# Decision 0050 — Ordinary review-ready dispatch also executes source-free recovery before paid authorization

**Date:** 17 November 2026
**Incident:** BSA-20261117-189
**Historical incidents reused:** BSA-177 registered deterministic content repair and private candidate handoff; BSA-184 local parse capture; BSA-186 shared provider circuit; BSA-187 source-free under no eligible/blocked provider STOP; BSA-188 conservative provider reporting.

## Reproduced normal-path fault

BSA-187 fixed source-free recovery before paid permission denial in the Section9.6 *fallback* branch, and independently when no original course review was eligible. But the **normal course review-ready branch** of `scripts/run_v3_yoga6_recovery_worker.py --auto-advance` still invoked `authorize_paid_v3_action` before accessing independent source-free repair. When that paid charter was denied or expired, source-free registered content repair, immutable QA handoff and exactly source-bound untouched activity inputs did not execute, although they do not require a model submission.

`test_normal_ready_paid_denial_does_not_strand_source_free_work` reproduced the discrepancy using the real normal worker, a real-shaped private frozen 18-activity Section9.6 synthetic course checkpoint and a denied paid-action stub. Before correction, the worker returned the expected paid STOP but no private source-free packages or receipt existed; its new pre-fix assertion failed.

## Verified executable correction

The normal `--auto-advance` review-ready branch now requires the specifically authorized Yoga 6 host, calls the same `advance_source_free_until_boundary` as the fallback and offline mode, then checks `authorize_paid_v3_action` before any allowed model transport. The BSA-188 common supplemental provider circuit and old BSA-183 uncertainty remain unchanged. The ordinary one-activity reviewer still checks its original gate after authorization. Idempotent duplicate source-free preparation is harmless, source-bound and never creates model `PRE_CALL` reservations.

The corrected previously failing normal-path test confirms a paid permission denial still returns STOP but *does not strand* the twelve exact frozen-original untouched input packages and durable private source-free receipt; the model reviewer, SDK/credentials and metadata were never invoked. The earlier fallback denial, no-permission source-free mode, supplemental provider error, crash/restart, owner-lock and corrupt-checkpoint regressions remain mandatory.

This closes an **engineering integration** boundary, not the real unknown BSA-183 Gemini response. No extra paid permission, model replay, course version admission, scheduler, merge or publication is implied. Full exact-head CI must pass before treating the closure as verified across the repository.

## Hosted CI fixture mismatch and permanent test correction

Exact-head GitHub run `44106596756` executed 1,481 tests and found one failure in `test_v3_forward_progress.ForwardControllerTests.test_script_dispatches_controller_from_normal_entrypoint` (all other 1,480 tests passed, one opt-in live test skipped). This older source-free *controller-routing unit test* injected a fake `READY` dispatch but provided **no real frozen six-package Chapter9 contents or private reviewer evidence**. With the new BSA-189 source-free-first preflight, correctly validating that invented source state fails closed, so the prior expected return code 0 is no longer appropriate without mocking the newly invoked local controller. The existing test now explicitly supplies a **zero-provider source-free result stub** and asserts that the ordinary entrypoint calls it, while the separate BSA-189 full normal-path test continues to execute the real source-free controller with genuine-shaped synthetic frozen content under denied paid permission. This modifies **test fixture fidelity only**, does not weaken production source or provider gates, and preserves strong end-to-end source-bound checks. The corrected single test passed locally; exact new-head GitHub CI remains required before closing validation.

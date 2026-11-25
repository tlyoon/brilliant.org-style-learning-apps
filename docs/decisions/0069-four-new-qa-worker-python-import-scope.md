# Decision 0069 — Normal four-new Gemini dispatcher must not shadow a module-level import

**Date:** 18 November 2026. **Incident:** BSA-20261118-211. **Authority:** The owner's separate new 4-activity / maximum eight Gemini calls on Yoga 6; no extra paid scope is created.

## Real failure and historical boundary

GitHub CI 44295739064 on `5d310773a4f02840be565b3e52c412a385349de2` completed SUCCESS, including real hosted synthetic Chrome preview after the BSA210 cache correction. Genuine Yoga6 exact-head 108 activities / 698 checks passed and were persisted. The first owner-authorized normal `--advance-new-four --execute --allow-generated-text-transfer --max-forward-activities 4 --max-forward-seconds 900` invocation then returned `STOP_YOGA6_RECOVERY_WORKER` with `reasonClass: UnboundLocalError` and exit3 before any new role submission. Read-only inspection of all four pinned `v3-generated-<sha>` directories found **none present**, zero role claims, zero aggregates, so **zero paid Gemini reviews** were started and no ambiguous new role exists.

This reuses the BSA208 same-entrypoint forward progress failure family. The precise Python cause is that `main()` already imports `diagnose_declared_generation_support` at module scope but redundantly imported the same name inside a later `if args.advance_revised_96` branch. Python treats a function-scoped import as a local assignment throughout the entire function. Therefore an earlier newly added `if args.advance_new_four` branch accessing that name raised `UnboundLocalError` even though the top-level import exists. This was a code-path coverage gap, not Gemini billing, latency, model refusal or an old role requiring replay.

## Permanent normal-path correction

Remove the redundant late `main()` diagnostic import; reuse the existing module-level binding. Preserve the earlier `_advance_unchanged_frozen_tail()` independent function import, which has a different Python lexical scope and is safe. No provider/charter/role or locale model logic changes.

Add `tests/test_v3_four_new92_worker_dispatch.py`: the real normal `main()` four-new paid-gated branch is exercised with mocked host, source-free browser, Gemini SDK delegation, metadata diagnostic, reviewer, and continuation. It verifies exact forward dispatch and rejects incompatible flag modes with **zero real model or browser calls**. This test reproduces the earlier UnboundLocalError before the source correction and passes with the correction. The existing 11 owner-budget/source/no-replay tests and four subtests remain unchanged and passed; complete focused total 13 tests plus four subtests PASS.

## Closure rules

The corrected live runner's dry-run still identifies exactly the four untouched original Section9.2 source SHA inputs and zero paid calls. Before any paid request, pass lint, recovery contract, cross-path regressions and hosted GitHub CI at the *new* committed head. Then retry exactly the same owner-authorized four new SHA identities, with no old-role replay, maximum eight calls, bounded 900 seconds, immutable two-Gemini evidence, scientific-failure handling and immediate eligible source-free browser continuation. If another blocker occurs, quarantine ambiguous requests and preserve them rather than retrying or weakening the scope. No automatic merge, course admission, publication, extra model calls or scheduler.

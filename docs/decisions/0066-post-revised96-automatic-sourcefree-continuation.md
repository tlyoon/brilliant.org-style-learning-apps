# Decision 0066 — Automatically continue to source-free acceptance after revised Section 9.6 scientific QA

**Date:** 18 November 2026. **Incident:** BSA-20261118-208.

## Repeated blocker and historical recovery

The genuinely owner-authorized normal `--advance-revised-96` worker had completed its exact two revised Section 9.6 independent Gemini assessments and returned. The separately implemented BSA207 source-bound 108-activity versioner and real Chrome acceptance were valid, but the paid review entrypoint did not invoke that next eligible source-free stage. Thus a user had to issue another "proceed" request. This recurs from the historical forward-progress and checkpoint families BSA175/185/189/203/207, not a provider failure or missing source.

The old 17 November charter and the four-call 18 November revised reviewer limit remain immutable. BSA206's actual four complete Gemini role claims and source-bound assessments, prior BSA207 real 698 Chrome pass, and all old ambiguous/failed original claims stay intact. No existing model request is retried.

## Runtime correction

`app_generator/runtime/v3_revised96_forward.py` implements `advance_post_revised96_science`. The ordinary Yoga6 `scripts/run_v3_yoga6_recovery_worker.py --advance-revised-96` dispatcher now calls it immediately after receiving the model result. **A completed batch is not automatically scientific PASS:** the reviewer can return a completed batch with a scientific FAIL. The continuation therefore requires BOTH exact authorized one-activity source hashes (indices 5 and 9), genuine reviewer `newConsensusPass=true`, `newScientificRepairRequired=false`, `newUncertain=false`, and unchanged nonpublication/version state. The preceding reviewer engine validates real immutable two-role evidence; the subsequent source-free versioning independently revalidates that evidence.

Only then does the same normal invocation stage the revised 108-activity unadmitted proposal and run source-free Chrome. Success requires exactly 108 activities, 648 locale/viewport checks, 698 total checks, matching proposal identity, and zero new paid model calls. The result carries a separate `postReviewAutomaticContinuation` status. A scientific FAIL, uncertainty, missing/changed source, exception, or incomplete browser receipt stops without a false PASS, new provider request, old-role replay, merge, release, scheduler or unbounded retry. A restart reconciles original complete reviewer roles and reuses any genuine identity-bound Chrome receipt.

## Verification and limits

`tests/test_v3_revised96_forward.py` provides eight synthetic source-free adversarial tests, including completed-but-science-FAIL, uncertain role, altered index or SHA, partial two-role completion, forged browser result, local Chrome exception, receipt reuse, and the real normal worker dispatch function with mocked downstream local stages. No live Gemini calls are made by these tests. Regression contract, content/lint CI, exact-commit real Chrome on Yoga6, and full hosted CI must pass before marking BSA208 resolved.

This improvement only removes the extra prompting boundary after previously authorized reviewer success. The remaining previously unreviewed originals, historic unknown original requests, general 108-activity scientific acceptance and any publication/merge remain separate boundaries; this decision does not grant new paid calls or additional authorizations.


## Genuine owner Yoga6 acceptance (18 November 2026)

Exact code commit 460ef302e05dae8086d7879f2f0844ae97712103 was pushed to existing draft PR #223. GitHub Actions 44285300060 completed SUCCESS with lint, source-free, regression, and test gates. Genuine private source-bound previously completed two-role Gemini scientific evidence for BOTH exact revised index 5 and index 9 one-activity source identities was independently re-read and verified without any new model request. The **normal worker post-review dispatch function** then invoked actual source-free course generation and real Chrome acceptance for new unadmitted 108-activity proposal c02dcdc4513a54f3cf6a04924ef76322d280081784b9d5b46f5c79021c44ef9e, returning REVISED96_AUTOMATICALLY_ADVANCED_TO_108_BROWSER_PASS, immutable exact-head browser receipt cbecf7dd5bf3212eafabd2496da792128d341a16d3630a18c55a1cab561069ee, paid calls zero, release false, exit zero. Immediate restart reverified both saved genuine roles and returned the same receipt with reusedVerifiedBrowserReceipt true, exit zero. Focused regression: 41 passed + 22 subtests; actual repo recurrence and lint checks passed. Historical original and revised roles were not resubmitted.

BSA208 was promoted to resolved in the executable recurrence registry only AFTER source-bound real browser and restart reuse evidence was recorded. This closure-metadata successor commit still requires its own exact-head CI and SHA-bound normal browser check; this does not grant scientific acceptance for the other original items, unadmitted version release or additional paid calls.

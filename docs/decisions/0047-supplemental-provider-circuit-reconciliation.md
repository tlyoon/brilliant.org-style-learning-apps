# Decision 0047 — One provider circuit across original and supplemental V3 reviews

**Date:** 17 November 2026
**Incident:** BSA-20261117-186 (code-level recurrence resolved)
**Unresolved real external incident:** BSA-20261117-183

## Reused historical evidence

Decision 0040/0041 and BSA-165/183 prohibit treating an unknown provider error as safe for other paid requests. Decision 0045/BSA-184 permits *only authenticated, captured local* parse/rubric failures to be isolated. Decision 0046/BSA-185 introduced separate, immutable single-activity review slice identities for never-submitted original Section 9.6 activities. Those prior remedies were individually useful, but a supplemental slice could fail under its new package SHA without being included in the original six-package provider-capacity scan.

## Reproduced failures before repair

1. A realistic single-activity synthetic unknown provider `ValueError` produced a supplemental `AMBIGUOUS` immutable role. The existing `provider_capacity_gate` did not accept the additional package identities. A later run could otherwise regard the original cooled provider circuit as READY while ignoring the new error.
2. A deliberately fsynced `PRE_CALL_NO_REPLAY` without a verified role/aggregate was treated as a skipped slice. The controller was able to attempt another original slice despite the prior delivery being uncertain.

Both targeted regression tests failed against the previous runtime.

## Integrated production correction

- `provider_capacity_gate` accepts only a bounded, strictly checked list of additional package SHA-256 identities derived from the unchanged frozen original-tail planner. It scans original and supplemental immutable role claims through one provider-wide denial/unclassified/cooldown circuit; duplicate identities cannot inflate counts.
- `supplemental_provider_preflight` runs in the bounded original-tail controller **on every iteration and restart**. Any unconfirmed reserved `PRE_CALL`, incomplete prior role checkpoint, provider external denial, unclassified response or still-active capacity cooldown stops new activity attempts. An authenticated captured local `PARSE_FAILED` or `RUBRIC_FAILED` with a completed uncertain aggregate remains isolatable, and genuinely untouched later content may proceed.
- The **normal** `scripts/run_v3_yoga6_recovery_worker.py --auto-advance` calls both original and supplemental read-only provider checks **before** SDK bootstrap, credential access, metadata probe or new paid request. This is executable behavior, not merely a ledger note.
- Preserve the original Section 9.6 role and its `AMBIGUOUS ValueError` as **ACTIVE**. Do not infer delivery, reclassify the error, retry it, replace a course version, lift scope admission, publish, merge, or schedule paid work based on a source-free test.

## Source-free evidence and verification

- Regression `test_supplemental_unknown_provider_fault_stops_next_original` exercises an immutable fake-Gemini-role `ValueError` after its own package SHA is reserved, followed by the provider circuit and restart controller; it must refuse new work.
- Regression `test_orphan_precall_must_stop_new_slice_until_reconciled` protects the crash/no-response boundary.
- Regression `test_normal_worker_supplemental_provider_failure_stops_before_sdk` executes the actual paid-worker entrypoint with a cooled synthetic historical ServerError plus a subsequent unknown supplemental failure, proving SDK, credentials and metadata are never reached.
- Existing `test_locally_captured_malformed_role_isolated_and_next_original_advances` is the positive control. Original frozen activity/role source hashes, 108-activity progress, academic PASS and release authorization are unaffected.

BSA-186 is a **source-free software boundary closure** only. Real Section 9.6 BSA-183 still requires independently verifiable old-provider attribution or separately authorized new-version assessment; no fabricated previous response or waived provider-wide denial is allowed.


## Further restart-negative control

The initial BSA-186 repair exposed a related issue: an existing supplemental uncertain aggregate with a local `PARSE_FAILED` role was regarded as isolatable on a later invocation even if its previously captured raw-response sidecar had disappeared. A new synthetic test removed that sidecar **only in a temporary test fixture** and reproduced an incorrect next-activity attempt. The production supplemental preflight now revalidates the local response via the existing exact hash/prompt/reviewer check on every invocation before continuing. An intact captured local error remains isolatable across restart. Both negative and positive tests passed after correction. An unsupported local-failure label is not sufficient; immutable captured evidence is mandatory.


## Ordinary course dispatcher cannot route around the tail

A third pre-fix regression established that, with the earlier original provider ServerError cooled, `plan_v3_course_review(..., continue_independent=True)` could declare a different original section `READY_FOR_AUTHORIZED_REVIEW_SESSIONS` even while an unclassified supplemental review already existed. The normal V3 dispatcher now invokes `existing_frozen_original_tail_preflight` when any historical supplemental slices or attempts exist, reusing the same exact-source preflight before selecting a new original course activity. This makes historical supplemental no-replay protection apply to both original-course dispatch and supplemental-tail dispatch, not only the fallback worker. The source-free pre-fix test failed READY; after repair it passed STOP. No old claim is replayed or edited.

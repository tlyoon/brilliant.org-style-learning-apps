# Decision 0048 — Autonomous source-free forward progress under provider STOP

**Date:** 17 November 2026
**Incident:** BSA-20261117-187
**Unresolved external incident:** BSA-20261117-183

## Root cause and historical remedy reuse

The native Yoga 6 `--auto-advance` controller previously invoked the registered BSA-173/174 language repair and the BSA-180 versioned proposal only inside an explicitly paid, eligible model-review session. The real Section 9.6 `AMBIGUOUS ValueError` now causes the existing BSA-183 / Decisions 0040–0041 provider-wide circuit to STOP *before* that controller can execute. This accidentally prevented independently safe source-free work, even though BSA-174/175/176, BSA-178/179/180, and BSA-185 had already supplied verified, idempotent, local handlers.

**It would be unsafe to turn the provider stop into READY or to replay the original Section 9.6 index 5 physics role.** The architectural correction is to separate the source-free recovery control plane from model transport, not to override the model safety gate.

## Executable contract

New `app_generator/runtime/v3_source_free_forward.py` implements a finite, Yoga 6 local-only controller. It:

1. Acquires the same OS-owned exclusive reviewer coordinator lock; recomputes the six-section 108-activity immutable roster and original evidence counters; validates any prior integrity-bound source-free receipt.
2. Invokes the previously registered and provenance-checked BSA-173/174/175/176 handler. This can stage the exact Section 9.2 corrected candidate, two-Gemini *handoff metadata*, isolated review slice, and versioned 108-activity proposal, but cannot submit a model request.
3. Independently verifies/refreshes the immutable unadmitted versioned proposal if the registered source repair was staged; all genuine model evidence remains unchanged and its actual review status is read-only.
4. When Section 9.6 is quarantined, stages the 12 individually source-hash-bound, *never-submitted* original activities 6–17 into private immutable one-activity packages. These are future review inputs only. **No PRE_CALL**, provider SDK, credential read, model QA, positive scientific verdict, paid transfer, or release is generated.
5. Re-reads and compares original SHA roster and per-category assessed/PASS/uncertain/FAIL counts; writes an atomic fsynced, SHA-checked private source-free checkpoint. Reruns are deterministic/idempotent; corrupt receipts, source changes, unauthorized handlers, and unexpected content changes STOP before accepting evidence.

The **normal** `scripts/run_v3_yoga6_recovery_worker.py --auto-advance --execute --allow-generated-text-transfer` automatically invokes source-free advancement on both original-provider and supplemental-provider circuit STOP, and when no eligible original-review section remains. An explicit `--source-free-advance` mode performs exactly these local stages on Yoga 6 without any paid flags and *rejects* combinations with paid/diagnostic modes. The default no-flag worker remains strictly read-only. This branch does not create a Windows scheduler or authorize ongoing external execution.

## Authentic source-free Yoga 6 proof

On the unchanged real 17 November Section 9.6 BSA-183 provider-stop state, `python scripts/run_v3_yoga6_recovery_worker.py --source-free-advance` returned:

- `SOURCE_FREE_BOUNDARIES_STAGED_PROVIDER_STILL_BLOCKED`
- `repairStatus=PRIVATE_REPAIR_STAGED_PENDING_TWO_GEMINI_REVIEWS`
- `proposalSha256=3b4a3dfcda78c673028646f0cf0e9d7e86e23af9498dcb008438dba66c422a82`
- 12 immutable unchanged original-tail slices prepared and independently verifiable.
- Original evidence **75/108 assessed, 72 real original Gemini consensus PASS** unchanged; zero new paid provider calls, zero new model verdicts; original ambiguous request preserved. `providerCapacity=STOP_UNCLASSIFIED_PROVIDER_REVIEW`, `publicationAuthorized=false`, `versionedScopeAdmitted=false`.

The real data are not proof that BSA-183 is resolved, that 12 activities passed review, or that a revised Section 9.6 version was authorized. Safe source-free steps now finish on the fly; actual paid Gemini content review remains restricted to genuinely authorized scope and the existing provider circuit.

## Crash/restart regression

A source-free disk-interruption test intentionally stops the third immutable original-tail package staging call after two valid immutable private packages have been created. The normal Yoga6 `--source-free-advance` entrypoint returns STOP without any paid operation, PRE_CALL or fabricated checkpoint. Reinvoking the same normal path validates and reuses the two existing immutable packages and successfully completes all twelve with the exact SHA-bound source and unchanged original model evidence. This is permanently registered as `test_source_free_tail_crash_resumes_without_paid_or_duplicate`.

## Paid-authorization negative control

The normal unchanged-original tail fallback runs the source-free controller *on the authorized Yoga 6 host before its separately scoped paid-review authorization check*. Thus a denied or expired paid charter does not needlessly stop legitimate local repair, proposal validation and original-tail input staging. The subsequent paid authorization still stops, with zero provider calls, immutable original reviewer claims untouched and no PRE_CALL reservation. The permanent `test_normal_worker_paid_auth_denial_stops_before_any_claim` verifies all twelve source-free slices can exist despite a refused paid action. No paid-authority bit is ever granted by source-free preparation.

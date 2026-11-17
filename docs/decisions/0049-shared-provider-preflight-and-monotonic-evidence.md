# Decision 0049 — Share provider preflight and enforce monotonic evidence in source-free recovery

**Date:** 17 November 2026
**Incident:** BSA-20261117-188
**Historical remedies reused:** BSA-162/163 checkpoint no-replay, BSA-183 unknown-provider mandatory stop, BSA-184 captured response attribution, BSA-186 original/supplemental shared provider circuit, BSA-187 independent source-free continuation.

## Root cause

BSA-187 correctly allowed source-free progress while genuine BSA-183 remained blocked, but its status receipt called `provider_capacity_gate(private, plan["sectionProgress"])` on only the six original course package SHAs. Supplemental frozen-original one-activity review claims and orphaned `PRE_CALL_NO_REPLAY` reservations were NOT included. The normal paid dispatcher already used BSA-186's `existing_frozen_original_tail_preflight`, so identical historical evidence could receive **STOP** in the paid worker but misleadingly **READY** in the source-free checkpoint. Separately, a properly checksummed older source-free checkpoint could replace a prior valid receipt recording higher genuine assessed/PASS counters, even with an unchanged frozen six-section 108-activity roster.

## Adversarial pre-fix proof

Three realistic tests failed **against the previous production implementation**:

- `test_normal_worker_supplemental_provider_failure_stops_before_sdk`: synthetic original provider ServerError had legitimately cooled to READY, but a subsequent one-activity supplemental `AMBIGUOUS ValueError` was ignored; source-free receipt falsely reported `providerCapacity=READY`.
- `test_source_free_orphan_precall_not_reported_provider_ready`: a durable no-replay reservation lacked a provider response; the receipt again incorrectly reported `READY`.
- `test_source_free_checkpoint_rejects_assessment_rollback`: a properly SHA-recomputed receipt representing 7 assessed/6 PASS was overwritten by the current older 6 assessed/5 PASS without raising an error. This is not a cryptographic tamper-prevention claim; source-free workflow must additionally enforce domain-level monotonicity.

## Integrated production correction

`app_generator/runtime/v3_source_free_forward.py` now **reuses the exact same shared provider checker as the paid course dispatcher**, rather than inventing a second set of provider rules:

1. After source-free staging, call `existing_frozen_original_tail_preflight(course, repo, private)`. This examines all historical supplemental slice SHA identities and orphaned reviewer reservations; unknown provider errors and missing captured parse/rubric evidence remain STOP.
2. Combine it with the original `provider_capacity_gate`: a source-free receipt may advertise provider `READY` only when **both** original and supplemental checks return `READY`. Otherwise preserve a concrete STOP, and report both component decisions read-only.
3. Validate exact source-free receipt data types, SHA-shaped package identities, a bounded 108-activity counter invariant and a bounded 12-slice preparation count. Reject original reviewed/PASS counter rollback **before** staging and again at durable checkpoint commit, even when the old receipt's digest is valid.
4. Preserve the existing finite exclusive OS owner lock, atomic fsynced checksum-bound private receipt, frozen 108 activities, original Gemini claims, source-free-only mode and all paid authorization/no-replay gates. No request is ever replayed or falsely marked PASS.

## Stress and negative controls

The registered normal-entrypoint tests assert provider STOP for captured synthetic supplemental `ValueError`, orphaned `PRE_CALL_NO_REPLAY`, lost local captured evidence and refused paid authorization, with **zero new SDK/metadata/provider calls**. Positive control: a genuinely cooled provider ServerError and clean supplemental circuit still report `READY` for source-free status without falsely blocking unrelated local progress. An exclusive-owner-lock test refuses concurrent invocation.

A new repeated-interruption matrix stops the normal source-free worker at indices **6, 11 and 17** in successive restarts, asserting immutable packages already committed survive, no completed receipt is fabricated after partial staging, no `PRE_CALL` or paid calls are created, and the final clean restart validates/stages all twelve originally untouched Section9.6 packages with exact unchanged original assessment source and reviewer bytes.

These are software engineering proofs, **not evidence that the actual Section9.6 BSA-183 unknown Google outcome has been reconciled**. The real external provider STOP remains mandatory for paid calls. Proposal admission, 108/108 model QA and final publication remain separate and ungranted.

## Real authorized-machine nonpaid regression (17 November 2026)

The corrected normal Yoga 6 worker `python scripts/run_v3_yoga6_recovery_worker.py --source-free-advance` completed on genuine private persisted assessment state, then default read-only worker reported the frozen original course status. Results: `originalProviderCapacity=STOP_UNCLASSIFIED_PROVIDER_REVIEW`, `supplementalProviderPreflight=READY`, `providerCapacity=STOP_UNCLASSIFIED_PROVIDER_REVIEW`; source-free work still completed and exact original receipt checksum `18146d6ed1a136c3126ac0df3dcd8d488ca82a33ab3ff8397288e89b5bc646b5` and version proposal SHA `3b4a3dfcda78c673028646f0cf0e9d7e86e23af9498dcb008438dba66c422a82` were unchanged from prior verified run. Twelve staged untouched original review input packages are intact. Genuine original academic ledger is **75/108 assessed, 73 fully model reviewed, 72 consensus PASS, 2 uncertain, 1 FAIL, 33 unassessed**. Zero paid Gemini calls during this test. No reviewer, source, model result, version admission or publication altered. Genuine BSA-183 external uncertainty remains active and unreconciled.

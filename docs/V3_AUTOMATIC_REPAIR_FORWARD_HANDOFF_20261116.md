# Bosla V3: source-free repair and immediate forward handoff (16 November 2026)

**Incident:** BSA-20261116-174. **Owner contract:** detect and classify a blocker; reuse or develop a safe remedy; stress-test; integrate into the normal executable workflow; persist the recovery; immediately advance to the next eligible development/QA stage while retaining finite retry, paid-operations and QA boundaries.

## Reproduced integration failure

Prior BSA-173 successfully detected two Thai Unicode characters accidentally embedded in the Malay prompt of Section 9.2 activity 14, and staged a hash-addressed private corrected candidate. This used a one-off development command. Prior BSA-172 implemented a bounded multi-activity forward worker, but it only dispatched reviews and did NOT stage the already verified repair automatically.

## Normal executable remedy

The normal scripts/run_v3_yoga6_recovery_worker.py --auto-advance now passes the source-free app_generator/runtime/v3_auto_repair.py stage as a callback into the existing app_generator/runtime/v3_forward_progress.py whole-run lock. The callback runs before dispatching any new eligible model activity.

It accepts only the known, reviewed failure. The frozen Section 9.2 package must have original SHA-256 cfe7bab820aa01ce71bd7a6a334c742101ebd10d8895cccd5f05d599030f971c. The exact activity ID act-int-iso-05 and position 13 must contain precisely two Thai Unicode characters U+0E40 and U+0E25 in the specific Malay question. The original exact-package assessment file must contain two distinct named Gemini API reviewers (physics and semantics), both confirming trilingualMeaning FAIL and three other dimensions PASS. Unknown parent, unknown new damage, missing/foreign/contradictory model evidence, or changed source stops instead of guessing.

On this exact evidence only, the normal worker invokes the existing v3_versioned_text_repair implementation. It verifies the corrected candidate SHA-256 49a7f18c7cc2b7c00e0b6b23838cca1ed7fe52262384e0c26bbc8360fa3e9174 and seven affected Malay text fields. The immutable private receipt is stored idempotently; a restart recognizes identical bytes but refuses any conflicting private package or receipt. The old package and FAIL verdict are never changed.

The recovery stage is durably recorded using the existing forward progress checkpoint status STAGED_VERSIONED_CANDIDATE_PENDING_FRESH_MODEL_QA before any new model dispatch. The controller re-reads and compares every frozen roster/assessment counter to ensure repair staging has not been misreported as completed reviewer work. It then proceeds automatically to the next eligible independently authorized model activity, currently within Section 9.5, **within the same running process**.

## Stress tests and limits

Nine source-free, adversarial v3_auto_repair tests exercise real original frozen source bytes and synthetic reviewer receipts (explicitly not real model evidence): identical idempotent restarts, absent reviewer, contradictory review, non-Gemini reviewer, changed parent, unknown corruption and tampered candidate. Thirty forward-progress tests exercise the normal callback-before-review order, the authorization gate, crash/no-replay, forged success, finite full-course simulations, concurrent worker lock and authorized next-section progression. One Windows symlink creation test is skipped on hosts without permission to create symlinks. Real Yoga 6 private reviewer role/provider names were independently checked read-only, and the exact known candidate was re-recognized without any paid call. Run the permanent regression and exact-commit CI suite before claiming production integration.

The forward driver still requires BOTH --execute and --allow-generated-text-transfer explicitly; it bounds 1-6 activities, elapsed time and provider retries. No Windows scheduled task or background agent has been recreated. After an authorized process exits, the next invocation can resume from a checkpoint but the computer does not autonomously restart the process. No claim of background continuation is made.

## Scientific and release state

The correct original source-bound model assessment remains 52/108 activities attempted, 51 fully independently reviewed, 50 unanimous PASS, one Section 9.1 historic ambiguous AI_UNCERTAIN that must not be replayed, and one original Section 9.2 language AI_REPAIR_REQUIRED. The newly staged Section 9.2 candidate is NOT admitted into the frozen 108-scope, and has no fresh two-Gemini QA. All 56 remaining unassessed original activities, genuine revised candidate QA/admission, keyed Batch API live provenance, exact accepted-artifact accessibility/privacy checks and final release receipt remain outstanding. This milestone neither requests paid Gemini operations nor merges/publishes the app.

## Atomic repair checkpoint hardening (BSA-20261116-175)

The prior private staging code created the final package SHA directory before writing the two files. Power loss after the first file could leave an incomplete final identity that was rejected forever on restart. The corrected storage code now writes both fsynced files into a new, same-filesystem temporary directory and atomically promotes that completed directory by rename. An abandoned precommit temporary stage is not a final candidate and does not block recovery; conflicting files in an existing final SHA directory are never silently overwritten. Two new adversarial tests cover failure exactly before rename and a simulated orphaned crash directory. The normal BSA-174 worker uses this same shared storage helper and inherits the fix. The private candidate remains pending genuine Gemini QA and publication remains unauthorized.

## CI portability recurrence (BSA-20261116-176)

Hosted GitHub Actions run #714 exposed that the original frozen Section 9.2 file is stored with Windows CRLF byte SHA-256 cfe7bab820aa01ce71bd7a6a334c742101ebd10d8895cccd5f05d599030f971c, whereas the Linux Git checkout uses LF byte SHA-256 327c9ae8add51fd95eb0d970ff89d3473c37965d232f5f51da7d051108301802. Its canonical Git blob SHA-1 is 779deb4e207078f9081a9de78a14226d473f9b25. The prior BSA-20261107-127 accepted exactly these two byte renderings while rejecting modified/mixed content. New BSA-174 had inadvertently reintroduced Windows-raw-SHA-only matching. Rather than weakening checks, the repair stage now reuses the existing frozen SHA plus Git blob validator, and records the actual local artifact digest separately from the archival parent digest so original per-host immutable assessment IDs still match. Positive LF/CRLF and negative mixed-EOL regressions are mandatory in CI. No historical review is changed or new model PASS inferred.

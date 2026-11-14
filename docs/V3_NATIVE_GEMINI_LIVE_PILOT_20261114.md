# BOSLA native Gemini V3 — genuine one-activity pilot (2026-11-14)

**Project:** tlyoon/brilliant.org-style-learning-apps  
**Milestone:** First genuine source-free Gemini API assessment of frozen Chapter 9  
**Execution revision:** `9b570101dc23375b5277ef8055ba4673f7507348` (draft PR #223, unmerged)  
**Device:** HP (Windows), independently configured Google credentials  
**Model:** `gemini-3.8-flash`; 2 distinct one-shot SDK reviewer contexts per activity

## Directly verified live outcome

The ordinary `scripts/run_v3_native_gemini_review.py` was invoked with both
`--execute` and `--allow-generated-text-transfer`, `--batch-size 1`,
`--max-batches 1`, using an exact frozen Chapter 9 package and its default
machine-local private checkpoint. Both reviewer requests were created through
`advance_v3_course_review` and the existing V3 source-free assessment engine.
The invocation completed exit code 0 (151.29 seconds).

The read-only assessment result after execution showed:

- `selectedSection=section-9-1`
- `activitiesAssessedRows=1`, `activitiesFullyModelReviewed=1`
- `modelConsensusPassActivities=1`
- `modelUncertainActivities=0`, `modelRepairRequiredActivities=0`
- `dispatchStatus=READY_FOR_AUTHORIZED_REVIEW_SESSIONS`
- `publicationAuthorized=false`

Private evidence was inspected **only as metadata**: two per-role claims,
both `COMPLETE`, each with `providerId=gemini_api`; one aggregate review
with `status=AI_CONSENSUS_PASS` and both provider IDs `gemini_api`;
no leftover run lock. Model output text, prompt bodies, credentials,
raw PDFs and private source records were not copied into the repository.

The independent reviewer identities distinguish **separate SDK contexts**,
not independent providers or an external scientific verification. This
result verifies real model transport, checkpoint integrity and automated
consensus for one generated activity, not physics correctness, full multilingual
semantic validation, learner acceptance, or publication readiness.

## Runtime blocker and reusable remedy

A separate first attempt on Dell-115 stopped before any review claim with
`STOP_NATIVE_GEMINI_REVIEW` / `AttributeError`. Its global Python had
`google-genai==1.4.0` and lacked the SDK's `HttpRetryOptions`; the repository
already pinned `google-genai==2.25.0`. No private review root, claim, model
result or lock was created on Dell. An attempted isolated dependency
installation encountered a DNS-resolution failure; no ambiguous model
request was retried.

An already-compatible HP worker had `google-genai==2.28.0`, two configured
key candidates and no existing role claims for this new private root.
HP then completed the genuine one-activity run described above.

In the follow-on draft code, BSA-20261114-164 integrates the remedy into the
normal native CLI: detect missing SDK no-retry support before constructing
model clients, select a compatible ignored project `.venv` if available,
or perform one bounded pip installation of the **already pinned project**
dependencies in that isolated venv, then delegate exactly once. A recursion
guard and no-retry pip option prevent loops; if network or dependency repair
fails, no model request is sent. The core native SDK factory now rejects
an unsupported SDK before key discovery. This follow-on code was not
present in the already-completed live activity, and remains on draft PR #223.

## Validation boundary and next step

The BSA-164 source-free tests validate the normal CLI delegation and safe
failure paths, while existing V3 stress tests cover immutable role claims and
non-replay. A hosted exact-head CI and a live execution on the new code
revision remain separate requirements; do not credit synthetic results as
genuine academic acceptance.

The first activity is genuine, but the chapter-wide review remains incomplete.
The normal course planner must resume from stored exact-package claims,
never re-send activity 1, and stop on genuine uncertainty or an academic
FAIL. No release receipt is granted by this pilot.

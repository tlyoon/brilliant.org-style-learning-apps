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

## Follow-on genuine checkpoint continuation: Activity 2

A second independently authorized normal CLI invocation used the same
frozen local checkout and **same default machine-private state root**, with
the same one-activity limit. It did not replay activity 1. Actual runtime
was 326.66 seconds. The resulting course status was:

- `activitiesAssessedRows=2`, `activitiesFullyModelReviewed=1`
- `modelConsensusPassActivities=1`, `modelUncertainActivities=1`
- `dispatchStatus=STOP_UNRECONCILED_MODEL_REVIEW`
- `publicationAuthorized=false` (process exit code 1)

Private metadata inspection confirmed activity 2
(`act-mcq-02-si-units`) has a physics-role claim
`AMBIGUOUS` / `reasonCode=ServerError`, while the second
Gemini role is `COMPLETE`. The aggregate status is
`AI_UNCERTAIN`. Both reviewer contexts were created on the configured
Gemini API transport; no leftover run lock was found. The first
activity's two `COMPLETE` claims and consensus PASS remain intact.

The SDK error class alone cannot establish whether Google's service
accepted the first activity-2 request. **Do not automatically resubmit
that request, rotate credentials to replay it, or mark the aggregate
as PASS.** The existing course dispatcher stops safely before opening
another Gemini session. This is a genuine unresolved provider-side
dependency, not evidence that both reviewers failed, and not an SDK
version mismatch. Independent, source-free engineering validation may
continue while provider reconciliation or a versioned review policy
is developed. No chapter-wide release eligibility is asserted.

## Decision 0040 genuine independent continuation — Section 9.2

A newly implemented **quarantine-aware** V3 native runner was checked against
the existing HP private frozen-course state, which still contained the
Section 9.1 activity-2 `ServerError`. The read-only normal CLI selected
`section-9-2`, listed `section-9-1` under `quarantinedSections`, and
left `publicationAuthorized=false`. Historical source/request identities
were not rewritten.

**Genuine execution:** On the first Decision-0040 source revision
`fdf17b848a4b9dc000247d97297b44fc70c1ca65` (draft PR #223),
the normal `run_v3_native_gemini_review.py` was invoked again
with `--execute --allow-generated-text-transfer --batch-size 1
--max-batches 1`. It selected **Section 9.2 activity 1**, not the
quarantined Section 9.1 activity. The genuine run exited **0** after
488.11 seconds. It added one fully model-reviewed, consensus-PASS activity.

A separate **read-only metadata inspection** after the run and update to
the later draft revision `81455a59be921db403f385bc1a3c7294dab75809`
confirmed all six role claim files:

- Section 9.1 activity 1: physics `COMPLETE`, semantics `COMPLETE`;
- Section 9.1 activity 2: physics **`AMBIGUOUS` / `ServerError`**,
  semantics `COMPLETE` — **unchanged**;
- Section 9.2 activity 1: physics `COMPLETE`, semantics `COMPLETE`,
  both with `providerId=gemini_api`.

No run locks remained. The course now records
`activitiesAssessedRows=3`, `activitiesFullyModelReviewed=2`,
`modelConsensusPassActivities=2`, `modelUncertainActivities=1`,
`quarantinedSections=["section-9-1"]`, and
`dispatchStatus=READY_FOR_AUTHORIZED_REVIEW_SESSIONS` for the next
eligible independent activity. The release flag remains false.

**What this establishes:** Real independent-section continuation and
immutability of the original uncertain request were observed on HP.
This is not a successful reconciliation of the original Google request
and not an academic, multilingual, learner-pilot or release certification.
The later runtime revisions added stronger global active-lock and
external-denial checks, verified separately by deterministic regressions;
the live result should not be misattributed to those later changes.

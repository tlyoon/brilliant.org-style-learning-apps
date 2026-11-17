# V3 Batch-to-Reviewer-Checkpoint Adoption — 17 November 2026

**Incident:** BSA-20261117-181. **Owner scope:** Bosla V3, Yoga 6 only. **Status:** Source-free executable adapter stress-tested; genuine authenticated Batch job trial NOT performed or authorized by this milestone.

## Root cause

BSA-20261115-171 already implemented Google Gemini's documented file-backed keyed JSONL Batch protocol, immutable SUBMITTING/AMBIGUOUS journal, exact provider job identifier, read-only job GET and checked file download. However `reconcile_keyed_sdk_job` stopped after **mapping provider rows** back to activity/role pairs. It explicitly returned `modelRowsAccepted=false`, with no verified step to parse Gemini text candidates through the existing BOSLA V3 rubric or import authenticated responses into private `v3-review-<package>-<activity>-<role>.json` role claims. Without that bridge, a successful real Batch job would not advance any assessed V3 activity.

## Production adapter added

`app_generator/gemini/v3_batch_claim_adoption.py::adopt_verified_keyed_batch_one_activity` is now available through the existing normal Batch recovery module as `app_generator/gemini/v3_batch_recovery.py::reconcile_submitted_v3_review_batch`.

The adapter is intentionally limited to **one separately versioned, unique-package review activity**, two distinct `physics` and `semantics` Gemini roles, and one previously registered provider job. The caller must supply its own previously authorized SDK client plus explicit `provider_reconciliation_authorized=True`; the adapter makes **only** provider `batches.get` and `files.download` calls, never `batches.create`, `files.upload`, credential rotation, or model `generate_content` calls. It requires:

1. Exact private-root BatchJournal, verified manifest, provider-job ID/display name and complete keyed result roster; no matching by provider output order.
2. Exact local review-package SHA and both independently computed `make_prompt` SHA values bound to the original Batch manifest. Historical synchronous Section 9.1 ServerError claims remain ineligible.
3. The documented Gemini `GenerateContentResponse.candidates[0].content.parts[0].text` result shape, with **exactly one candidate**, exactly one text part, and `finishReason=STOP`. A partial, blocked, multimodal, malformed, duplicate-key or provider-error row fails; provider SUCCEEDED alone never becomes academic PASS.
4. Both raw response texts passed through BOSLA's original strict `_parse_response` (all four physics/language/visual/learner dimensions, rationales, counterexample and activity ID). Two role-specific assessments are independently combined by the existing `_review_consensus` and revalidated by `assessment_progress`.
5. Exclusive existing per-package `.active-review.lock` and private `RunContext` store. Before writing any claims, reject conflicting original, ambiguous, stale, differently sourced or mismatched role evidence. On a crash between role writes, authenticated **read-only** GET/downloading the same job can idempotently finish importing the other role. Existing full assessment is never overwritten. Finally the standard `assess_with_models` engine is run with offline-only dummy conversations to prove it can reconstruct the exact cached outcome **without any model request**.
6. Output explicitly keeps `wholeCourseScopeAdmitted=false` and `publicationAuthorized=false` even if two model outputs form a consensus PASS. Genuine pass means only evidence attributed to authenticated provider response, NOT externally validated physics truth or permission to publish.

Provider shape/source checked against official Google docs: https://ai.google.dev/gemini-api/docs/batch-api and https://ai.google.dev/api/batch-api. File-backed JSONL keyed echo and `candidates.content.parts` are documented there.

## Source-free stress test and actual Yoga 6 provider readiness

New `tests/test_v3_batch_claim_adoption.py` includes 13 fully synthetic, **no-network** cases: reversed output-row order; normal module dispatch; no authorization; job RUNNING/ERROR; invalid finish reason/text/multimodal candidates; genuine rubric FAIL under mixed synthetic model perspectives; unknown prompt/package; preexisting historical AMBIGUOUS role; a conflicting result; interruption after the first locally imported role and idempotent next-run completion; and a competing native review lock. Together with prior 19 keyed-file and 23 Batch journal tests, this provides 55 source-free tests of the Batch transport and claim-adoption code. **No fake model output is counted toward the genuine V3 acceptance total.**

A separate owner-device **metadata-only** Yoga 6 run of the normal `run_v3_yoga6_recovery_worker.py --diagnose-only` returned `DIAGNOSTIC_READY_SOURCE_FREE_ONLY`, Google HTTP 200 on configured credential candidate index 1, and provider status READY. This is a real connectivity/metadata observation, **not Batch job creation or validated new review results**. The original genuine reviewer totals therefore remain 52/108 attempted, 51 fully reviewed, 50 model-consensus PASS, one original Section 9.1 unresolved, one original Section 9.2 FAIL, 56 original unassessed. The next independently eligible original activity is Section 9.5.

## Remaining mandatory acceptance

The five true boundaries **are not all closed**: new genuine two-Gemini review of the 56 remaining original activities; provider-safe resolution/replacement (never replay) of original Section 9.1; fresh two-Gemini review and separately admitted exact revised scope of Section 9.2; a specifically authorized **live** keyed Batch pilot to verify Google provider echo/job output semantics if Batch is used; and full exact accepted-artifact scientific/EN-MS-ZH/visual/accessibility/browser/privacy/release evidence. The original frozen Chapter 9 browser campaign is terminal under the approved `docs/acceptance_closure_chapter9.json`; it must NOT be silently restarted or reset simply because this code changed.

The user-retired Windows task `BoslaYoga6V3Recovery` remains absent. No automated paid call, Batch create, publication or merge was initiated. Follow-up real model work remains under explicitly authorized bounded invocations; no background process is promised after this chat.

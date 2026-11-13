# V3 native Gemini source-free stress campaign — 13 November 2026

**Project:** BOSLA / brilliant.org-style-learning-apps
**Milestone:** Decision 0039 native Gemini API workflow hardening
**Incident:** BSA-20261113-162
**Execution:** Yoga 6, offline deterministic synthetic SDK clients and fake
Chapter 7 course packages. All private checkpoint directories were created
only inside disposable test temporary folders. Actual frozen Chapter 9
content and all prior private production state were NEVER modified.

## Objective and independent-verification boundary

Exercise the real normal V3 `advance_v3_course_review` dispatcher, shared
`advance_v3_generated_text` engine, package-hash validation, persisted
reviewer claims, two one-shot native Gemini SDK clients, strict
four-dimensional assessment rubric and read-only course readiness. Stress
inputs must be clearly marked SYNTHETIC: they are not Google API responses,
independent academic acceptance, live model connectivity, source-quality
proof, release authorization or learner-pilot evidence.

Tests run under `tests/test_v3_native_gemini_stress.py`, automatically
discovered by the normal CI test suite. They reuse the same 6-section
18-activities-per-section shape as original Chapter 9, but **use entirely
fake Chapter 7 activities**. Each reviewer client generates synthetic
valid JSON using `FakeReviewer`; no `google.genai` API network request,
browser, ChatGPT reviewer, credential read, PDF or student record.

## Executed stress scenarios

| Scenario | Source-free observed result |
| --- | --- |
| Full 6×18 activities | All 108 activities assessed and 108 synthetic two-model consensus PASS rows captured; exactly 216 fake SDK model calls; exactly 216 distinct SDK instances each closed once. All 6 section boundaries traversed. One extra dispatcher invocation made **zero** further calls. Final disposition: `PENDING_DETERMINISTIC_RELEASE_EVIDENCE`, not publication PASS |
| Partial loss at activity 32 | 31 two-role PASS reviews captured. Simulated timeout on the second role of activity 32: exactly 64 requests total, 32 aggregate rows, 31 fully model-reviewed activities, `STOP_UNRECONCILED_MODEL_REVIEW`. Four resume attempts submitted **zero** new calls |
| Adversarial `FAIL` | One activity with both roles captured, one dimension FAIL: one fully model-reviewed row but zero consensus-PASS, and `STOP_VERSIONED_CONTENT_REPAIR_REQUIRED`. Later invocations sent no requests |
| Crash after role claim | Simulated process `KeyboardInterrupt` after saving `IN_FLIGHT` for first role but before aggregate. A new process-level review attempt would previously see `READY_FOR_AUTHORIZED_REVIEW_SESSIONS`. Corrected read-only planner now returns `STOP_UNRECONCILED_MODEL_REVIEW` and no new clients or calls. Real request count stays at one synthetic dispatched call |
| Two simultaneous workers | First worker paused during first SDK request; second worker assessed same private scope. Second returned `STOP_UNRECONCILED_MODEL_REVIEW` without creating an SDK client; first subsequently completed exactly two calls and one aggregate row |
| Orphan run lock | Preexisting lock blocked a second review with `V3_REVIEW_RUN_OWNERSHIP_UNCERTAIN`. Its contents remained unchanged. Removing *only the synthetic test lock* allowed safe execution. Production locks must never be deleted without independent ownership/reconciliation |
| Provider provenance tampering | Changed cached `providerId` from Gemini API to ChatGPT. Both read-only plan and execution failed closed before any additional calls |
| Frozen package drift | Mutated synthetic package bytes; exact frozen-candidate identity preflight failed before constructing the provider or private checkpoint |
| Provider fault matrix | Simulated Gemini HTTP 401, 429, 503 errors, malformed JSON and empty model text. Every scenario stopped as `STOP_UNRECONCILED_MODEL_REVIEW`; repeated attempts made zero new calls. Private checkpoint JSON did not expose synthetic secret-bearing error strings |

## Reproduced failure and permanent normal-pipeline fix

**Before the fix:** The normal V3 planner only inspected package-level
`v3-assessment-<sha>` aggregate rows. An actual reviewer request is first
persisted as an immutable per-role `IN_FLIGHT` claim; process loss before the
aggregate meant no row existed for the activity. The pre-fix adversarial test
reproduced a false `READY_FOR_AUTHORIZED_REVIEW_SESSIONS` after this crash.

**After the fix:** `app_generator/validation/v3_course_readiness.py`
checks the exact next-unaggregated-activity role claim files for the frozen
package. The read-only check validates package SHA, activity ID, role index,
claim state, safe file path and bounded size. Non-`COMPLETE` claims
(`IN_FLIGHT`, `AMBIGUOUS`, `BLOCKED_EXTERNAL`,
`SKIPPED_UNSENT`) are reported as `unreconciledRoleClaims`. The normal
`app_generator/runtime/v3_course_review.py` dispatcher stops **before**
creating Gemini clients if any such claim exists. No further call is
possible from the normal runner until external reconciliation or a
legitimate versioned content repair. Persisted complete claims are not
misclassified as unresolved.

**Registry:** `docs/recurrence_registry.json` now records
`BSA-20261113-162` against the actual normal runtime path and adversarial
stress regressions. This is a permanent code-level rule, not a ChatGPT-only
instruction or a script that fixes one PDF.

## Acceptance boundary and next legitimate milestone

The stress campaign verifies deterministic execution behavior, **not**
live Gemini API availability, quota, billing, independent science,
trilingual meaning, learner utility, or a release receipt. It must never
change the genuine Section 9.1–9.6 review count, currently 0/108, or set
`publicationAuthorized=true`.

The next separate step is an independently owner-initiated, authorized
native Google Gemini API one-activity run using the protected local
credentials and configured model. Any genuine provider error must be
captured and classified without replaying an ambiguous request, and its
distinct permanent remedy must have a normal-path regression. The
previously reported ChatGPT browser/connector denial remains separate
and must not be evaded via the remote tool.

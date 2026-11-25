# V3 six-section versioned acceptance proposal — BSA-20261117-180

**Date:** 17 November 2026. **Repository:** Bosla / brilliant.org-style-learning-apps, draft PR #223. **Host:** Yoga 6, source-free and no paid Gemini operation.

## Root cause and milestone

The original V3 frozen 108-activity roster has genuine independent Gemini assessments on only some activities. BSA-173/174 repaired the original Section 9.2 Malay-language defect in a private 18-activity candidate, BSA-178 prepared a two-role QA handoff, and BSA-179 prepared an **isolated single-activity** review package so the other 17 unchanged Section 9.2 activities need not be resubmitted. However, the project still had no reproducible way to represent the corrected 108-activity course while preserving genuine reviews of exactly unchanged material or to distinguish a *proposal* from an approved course version.

## Executable solution

`app_generator/runtime/v3_versioned_acceptance_scope.py::prepare_versioned_course_proposal` now performs a deterministic read-only V3 evidence audit and writes a **private immutable proposal**:

- Revalidates the owner's frozen six-section roster (6 × 18 = 108), approved exact hashes and legitimate checkout EOL variation, the previous corrected activity/handoff/one-activity slice, and genuine original two-Gemini checkpoint reports through Bosla's existing strict V3 validator.
- Verifies the replacement Section 9.2 package has the same 18 activity IDs and **exactly one changed activity**, `act-int-iso-05` at zero-based index 13. The other 17 activities are checked for exact equality, not merely matching titles or positions.
- Enumerates only original `AI_CONSENSUS_PASS` activities whose individual content is exactly unchanged, with original source package digest, activity digest and reviewer receipt digest. This is labeled **POTENTIALLY_REUSABLE_NOT_RELEASE_ACCEPTED**. The old FAIL is never imported as PASS; the old Section 9.1 uncertain role remains blocked.
- Reads genuine revised single-activity reviewer evidence, if it exists in a later authorized run, using `assessment_progress` against the exact isolated slice package. A corrected PASS, FAIL or uncertain verdict updates the *proposed* snapshot; it cannot by itself admit the new course or authorize public release. Fake/invalid reviewer reports fail closed.
- Fsyncs the source-free manifest to an exclusive same-volume staging directory and atomically promotes it under the SHA-256 of its own payload. A newer genuine assessment produces a **new snapshot identity**, leaving the earlier snapshot intact; corruption and partial writes are not overwritten. No prompts, learner data, reviewer rationale, PDF content, credentials or model requests are stored in the manifest.
- The **normal** `app_generator/runtime/v3_recovery_policy.py` now performs this next eligible non-paid step automatically after a verified content repair, two-role handoff and isolated review slice. The one-shot authorized review process continues to advance separately eligible frozen material under its established finite model/circuit/authorization limits. No Windows scheduled task is created.

## Authentic source-free Yoga 6 result

A genuine read-only source-free run on the owner's existing Yoga 6 reviewer records created proposal SHA `1f99b2143c2057e3954622b1bd9c0668dd5a0476ccf3ae7b74fe2cedd325b02b`, with **50 independently recorded genuine original consensus PASS activities potentially reusable**, six sections totaling 108 activities, and exactly one different Section 9.2 package hash. The current original V3 status is 52/108 attempted, 51 fully reviewed, 50 consensus PASS, 1 original Section 9.1 ambiguous AI_UNCERTAIN, 1 original Section 9.2 AI_REPAIR_REQUIRED, 56 original unassessed. Corrected isolated activity has zero genuine new reviewer replies. Next separately eligible original activity remains Section 9.5. The proposed version is **NOT ADMITTED**; publication remains unauthorized. No original section or review was overwritten.

## Verification and boundaries

Dedicated source-free tests verify six-section 108 identity, exactly-one patch, immutable unchanged activity IDs, no fabricated PASS from an absent model record, forgery rejection, crash at atomic manifest promotion and restart, idempotence, isolation from original review counts, and synthetic two-context Gemini reviewer PASS/FAIL scenarios using Bosla's actual V3 checkpoint engine. These model results are **synthetic test fixtures, not genuine scientific evidence**; they prove only the future re-evaluation logic will rederive an updated proposal rather than silently keep outdated counts.

This engineering milestone does not close V3 release. Actual outstanding requirements include independent Gemini QA for the corrected activity, 56 original unassessed activities, safe evidence-based resolution of the historical Section 9.1 uncertainty **without replay of the ambiguous request**, genuine validation of any revised 108-activity scope, successful exact-artifact visual/accessibility/privacy/browser assessment, the authenticated keyed Batch provider pilot if used, and valid technical release receipt and separate publication permission. The user-retired `BoslaYoga6V3Recovery` Windows scheduled task remains absent. All paid model calls must still pass established explicit authorization and finite limits.

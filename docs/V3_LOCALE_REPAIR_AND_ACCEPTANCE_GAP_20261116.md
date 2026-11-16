# Bosla V3 — genuine Section 9.2 language failure and private versioned repair

Date: 16 November 2026. Incident BSA-20261116-173; draft PR #223.

## Source-grounded failure

The true, existing two-Gemini V3 reviewer evidence for Section 9.2, activity index 13 (human ordinal 14; ID act-int-iso-05) contains a unanimous FAIL for trilingualMeaning. Both reviewers independently found THAI Unicode codepoints U+0E40 and U+0E25 embedded in the Malay question. Both reviewers passed physicsAnswer, visualValue and accessibleLearnerExperience. This real two-reviewer FAIL cannot be rewritten, inferred away, or replayed using the original frozen SHA.

The frozen parent package SHA-256 is cfe7bab820aa01ce71bd7a6a334c742101ebd10d8895cccd5f05d599030f971c. Its 18 activities and all historical model checkpoints remain unchanged.

## Reusable normal-path fix

The source-free app_generator/validation/v3_locale_script_integrity.py scans localized activity text, returns only activity IDs / field paths / Unicode codepoints, tolerates mathematical Greek symbols and correct Chinese locale text, and rejects inappropriate Thai/Cyrillic/Arabic/other foreign scripts and replacement glyphs. app_generator/runtime/v3_course_review.py runs it before eligible Gemini reviewer dispatch. It quarantines the malformed section without submitting new content to the model or blocking other genuinely eligible sections. app_generator/runtime/v3_yoga6_recovery.py persists codepoint counts by section through the normal atomic source-free status record.

Across all nine retained Section 9.* content package files, the real source-free scan found only the two Thai glyphs in this one Malay prompt. Section 9.2 is already quarantined by a genuine content FAIL. Section 9.5 is independently eligible.

## Exact-parent private corrected candidate

The generic app_generator/validation/v3_versioned_text_repair.py creates a source-free, reproducible candidate without modifying the parent. The localized Section 9.2 proposal used three reviewer-grounded substitutions to remove the corrupted noun, replace an unnatural borrowed/garbled sled noun throughout Malay text, and correct a separate Malay deceleration typo. This revised *one* activity changes seven Malay localized fields, with eight substring replacements. Every other activity and English/Chinese field is byte-for-byte semantically unchanged within its parsed structure; the source package bytes are unchanged.

The new candidate SHA-256 is 49a7f18c7cc2b7c00e0b6b23838cca1ed7fe52262384e0c26bbc8360fa3e9174. It is stored only under the owner-controlled local %LOCALAPPDATA%/Microvid/BoslaV3ReviewYoga6/repair-proposals/section-9-2/<new candidate SHA> folder, alongside a source-free pending-review receipt. Private candidate identity is idempotently checked on restart and conflicting or tampered file contents are rejected. Original 18-activity content schema validation on the new private candidate returned 0 errors; locale script scan returned 0 findings.

**This candidate has NOT been reviewed by new Gemini sessions** and is NOT admitted as the frozen V3 source, which remains immutable. Fresh two-Gemini-model adversarial review, a separately versioned authorized course scope, and all exact-candidate deterministic release gates are still necessary. A stored repair proposal cannot be used to claim a reviewer PASS.

## Remaining acceptance requirement inventory

- Frozen Chapter 9: 108 approved activity IDs; 52 assessed, 51 with both Gemini responses, 50 unanimous model-consensus PASS. One original 9.1 provider-ambiguous activity remains AI_UNCERTAIN; one 9.2 language issue remains AI_REPAIR_REQUIRED.
- Remaining 56 unassessed original activities are pending genuine Gemini two-context review. No scheduled task remains on Yoga 6. ChatGPT's remote tool has NOT initiated paid Google operations as part of this repair.
- The original Section 9.1 provider request has no attributable job ID for safe reconciliation; it cannot be silently repeated. A genuinely new separately versioned scope is required if replacement is contemplated, rather than resetting its old ambiguous role claims.
- The private Section 9.2 correction must receive fresh real model evidence and be admitted with explicit versioning without deleting the parent. Existing Batch keyed JSONL response matching remains mock-verified, not an authenticated response-to-V3-checkpoint adoption.
- Final automated V3 release demands valid two-context scientific/translation/visual/accessibility assessment of each accepted version, exact-head tests, source-free browser/privacy/accessibility checks, and exact-package release receipt. Publication remains unauthorized; this work does not auto-merge or distribute third-party/source material.

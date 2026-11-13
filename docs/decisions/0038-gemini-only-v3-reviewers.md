# Decision 0038 — Gemini-only V3 academic assessment

**Status:** Binding BOSLA owner decision, 13 November 2026.
**Transport refinement:** Decision 0039 now permits the native `gemini_api` transport in addition to the former `gemini_browser`. Both remain Google Gemini, with two separate role contexts and no ChatGPT reviewers. The older browser-only descriptions below are historical and must be read under Decision 0039.
**Scope:** The V3 two-context generated-activity assessment engine,
course dispatcher, private review checkpoint, and automatic release validator.
This decision narrows Decision 0036's provider allowance; all other V3
requirements and Decisions 0028/0037 remain in force.

## Binding change

The two V3 adversarial reviewer contexts **must both be Gemini**. Use two
distinct, fresh, role-isolated Gemini conversations, not a Gemini+ChatGPT
pair and not ChatGPT-only. A single previously authorized Gemini Google
account may host the two separately owned conversation tabs; separate
provider accounts are not required. Independence refers to role, prompt,
conversation context and session identity, not separate companies.

* The only permitted V3 reviewer provider is `gemini_browser`.
  `chatgpt_browser`, mixed pairs, unknown providers, missing provider
  provenance and any ChatGPT fallback are forbidden.
* Each actual supplied session must carry explicit
  `provider_id="gemini_browser"`. The V3 engine and the normal
  `advance_v3_generated_text` bridge validate BOTH session providers
  before a request, run lock or private checkpoint can be created.
* Write provider identity into each immutable per-role request claim and
  each assessment response. The same exact-provider requirement applies
  to resumed checkpoints, read-only course status and automatic
  release-receipt verification. Unattributed legacy review records are
  **not** silently promoted or assumed to be Gemini.
* The existing `V3ExistingLoginSessions` uses a verified, exclusive,
  authorized Gemini profile, two distinct new conversations and
  generated activity JSON only; no textbook PDFs, third-party assets,
  learner records, credential extraction, model switching, or ChatGPT.
* All review findings remain advisory model judgments, and the existing
  strict four-dimension consensus, bounded 1–6 review cadence, immutable
  no-replay rule, source privacy and deterministic CI/browser release
  checks stay mandatory.

## Root-cause finding versus hypothesis

The previous current V3 contract allowed both Gemini and ChatGPT. This
created provider ambiguity and permitted a ChatGPT or mixed pair to be
submitted and recorded as valid V3 evidence. The corrected code prohibits
this path. **The earlier external platform denial has not been shown to
originate from ChatGPT**. It concerned a rejected authenticated browser
operation; removing ChatGPT as a provider does not grant permission to
rerun that operation. No tool, account, device, script wrapper or prompt
may be substituted to evade that denial. A separately approved platform
execution decision is still required before the first real model call.

## Normal pipeline and regression protection

The ordinary `app_generator/validation/autonomous_completion.py`
`load_policy`, `assess_with_models`, `_validate_cached_review`,
`assessment_progress`, and `verify_automated_release_assessment`
consume the same Gemini-only rule. The shared
`app_generator/runtime/v3_authorized_review.py` checks reviewer
provider identities before creating run state. The normal
`app_generator/runtime/v3_course_review.py` dispatches via that bridge,
using the source-free Gemini-only provider when externally approved.

Register this incident with a real normal-entrypoint `automaticRemedy`
and tests for wrong provider, mixed provider, missing provenance,
tampered cached verdict, and forbidden release. Exact-head CI must pass.
Synthetic Gemini-tagged test doubles prove enforcement, never genuine
Gemini output or live session authorization. Preserve
`PENDING_AUTOMATED_ASSESSMENT` and 0/108 genuine Chapter 9 reviews
until actual approved Gemini responses are verified.

# Decision 0036 — Autonomous AI technical completion, no mandatory manual sign-off

**Provider amendment (13 November 2026):** Owner Decision 0038 (`0038-gemini-only-v3-reviewers.md`) narrows only the V3 review provider choice to **two distinct Gemini browser conversations, never ChatGPT**. The strict active policy and all assessment/release logic enforce the explicit `gemini_browser` identity. Other Decision 0036 requirements remain unchanged; this does not unblock the previous platform-denied browser execution.\n\n**Owner-directed amendment:** 11 November 2026. **Status:** Binding for current
BOSLA technical completion and release eligibility. Supersedes earlier
Decisions 0032–0035 **only** where they made independent educational-content
validation, independently certified meaningful visuals, real learner-pilot
evidence, or an explicit per-release owner approval mandatory. Decision 0033's
permanent removal of textbook-edition, rights-holder and technical rights gate
remains in force. Historical original Chapter 9 campaign attempts remain frozen
and are not automatically restarted.

## Current executable contract

The current technical acceptance authority is
`docs/autonomous_completion_v3.json`, enforced by
`app_generator/validation/autonomous_completion.py` and the common
`app_generator/runtime/academic_release.py::enforce_academic_release_gate`.
Its name is `AUTONOMOUS_AI_TECHNICAL_COMPLETION_V3`.

**The following are NOT mandatory technical completion gates:**

1. Independent human or outside educational-content/physics/EN-MS-ZH review.
2. Independently validated meaningful diagrams or a quota of visual assets.
3. Evidence from an approved real-student classroom or learner pilot.
4. A separate manual/explicit release authorization after the code satisfies
   the applicable automatic software acceptance checks.
5. Textbook edition, legal rights-holder identification, or
   `sourceAndFigureRights` approval.

None of those may be reintroduced as an equivalently named hidden manual gate.
This changes **the required mechanism**, not the importance of physics or
translation correctness, valid answers, useful illustrations, or accessibility.
A zero-visual/text-first activity is acceptable when an AI reviewer supplies
a justified pedagogical rationale; an image is not required for every item.

## Fully autonomous replacement mechanism

1. Every activity in a selected exact-SHA-256 generated package is submitted to
   **two distinct adversarial LLM review contexts**, using bounded, explicit
   roles (physical counterexamples; trilingual back-translation and learner
   concerns) and a strict four-dimension JSON schema:
   `physicsAnswer`, `trilingualMeaning`, `visualValue`,
   `accessibleLearnerExperience`. Prompts treat activity text as untrusted
   data and require substantive rationales and a physical counterexample.
2. Both models must say PASS on every dimension for every activity; FAIL
   triggers a versioned automatic repair decision, while UNCERTAIN, malformed,
   missing, conflicting or uncaptured responses remain pending. No self-written
   single-line `PASS` field or incomplete package can authorize publication.
3. Requests are bounded at six activities per invocation with distinct
   reviewer sessions and run-context IN_FLIGHT/COMPLETE/AMBIGUOUS checkpoints.
   An ambiguous remotely submitted prompt is **never blindly replayed**.
   Continuations proceed on remaining eligible work without asking for a
   manual academic sign-off.
4. Deterministic software evidence is still required: exact package digest,
   successful exact-head CI, browser accessibility checks and source-free
   privacy/no-exfiltration tests. These are machine-operational checks, not
   real learner pilot or independent academic review requirements.
5. The shared public merge/deployment and standalone release builder consume
   the same private, locally attested exact-artifact V3 release receipt. Once
   all AI and deterministic evidence passes, the technical release decision
   is **automatic**, without a second human authorization gate. Missing or
   stale receipts cause `PENDING_AUTOMATED_ASSESSMENT`, not silent approval.
   Each private receipt has a locally created HMAC attestation to prevent
   accidental or casual cross-run editing/replay; this is not a claim of
   cryptographic independent academic verification.

This is a **model-assessed technical confidence threshold**, not actual
independent scientific proof, institutional certification, or a claim that
real students were piloted. The model can make mistakes. The public app must
not describe its outputs as independently validated, teacher-approved or
trial-proven solely because the V3 gate passed.

## Operational limits are not technical clearance gates

This amendment authorizes automated LLM review of the **generated activity
text** through an already-authorized Gemini-only transport (Decision 0038), but does
not authorize transmission of the original textbook PDFs, copied figures,
protected external source extracts, real student identities or confidential
institutional records. Such operation-level constraints are not a disguised
requirement to identify the textbook's edition/rightsholder or obtain a
technical rights-PASS.

The established frozen Chapter 9 V2 charter remains read-only historical
evidence at `docs/acceptance_closure_chapter9.json` and
`python scripts/check_final_acceptance_closure.py --historical-v2`.
It records the real old terminal attempts but is not the current V3 technical
acceptance policy. The ordinary checker without that flag reads V3.

The V3 policy **does not automatically publish anything merely by being
adopted**. LLM responses, full coverage, exact-head CI and software-test
results must actually exist; until they do, the status is
`PENDING_AUTOMATED_ASSESSMENT`, with
`publicationAuthorized=false`. No fabricated model answers, fake CI
statuses or private-user content transmissions are permitted. A release
decision may be generated without a separate explicit approval, but actual
publisher operations must still follow account access controls, permitted
assets and applicable law. This is a separation of operational constraints
from technical acceptance, not a resurrection of removed rights gates.

## Implementation and test entrypoints

- `app_generator/validation/autonomous_completion.py`: binding V3 policy,
  adversarial prompts, bounded model-response checking, exact activity
  coverage, consensus, resumable stages and automatic release derivation.
- `app_generator/runtime/academic_release.py`: normal publisher gate.
- `app_generator/publishing/public.py`: existing public publisher using the
  normal V3 gate.
- `scripts/build_public_release.py`: alternative bundle path using the same
  common release gate, not the historical V2 frozen publication decision.
- `scripts/check_final_acceptance_closure.py`: current V3 status; optional
  historical V2 archive inspection.
- `tests/test_autonomous_completion_v3.py` and the updated publication
  regressions: model disagreement, missing evidence, changed package,
  tampered receipt, no mandatory human review, no real pilot, text-first
  content and automatic eligibility on fully satisfied artificial test data.

**Execution limitation at this decision's creation:** The current chat has
not performed real Gemini-only V3 assessments of the six original draft
Chapter 9 packages. The direct authenticated-browser assessment-runner step
was blocked by the available tool environment. Do not claim otherwise.
The provider-neutral engine can be called by a connected, authorized LLM
adapter; until a verified adapter executes all activity reviews, V3 remains
pending. No direct model invocation/response receipt is invented to fill it.

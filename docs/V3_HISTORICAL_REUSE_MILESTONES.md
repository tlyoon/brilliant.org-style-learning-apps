# BOSLA V3 — verified reuse map for the three next milestones

Status: 12 November 2026. Project-specific history was checked against Git
commits, `docs/FAILURE_TO_FIX_LEDGER.md`, `AGENTS.md` and current source.
This is not a new authorization to run an external provider, restart frozen
source/PDF campaigns or publish material.

## Milestone 1: generated-text-only two-context execution

| Historical incident / evidence | Reusable, already coded | What must not be assumed |
| --- | --- | --- |
| BSA-20261026-019/-021, BSA-20261028-031/-041 | Browser profiles require real login and exclusive ownership; directory existence is not proof of authentication | None of the older profile roots establishes a currently authorized V3 transport |
| BSA-20261026-022, BSA-20261029-044, BSA-20261030-046 and BSA-20261031-053 | Existing-login Gemini `ReviewerSession` interface, fresh owned tabs, protected restored tabs, bounded pre-submission redirect handling | `ExistingLoginReviewerFactory` *requires* original PDF attachment and belongs to closed historical campaigns. Do not invoke it as a V3 adapter |
| BSA-20261026-023, BSA-20261029-042, BSA-20261030-047/-050/-052, BSA-20261031-057 | Strict response JSON/diagnostics, immutable request claims, unsent-role circuit and read-only reconciliation | Historical captured JSON or source-bound 7/10 verdicts cannot substitute for new V3 four-dimension reviewer responses |
| BSA-20261103-099, Decision 0028 | A rejected host operation is terminal; do not replay, reword or route through another device | The previously denied direct authenticated model runner remains blocked; no permission is inferred from source code |
| BSA-20261111-147, BSA-20261112-148/-150/-151 | Generated activity only, two role contexts, exact package/prompt digests, six-item checkpoint resume, immutable denial, trustworthy release evidence | The V3 engine has not yet received genuine two-context verdicts for the original Chapter 9 activities |
| BSA-20261112-152 | **New canonical provider-neutral service** `app_generator/runtime/v3_authorized_review.py::advance_v3_generated_text` integrates the existing `RunContext` and `assess_with_models`; it uses stable off-repository per-package private state, bounded 1–6 activity calls, an exclusive run lock, no-repeat restart, and privacy-safe status | The service accepts only externally supplied already-authorized sessions. It does not open Chrome, authenticate, transmit PDFs, invent provider access, or itself provide model inference |

**Next genuine dependency:** A *separately authorized and already functional*
Gemini/ChatGPT generated-text-only reviewer session provider. Any connected
provider should supply two distinct `ReviewerSession`-compatible objects with
`conversation.ask(prompt, stage=...)`, clear permission for generated-activity
text transfer, and distinct session identities. It may then call the canonical
service with `max_activities=1` for the first actual activity. A new browser
runner must not be created to avoid the earlier denial.

## Milestone 2: six Chapter 9 sections, 108 genuine V3 reviews

- **Reuse:** the existing six unchanged
  `content/chapter-9/section-9-[1..6]/package.json` (18 activities each),
  mode-aware canonical identity (BSA-149), bounded full-package checkpoint
  progression (BSA-148), and automatic circuits/claim integrity (BSA-150).
- **Reuse for *diagnostics*, not V3 signoff:** historical source/PDF location
  receipts and academic v5 results from BSA-20261029-043 and later campaigns.
  Those original-PDF campaigns are terminal and were bound to different
  source/version/criteria. No replay, no importing old PASS fields.
- **Required new real evidence:** every generated activity gets both V3 model
  reviews, all four criteria checked, and any model-identified repair followed
  by a new *versioned* assessment of the changed package. The service cannot
  convert synthetic regression data into genuine 108/108 coverage.

## Milestone 3: six-section learner and release candidate

- **Already available engineering slice:** BSA-20261111-145/-146, Decisions
  0034/0035; six-concept prerequisite planner plus actual checked-answer-event
  bridge for the six draft sections. The RC1 Chrome/Node journey tests used
  **synthetic** packages and no real student data.
- **Already available deterministic QA:** six Section 9 packages pass content
  schema; local source-free browser screens/keyboard capture and SHA-based
  staging families exist from earlier pilot work. Historical Chapter 9
  browser/source campaigns must not be restarted.
- **Already available release plumbing:** one shared publisher gate with exact
  package/reviewer-prompt/receipt integrity (BSA-151), local bundle builder,
  per-commit hosted CI and recurrence registry. PR #223 remains draft/unmerged.
- **Actual completion still requires** the V3 real model evidence and current
  exact-head deterministic CI/browser/privacy proofs, an integration decision
  for the open draft PR chain, and lawful/public-operation compliance. Do not
  claim classroom-pilot, independent scientific or accessibility certification
  based on software tests.

## Engineering acceptance for BSA-152 (source-free only)

`tests/test_v3_authorized_execution_bridge.py` must reproduce:
1. No allowed generated-text transfer or missing reviewer sessions causes no
   checkpoint/file writes or remote requests.
2. An authorized *injected synthetic* two-role interface advances exactly
   one activity and resumes 6+1 more from the same private package-hash state
   with zero duplicate submissions after completion.
3. Missing/unsafe private roots, invalid batch limits, occupied run lock and
   corrupted saved prompt digest fail before sending any new model request.
4. Six **actual repository package identities** are structurally usable but
   cannot be model-assessed without sessions; no original PDF or browser
   access is performed by this smoke test.

This is a meaningful **internal execution integration** milestone, not a
completed external reviewer-transport or release milestone. Continue to use
`PENDING_AUTOMATED_ASSESSMENT` and **0/108 actual V3 reviews** until new
legitimate provider evidence exists.

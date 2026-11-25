# Decision 0039 — Native local Gemini API review worker (no ChatGPT reviewer or remote execution dependency)

**Date:** 13 November 2026
**Status:** Binding BOSLA development contract, refining Decisions 0036–0038.
**Scope:** V3 generated-activity-only automated review and normal runtime
dispatch. The historical frozen V2 evidence and other app generation stages
are outside this narrow amendment.

## Problem and root cause

The old V3 course executor provided role-specific reviewer prompts and
immutable checkpoints but accepted only `gemini_browser`. Its optional
Selenium factory could be invoked indirectly from a ChatGPT remote desktop
session. When no external browser sessions were supplied, the executor
returned its OWN `BLOCKED_EXTERNAL_REVIEW_TRANSPORT` status, which was
repeatedly misdescribed as a confirmed fresh OpenAI refusal. The original
historical host denial had no preserved first-party error/arguments and
cannot establish that today's Gemini-only operation is prohibited.

A normal BOSLA generation/assessment program should not require ChatGPT
to invoke a connected computer for every model request. Instead, when an
owner operates an independently authorized local workflow on their own
machine, BOSLA must call Google's Gemini API directly from within that
local worker. This architecture does not constitute permission to replay
any specifically blocked ChatGPT tool operation by another route.

## Binding implementation

- **Both reviewers must be Google Gemini.** The strict V3 policy allows
  `gemini_api` (new first-class native transport) and `gemini_browser`
  (previously validated independent-browser path). `chatgpt_browser`,
  other providers, and missing provider provenance remain forbidden.
  The **default new local worker is API only**; there is no automatic
  browser or ChatGPT fallback after a Gemini API failure.
- Review roles remain `physics-adversary` and
  `language-and-learner-adversary`. Each assessed **activity** opens two distinct
  source-free Gemini SDK clients and fresh stateless reviewer contexts;
  separate session and reviewer IDs remain mandatory. This is
  independent *conversation context*, not independent vendors,
  independent credentials or a guarantee of model impartiality.
- The only model input is the generated-activity adversarial text
  produced by V3 `make_prompt`. No original PDF, source figure,
  learner identity, external scraped content or browser credential may
  enter the request. The SDK must request JSON text, and the existing
  strict V3 four-dimension verdict parser is the acceptance authority.
- The SDK client uses the project's existing authorized Google key
  discovery outside Git and **disables SDK automatic retries**. It
  selects one configured key for a bounded batch with no uncheckpointed
  model preflight and no automatic key or model fallback. An attempted
  request is latched BEFORE dispatch; an uncertain response is recorded
  as `AMBIGUOUS` by the existing per-role checkpoint and is NEVER
  replayed from a new process. No source-bearing API client or browser
  Gem/PDF editor is reused.
- All roles and requests remain bound to the immutable package digest,
  prompt hash, `providerId`, activity ID, role index and private
  single-writer checkpoint. The V3 engine rejects provider drift in a
  resumed claim and checks `gemini_api` provenance at read-only course
  status and private release-verification time. Unlabeled old reviews
  stay untrusted. A separate genuine browser/CI/privacy acceptance
  proof is still needed before any technical release receipt; native
  API completion alone does not publish an app.
- The normal course-level dispatch
  `advance_v3_course_review(...,session_factory=...)` is unchanged
  apart from accepting the additional Gemini provenance value. This
  centralizes bounded progress, stale/uncertain-stop rules and
  source-only privacy checks rather than maintaining a second
  assessor. Neither ChatGPT nor Remote Desktop Commander is required
  for **ordinary locally initiated reviewer requests**.
- The standalone CLI `scripts/run_v3_native_gemini_review.py`
  defaults to **read-only** status with no imports of Google SDK,
  credentials, private writes or model calls. The account holder
  explicitly opts into an independent native Google request with
  BOTH `--execute` and `--allow-generated-text-transfer`.
  A default invocation assesses at most 1 activity. CLI `--batch-size`
  groups 1–6 **separate one-activity sessions** per bounded batch,
  and `--max-batches` up to 108 permits autonomous progress if each
  genuine model response is accepted. The course dispatcher rejects
  `max_activities>1` for a one-shot native session factory *before*
  any API client is created; one Gemini request is never resubmitted.
  A FAIL/UNCERTAIN or ambiguous call stops further work without replay.

## Authorization and non-evasion boundary

Direct independently owner-executed Google API requests rely on
Google's ordinary credentials/terms/billing, and do not require an
ongoing ChatGPT conversation or ChatGPT remote tool permission.
Nevertheless, this **does not authorize** any previously denied
ChatGPT/Remote Desktop Commander operation or justify a remote
assistant invoking the new CLI to disguise that operation.
The new code must NOT be used to obtain a different execution route
for an operation known to remain denied. No live Gemini API call
was performed by the code integration milestone; actual provider
availability, Gemini model identifier, account/billing, and real
Chapter 9 academic results remain unverified until a properly
permitted independent local execution.

The older Decision 0028 exact-denial/no-bypass safeguards remain
binding when the blocked task is genuinely the same. The optional
support escalation/runbook is only relevant to execution actions
actually refused by the ChatGPT or Remote Desktop Commander platform;
it is not a mandatory BOSLA model-review prerequisite.

## Regression protection and release truth

- Synthetic independent SDK clients prove two distinct roles and
  requests, allowed provider policy, JSON-only API transport,
  no PDF attachment, no retries/model fallback, generated-text transfer
  gate, no-send dry run and immutable private checkpoint behavior.
- Injected failure and malformed response must yield UNCERTAIN or
  `STOP_UNRECONCILED_MODEL_REVIEW`, not fake AI PASS.
- Synthetic native Gemini API results are checked using the SAME
  `verify_automated_release_assessment` gate as browser Gemini;
  tampering the `providerId` to ChatGPT must fail.
- Reuse the normal recurrence registry/CI as a durable prevention
  mechanism, not a workaround script.
- Real Chapter 9 course remains `PENDING_AUTOMATED_ASSESSMENT`,
  0/108 genuine Gemini reviews, unpublished until verified authentic
  responses and deterministic release evidence exist.

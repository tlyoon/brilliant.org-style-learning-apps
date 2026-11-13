# External execution denial — authorized recovery runbook

This runbook applies to the Brilliant-style learning app. Before evaluating any action, establish the exact Git head, original PDF digest, candidate package digest, current authorizations and prior evidence receipts.

## Classify before action

| Observed failure | Classification | Required handling |
|---|---|---|
| Python unit test fails or times out | Code/environment failure | Preserve failing test/stack; use bounded diagnostics, not a security-denial record |
| Browser login or permissions fail | Authentication or session issue | Inspect state; do not send model requests until authorized |
| An external tool explicitly denies execution | `BLOCKED_EXTERNAL` | Record denial; do not retry, reword or reroute the same blocked operation |
| Provider request may have been sent | `IN_FLIGHT` / `AMBIGUOUS` | Preserve immutable evidence; never blindly replay |
| Original-source/science evidence is missing | Academic `REVIEW_REQUIRED` | Continue independent authorized review; never fabricate PASS |

## Gemini API versus upstream execution refusal (4 November 2026)

Use [the boundary-aware Gemini denial audit](GEMINI_EXECUTION_DENIAL_INTEGRATION_20261104.md)
to classify a reported host-level refusal independently of an actual Gemini
provider HTTP result. A host/connector block is **not** a Gemini HTTP 403,
and it cannot authorize credential rotation, command rewording or execution
through a different route. No historical original denial payload has been
independently recovered in the project. The metadata-only tool never sends
a request, reads credentials or grants permission.

The shared Python client now propagates typed `ExternalExecutionDenied`
through source-free key selection and source-bearing generation, without
replay. A previously denied upstream operation still requires an **approved
execution decision** from the relevant platform authority, separately from
the user's ordinary permission.

## Exact v11 science boundary

The last verified academic matrix contained 18 source locations verified and 0/18 formal academic PASS. Exact-v11 MCQ and collision-property receipts were accepted. The 30 browser screenshots cannot establish visual scientific semantics. Reviewer-claim and technical visual-coverage audits had not produced accepted v11 receipts at the last checkpoint. Do not equate an empty *current-version* reviewer roster to proof that earlier requests were never sent.

## Metadata-only CLI

The CLI stores hashes and bounded event identifiers only; it never invokes another tool, connects to GitHub, runs a source audit, calls Gemini or provides authorization.

```text
python scripts/plan_external_execution_recovery.py init --source-sha256 <SOURCE_SHA256> --package-sha256 <PACKAGE_SHA256> --out <NEW_PRIVATE_JSON>
python scripts/plan_external_execution_recovery.py plan --state <PRIVATE_CHECKPOINT_JSON>
python scripts/plan_external_execution_recovery.py deny --state <PRIOR_PRIVATE_JSON> --out <NEW_PRIVATE_JSON> --task visual_receipt_verify --event-id <EVENT_ID> --denial-class SECURITY_CONTROL --tool-class REMOTE_DESKTOP
python scripts/plan_external_execution_recovery.py receipt --state <PRIOR_PRIVATE_JSON> --out <NEW_PRIVATE_JSON> --task source_verify --event-id <EVENT_ID> --receipt-sha256 <TRUSTED_RECEIPT_SHA256>
```

Do not submit a `deny` transition until the associated operation was actually denied. Do not submit a `receipt` transition until independently accepted evidence exists. Each transition writes a new local private file; it cannot overwrite an old checkpoint. A receipt digest is not a scientific verification or permission grant. A blocked operation remains terminal for its exact-version checkpoint; `plan` only identifies genuinely independent work that may separately be authorized.

## Escalate without leaking private data

Provide the project/workstream name, approximate date/time, affected connected application, operation category, generic denial message, bounded event ID, Git head, and whether app-specific permissions were already granted. Ask the relevant provider/support channel which **approved** execution method supports the desired legitimate operation. Do not include arbitrary shell commands, student files, original PDFs, source excerpts, Gemini responses, credentials, Chrome cookies or OAuth tokens.

## Durable safeguards

- Fixed canonical task IDs; SHA-256 fingerprints bind operation intent to exact original source/package.
- Immutable event records reject duplicate attempts, aliases, forged receipts, malformed data and changed event order.
- The event chain is a checksum, not a signature. Pin chain-head hashes independently if tamper-resistance is required.
- Unit tests for failure isolation are part of ordinary CI, protected by Decision 0027 regression-registration requirements.
- The scheduler never grants authorization or changes `git_auto_merge=false`, `git_publish=false`, academic PASS or release controls.
- Do not use this mechanism to bypass a platform's explicit denial or an access restriction.

## Next development tasks

After CI validation of this draft code, perform an authorized private initial-checkpoint integration, preserving historic-denial records in a separate audit trail if the authorizing environment requires it. Then return to the independently admissible exact-v11 academic tasks. Neither a green CI result nor this document authorizes source-content publication or a merge.

## Permanent first-party escalation workflow for Gemini-only V3 (13 November 2026)

**Authority boundary:** An owner request, a locally constructed permission
Boolean, source-free green CI and an app-level `Allow all actions` setting
do NOT create approval for a formerly denied authenticated browser operation.
A stale historical denial report without the original client error/tool
arguments cannot be used to invoke the exact-call review panel or to assert
that Gemini has refused a current request. Never create a new wrapper,
switch devices/accounts/models, or submit a probe merely to manufacture a
reviewable denial. The binding V3 provider is **Gemini only** (Decision 0038).

**Approved escalation channels:**

- For an actual **fresh** Remote Desktop Commander client-side refusal before
  the action reaches Yoga 6, if one **unchanged** retry was stopped too, use
  the connector's `review_device_call` first-party review control with the
  exact refused tool name, unchanged arguments and actual client error. The
  control only asks the user to review the original call; it cannot itself
  override or submit a denied operation. Never use it for a historical
  refusal without those exact details, a timeout, or an account failure.
- Otherwise, request the independently authorized execution path through
  **OpenAI Support**, officially reached via the chat bubble at
  https://help.openai.com/ (see
  https://help.openai.com/en/articles/6614161-how-can-i-contact-support).
  File the support case through the account holder's signed-in Help Center;
  repository issue comments and locally prepared support messages are **not**
  actual submissions. Include affected conversation, approximate original
  date/time/timezone, sanitized bounded operation, device/tool name and
  actual error/correlation ID if preserved. Do not include private source,
  password, browser token, personal data or raw student content.
- The account holder can use the private Yoga 6 support packet
  `V3_GEMINI_ONLY_OPENAI_SUPPORT_SUBMISSION_20261113.md` (private Yoga 6 project-continuity folder).
  It is marked **PREPARED, NOT SUBMITTED** until a real support case receipt
  is received. A support request alone is **not** an execution grant.

**One reusable decision instead of repeated manual fixes:** Request a durable,
scope-specific statement whether the existing `advance_v3_course_review`
normal dispatcher may run authenticated Gemini-only generated-text reviews
for initial batch size 1 followed by finite 1–6 batches on the same authorized
profile. Preserve actual approval scope, permitted tool, case/decision ID,
expiry and revocation conditions outside Git. If approved, a caller may
supply its separately verified authorized `V3ExistingLoginSessions`; retain
all package, transfer, two-context, no-replay and release checks. If
pending/denied/uncertain, return `BLOCKED_EXTERNAL_REVIEW_TRANSPORT`
without a browser launch or fabricated V3 verdict. Support staff, not this
repository, determine whether any approval is reusable across runs.

**Historical case caveat:** First-party details for the original reported
authenticated-browser denial were not preserved, so the project cannot
prove that the 13 November Gemini-only operation is currently denied or that
ChatGPT caused the denial. A source-free offline preflight on Yoga 6 has
already verified the *canonical* `scripts.sync_configured_workstation`
configuration, existing unoccupied Gemini profile, Selenium import and
normal source-free recurrence checks. Calling the generic synchronization
renderer without `configure_core()` produces a misleading
`[compatibility]` error; the correct production path passes. Do not
introduce a second config-renderer workaround.

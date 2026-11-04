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

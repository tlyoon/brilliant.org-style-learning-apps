# Gemini execution denial: boundary-aware recovery (4 November 2026)

**Scope:** General project implementation in draft [PR #223](https://github.com/tlyoon/brilliant.org-style-learning-apps/pull/223), not an attempt to override ChatGPT/Remote Desktop Commander policy, run a new Gemini probe, repeat a source-bearing request or reopen the Decision 0029 two-round campaign.

## Historical facts and evidence limit

- Earlier source-free requests reached Google's Gemini API and returned **HTTP 402** on the selected project/model. That is an **actual provider response** and may support automatic testing of a distinct, already configured key *only within a previously authorized, new source-free preflight*.
- A later source-free authenticated remote request was **reported** as denied by execution safety controls *before tool invocation*. The original complete first-party denial payload and incident/correlation identifier are **not available** in this project's retained evidence. A report of a pre-tool denial is not a new Gemini HTTP 403 or proof that the first API key failed.
- The user's approval to run a source-free test on Yoga 6 is explicit. Remote Desktop Commander has previously reported app-specific **Allow all actions**, with its directories still limited to `G:\\My Drive` and `%LOCALAPPDATA%\\Microvid`. Those app/user permissions do not independently authorize bypassing an upstream execution restriction.
- The current source-free client safely handles up to eight distinct credentials, 401/402/403/503/504 rotations, 429 fail-closed, and no source replay. Its synthetic tests and SDK-shape checks do **not** verify today's real account access.

## Codebase improvement: separate failures by origin

The new shared `ExternalExecutionDenied` exception prevents an upstream host/connector refusal from being mistaken for a Google HTTP 403 just because a wrapper supplies `status_code=403`. Source-free credential selection **must propagate the denial immediately**, without switching keys or trying a different route.

The PDF-bearing `GeminiApiClient.ask()` also preserves that typed upstream denial and leaves its unresolved-call latch set; it cannot retry the same possibly submitted PDF from the same client. Other original provider transport policies are unchanged.

A strictly structured, nonexecuting classifier lives at `app_generator/validation/gemini_execution_boundary.py`. It separates:

| Supplied origin | Stage | Safe classification |
|---|---|---|
| Host or connector denied before dispatch | Source-free | `BLOCKED_EXTERNAL`; no key rotation, no provider status |
| Provider returned 401/402/403/503/504 | Source-free | Eligible **within an already authorized existing preflight**; the classifier does not call or authorize one |
| Provider returned 429, 400 or an unknown status | Source-free | Stop; do not silently rotate |
| Any provider response after a source-bearing attempt | PDF generation | Reconcile original request, never automatically replay |
| Unknown dispatch outcome | Either | Assume it *may* have been sent; preserve evidence and stop |

The classifier never reads raw tool logs, account numbers, source PDFs, keys, local config or .env. It validates exact nonsecret metadata fields, rejects contradictory combinations and never asserts that user-supplied metadata is an independently verified provider receipt. The metadata-only CLI prints only a sanitized JSON result.

## Safe example for an earlier reported pre-tool refusal

```powershell
python scripts/triage_gemini_execution_boundary.py --origin HOST_OR_CONNECTOR --stage SOURCE_FREE_PREFLIGHT --dispatch DENIED_BEFORE_EXECUTION
```

The output is `BLOCKED_EXTERNAL` and `unblocksExistingDeniedOperation=false`. It **does not contact Gemini or remove the upstream restriction**. A true prior provider HTTP 402 should instead be represented as `--origin GEMINI_PROVIDER --dispatch STARTED --provider-http-status 402`, with evidence level `HISTORICAL_REPORT` unless genuine original receipt verification exists. Never change an event's origin to obtain a more convenient outcome.

## Escalation and effective unblock boundary

The original remote executor/policy owner must supply an approved authorization path or a new, independently permitted execution decision. The code cannot create such a grant or override the host safety check. The previously prepared private support packet on Yoga 6 is `%LOCALAPPDATA%\\Microvid\\GEMINI_API_EXECUTION_DENIAL_SUPPORT_REQUEST_20261104.md`; it contains no API key values or protected PDF content. Do not run the originally denied operation under a reworded script, another device, another connector, or a modified execution policy.

A positive **new** authorized source-free response through the existing shared key-selection client is required to verify live key rotation. The independent three-PDF C3/C4 acceptance is a distinct, separately authorized task; no campaign round reset or publication.

## Regression obligation

- `tests/test_gemini_execution_boundary.py` provides eleven source-free synthetic negative controls against confusion of a host refusal and provider HTTP status, accidental key rotation, source-bearing replay, unverified receipts and secret-bearing metadata.
- `tests/test_gemini_api_client.py` verifies that a typed upstream refusal after SDK entry remains typed and latched (no retry).
- `BSA-20261104-111` is registered with the permanent regression contract.
- The codebase outcome is **FAILURE CLASSIFICATION AND NO-REPLAY HANDLING IMPLEMENTED**, not **PLATFORM DENIAL LIFTED**. Exact-head hosted CI is required to substantiate implementation.

No live Gemini API request, source-PDF submission, credentials disclosure, Git merge, or publication was performed in this repair.

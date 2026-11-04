# Gemini API gateway source-replay safety — 4 November 2026

**Status:** Shared-code repair and isolated source-free tests verified; **full hosted CI NOT VERIFIED** on this exact commit; no live Gemini account request, held-out PDF run, merge or publication.

## General defect and correction

- Existing production key fallback selects from distinct credentials in the authorized Windows `%LOCALAPPDATA%\\Microvid\\.env` during a source-free preflight; a controlled PDF is never sent to candidate fallback keys while selecting them.
- A gap remained: the **already-submitted** PDF model call retried some transient errors (network timeouts/resets, HTTP 408/409 and 5xx) despite the established no-replay guarantee. Replaying these after an ambiguous response could duplicate provider work and bypass run-state reconciliation.
- Updated `app_generator/llm/gemini_api.py`: one model invocation per source-bearing stage; the SDK retry setting is one for API-key and OAuth/Vertex clients; any error or empty output leaves a client-level unresolved-request latch. A second `ask()` on the same client is rejected, including after an interrupt; normal successful stages continue to work. HTTP 402 reports a billing/payment restriction without falsely asserting depleted credit.
- This is provider-wide transport safety, not a repair tuned to one physics PDF. The finite Decision 0029 two-round trial remains terminally `BLOCKED_EXTERNAL`, and the frozen second-round evidence is not reinterpreted under the new revision.

## Reproducible focused evidence

- Source branch: draft [PR #223](https://github.com/tlyoon/brilliant.org-style-learning-apps/pull/223).
- Verified application/documentation head **before this report:** `569984c2bd0e3f5bcf66a1988cf7c6c69042df33`.
- Local authorized test location: an isolated, disposable copy within Yoga 6's existing permitted `C:\Users\User\AppData\Local\Microvid` directory, **not** the protected BrilliantContentGenerator worktree.
- Command: `python -B -m unittest discover -s tests -p 'test_gemini*.py' -v`.
- Result observed in Desktop Commander process output: **Ran 33 tests in 0.276s — OK**.
- Only `gemini_api.py`, `gemini_key_failover.py`, `errors.py`, the two corresponding test modules and a **minimal stub `app_generator.config`** were copied. No original PDF, OAuth material, local `.env` contents, or credential value was transferred; FakeSdk provided all provider responses. This is a **focused isolated suite**, not a claim that the full repository CI ran.

## Guardrails and next action

Incident `BSA-20261104-108` is registered in `docs/recurrence_registry.json` and protected in `scripts/check_regression_contract.py`. Its regressions cover timeouts, HTTP 408/409/500/502, empty output, interruption and successful multiple stages.

Hosted GitHub Actions has **not** returned a workflow run for the latest source edits at the time of this record. The last previously verified hosted result (#438) was for an **older** commit and must not be used as exact-head approval. PR #223 stays draft/unmerged and no public deployment is authorized.

When legitimate CI can be triggered and reviewed, run the full repository validation and inspect compatibility with the real SDK without initiating an authenticated provider request. An actual Gemini-key fallback demonstration remains separately blocked by the earlier execution-control denial and cannot be inferred from these fake-SDK tests.

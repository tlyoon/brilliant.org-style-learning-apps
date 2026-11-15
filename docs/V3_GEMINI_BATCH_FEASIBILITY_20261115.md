# Step 3 assessment — Gemini Batch API for BOSLA V3 (2026-11-15)

**Status: architecture assessed; no batch content submitted and no batch acceptance claimed.** This note implements the assessment component of the owner's five-step Decision 0042 while Step 1/2 runtime recovery is being verified.

## Provider availability and relevance

Google documents `gemini-3.8-flash` as Batch API-capable:
https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash
The Batch API queues `batchGenerateContent` jobs and returns durable provider job identities (`batches/{batchId}`), with inlined requests/responses or a JSONL file:
https://ai.google.dev/api/batch-api
Google's batch rate limits are separate from interactive limits; per-project limits and billing/usage tier must still be verified:
https://ai.google.dev/gemini-api/docs/rate-limits
Google describes batch workloads as asynchronous/offline, with a target around 24 hours and reduced token cost, not an instant fix or guaranteed acceptance:
https://ai.google.dev/gemini-api/docs/optimization
Google's provider forum notes that 503 indicates overloaded capacity rather than the same condition as 429 quota:
https://discuss.ai.google.dev/t/handling-429-503-errors-from-the-gemini-api/124640

## BOSLA-specific fit

108 activities × two adversarial reviewer contexts yield **216 logical review requests** for fully unreviewed content. Each request must remain bound to exact frozen course / package digest, activity ID, perspective (physics vs multilingual learner semantics), prompt hash and reviewer identity. Existing Section 9.1 `AMBIGUOUS` claims must remain excluded; switching from synchronous API to batch **cannot** replay or implicitly reconcile them.

A safe future implementation requires:

1. A source-free, dry-run-only batch manifest with deterministic job key, package/activity/role/prompt hashes and no PDF/student data. A verified package is selected by the same frozen-course planner. No batch is submitted as part of this assessment.
2. At most one provider batch CREATE per immutable job. Persist `PREPARED` and `SUBMITTING` *before* HTTP call; on a returned job name, persist `SUBMITTED` and that precise provider ID. On an interrupted/ambiguous create, do **not** create it again; reconcile via existing provider job listing/get, where attributable.
3. Separate GET/poll workers with finite poll intervals and backoff. A persistent `batches/{batchId}` handles reconnection after ChatGPT or Windows restart. An expired/cancelled/partial result is not PASS.
4. Map each response only to its original input row and role; verify exact hashes and invoke the existing V3 decision parser and two-role consensus engine. No synthetic PASS, and no role result borrowed from another batch or previous package version.
5. Only after source-free acceptance and workload quota review, run a small **new** two-role activity batch as a bounded authenticated pilot on **Yoga 6**. Missing Google permission/capacity, model-specific batch limits, or unresolved job creation are stop conditions; neither HP claims nor the older Yoga 6 Section 9.1 ambiguous request can be replayed.

## Decision

**Pursue Batch API as a follow-up engineering candidate, not as an automatic fallback for an already submitted request.** The model and APIs exist, but this repository's current V3 checkpoint engine is synchronous; a batch adapter must be built and independently tested before requesting live throughput. Meanwhile, Step 4 application/browser work can proceed from frozen source-free fixtures independently of both synchronous Gemini and batch availability. This recommendation should not relax the original draft/unmerged and no-publication contract.

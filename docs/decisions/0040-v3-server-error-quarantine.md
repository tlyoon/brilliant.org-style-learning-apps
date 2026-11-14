# Decision 0040 — Quarantine ambiguous Gemini review; recover independent work

**Status:** Owner-requested and implemented in draft PR #223, 14 November 2026.
This is a local refinement of Decisions 0027, 0028, 0037–0039; it does not
authorize publication, model-request replay, additional providers or source-PDF
transfer.

## Historic incidents reused

- **BSA-20261104-104**: a source-free 503/504 probe could identify another
  credential, but a submitted source-bearing request must never be replayed
  with that credential.
- **BSA-20261104-108**: remove unsafe automatic retries for ambiguous submitted
  5xx/timeout source calls; preserve request outcome and stop on uncertainty.
- **BSA-20261113-162/163**: read-only planner must detect role claims without
  aggregates and corrupted future-index claims *before* opening reviewer
  contexts; no restart may resubmit an in-flight request.
- **BSA-20261114-164**: a stale local Google SDK can be repaired before model
  dispatch by bounded project-local environment selection; no global Python
  change or invocation loop.

## Real blocker

On HP, the frozen Chapter 9.1 first activity completed two genuine distinct
Gemini API reviewer contexts and received a consensus PASS. A new,
independently authorized run attempted activity 2
(`act-mcq-02-si-units`) and persisted an `AMBIGUOUS` physics role with
`reasonCode=ServerError`, a `COMPLETE` semantics role, and an
`AI_UNCERTAIN` aggregate. The SDK error does **not** prove that Google failed
to accept the original request. Its prompt must never be replayed,
even using another key, model, machine or protocol.

## Permanent normal-path resolution for forward progress

1. **Quarantine at verified section scope.** On the native V3 runner's normal
   planning path, an approved section is quarantined if its validated
   evidence contains uncertain model outcomes, orphaned role claims,
   skipped-unsent requests or an academic repair requirement. It is never
   reopened by this mechanism. The original JSON files are read-only and
   remain bound to exact frozen package SHA-256.
2. **Continue only genuinely independent work.** If another frozen section
   has no such blocker and still has unassessed activities, select that
   section for *new* requests. Do not try a different reviewer for the same
   blocked activity; do not create synthetic PASS or quietly erase its
   uncertainty. The stricter generic planner remains the default for callers
   that do not explicitly opt into independent continuation; the native CLI
   activates this policy automatically for its normal execution path.
3. **Throttle provider-capacity faults.** Recognized `ServerError` /
   `ServiceUnavailable` / `TransientGeminiError` ambiguous role claims
   trigger a minimum 30-minute cooldown before another new independent
   model request. Two such claims within a rolling hour open a circuit
   until the earlier event ages out and the newer event has cooled down.
   The gate uses bounded claim metadata and local file modification times
   **only for rate limiting**, never to prove a model verdict or authorize
   replay. No probe request, key rotation, token leak or hidden retry occurs.
   If **any** prior role claim records `BLOCKED_EXTERNAL`, the normal native
   course remains blocked globally: switching sections cannot bypass an
   authorization or platform denial. Likewise, an unclassified ambiguous
   provider failure (which could be authentication, quota or malformed
   content rather than capacity) stops with
   `STOP_UNCLASSIFIED_PROVIDER_REVIEW`, not a new model request.
4. **Truthful completion.** When no eligible unblocked section remains,
   return `STOP_UNRECONCILED_MODEL_REVIEW` (or the preserved academic repair
   stop). A quarantined course can never reach complete review or publish
   merely because all other sections have passed. Audit reports expose
   `quarantinedSections`, `providerCapacity` and exact real review counts.
5. **Bounded unattended operation.** A cooldown causes a truthful stop,
   not a busy loop. A later eligible normal invocation can proceed
   automatically without owner approval, but cannot infer success for the
   quarantined request or promise a background worker where none exists.

## Validation and scope

The source-free regression suite injects synthetic `ServerError` claims,
tests historical aggregate and claim preservation, cooldown, two-fault
circuit, cross-section forward progress, and fail-closed course status.
Separate execution on the genuine HP private state must verify that the
new planner chooses Section 9.2 while Section 9.1 remains `AI_UNCERTAIN`.
Any real Section 9.2 Gemini response must be treated as fresh evidence,
not reconciliation of the original Section 9.1 physics request.

**This is a blocker-isolation and forward-progress remedy, not proof that
Google's prior ServerError was repaired.** Closing Section 9.1 itself
would require an attributable provider receipt or a separately versioned,
audited content/review transition; neither can be fabricated from a
generic HTTP error. PR #223 remains draft/unmerged and no public release
is authorized.

## Authentic follow-on evidence (14 November 2026)

On HP the existing frozen Section 9.1 activity-2 `AMBIGUOUS ServerError`
was recovered as a **quarantined section**, not as an authorized retry.
The new read-only native planner chose Section 9.2; a one-activity genuine
Gemini API invocation on commit `fdf17b848a4b9dc000247d97297b44fc70c1ca65`
then completed Section 9.2 activity 1 with **two COMPLETE Gemini API role
claims and AI consensus PASS**, exit code 0. The real private checkpoint
retained the original Section 9.1 `AMBIGUOUS` request and `AI_UNCERTAIN`
aggregate, with no active review lock.

Overall course state after the new genuine request: **3/108 assessment
rows, 2/108 fully model-reviewed, 2 consensus PASS, 1 uncertain,
0 published**. Source-free regressions protect cooldown, circuit, active
ownership and external-denial boundaries. Later commits that harden these
checks were not part of the original real Section 9.2 submission;
their validation is reported separately. Exact receipts and scope details:
`docs/V3_NATIVE_GEMINI_LIVE_PILOT_20261114.md`.

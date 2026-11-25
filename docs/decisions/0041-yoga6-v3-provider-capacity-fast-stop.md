# Decision 0041 — Yoga 6 ownership and provider-capacity fast-stop for native V3

**Date:** 15 November 2026. **Status:** Implemented on draft/unmerged PR #223.
Supplements Decisions 0027, 0028, 0037, 0039 and 0040. No public
deployment, source transfer, model-request replay, publication, or automatic
merge is authorized.

## Designated workstation

The Yoga 6 continuity authority at
`G:\My Drive\Projects\yoga 6\brilliant-project-continuity\BOSLA_9_RECOVERY_20261106.md`
identifies Yoga 6 as the Bosla workstation. Earlier live V3 testing was
performed on HP rather than the owner-designated machine; HP records remain
separate historical evidence, not acceptance for Yoga 6.

`config/configure_project.toml` now declares
`[project].native_gemini_review_host = "YOGA6"`. The normal native runner
checks the Windows hostname using the OS's hostname before SDK preparation,
credential lookup, claims or generated-text transfer. A nonmatching
host stops `V3_NATIVE_REVIEW_WRONG_WORKSTATION`; missing/invalid authority
stops closed. Read-only planning remains possible on other machines.
This is an operational misrouting safeguard, not cryptographic device
attestation. Generalized or reassigned projects must update their
project-specific authority through the ordinary review process.

## Genuine Yoga 6 failure

On a clean isolated checkout of source commit `089681b013c6cd496640dd142f13896a1bde09e2`,
with Google SDK 2.25.0 supporting `HttpRetryOptions` and two configured
credential candidates, the one-activity native Gemini V3 review selected
frozen Section 9.1. It invoked two distinct one-shot contexts for the first
activity. **Both roles returned `ServerError`** on Yoga 6; durable role
claims are `AMBIGUOUS` and the aggregate is `AI_UNCERTAIN`.
The course recorded one attempted activity, zero fully reviewed,
`STOP_PROVIDER_CIRCUIT_OPEN`, no release receipt and no publication.

A source-free unauthenticated connectivity check on Yoga 6 successfully
resolved the generativelanguage.googleapis.com hostname and reached its
HTTPS API endpoint (HTTP 403 without an API key); this does not identify
the cause of the model-level 5xx or prove provider readiness. No Google
response body, key value, or generated prompt is committed. The status
class does NOT prove either request was unsent; neither may be replayed.

## Previously established remedies reused

- BSA-20261104-104 and BSA-20261104-108: source-free credential preflight,
  bounded provider handling and NO replay of an ambiguous submitted request.
- BSA-20261113-162/163: role-specific immutable pre-dispatch claims,
  resume safety and orphan-claim protection.
- BSA-20261114-165: quarantine affected frozen section; proceed only with
  genuinely distinct work, subject to minimum 30-minute cooldown and
  a rolling-hour provider circuit after two capacity errors.

## Permanent adjustments

1. **Fast-stop sibling review.** If the first role raises a recognized
   provider capacity exception (`ServerError`, `ServiceUnavailable` or
   `TransientGeminiError`), the normal assessment records an immutable
   `AMBIGUOUS` first-role claim; the second role is
   `SKIPPED_UNSENT` with `requestSubmitted=false` and
   `reasonCode=PROVIDER_CAPACITY_UNSENT`. It never contacts Google for
   that second role, still produces `AI_UNCERTAIN`, and accurately
   counts the unsent request. Other noncapacity errors retain the
   existing role-specific handling.
2. **Finite cooldown is nonnegotiable.** The existing Section 0040
   provider-capacity gate stops before starting any new model activity
   until its cooldown/circuit deadline. The earlier Yoga 6 failure
   triggered that circuit and was NOT resubmitted.
3. **Future-only key diversity.** Once the gate is READY, the normal native
   runner can use the next already-configured key on a NEW, independent
   frozen activity, using the historical number of distinct activities
   with provider-capacity failures as its bounded candidate offset.
   Both roles of that new activity use the same fixed key and independent
   clients. No probe, fallback or key change can occur after a submitted
   request; no key string is logged or checked into Git.
4. **Full-course truth remains unchanged.** A quarantined or skipped
   activity cannot become consensus PASS from software checks or successful
   new-section reviews. Any provider denial, unknown ambiguity, active
   run lock, changed package SHA or version-binding conflict still stops
   independently of this policy.

## Validation standard

Unit/integration tests inject synthetic `ServerError`, verify the second
model request count remains zero, durable `SKIPPED_UNSENT` state and
non-replay across restart, wrong-host refusal before SDK creation, deterministic
new-activity key selection without probe, and the existing cooldown/circuit
and frozen-package constraints. The live Yoga 6 error was observed on
the earlier source revision, **not** resolved by a post-fix genuine
Google rerun, because the authenticated provider circuit remains open.
A later authorized fresh activity after the deadline is necessary
to verify whether Google's capacity has recovered.

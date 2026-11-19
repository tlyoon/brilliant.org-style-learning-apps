# Decision 0081 — BOSLA v7.1: V6 checkpoint must dispatch real public builder

**19 November 2026.** BSA-20261119-225. Workstream: BOSLA, draft PR #223, owner Yoga 6.

## Root cause and historical review

The BSA223 V6 native V3 technical release adapter genuinely verified all six
18-activity packages using saved two-Gemini role pairs, exact CI, private
browser and HMAC receipts. BSA224 fixed an exact-head CI wait race. Yet the
ordinary `--source-free-advance` path returned success at V6 after recording
`GENERIC_FULL_COURSE_V3_RELEASE_ADAPTER_WITHOUT_FORGED_ATTESTATION` as the
next milestone; it did not actually invoke the existing public bundle builder.
That is an unexecuted handoff under the owner v7.1 contract.

## Executable recovery

The ordinary `scripts/run_v3_yoga6_recovery_worker.py --source-free-advance`
now immediately invokes
`app_generator/runtime/v3_public_bundle_handoff.py::dispatch_private_public_bundle_build`
after real V6 success and before returning success.

This step rechecks clean exact Git head, genuine hosted CI, immutable saved
readiness, V6 integrity, six exact private V3 HMAC receipts, correct 108-activity
roster and unaltered private content. It invokes the **original**
`scripts.build_public_release.build` in release mode, once for each of the
six actual packages, through a private scratch overlay of ordinary application
and domain assets. Each release gate and resulting bundled package is checked
against exact source SHA256; deterministic manifest hashes are saved in the
private V7 checkpoint. Successful replay recomputes and verifies, never
silently overwriting an altered checkpoint. The worker cannot return success
after a merely saved V6 if V7 has not actually executed.

**This does not invoke PublicPagesPublisher, Git merge, Git push, public
deployment, paid Gemini, new PDF acquisition or third-party source transfer.**
All generated package bytes stay in LOCALAPPDATA private temporary space and
are deleted after building. Public operational authority remains separate.
Historical Decision 0029 finite C3 `FAILED_LIMITED_CAMPAIGN` is unchanged.

## Verification and next boundary

A standalone read-only production-builder probe on Yoga6 confirmed six of six
genuinely attested packages each produce eight release files with exact
package bytes, no model calls and no deployment. Ten synthetic fault tests
exercise six-builder dispatch, repeat/idempotence, changed source and receipt,
tampered V6/V7, missing CI, dirty tree and corrupt bundle output. Existing
normal-worker CI-race tests are extended to require the downstream V7 dispatch.

The new integrated head must pass hosted CI and the genuine normal Yoga6
source-free worker must execute V7 before BSA225 can be called resolved.
After V7, the remaining boundary is publication/deployment scope and permission,
not a pretext to reopen exhausted historical C3 or repeat scientific reviews.
If no authorized deployment action is available, retain a truthful stop rather
than infer public publication from private technical evidence.

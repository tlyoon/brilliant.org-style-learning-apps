# Decision 0084 — Non-destructive public Pages PR handoff and pinned Chapter 9 guard

**20 November 2026.** BOSLA BSA-20261120-228, owner v7.1, Yoga6.

## Verified inherited evidence

BSA225/BSA226 closed all six genuine per-package private release builds.
BSA227 closed the exact-source public Pages destination audit and proved
existing `section-9-1` through `section-9-9` routes on
`tlyoon/section-8-1-learning-app` main, push/admin permissions, three
source-different sections, and five changed activities. Genuine source-bound
V8 is a read-only scope receipt, **not permission to rewrite or merge**.

## Historical failure and immediate repair

The older `PublicPagesPublisher.publish` always called `gh pr merge`
after creating or finding a publication PR. It ignored the configured
`public_deploy_auto_merge=False` setting and could therefore make a
non-destructive review handoff irreversible. Its route check also accepted
unsafe non-numeric path input after dot replacement.

The publisher now:
1. Blocks direct public auto-merges of the six existing protected Chapter 9
   routes on the real configured site until a separate revision-pinned,
   non-destructive release proposal is constructed. This guard runs before
   the lease, academic receipt lookup, Git command, public branch push or
   PR creation; no new manual academic/pilot signoff is introduced.
2. Honors `public_deploy_auto_merge=False`, returning a PR result with
   `merged=False` rather than running the old unconditional merge.
   Missing/unspecified flag also defaults to non-merging behavior.
3. Requires numeric dotted section IDs for public route construction so
   slashes, dot segments and other path strings fail closed.
4. Retains an explicit auto-merge path for other unprotected sections only
   when the flag is `True`; existing academic V3 release gate remains
   mandatory.

## Test semantics

Six fake-only regression tests cover protected 9.1–9.6 no-remote-stop,
non-merging PR handoff, explicit unprotected merge behavior, missing-flag
safe defaults, and malicious route rejection. No fake model payload counts
as genuine educational validation. A separate **actual Yoga6 source-path
direct invocation** with the configured public repository and
`public_deploy_auto_merge=True` proved the protected route stops before
any lease or Git I/O. No real public push, PR creation, merge or deploy
was executed. Existing genuine V8 SHA-pinned scope remains authoritative.

## Next substantive boundary

Generate a deterministic local, non-destructive proposal for only the
three actually changed public section routes (9.1, 9.2, 9.6), tied to
the actual remote main SHA and exact genuine V7 HMAC package identities.
Verify complete runtime assets and staged browser behavior, then create
an explicitly scoped public PR only through a separate safe workflow.
Do not reuse historical failed C3 multi-topic results as generalization.

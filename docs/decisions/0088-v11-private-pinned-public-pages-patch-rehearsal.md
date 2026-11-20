# Decision 0088 — BSA232: pinned, private three-route Git patch rehearsal

**20 November 2026, owner Yoga 6, v7.1 handoff after genuine V10.**

## Accepted prior evidence

The genuine Yoga6 `--source-free-advance` run on clean
`e78ac52a7ee683c006aaffb996ea32e85a7d5a4e`
returned exit 0 and saved source-bound V1–V10 signed receipts.
The actual V10 receipt
`a409e58bb29bf71ada3bda1f7101bfdc130c59c44015c5431c609423c21feab6`
established 3/3 private production bundle Selenium Chrome acceptance
for Sections 9.1, 9.2 and 9.6 with 24 SHA-verified files.
Exact-head GitHub Actions #44688669609 succeeded, including the
historical BSA-20261107-128 disabled locale selector race repair.
BSA230/BSA231 were marked resolved only after this real result.

BSA227 previously verified the existing public GitHub Pages repository
`tlyoon/section-8-1-learning-app`, including Chapter9 routes 9.1–9.9.
Its public `main` was pinned to
`eb86fe8eb94ec33f8c0c055d2423b245e5898241`.
Existing content was identical for 9.3–9.5, and 9.7–9.9 are outside
the owner-approved six-section update.

## First private rehearsal and historical failure

One genuine read-only private Git patch rehearsal was attempted after
V10. The first clone failed in a *deep per-commit evidence folder*.
The retry placed the temporary checkout under the shorter
`%LOCALAPPDATA%/Microvid/BoslaV3ReviewYoga6` path, avoiding the
Windows legacy MAX_PATH risk without touching source-bound evidence.

The repaired rehearsal cloned the exact pinned public main, copied
only the three privately built complete eight-file production
bundles, and ran a local staged `git diff` and separate
`git apply --check` against a second clean pinned checkout.
The patch contained 21 changed Git paths (7 per section, comprising
3 additional runtime assets plus 4 modifications, while `.nojekyll`
remained unchanged). Its 756,429 bytes have SHA-256
`2548cc149463e6e706d741ea3bf0f032c6b9473cba575ad4511bf626ceae6bab`.
No public PR/branch push/merge/deployment occurred.

## Executable continuation

A successful normal V10 checkpoint must **dispatch V11 in the same
`scripts/run_v3_yoga6_recovery_worker.py --source-free-advance` run**.
The implementation `v3_private_public_patch_rehearsal.py` first
verifies original V9/V10 signed integrity, exact clean new source CI,
all 24 private file SHA values, destination and pinned public main.
It uses a short private temp checkout, restricts Git commands to
read-only clone/rev-parse/ls-remote plus local-only add/diff/apply,
copies only Sections 9.1/9.2/9.6, validates precisely 21 changed
paths, and performs independent pinned-base `git apply --check`.
It persists a private patch and immutable signed V11 receipt;
source restarts reject any changed patch.

**Never push, create a public PR, merge or deploy from V11.**
This boundary is a reversible private integration rehearsal, not
authority to replace existing public Chapter9 routes. The next
boundary is a scoped non-merging PR proposal only when its separate
authorization and integrity conditions are met, not public release.
The finite heldout C3 campaign remains `FAILED_LIMITED_CAMPAIGN`.

## Acceptance

Required: fault-injection tests for exact 3-route scope, remote main
movement, unexpected 9.7 path, missing public route, tampered V10
receipt, changed private patch and unsupported Git commands; normal
source-free worker synthetic V10→V11 dispatch tests; strict recurrence
registry; exact new-head hosted CI; genuine owner Yoga6 complete
source-free V1–V11 EXIT0, plus signed V11 receipt verified against
private patch and unchanged public main.

Do not label BSA232 resolved until these tests and genuine pipeline
evidence are present.

# Decision 0090 — BSA234: reuse historical GitHub draft PR with exact version and automatic restart

**21 November 2026 — owner Yoga 6; v7.1 forward-progress and failure recovery contract.**

## Historical fault review

The public site `tlyoon/section-8-1-learning-app` already had 15 prior
merged PRs by 20 November 2026, including 9 per-section Chapter 9 review
PRs and three later shared-player PRs. Historical BSA228 (decision 0084)
corrected an unconditional `gh pr merge` defect and made protected
Chapter9 public auto-merge refuse before any Git side effect; it honors
`public_deploy_auto_merge=False` for a non-merging PR. BSA227/BSA232
proved the actual public `main` at
`eb86fe8eb94ec33f8c0c055d2423b245e5898241`, only three changed
Sections 9.1,9.2,9.6, and an immutable exact 21-path 756429-byte patch
SHA-256 `2548cc149463e6e706d741ea3bf0f032c6b9473cba575ad4511bf626ceae6bab`.
BSA233 actually completed V1–V12 on owner Yoga6 with signed V12 hash
`87f202bb850d8263c0ddd9e6e04bf92afd39019381c2d6986142a7943d6c6b7d`.
Yet V12 merely labeled a public PR action and the outer worker returned.
The root cause is the same **next-task marker without executable dispatch**.

## Targeted design correction

A genuine signed V12 stage must automatically dispatch the next safe
review-only V13 stage **in the same normal source-free worker process**.
The existing `PublicPagesPublisher` and GitHub CLI's proven branch/PR
creation semantics are reused, with BSA228 non-merge protections and
BSA232 signed source/patch identity restrictions. The permitted external
actions are strictly:

- an exact deterministic public review branch
  `bosla/private-ch9-three-section-2548cc149463`, using existing
  public main as parent and the same signed three-section patch;
- a **draft**, unmerged GitHub PR pointing to main. Neither main nor
  GitHub Pages output is changed by the review branch itself;
- read-only reconciliation against public main, branch contents, PR
  state and immutable private receipts.

A pre-call exact-proposal checkpoint is persisted before public writes.
On restart, the worker computes the same expected Git tree; if the
review branch exists it must match that tree. If a push or PR-create
returned an uncertain result, the worker checks the actual GitHub
branch and PR **without replaying the uncertain operation**. A forged,
duplicate, closed, merged, non-draft, mis-scoped, modified-tree or moved-base
PR fails closed. A successful remote PR yields immutable V13 receipt.

**Never merge this PR automatically.** Publication authorization remains
false until the separate release acceptance. Historical C3
`FAILED_LIMITED_CAMPAIGN` is unchanged. Previous owner decision 0043
removed the Yoga6 scheduler; no scheduled task is recreated.

## Acceptance required to close

1. Historical BSA228/BSA232/BSA233 remedies reused without duplication.
2. Simulated real Git commands, read-only GitHub API and draft PR
   creation, plus fault injection: uncertain push, uncertain PR create,
   double dispatch, remote drift, wrong tree, malicious PR, forged V12,
   duplicate PR, unsupported merge commands.
3. The normal worker's V12→V13 dispatch and failure exit tests.
4. Strict recurrence registry/contract checks and exact new-head CI.
5. Genuine owner Yoga6 V1–V13 run, real authenticated public review
   branch + draft PR with correct 21-file GitHub diff, public main
   unchanged, PR unmerged, and signed source-bound V13 receipt.

Do not mark BSA234 resolved based on mock tests or CI alone; the actual
GitHub state must confirm the non-merging PR, and no public deployment
may occur in this stage.

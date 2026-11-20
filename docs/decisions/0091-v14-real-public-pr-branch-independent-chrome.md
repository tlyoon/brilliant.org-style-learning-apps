# Decision 0091 — BSA235: automatic independent Chrome QA of actual PR branch

**20 November 2026 — owner Yoga6 and v7.1 contract.**

## Historical review

BSA230/BSA231 previously solved original Chrome load errors and a harmless
localhost favicon 404. BSA232 verified an exact 21-path private Git patch
for Sections 9.1, 9.2 and 9.6. BSA233 staged an immutable private PR
draft. BSA234 proved genuine normal V1–V13 success, public GitHub draft
PR #16, independent remote tree/parent and 21-path GitHub diff. Its
signed V13 receipt was `b898f0c34105bc0c136832a1eebe1677db562c129c4514a1a2b888777803a1b3`.
An independent owner Yoga6 script
`%LOCALAPPDATA%\Microvid\BoslaV3ReviewYoga6\bosla_v14_public_pr_browser_probe.py`
already cloned that exact GitHub PR branch and loaded all nine Chapter9
routes in genuine Chrome (EXIT0). It signed private V14 evidence
`961d31322a6c77000470f07b0248f59c98895b2a7606c82a0e6c9bedf43b45c6`
for BSA234 source head `430cd08`. This was a one-off detached check,
not an executable automatic V13→V14 stage.

The recurring root defect is **successful checkpoint but no next
execution dispatch**. Previous fixes must be reused rather than
reimplementing locale handling or independent PR routing.

## Reusable executable remedy

The ordinary `--source-free-advance` worker now invokes
`app_generator/runtime/v3_public_pr_independent_browser_acceptance.py`
**immediately after** actual V13 draft PR creation/reconciliation.
Its safe behavior:

1. Replay the BSA233 strict exact-code, hosted CI, clean source,
   private 24-file manifest, V11 patch SHA and 21-scope preflight.
2. Verify the signed V13 receipt belongs to the same source and
   proposal; check actual GitHub PR state is OPEN, DRAFT, unmerged
   with base exactly pinned public `main`.
3. Compare all 21 actual GitHub changed paths to the signed private
   patch; reject extra Sections 9.7–9.9, deletions, duplicates,
   changed base, changed branch or forged receipt.
4. Verify remote commit parent and tree using authenticated read-only
   GitHub API; clone exactly the existing PR branch, compare HEAD SHA.
5. Load **all nine** Chapter9 public-branch routes in real headless
   Chrome, including the unchanged public routes; require package
   content, buttons and clean severe-console check. Reuse the
   historical narrow favicon 404 exception.
6. Recheck remote PR/base/branch after browser, persist immutable
   source-bound signed V14 result. No GitHub writes, public merge,
   public Pages deployment, new Gemini calls, or Yoga6 scheduler.

## Acceptance and recovery

- Tests for forged V13, wrong head, malicious branch, PR no longer
  draft/merged/moved base, unexpected file/deletion/duplicate, browser
  missing content and severe console error, and positive historical
  favicon exemption.
- Normal worker tests prove V13 success triggers V14; incomplete
  prior stage must not trigger it.
- Strict recovery registry validation, exact-hosted CI on new head,
  actual normal owner Yoga6 V1–V14 with signed V14 receipt, all nine
  live local Chrome routes and unchanged public PR/base.
- Do not call this boundary resolved based on a mock alone.
- Existing user-directed retirement of the Yoga6 30-minute scheduled
  task (Decision0043) remains authoritative. The historical limited
  three-topic C3 campaign remains `FAILED_LIMITED_CAMPAIGN`.
- Passing V14 is evidence of private review readiness, not permission
  to merge or publish the draft PR. Release admission is a separate
  future checkpoint with honest authorization status.

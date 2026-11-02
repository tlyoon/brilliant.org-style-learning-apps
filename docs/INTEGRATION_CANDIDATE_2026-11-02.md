# Combined integration candidate — 2 November 2026

This branch is a **readiness candidate**, not a release, published build, or permission to merge.

## Provenance and branch boundary

- Integration base: `main` at `aad23b3d27cfabde94950221159a413e6c8cf9cf`.
- Combined source head: PR #221 at `c7d71cd536429736090baac7a8f8cc901064b32d`, with 129 commits ahead of that base before this document.
- The open draft series #108–#221 (excluding issue #220) contains **113** PRs. Actual Git ancestry verifies **112** branch heads are ancestors of PR #221. Every PR is still draft/unmerged.
- **Exception PR #193:** `feature/source-bound-mcq-all-option-physics-20261031` at `a422839137865429c8c9a113065555892e385d4a` is *not* an ancestor. Both PR #193 and PR #194 descend from PR #192; PR #194 intentionally starts another audit lineage. In the current head, PR #195 provides source-bound all-option semantic physics tests and PR #196 provides the Newton-cradle source/physical-force extension. They overlap PR #193's objective, but functional equivalence must be reviewed before closing that side-branch. Do not claim it was integrated.
- A separate older open PR (e.g. #40) is outside this integration series; do not silently close, merge or retarget it.

## Verified integration preflight

- A read-only `git merge-tree --write-tree` rehearsal against the stated `main` produced a conflict-free tree for PR #108, through PR #113, and for the PR #221 head; **textual conflict-free does not imply academically verified**.
- On the inherited code head, GitHub Actions #356 reported SUCCESS; the revised recurrence contract protects 25 historical incidents through discoverable regression test identifiers.
- In the same Yoga 6 worktree, the regression contract, 10 adversarial contract tests, lint, 16 content packages and 13 bounded academic test modules passed.
- **This candidate must receive its own GitHub Actions validation against `main`** and source-free functional checks before being called integrated-ready. The CI outcome is recorded on its PR, not presumed by this document.

## Remaining release and owner gates

- Do not automatically merge this branch or predecessor drafts. Do not close dependent draft PRs simply because this candidate is green. Existing `git_publish=false` and `git_auto_merge=false` remain unchanged.
- Section 9.4 independent source/answer/physics/visual/multilingual academic acceptance remains **0/18 formally PASS** in the last verified private receipt; this candidate's CI cannot upgrade that status.
- Preserve exact original PDFs, private review receipts, credentials, student records and generated original runs outside Git.
- Before any real integration: verify PR #193 equivalence or retain it explicitly, run full CI against `main`, complete release-safety regression, and follow the independent academic gate and owner release authority in the current decisions.
- Track all work and evidence in issue #220 and the private project checkpoint; do not confuse technical-readiness PR creation with release.

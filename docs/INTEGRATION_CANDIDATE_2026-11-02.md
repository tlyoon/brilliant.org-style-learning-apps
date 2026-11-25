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

## Reconciliation of independent PR #193 and local integration run

- PR #193 was the **one divergent side-branch**, not in the combined head. The isolated original branch passed its 8/8 existing unit tests; the later statement-physics and contact-force replacement passed 11/11. Both cover nine MCQs and all 36 options; the later implementation additionally binds original source and EN/MS/ZH label digests and resolves the previously missing finite-contact-force proof. The old module was not imported by the active code. PR #193 was therefore **closed as superseded, unmerged**, without deleting its branch or Git history. This is functional development replacement, not proof that every historical witness dictionary is byte-identical.
- Original combined-hosted GitHub Actions #357: **SUCCESS** against main. Local Yoga 6 original bounded sweep: **125 PASS, 1 TIMEOUT** across 126 Python test modules, failure isolated to a *fake SDK 403 test* importing the real Google GenAI package from cloud-synced venv; no model API call. A subsequent stack trace confirmed importlib reading `websockets/asyncio/client.py` from the synchronized venv. Production error handling was not found to be at fault.
- Incident `BSA-20261102-098` now provides an optional fake provider types adapter for deterministic unit tests and a **separate offline, real-SDK type smoke check on hosted CI**. Production's default real SDK path is unchanged. The amended candidate requires a fresh complete hosted CI run and local bounded sweep before technical acceptance.
- The originally stacked drafts remain retained for provenance. Closing one off-chain superseded PR does **not** authorize merging the remaining drafts, altering private QA evidence, or public deployment.

## Remaining release and owner gates

- Do not automatically merge this branch or predecessor drafts. Do not close dependent draft PRs simply because this candidate is green. Existing `git_publish=false` and `git_auto_merge=false` remain unchanged.
- Section 9.4 independent source/answer/physics/visual/multilingual academic acceptance remains **0/18 formally PASS** in the last verified private receipt; this candidate's CI cannot upgrade that status.
- Preserve exact original PDFs, private review receipts, credentials, student records and generated original runs outside Git.
- Before any real integration: retain the recoverable closed PR #193 history, run full CI against `main`, complete release-safety regression, and follow independent academic gates and owner release authority in the current decisions.
- Track all work and evidence in issue #220 and the private project checkpoint; do not confuse technical-readiness PR creation with release.

# Isolated repository integration and CI recovery — 4 November 2026

This record covers general codebase integration of the [consolidated draft PR #223](https://github.com/tlyoon/brilliant.org-style-learning-apps/pull/223). **Not** a new held-out PDF campaign, permission to reissue a previously denied Gemini operation, independent academic acceptance, merge approval, or publication authorization.

## Observed integration evidence

- GitHub candidate head before this audit commit: `943f6743e4680289af0d260072f6258f3c8a35da`; base `aad23b3d27cfabde94950221159a413e6c8cf9cf`.
- Isolated, newly cloned `git` worktree on Yoga 6: `%LOCALAPPDATA%\Microvid\bosla-integration-audit-20261104`, inside the **existing allowed directory**. The protected working checkout and the stored `.env` were not modified.
- `git merge-tree --write-tree origin/main HEAD` returned exit code **0** and merge tree `abf770323c4371412a4217fe1d072d9a27bcee57`. No text conflict is demonstrated. GitHub's direct PR API reported `mergeable=null, mergeable_state=unknown`, while its GraphQL UI reported `mergeable=UNKNOWN`; neither constitutes a proved merge conflict.
- GitHub Actions workflow `.github/workflows/validate.yml` was **active**. No check suite was attached to the above candidate SHA when inspected. Runs #439–442 had failed for earlier intermediate commits; run #442's recorded failure was a stale `doctor` unit expectation, which was revised later on the candidate branch. Do not reuse either the earlier failure or an earlier PASS as exact-head evidence.

## Current source-free validation (Yoga 6 isolated clone)

- `python scripts/lint.py`: PASS.
- `python scripts/check_regression_contract.py`: PASS.
- `python scripts/check_documentation_impact.py`: PASS.
- `python scripts/check_gemini_sdk_types.py` in isolated virtual environment: PASS, no Gemini request.
- `python scripts/validate_content.py`: PASS, 16 package files.
- `python -m unittest discover -s tests -v`: **969 tests, OK (skipped=1)**.
- `node --check` application and visual renderer: PASS; **12** JavaScript learner/renderer suites: PASS.
- Isolated venv requirements from the pinned project requirements; no provider credential, secret, source PDF or protected source receipts used.

These results validate the **general software code candidate** only. They do not prove any held-out source PDF completed, source rights, English/Malay/Chinese semantic quality, real learner browser acceptance, actual Gemini key fallback, or release readiness.

## Exact-head hosted CI recovery step

This documentation-only commit and an ordinary authenticated Git branch push from the isolated clone are intended to obtain a new GitHub `pull_request` synchronize event for the draft PR after GitHub attached no check suites to several connector-origin commits. Record the resulting workflow run and **its actual head SHA** separately. If no run is triggered, do not report CI success and do not bypass workflow permissions.

The terminal Decision 0029 `BLOCKED_EXTERNAL` disposition and prior source-frozen campaign limits remain binding. `git_publish=false`, `git_auto_merge=false`, `public_deploy=false` for any future private evaluations; no automatic merge or publication from this audit.

## General CI trigger resilience

The original validation workflow listens for `pull_request` and pushes to `main` only. Although the Git ref reached a new commit, GitHub's pull-request metadata remained `mergeable_state=unknown` with its head index at an older commit and no new check suite. This differs from an actual Git conflict (the independently computed merge tree was clean). Past GitHub status incident records describe PR update delays, but they do not establish an active root cause for this individual repository.

The workflow now accepts `push` on ordinary development prefixes (`feature/**`, `fix/**`, `docs/**`, `refactor/**`, `integration/**`, `test/**`) as a **second path** to exact-head validation, plus a future manual `workflow_dispatch` entry. PR and branch-push triggers retain **separate** concurrency groups, canceling only older runs of the same event/ref, not canceling required PR checks. The full existing test set and release permissions are unchanged.

This repair is not evidence that GitHub hosted validation has passed. Preserve separate reporting of the observed workflow head and result after the following ordinary authenticated Git push.

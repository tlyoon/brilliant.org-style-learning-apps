# 0027 — Regression-Immunity and Autonomous Blocker-Recovery Contract

**Status:** Owner-approved development amendment, 2 November 2026. Applies to this repository only. It supplements existing product, privacy, academic QA and publication decisions; it never relaxes them.

## Principle

A solved defect becomes a **permanent executable invariant**. A fix is not "resolved" merely because a local run succeeds: it needs an adversarial regression case, an incident reference, and continued CI execution. Tests reduce the chance of recurrence, but cannot guarantee external tools, model providers, browsers or authorization services never fail.

## Definition of resolved

1. Record a distinct \`BSA-YYYYMMDD-NNN\` record in \`docs/FAILURE_TO_FIX_LEDGER.md\` with symptoms, root cause, correction, negative control and uncertainty. Do not reuse an incident ID; historical duplicates must be reconciled rather than copied.
2. Register it in \`docs/recurrence_registry.json\` with a concrete test method (Python) or assertion string (JavaScript). A new incident starting at \`BSA-20261102-096\` must appear in the registry even while active. Mark it \`resolved\` only with executable tests; mark \`active\` with a safe next action when evidence is missing. Older high-impact protections have seeded entries.
3. Show that the regression fails with the known defect or an isolated falsifiable negative fixture, then succeeds on the repair wherever possible. Keep original source PDFs, actual learner data and provider credentials out of the repository and CI.
4. Keep the regression in ordinary CI, not an optional developer-only command. Do not delete a test, its assertion, or its manifest entry just to achieve green checks. When refactoring, replace it with a functionally equivalent or stronger proof and record why.
5. Run \`python scripts/check_regression_contract.py\` on every PR to reject missing/deleted locked protections, stale test references, absent CI execution, missing incident ledger records and unregistered incidents after the cutover. Run \`tests/test_regression_contract.py\` for adversarial verification of the guard itself.
6. If an identical failure recurs, open a new incident **linked to the old** and expand the regression to cover the newly discovered circumstance. Do not repeat the same ineffective repair or weaken the original test.

## Autonomous development cycle

**DISCOVER → PREFLIGHT → REPAIR → PROVE → INTEGRATE → CHECKPOINT**

- **DISCOVER** latest project contract, verified GitHub head/base/CI, saved run state, owned local worktrees, matching source and package hashes, previous incidents and active or ambiguous model requests. Do not trust stale chat statements over machine state.
- **PREFLIGHT** the right interpreter/venv, dependencies, browser/profile ownership, required source and privacy boundaries, Git cleanliness, available authorized tools, model session readiness, costs/quotas and branch ancestry. Never launch a browser before preflight dependencies. Do not run a paid API merely to check availability.
- **REPAIR** one independently confirmed root cause in an isolated worktree. Preserve protected original checkouts, student data and private source bytes. Make the smallest change and retain evidence of the pre-fix defect.
- **PROVE** focused positive/adversarial tests, affected historic regressions, Python/Node/schema lint, content QA, and independent academic proof when applicable. Academic outcomes remain **PASS / FAIL / REVIEW_REQUIRED**; CI green, model agreement or a screenshot is not full scientific correctness.
- **INTEGRATE** verify dependency and head/base SHA, resolve conflicts with isolated integration trials and full regression, then mark integration separately from implementation. The existing #108–#219 draft debt (issue #220) takes priority over unrelated feature stacking. Do not create a fresh chain of more than five dependent unmerged feature PRs; when legacy debt already exceeds this, permit only focused blocker fixes or integration work. Neither a clean PR nor CI green authorizes merge/publication.
- **CHECKPOINT** persist exact branch/SHA, tests and CI, private-evidence digests (not bytes), owned-process state, completed vs unattempted actions, failure class, retry budget, and next safe independent task. Do not claim work can continue outside an active authorized execution.

## Failure classifier (no blind retry)

| Class | Bounded action | Forbidden shortcut |
|---|---|---|
| Deterministic program failure | Save minimal reproducer; patch root cause; add regression; rerun affected suites | Retry identical failed job indefinitely |
| Wrong environment/interpreter | Locate correct existing project venv; check imports and dependency versions before opening browser | Start Chrome or mutate profiles before dependency preflight |
| Silent/hanging test | Use \`scripts/run_bounded_regression.py\` with per-module timeout, owned-process-tree cleanup and last active test diagnostics | Blanket kill unrelated processes; treat timeout as PASS |
| Intermittent network/provider/browser | Read readiness and request lifecycle; bounded backoff only if no request may have been sent; continue independent tasks | Resend ambiguous or possibly submitted model requests; alter restored user tabs |
| External operation with ambiguous outcome | Save \`IN_FLIGHT\`/\`AMBIGUOUS\` immutable receipt and reconcile read-only | Replay, double-charge, or claim completed |
| Tool/security/policy denial | Save \`BLOCKED_EXTERNAL\` without secrets; pivot to genuinely independent offline/read-only work. A separately authorized interface is usable only if expressly allowed for that operation | Rephrase calls to evade a restriction; bypass permissions or safeguards |
| Missing original-source/academic proof | Keep unresolved exact per-activity gates \`REVIEW_REQUIRED\`; gather independent source/math/translation/visual evidence or target a private correction | Fabricate PASS or require mandatory human academic signoff |
| Long unmerged PR dependency chain | Inventory exact base/head/CI; integration simulation in dependency order; focus on closing debt | Unverified bulk merge, auto-publish, accumulate unrelated descendants |

Retries must have a **reason, count and stopping condition** in the appropriate owned subsystem; no global forced retry. After repeated same-class failure, escalate diagnostics and change the approach, not the threshold. An external safety decision cannot be prevented or overridden by repository code.

## Stage and release accounting

Track **implemented, locally tested, CI-validated, integrated, academically accepted and published** as different statuses. A visual screenshot proves bounded rendering evidence only. Autonomous independent AI academic QA does not require mandatory human approval, but its verdict alone is not deterministic source/mathematical proof. Keep \`git_publish=false\`, \`git_auto_merge=false\` and private content off the public branch without separately granted authorization.

## Enforcements and references

- \`docs/recurrence_registry.json\`, \`scripts/check_regression_contract.py\` and \`tests/test_regression_contract.py\`: permanent incident-to-test links.
- \`docs/FAILURE_TO_FIX_LEDGER.md\`: symptom, root cause and known limits.
- \`docs/CONTINUOUS_AUTO_TESTING.md\`: bounded local test recovery.
- Decision 0024: independent AI academic review without mandatory human signoff.
- Issue #220: existing long stacked integration debt.

## Superseding strengthening: Decision 0037 (13 November 2026)

Owner Decision 0037 makes the existing regression-immunity rule explicit:
**automatic recovery must be part of normal pipeline execution, not depend
on you repeatedly asking me to fix the next blocker.** Its machine-readable
invariants in `docs/normal_pipeline_recovery_contract.json` are checked
by the ordinary `scripts/check_regression_contract.py` CI gate. A repaired
defect is not closed by a manual-only workaround, a standalone tool, or a
synthetic green test that was never exercised by its normal dispatch path.
Safe automatic recovery must remain finite and respect external permission,
request-ownership and no-replay boundaries. This is an additive development
obligation, not an override of Decision 0028 or the V3 release proof.

## Mandatory normal-path activation proof (10 November 2026, BSA-20261110-137)

Effective for each newly RESOLVED BSA incident from BSA-20261110-135
onward, the machine-readable recurrence registry must contain an
automaticRemedy declaration with the actual normal runtime file,
automatic trigger marker, remedy/stop marker and at least one
real application/CI/coordinator dispatch entrypoint. A standalone manual
script, incident record or test-only helper is not sufficient.

The existing normal CI check_regression_contract.py verifier rejects
missing, unsafe, inactive, or disconnected runtime/dispatch declarations.
Do not weaken earlier tests, budgets or accepted review stop decisions.
A static wiring check is necessary but not sufficient: each repair also
requires a failing pre-fix negative fixture, a normal-path execution test,
and exact-head CI before claiming integration or permanent coverage.
No contract entry can imply autonomous merge, deployment, protected-source
submission, student-data use or publication.

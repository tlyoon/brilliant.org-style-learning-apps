# Decision 0092 — BSA236: global post-PR roadmap dispatch, not another text-only next stage

**20 November 2026 — BOSLA owner Yoga6, v7.1.**

## Historical root cause

V1–V14 genuine source-free acceptance passed on exact source
`f94d20105e81d9723cff76674675f5fe2a35b1cd`, with hosted CI
#44718808843 SUCCESS and immutable V14
`ee873780e3a5e2110ad3bd01ee654fb2fe8a4afd311a7598a32706fc14952ea1`.
Live GitHub draft PR #16 remained open and unmerged; all nine actual
review-branch Chapter9 routes passed independent Chrome and exactly 21
review files changed. BSA235 was closed in source `e49da57`.

Nevertheless, the ordinary worker exited after V14, even though the
next issue was concrete and independently executable: public PR security,
status-check/review inventory and global cross-workstream recurrence scan.
This repeats the checkpoint-to-note instead of checkpoint-to-dispatch
flaw previously tracked in BSA222/BSA229–BSA235. v7.1 requires a
**real same-invocation handoff** after success, with no speculative
persistent runner.

## Executable remediation

Add `app_generator/runtime/v3_global_post_pr_readonly_roadmap.py`
to the ordinary source-free path **immediately after V14**.
It is a conservative allowlisted registry, not arbitrary dynamic code.
It verifies the full source-bound V14 signed chain and scans a bounded
global set of safe independent tasks:

1. `ACTUAL_PR_BRANCH_RECONCILIATION`: actual GitHub draft PR state,
   scoped 21-path diff, branch SHA and pinned public base main;
2. `PUBLIC_GITHUB_NATIVE_CHECKS_AND_REVIEWS`: actual read-only
   GitHub status, check-runs and review inventory. Historically the
   public repository lacked native GitHub checks even for merged PRs;
   **zero checks is not a PASS or an invented approval**;
3. `HISTORICAL_C3_AND_GLOBAL_RECURRENCE_SCAN`: entire executable
   recurrence registry active incidents and unchanged
   `FAILED_LIMITED_CAMPAIGN` source evidence, without any paid
   replay or new authorization.

For each eligible task, the controller writes a source-bound
`PRE_CALL` checkpoint **before actually invoking** the handler, then
writes the separate signed `RESULT` receipt. It records true task
order and actual dispatch counts. A failure is quarantined, and later
independent tasks still execute. A restart verifies/reconciles
immutable results; any tampering or changed external evidence stops
with an explicit non-PASS. Only read-only handlers are in the registry.

The final V15 receipt captures the actual three-task execution, any
quarantined failures and the next global dependency. The ordinary
worker's exit0 acceptance requires all three tasks to execute
successfully, not merely save a next-task label. No auto-merge,
public deployment, paid AI request, new scheduler or claim of a
cross-session persistent supervisor is permitted.

## Test requirements and honest limits

- Synthetic normal-worker V14→V15 dispatch must occur exactly once,
  no false success on failing earlier stages.
- Direct controller test: three task PRE_CALL and RESULT receipts;
  restart revalidation; forged V14; unexpected branch/main changes;
  failure of the middle audit followed by execution of the third;
  tampered saved result and unregistered handler refusal.
- Exact-head hosted CI and **genuine** owner Yoga6 V1–V15 normal
  worker must pass before this incident is marked resolved.
- Public PR can be "technically mergeable" but still draft and
  unapproved. Native GitHub checks/reviews absent is a documented
  release-evidence boundary, not proof of approval. C3 is still
  `FAILED_LIMITED_CAMPAIGN`.
- Owner Decision0043 retired the Yoga6 time scheduler. This
  bounded in-process controller does not reinstate it and does
  **not** claim execution continues after the tool/chat session.
- A truly comprehensive project-wide supervisor and later
  independent public release readiness remain future work;
  these three allowlisted tasks do not falsely constitute
  project completion.

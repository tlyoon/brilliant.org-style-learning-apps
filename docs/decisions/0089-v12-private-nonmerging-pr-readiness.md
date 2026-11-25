# Decision 0089 — BSA233: automatic V11→V12 private non-merging PR draft

**20 November 2026 — owner Yoga 6, v7.1.**

## Historical evidence and boundary

BSA232's exact-head `f3a7deac9d0c8c025eeb1be88cddfa34654c043b` hosted GitHub CI
#44692645543 succeeded, and the real Yoga 6 `--source-free-advance` V1–V11
normal workflow returned exit 0. Its immutable signed V11 receipt
`67420d2f4e8305f0d5d8baf4a6282175944678b25e1c1a5794105df99a7bf98f`
recorded a private 756,429-byte Git patch with SHA-256
`2548cc149463e6e706d741ea3bf0f032c6b9473cba575ad4511bf626ceae6bab`.
Exactly 21 existing public paths in 9.1, 9.2, 9.6 changed, and
`git apply --check` passed against a second clean, pinned public
main `eb86fe8eb94ec33f8c0c055d2423b245e5898241`.
No GitHub writes occurred.

The previous worker returned successfully after V11 but only recorded
`SCOPED_NONMERGING_PUBLIC_PR_PREPARATION`, without dispatching that
next authorized *private* boundary. This violates v7.1's
`checkpoint_committed → next_task_dispatched` invariant.
BSA233 implements the next safe task directly in the normal worker.

## No-scheduler decision preserved

Historical decision 0043 (16 Nov 2026) explicitly removed the Yoga 6
30-minute scheduled task at the owner's direction. Do not reinstate it.
The current V12 step is **in-process** automatic handoff only. A
persistent *independent* supervisor remains an unsatisfied separate
objective unless expressly authorized and verified without replacing
the owner's scheduler decision. No claim of unattended cross-session
operation is supported.

## Executable V12 behavior

After genuinely accepted V11, the existing normal
`scripts/run_v3_yoga6_recovery_worker.py --source-free-advance`
must immediately invoke
`app_generator/runtime/v3_private_nonmerging_pr_readiness.py`.
The V12 stage:

1. Reuses authoritative strict V9 source/CI/clean-working-tree preflight
   including original release bundles.
2. Verifies the immutable signed V11 receipt and its exact source SHA,
   proposed package digest, pinned public base, and 21-file scope.
3. Checks local patch bytes against signed V11 digest and independently
   parses all 21 `diff --git` headers, refusing path injection,
   changed 9.7 routes, duplicate files and mismatched paths.
4. Performs **only a remote read** of existing public `main` and
   refuses divergence from the pinned SHA.
5. Atomically stages an immutable local PR title/body *draft* and a
   source-bound, signed private V12 result. A restart refuses altered
   private draft bytes or changed signed predecessor.
6. Performs **no** GitHub branch push, PR creation, merge, deployment,
   Gemini request or scheduled task creation.

The review draft is conspicuously labeled **NOT A CREATED GITHUB PULL
REQUEST** and does not claim an academic learner pilot, complete
external scientific acceptance, or public release authorization.
Historical C3 remains `FAILED_LIMITED_CAMPAIGN`.

## Required acceptance before closure

- Fault injection for forged predecessor, patch tamper, extra route 9.7,
  mismatched old/new diff paths, moved public HEAD, altered draft at
  restart, missing patch and changed source identity.
- Normal worker synthetic in-process V11→V12 dispatch,
  wrong/failed status exits 3, plus independent previous stages.
- Strict regression-contract validation, exact new-head hosted CI.
- **Actual** owner Yoga 6 normal source-free V1–V12 run exit 0,
  and immutable signed V12 receipt tied to genuine V11.
- Never mark public publication completed without separately
  authorized real operation and release evidence.

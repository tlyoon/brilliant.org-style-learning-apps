# `--selection-mode auto` completion roadmap

This document records the remaining productionization phases after the initial continuous multi-PC coordinator/recovery implementation.

## Phase 1 — Continuous coordinated generation and recovery

Implemented by `feature/continuous-auto-mode` / PR #43.

The Phase-1 worker:

- discovers every controlled Google Drive `source.pdf` below the configured source root;
- claims work atomically through the Apps Script coordinator;
- uses leases and heartbeats so abandoned work becomes recoverable;
- prioritizes interrupted work last owned by another worker before untouched work;
- stores only parsed generation-stage JSON as durable shared checkpoints;
- restores compatible checkpoints on another PC;
- continues taking globally available jobs until the queue is complete;
- waits when all remaining unfinished work is leased elsewhere;
- treats terminal failures as a non-zero global completion blocker.

## Phase 2 — Durable shared publication

Implemented on `feature/auto-durable-publication` on top of Phase 1.

### Production invariant

A globally coordinated auto worker must never mark a job `generated` when the resulting artifacts exist only in one worker's local checkout.

Therefore continuous auto mode requires:

```toml
git_publish = true
```

The existing one-job orchestrator publishes validated artifacts through the configured Git remote before the auto coordinator marks the lease `generated`. The durable handoff can be an open PR/remote branch or a merged result according to the configured Git policy.

If `git_publish=false`, both auto doctor and auto execution fail early with `AUTO_MODE_BLOCKED`; no Drive job is claimed and no Gemini generation starts.

This keeps the authoritative roles separated:

```text
Google Drive       controlled source PDFs
Apps Script/Sheet  global queue, leases, recovery state
Checkpoint folder  recoverable parsed generation stages
GitHub              durable generated artifacts / PR handoff
Local PC            transient execution state only
```

## Phase 3 — Turnkey unattended operation and retry hardening

Phase 3 is the final planned productionization phase. It should complete the operational contract by addressing the crash windows around Git handoff and making auto mode a first-class persistent operating mode.

Planned Phase-3 requirements:

1. Allow `selection_mode = "auto"` as a validated persistent project configuration instead of requiring the CLI-only compatibility wrapper.
2. Make deterministic Git job branches idempotent across retries:
   - safely discard a stale local job branch that contains no job commit;
   - detect a previously pushed deterministic job branch for the same `job_key`;
   - recover/create the corresponding PR rather than regenerating the source;
   - reconcile the coordinator to `generated` after the remote handoff is confirmed.
3. Preserve the existing lease boundary while recovering publication so two workers cannot both finalize the same job.
4. Improve startup/exit diagnostics for unattended workers and make the supported launch command explicit.
5. Add regression tests for persistent-auto configuration and the Git publication recovery cases.

Phase 3 must build on the durable-publication invariant from Phase 2: a successful global `generated` state is never local-only.

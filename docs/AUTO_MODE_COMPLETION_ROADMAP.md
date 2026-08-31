# `--selection-mode auto` completion roadmap

This document records the productionization phases for continuous multi-PC automatic generation.

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

Implemented by `feature/auto-durable-publication` / PR #44 on top of Phase 1.

### Production invariant

A globally coordinated auto worker must never mark a job `generated` when the resulting artifacts exist only in one worker's local checkout.

Therefore continuous auto mode requires:

```toml
git_publish = true
```

The one-job orchestrator publishes validated artifacts through the configured Git remote before the auto coordinator marks the lease `generated`. The durable handoff can be an open PR/remote branch or a merged result according to the configured Git policy.

If `git_publish=false`, auto configuration/execution fails early; no Drive job is claimed and no Gemini generation starts.

This keeps the authoritative roles separated:

```text
Google Drive       controlled source PDFs
Apps Script/Sheet  global queue, leases, recovery state
Checkpoint folder  recoverable parsed generation stages
GitHub              durable generated artifacts / PR handoff
Local PC            transient execution state only
```

## Phase 3 — Turnkey unattended operation and retry hardening

Implemented by `feature/auto-turnkey-hardening` on top of Phase 2.

Phase 3 completes the intended auto-mode production contract:

1. `selection_mode = "auto"` is a validated persistent project configuration. The CLI compatibility shim that temporarily loaded auto as specific mode is removed.
2. Auto mode validates the same coordinated-operation prerequisites as distributed mode: a Google Apps Script coordinator URL, Google Drive discovery, and `git_publish=true`.
3. Before auto doctor trusts a locally visible generated package, the publisher synchronizes the configured Git base. This makes the synchronized Git base—not an arbitrary worker filesystem—the basis for existing generated content.
4. Deterministic job branches are retry-safe:
   - an empty stale local job branch is deleted safely and generation may restart;
   - a local job branch with an existing job commit is treated as recoverable rather than overwritten;
   - a previously pushed deterministic remote branch is treated as recoverable rather than regenerated;
   - an existing open PR is reused, a closed unmerged PR can be reopened, and an already merged PR is recognized.
5. Recovery runs under an exact coordinator lease. Two workers may discover the same stale handoff, but only one can claim and finalize it.
6. A recoverable Git handoff is validated against the expected generated artifact paths, published/reopened/merged according to policy, checkpoint storage is cleared, and the coordinator is marked `generated` without opening Gemini.
7. Publication failures clean only the known generated paths so a failed pre-commit publication does not unnecessarily leave the worker checkout dirty.
8. Worker diagnostics now explicitly report `AUTO_START`, `AUTO_RECOVERED`, `AUTO_IDLE`, and `AUTO_COMPLETE` states.
9. Regression tests cover persistent auto configuration, startup reconciliation behavior, empty stale-branch cleanup, and remote Git handoff recovery.

## Final operating form

Once the complete stack is merged and the coordinator is deployed, a project may make auto mode persistent:

```toml
[automation]
selection_mode = "auto"
coordinator_url = "https://script.google.com/macros/s/.../exec"

[git]
git_publish = true
```

The project-derived coordinator token remains machine-local and must be available in the configured coordinator-token environment variable.

With persistent auto mode configured, the normal commands are:

```powershell
python -m app_generator doctor
python -m app_generator run
```

The explicit override remains available when desired:

```powershell
python -m app_generator doctor --selection-mode auto
python -m app_generator run --selection-mode auto
```

Auto workers are expected to start from a clean repository. They synchronize the configured Git base before coordinated work and use GitHub as the durable generated-content handoff.

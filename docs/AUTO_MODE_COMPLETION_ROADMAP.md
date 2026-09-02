# `--selection-mode auto` productionization record

This document records the completed productionization phases for continuous multi-PC automatic generation. For current operating instructions use `docs/PDF_TO_APP_QUICKSTART.md` and `docs/CONTINUOUS_AUTO_TESTING.md`.

## Phase 1 — Continuous coordinated generation and recovery

Implemented and merged through PR #43.

The worker gained Drive inventory discovery, atomic coordinator claims, leases/heartbeats, interrupted-job recovery priority, durable parsed-stage checkpoints, cross-PC restoration, continuous queue processing, idle polling, and terminal-failure completion blocking.

## Phase 2 — Durable shared publication

Implemented and merged through PR #44.

Production invariant:

```text
A coordinated job must not be marked globally generated while its artifacts exist only on one PC.
```

Therefore `auto`/`distributed` require:

```toml
[git]
git_publish = true
```

Validated artifacts are durably handed off through Git before the coordinator marks the job generated.

## Phase 3 — Turnkey retry and handoff recovery

Implemented and merged through PR #45.

This completed persistent `auto` configuration, deterministic/recoverable job branches, stale local branch cleanup, pushed-branch/PR reconciliation, merged-PR recognition, exact-lease recovery, checkpoint cleanup, synchronized-base checks, and explicit auto diagnostics.

## Phase 4 — Repository-managed coordinator infrastructure

Implemented and merged through PR #46.

The current preferred architecture removes routine manual Apps Script provisioning from worker PCs.

With:

```toml
[automation]
coordinator_url = ""
```

an empty URL selects repository-managed coordinator infrastructure. An explicit valid Google Apps Script URL remains backward-compatible external mode.

Managed mode uses:

- one-time privileged `coordinator-bootstrap` on a trusted administrator PC;
- a refreshable administrator credential stored in a private GitHub Actions secret;
- a serialized `ensure-coordinator.yml` GitHub Actions deployment/repair workflow;
- private Drive metadata for worker discovery;
- private job ledger/checkpoint resources;
- live coordinator health verification before coordinated work begins.

Ordinary worker PCs do not need Apps Script deployment credentials and do not repeat the bootstrap.

## Current operating form

A project using continuous auto mode normally has:

```toml
[automation]
selection_mode = "auto"
coordinator_url = ""

[git]
git_publish = true
```

The one-time project bootstrap is:

```powershell
python -m app_generator coordinator-status --config <generated-local-config>
python -m app_generator coordinator-bootstrap --config <generated-local-config>
```

Subsequent worker readiness can be checked with:

```powershell
python -m app_generator coordinator-ensure --config <generated-local-config>
```

Normal auto operation is:

```powershell
python -m app_generator doctor --config <generated-local-config> --selection-mode auto
python -m app_generator run --config <generated-local-config> --selection-mode auto
```

The generated local config filename is workstation-specific; use the filename printed by `sync-workstation.cmd` rather than assuming `project.local.toml` on every PC.

## Authority separation

```text
Google Drive             controlled source PDFs
Managed coordinator      queue, leases, job/recovery state
Checkpoint storage       recoverable parsed generation stages
GitHub                    durable generated artifacts / PR handoff
Local PC                  transient execution state
Repository documentation current same-revision operating instructions
```

Generated work remains draft until qualified human review, regardless of coordinator or Git handoff status.

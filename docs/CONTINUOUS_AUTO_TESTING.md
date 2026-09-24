# Continuous auto mode: current operation and two-PC verification

This document describes Drive-native continuous auto mode. Normal `auto` operation no longer uses the repository-managed Apps Script/Google Sheet coordinator. See `docs/DRIVE_NATIVE_AUTO_COORDINATION.md` for the protocol.

Use documentation from the same `main` revision that you are running.

## Preconditions

Each worker PC should have:

- the same current `main` revision;
- a successful `sync-workstation.cmd` run;
- the project-scoped Google Desktop OAuth client JSON;
- writable Google Drive authorization for the configured OAuth account;
- Git/GitHub credentials for durable publication;
- a clean Git checkout;
- the local generated config filename printed by synchronization.

Continuous auto mode requires `git_publish=true` and defaults to `coordination_backend = "drive"`.

The first run after upgrading from read-only Drive authorization may open Google consent once to grant writable Drive scope. No Apps Script bootstrap, Sheet, worker coordinator token, or coordinator health check is required.
## Verify each PC before a multi-PC run

```powershell
git switch main
git fetch origin
git status -sb
git rev-parse HEAD
.\sync-workstation.cmd --quick
```

Then run:

```powershell
$py = (Resolve-Path ".\.venv\Scripts\python.exe").Path
$config = ".\<generated-local-config>.toml"
& $py -m app_generator run --help
& $py -m app_generator doctor --config $config --selection-mode auto
```

Both PCs should report the same `main` SHA. Auto doctor is a non-generation queue preview: it reads Drive coordination markers but must not create a claim or upload a PDF to Gemini.

## Recovery test

1. On PC A start unrestricted auto mode.
2. Allow a fresh section to complete several generation stages.
3. Stop PC A with `Ctrl+C`, simulate a technical failure, or terminate the worker.
4. On PC B run auto doctor, then start auto mode.

Expected behavior: PC B can acquire the interrupted section after the old lease is no longer active, reconstruct parsed-stage checkpoints from Drive events, continue from the last valid stage, and publish through Git before Drive success is recorded.
## Targeted auto test

On PC A run a protected single target:

```powershell
& $py -m app_generator doctor --config $config --selection-mode auto --pdf-subchapter-path 8.6
& $py -m app_generator run --config $config --selection-mode auto --pdf-subchapter-path 8.6
```

At the same time PC B may run unrestricted auto mode.

Expected behavior:

- PC A offers only 8.6 to Drive claim election and never falls through;
- if PC A wins 8.6, PC B selects another eligible job;
- if PC B already owns 8.6, PC A waits for that exact target;
- compatible checkpoints remain recoverable across machines;
- already successful 8.6 exits without regeneration;
- a missing or terminally failed target is reported instead of substituted.

Use targeted auto rather than ordinary `specific` mode whenever another auto worker may be active, because specific mode intentionally does not reserve a shared lease.

## Concurrency test

Start unrestricted auto mode simultaneously on two or more PCs. Claims may briefly coexist, but deterministic Drive election must leave exactly one elected owner per job. Losing workers delete only their own claim and continue to other eligible work.
## Lease-expiry fencing test

For a controlled test, stop the winning PC long enough to exceed `lease_seconds`, then allow another PC to claim the same job. Restart the old process only after the new claim exists.

Expected behavior:

- the old claim is treated as expired from Drive server timestamps;
- the old worker cannot revive it with a late heartbeat;
- `LeaseLostError` prevents stale publication;
- the new elected worker is the only worker allowed to proceed.

## Git handoff recovery test

If a worker crashes after pushing a deterministic job branch or PR, restart auto mode from a clean synchronized checkout.

Expected behavior:

- the existing valid remote handoff is reconciled under an exact Drive lease;
- a valid branch/PR is reused rather than overwritten;
- merged handoffs are recognized;
- Gemini is not rerun solely because the previous worker disappeared after durable publication.

## Source-corpus invalidation test

Change or replace a supplementary sibling PDF while leaving `source.pdf` unchanged. Auto doctor should now derive a different job identity for that subchapter. Old lease/checkpoint/success events remain historical and must not be reused for the changed corpus.
## Safety boundary

Shared Drive recovery state may contain lease metadata, failure metadata, and parsed generation-stage JSON tied to the exact corpus job key. It must not contain source PDF bytes, OAuth credentials, browser state, cookies, raw Gemini responses, machine-local paths, or general diagnostics.

Final repository content is installed/published only after validation succeeds. Generated content remains draft until qualified human review.

## Stopping and retrying workers

`Ctrl+C` is the normal manual stop. If a machine disappears, lease expiry makes the job recoverable. If repeated attempts exhaust `max_job_attempts`, review the failure and explicitly reset only the verified target:

```powershell
& $py -m app_generator coordinator-retry-failed --config $config --pdf-subchapter-path 9.1 --confirm
& $py -m app_generator doctor --config $config --selection-mode auto --pdf-subchapter-path 9.1
```

The command name is retained for compatibility; under the Drive backend it writes a retry-reset event and does not contact Apps Script.

## Troubleshooting

- `Configuration file does not exist` — pass the filename printed by `sync-workstation.cmd`.
- Google requests new Drive consent after upgrade — approve the writable scope once on that workstation; the former read-only token cannot create coordination markers.
- no job is claimable but work remains — another active Drive lease may own it; auto waits and polls.
- `LEASE_LOST` — the worker is no longer the elected unexpired owner; do not force publication from that process.
- dirty/diverged Git — resolve intentionally before auto mode; do not reset blindly.
- transient Gemini restart — recovery uses parsed-stage checkpoints and the authenticated automation browser profile.

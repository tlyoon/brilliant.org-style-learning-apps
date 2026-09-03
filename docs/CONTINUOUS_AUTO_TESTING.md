# Continuous auto mode: current operation and two-PC verification

This document describes the continuous-auto behavior on the current `main` branch. It replaces the older branch-only/manual Apps Script test procedure.

Use the documentation from the same `main` revision that you are running; see `docs/DOCUMENTATION_MAINTENANCE.md`.

## Preconditions

Each worker PC should have:

- the same current `main` revision;
- a successful `sync-workstation.cmd` run;
- the project-scoped Google Desktop OAuth client JSON in the derived local credential directory;
- working Drive authorization for the configured Google account;
- Git/GitHub credentials appropriate to the configured durable publication policy;
- a clean Git checkout;
- the local generated config filename printed by synchronization.

Continuous auto mode also requires `git_publish=true`.

## Managed coordinator bootstrap

Current `main` uses repository-managed coordinator infrastructure when `coordinator_url` is empty.

On any PC, check status using that PC's generated local config:

```powershell
$py = (Resolve-Path ".\.venv\Scripts\python.exe").Path
$config = ".\<generated-local-config>.toml"
& $py -m app_generator coordinator-status --config $config
```

If the coordinator is already current, do not bootstrap again.

If it is missing, choose **one trusted administrator PC** and run:

```powershell
gh auth status
& $py -m app_generator coordinator-bootstrap --config $config
```

The bootstrap may open Google consent for Apps Script/Drive administration scopes. It stores the refreshable administrator credential in the repository's private GitHub Actions secret, requests the serialized deployment, and waits for live health.

### First-project web-app recovery

If bootstrap reports no reachable `WEB_APP`, use the exact Apps Script editor URL in the error.
Do not select a similarly named older script project. In that exact project, reload the editor,
run `initializeCoordinator`, and create one **Web app** deployment with **Execute as: Me** and
**Who has access: Anyone**. Register its complete `/exec` URL:

```powershell
gh workflow run ensure-coordinator.yml --ref main -f project_name=<project_name> -f web_app_url=<web-app-url>
& $py -m app_generator coordinator-ensure --config $config
```

The workflow rejects URLs from another Apps Script project. If a new deployment is briefly
unreachable while Google propagates it, wait and rerun the same command rather than creating or
archiving another deployment. This recovery is once per project identity, not once per PC.

Other worker PCs do not repeat bootstrap. Verify readiness with:

```powershell
& $py -m app_generator coordinator-ensure --config $config
```

There is no normal requirement to manually paste `Code.gs`, create the ledger/checkpoint folder, or configure Apps Script properties on each PC in managed mode.

## Verify each PC before a multi-PC run

```powershell
git switch main
git fetch origin
git status -sb
git rev-parse HEAD
.\sync-workstation.cmd --quick
```

Then:

```powershell
& $py -m app_generator run --help
& $py -m app_generator doctor --config $config --selection-mode auto
```

Both PCs should report the same `main` SHA. CLI help should expose `specific`, `auto`, and `distributed` selection modes.

Auto doctor is a non-generation queue preview; it must not claim a generation job or upload a PDF to Gemini.

## Recovery test

1. On PC A, start:

   ```powershell
   & $py -m app_generator run --config $config --selection-mode auto
   ```

2. Allow a fresh section to complete several generation stages.
3. Stop PC A with `Ctrl+C`, or simulate a recoverable technical failure.
4. Confirm PC A exits/stops rather than continuing to hold the job indefinitely; an abandoned lease also becomes recoverable after expiry.
5. On PC B, run:

   ```powershell
   & $py -m app_generator doctor --config $config --selection-mode auto
   ```

6. Start PC B auto mode:

   ```powershell
   & $py -m app_generator run --config $config --selection-mode auto
   ```

Expected behavior:

- PC B may claim the interrupted/recoverable section before untouched work according to coordinator priority;
- compatible source-version-bound parsed-stage checkpoints are restored;
- already-completed valid stages are not needlessly regenerated;
- validated artifacts are handed off durably through Git before the job is globally marked generated;
- PC B then continues to the next globally eligible job.

## Concurrency test

Run auto mode simultaneously on PC A and PC B:

```powershell
& $py -m app_generator run --config $config --selection-mode auto
```

Expected behavior:

- active leases never assign the same source job to two workers;
- workers renew leases while generation is active;
- if all unfinished work is leased elsewhere, a worker waits/polls rather than declaring completion;
- recoverable interrupted work can move between PCs;
- a zero/success completion is valid only when the globally coordinated source inventory is successful;
- terminal failures block false global success.

## Git handoff recovery test

If a worker crashes after creating/pushing a deterministic job branch or PR, restart auto mode from a clean synchronized checkout.

Expected behavior:

- the existing valid remote handoff is reconciled under an exact lease;
- a valid open PR/remote branch is reused rather than overwritten;
- merged handoffs are recognized;
- Gemini is not rerun solely because the previous worker disappeared after durable publication.

## Safety boundary

Shared recovery state may contain parsed generation-stage JSON tied to the exact job/source version. It must not contain source PDFs, OAuth credentials, browser state, machine-local paths, cookies, raw Gemini responses, or general diagnostics.

Final repository content is installed/published only after validation succeeds. Generated content remains a draft until qualified human review.

## Stopping workers

`Ctrl+C` is the normal manual stop. The CLI reports interruption and returns an active auto lease safely when possible. If a machine disappears unexpectedly, lease expiry makes the job recoverable.

## Troubleshooting

- `Configuration file does not exist: project.local.toml` — pass `--config` with the filename printed by `sync-workstation.cmd`.
- `Managed coordinator: missing` — bootstrap once on a trusted administrator PC if the project has never been provisioned.
- coordinator health failure — run `coordinator-ensure`; managed mode may request the serialized repair/deployment workflow.
- dirty/diverged Git — resolve intentionally before starting auto mode; do not reset blindly.

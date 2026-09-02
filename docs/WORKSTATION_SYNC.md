# One-click workstation synchronization

Start with `docs/PDF_TO_APP_QUICKSTART.md` for the complete current workflow. This document focuses on synchronization, machine-local state, generated configuration, and troubleshooting.

Operational documentation is versioned with the code. Read this file from the same `main` revision that you are running; see `docs/DOCUMENTATION_MAINTENANCE.md`.

## Configuration authority

The tracked project authority is:

```text
config/configure_project.toml
```

Its `[project].project_name` determines the environment namespace and default Windows state root. For example:

```text
project_name = "BrilliantContentGenerator"
        ↓
%LOCALAPPDATA%\BrilliantContentGenerator
```

A recycled project such as `something_else` gets:

```text
%LOCALAPPDATA%\something_else
```

Machine-local paths remain tokenized in the tracked project file and are materialized per PC.

## Machine-local security boundary

Never place these in Git:

- Google OAuth client/token JSON;
- coordinator or GitHub token values;
- passwords, cookies, or `.env` files;
- Chrome profiles;
- controlled PDFs;
- run directories or raw Gemini responses.

The project-derived state root normally contains:

```text
%LOCALAPPDATA%\<project_name>\workstation-sync.toml
%LOCALAPPDATA%\<project_name>\credentials\drive-oauth-client.json
%LOCALAPPDATA%\<project_name>\credentials\drive-oauth-token.json
%LOCALAPPDATA%\<project_name>\chrome-profile\
%LOCALAPPDATA%\<project_name>\runs\
```

The same Google Cloud Desktop OAuth client JSON may be securely copied into multiple trusted PCs/project-scoped credential directories when appropriate. Keep each project's path independent and let each PC/project maintain its own generated OAuth token.

## First run on each PC

Prerequisites: Python 3.12, Git, Node.js, current Chrome, and network access. GitHub CLI is also required for repository-managed coordinator bootstrap and convenient GitHub operations.

A new checkout should first be confirmed current:

```powershell
git switch main
git fetch origin
git status -sb
```

If behind:

```powershell
git pull --ff-only origin main
```

Initialize only workstation settings if desired:

```powershell
python -m scripts.sync_configured_workstation --init-settings-only
```

Then run:

```powershell
.\sync-workstation.cmd
```

The synchronizer creates/verifies `.venv`, installs dependencies when needed, renders the project configuration for that PC, and in full mode runs repository tests and generator doctor.

## Generated local configuration filename

The workstation settings contain:

```toml
[output]
generated_config_file = "project.local.toml"
```

for a newly initialized default workstation. Older or deliberately customized machine-local settings may use another allowed ignored name, for example:

```text
generator.shared.local.toml
```

The synchronizer prints the exact result:

```text
Installed config/configure_project.toml as <generated-local-config>.toml (...)
```

That printed filename is authoritative for direct CLI commands on that PC.

If it is `project.local.toml`, the CLI default works:

```powershell
& .\.venv\Scripts\python.exe -m app_generator doctor
```

If it is another name, pass it explicitly:

```powershell
& .\.venv\Scripts\python.exe -m app_generator doctor --config .\generator.shared.local.toml
```

Do not copy a generated local config filename from another PC and assume it is correct locally.

## Routine synchronization

For a normal full validation:

```powershell
.\sync-workstation.cmd
```

After a successful full validation, routine code/config refresh can use:

```powershell
.\sync-workstation.cmd --quick
```

Quick mode still fetches the configured remote, refuses dirty/diverged state, fast-forwards only, validates/renders the tracked project config, and verifies the Python environment. It skips the full test suite and Drive doctor.

The synchronizer itself safely performs the Git fetch/fast-forward operation, but `git fetch origin` plus `git status -sb` remains a useful non-destructive manual check of whether a PC is current.

## Safety behavior

The synchronizer:

1. refuses a dirty worktree;
2. fetches the configured remote and branch;
3. refuses local-only/diverged commits and fast-forwards only;
4. creates/verifies Python 3.12 `.venv`;
5. caches package installation using dependency fingerprints;
6. reads `config/configure_project.toml` from the synchronized checkout;
7. derives `${PROJECT_ENV_PREFIX}`, `${STATE_ROOT}`, and `${REPO_ROOT}`;
8. writes the configured ignored local TOML atomically;
9. verifies project/workstation Google account consistency;
10. in full mode runs lint, content validation, unit tests, JavaScript syntax checks, and generator doctor.

`doctor` does not upload to Gemini.

## Live run shortcut

An explicit live run can be requested with:

```powershell
.\sync-workstation.cmd --run-generator
```

It reuses a successful validation stamp only when the synchronized revision/configuration/dependency/checkout identity is unchanged. Otherwise it reruns the required checks before live generation.

For controlled operator work, direct CLI commands with the printed generated config filename are clearer, especially when selecting `specific` versus `auto` mode.

## Managed coordinator on worker PCs

The coordinator is project-wide, not PC-specific. For repository-managed mode, one trusted administrator PC performs `coordinator-bootstrap` once. Ordinary worker PCs only need their normal Drive authorization and synchronized repository.

Check status using the local generated config:

```powershell
& .\.venv\Scripts\python.exe -m app_generator coordinator-status --config .\<generated-local-config>.toml
```

If the project is already bootstrapped, do not bootstrap again on every PC.

## Reusing the package for another project

Change `project_name` and other project-dependent values through `config/configure_project.toml` on a reviewed branch. The new project automatically receives its own `%LOCALAPPDATA%\<project_name>` state root, OAuth/token paths, Chrome profile, run state, environment namespace, and managed-coordinator project identity.

See `docs/GENERIC_PROJECT_SETUP.md` for the full recycling procedure.

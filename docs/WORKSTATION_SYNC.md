# One-click workstation synchronization

`sync-workstation.cmd` safely updates an existing Windows checkout, prepares its Python environment, renders the repository-tracked generator configuration for that PC, and validates the workstation. A separate `--quick` mode provides a fast routine update without weakening the checks required for live generation.

## Configuration authority

The active project-specific configuration is:

```text
config/configure_project.toml
```

It is versioned with the generator code and reaches every authorized PC through the normal Git pull. When this code package is recycled for another subject or textbook, change the non-secret project-dependent values in this file (or another explicitly documented file under `config/`) rather than editing Python source.

The `[project]` table supplies the canonical `project_name`. The synchronizer derives the environment namespace and all default local paths from that name. For example, `MyLearningProject` becomes `MY_LEARNING_PROJECT` for environment-variable names and `%LOCALAPPDATA%\MyLearningProject` for local state.

`config/configure_project.toml` is the normal user-facing project authority. `config/project.toml` is retained for compatibility with older tooling/tests during migration and is not selected by `sync-workstation.cmd`.

The tracked project file contains only approved, non-secret, machine-independent settings. It retains `${REPO_ROOT}`, `${STATE_ROOT}`, and `${PROJECT_ENV_PREFIX}` tokens where values should be materialized per workstation. The synchronizer accepts only an explicit allow-list of generator fields and refuses unknown fields, oversized files, symbolic links, invalid TOML, or an invalid repository-root token.

## Security boundary

Never place any of these items in Git or in the tracked project configuration:

- Google OAuth client JSON or OAuth token JSON;
- Google, GitHub, or coordinator token values;
- passwords, cookies, or `.env` files;
- Chrome profiles;
- controlled source PDFs or generator run directories.

Each PC must provision its own Google Desktop-app OAuth client outside the repository. Its default path is derived from `project_name`:

```text
%LOCALAPPDATA%\<project_name>\credentials\drive-oauth-client.json
```

The first generator `doctor` run opens Google's read-only Drive authorization flow and writes that PC's OAuth token beside the client file. Google Drive remains the controlled source-PDF service; it is not used to distribute machine-local configuration. Git and GitHub authentication also remain local to each PC.

## First run on each PC

Prerequisites are Python 3.12, Git, current Chrome, Node.js, network access, and an existing repository checkout. Authenticate Git locally before running the synchronizer when the repository requires it.

Double-click `sync-workstation.cmd`. The expected Google account comes from `config/configure_project.toml`, and a new workstation defaults to the `main` branch. Command-line options can override initialization values where supported.

To create only the machine-local settings first, without fetching Git or running `doctor`, run the same configured sync module used by the batch entrypoint:

```powershell
python -m scripts.sync_configured_workstation --init-settings-only
```

The first run saves the effective machine-local values outside the repository in:

```text
%LOCALAPPDATA%\<project_name>\workstation-sync.toml
```

Later runs require only a double-click. To change the branch or machine-local expected Google account, edit that machine-local, non-secret file.

## Routine quick synchronization

After the first full validation succeeds, use quick mode for ordinary updates from an already configured PC:

```powershell
.\sync-workstation.cmd --quick
```

Quick mode still refuses a dirty or diverged worktree, fast-forwards from the configured Git branch, validates and renders `config/configure_project.toml`, and verifies the installed Python environment. It skips the full repository test suite and Drive `doctor`.

Package installation is protected by a fingerprint of `pyproject.toml`, `requirements-generator.txt`, and `requirements-dev.txt`. If that fingerprint is unchanged and the required imports succeed, the synchronizer reuses `.venv` instead of running `pip install -e .`. A changed dependency manifest or failed import verification automatically triggers installation.

Use the default command when generator, configuration, synchronization, or dependency changes need full validation:

```powershell
.\sync-workstation.cmd
```

## Safety and behavior

The synchronizer:

1. refuses a dirty worktree;
2. fetches the configured remote and switches to the configured branch;
3. fast-forwards only and refuses local-only or diverged commits;
4. creates or verifies `.venv` with Python 3.12 and installs the repository package only when its dependency fingerprint is absent, changed, or fails import verification;
5. reads `config/configure_project.toml` from the synchronized checkout;
6. validates it, derives `${PROJECT_ENV_PREFIX}`, `${STATE_ROOT}`, and `${REPO_ROOT}` from the project identity and workstation, and atomically writes the ignored `project.local.toml`;
7. verifies that the project and machine-local expected Google accounts agree;
8. in full mode, runs lint, content validation, unit tests, the JavaScript syntax check, and generator `doctor`; quick mode skips this step. A successful full check is recorded outside the repository for the exact checkout and configuration.

`doctor` verifies Drive authorization, source discovery/download, checksums, and provenance, but does not upload a PDF to Gemini. A live run must be explicitly requested from a terminal:

```powershell
.\sync-workstation.cmd --run-generator
```

When the same checkout has already completed a successful full synchronization, that option reuses the recorded repository validation and skips the duplicate pre-run test suite and `doctor`. The live run still authenticates Drive, resolves and downloads the selected PDF, and validates its checksum and provenance before uploading it to Gemini. If the Git revision, dependency manifests, tracked project configuration, or checkout path changed—or no successful full check was recorded—`--run-generator` automatically runs the full tests and `doctor` first. `--quick` does not create this validation record. `--quick` and `--run-generator` are mutually exclusive. Leave `git_publish = false` and `git_auto_merge = false` until repository handoff is intentionally enabled. Auto-merge additionally requires a non-draft PR, honors GitHub branch protection, and leaves the package itself in `draft` status.

## Reusing the package for another project

For a different subject/textbook, edit `config/configure_project.toml` through a branch/PR. At minimum review the project identity, Drive source root, Gemini Gem/account, default subchapter, source filename/pattern, source ID prefix, edition/provenance wording, coordinator settings, and Git publishing policy. Machine-local paths and environment namespaces should remain tokenized so `sync-workstation.cmd` derives them automatically on each PC.

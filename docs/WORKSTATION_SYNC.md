# One-click workstation synchronization

`sync-workstation.cmd` safely updates an existing Windows checkout, prepares its Python environment, renders the repository-tracked generator configuration for that PC, and validates the workstation. A separate `--quick` mode provides a fast routine update without weakening the checks required for live generation.

## Configuration authority

The active project configuration is:

```text
config/project.toml
```

It is versioned with the generator code and reaches every authorized PC through the normal Git pull. Changes to project generator behavior therefore use the same branch, pull-request review, and rollback history as the code that consumes them.

The `[project]` table supplies the canonical `project_name`. The synchronizer derives the environment namespace and all default local paths from that name. For example, `BrilliantContentGenerator` becomes `BRILLIANT_CONTENT_GENERATOR` for environment-variable names and `%LOCALAPPDATA%\BrilliantContentGenerator` for local state.

Legacy generator example TOMLs have been removed. `config/project.toml` is the only tracked runtime configuration authority.

The tracked file contains only approved, non-secret, machine-independent settings. It retains `${REPO_ROOT}` exactly. The synchronizer accepts only an explicit allow-list of generator fields and refuses unknown fields, oversized files, symbolic links, invalid TOML, or an invalid repository-root token.

## Security boundary

Never place any of these items in Git or in the tracked project configuration:

- Google OAuth client JSON or OAuth token JSON;
- Google, GitHub, or coordinator token values;
- passwords, cookies, or `.env` files;
- Chrome profiles;
- controlled source PDFs or generator run directories.

Each PC must provision its own Google Desktop-app OAuth client outside the repository. Its default path is derived from `project_name`:

```text
%LOCALAPPDATA%\BrilliantContentGenerator\credentials\drive-oauth-client.json
```

The first generator `doctor` run opens Google's read-only Drive authorization flow and writes that PC's OAuth token beside the client file. Google Drive remains the controlled source-PDF service; it is not used to distribute configuration. Git and GitHub authentication also remain local to each PC.

## First run on each PC

Prerequisites are Python 3.12, Git, current Chrome, Node.js, network access, and an existing repository checkout. For the private GitHub repository, authenticate Git locally before running the synchronizer.

Double-click `sync-workstation.cmd`. The expected Google account comes from `config/project.toml`, and a new workstation defaults to the `main` branch. Command-line options can override either value during initialization.

To create only the machine-local settings first, without fetching Git or running `doctor`:

```powershell
python scripts\sync_workstation.py --init-settings-only
```

The first run saves the effective machine-local values outside the repository in:

```text
%LOCALAPPDATA%\BrilliantContentGenerator\workstation-sync.toml
```

Later runs require only a double-click. To change the branch or expected Google account, edit that machine-local, non-secret file.

## Routine quick synchronization

After the first full validation succeeds, use quick mode for ordinary updates from an already configured PC:

```powershell
.\sync-workstation.cmd --quick
```

Quick mode still refuses a dirty or diverged worktree, fast-forwards from the configured Git branch, validates and renders `config/project.toml`, and verifies the installed Python environment. It skips the full repository test suite and Drive `doctor`.

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
5. reads `config/project.toml` from the synchronized checkout;
6. validates it, derives `${PROJECT_ENV_PREFIX}` and `${STATE_ROOT}` from `project_name`, renders all approved tokens, and atomically writes the ignored `project.local.toml`;
7. verifies that the project and machine-local expected Google accounts agree;
8. in full mode, runs lint, content validation, unit tests, the JavaScript syntax check, and generator `doctor`; quick mode skips this step, while live generation forces it.

`doctor` verifies Drive authorization, source discovery/download, checksums, and provenance, but does not upload a PDF to Gemini. A live run must be explicitly requested from a terminal:

```powershell
.\sync-workstation.cmd --run-generator
```

That option always forces repository tests and Drive `doctor`, even when the machine-local `run_tests` or `run_doctor` setting is `false`. It uploads the controlled source to Gemini and starts generation only after those checks pass. `--quick` and `--run-generator` are mutually exclusive. Leave `git_publish = false` in the project configuration until automated publishing and the distributed coordinator are intentionally enabled.

## Genericization phase status

Phase 8 adds a two-project materialization test proving distinct environment namespaces, local state, OAuth paths, Chrome profiles, coordinator variables, Drive roots, Gems, and source IDs. The reusable setup is documented in `docs/GENERIC_PROJECT_SETUP.md`.

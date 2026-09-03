# Recycle the generator for another textbook project

Use `docs/PDF_TO_APP_QUICKSTART.md` for the complete normal workflow. This file is the specialist guide for turning the repository into a new project without leaking state or credentials from another project.

Operational documentation is versioned with the code; see `docs/DOCUMENTATION_MAINTENANCE.md`.

## 1. Start from current `main`

```powershell
git switch main
git fetch origin
git status -sb
```

If behind:

```powershell
git pull --ff-only origin main
```

Create a configuration branch:

```powershell
git switch -c config/new-textbook-project
```

## 2. Create a new project identity

Preview:

```powershell
python scripts\configure_project.py `
  --project-name "NewLearningProject" `
  --source-root-url "https://drive.google.com/open?id=SOURCE_FOLDER_ID" `
  --gem-url "https://gemini.google.com/gem/GEM_ID" `
  --login-name "authorized@example.com" `
  --gem-name "subject content generator"
```

Review the diff, then repeat with `--apply` when correct.

The tracked project authority is:

```text
config/configure_project.toml
```

Review at minimum:

- `project.project_name`;
- Drive source root and controlled source naming;
- Gemini Gem URL/editor/name/account;
- default subchapter selector;
- provenance/rights wording;
- automation mode and coordinator policy;
- Git publication/PR/merge policy;
- model preference policy.

Keep `${PROJECT_SLUG}`, `${PROJECT_ENV_PREFIX}`, `${REPO_ROOT}`, and `${STATE_ROOT}` tokenized.

## 3. Understand project isolation

The project name determines the Windows state root:

```text
%LOCALAPPDATA%\<project_name>
```

For example:

```text
BrilliantContentGenerator
        ↓
%LOCALAPPDATA%\BrilliantContentGenerator

something_else
        ↓
%LOCALAPPDATA%\something_else
```

Derived machine-local locations include:

| Item | Location |
|---|---|
| Workstation settings | `%LOCALAPPDATA%\<project_name>\workstation-sync.toml` |
| OAuth client | `%LOCALAPPDATA%\<project_name>\credentials\drive-oauth-client.json` |
| OAuth token | `%LOCALAPPDATA%\<project_name>\credentials\drive-oauth-token.json` |
| Chrome profile | `%LOCALAPPDATA%\<project_name>\chrome-profile` |
| Run state | `%LOCALAPPDATA%\<project_name>\runs` |
| Generator env prefix | `<PROJECT_ENV_PREFIX>_GENERATOR_*` |
| Coordinator token env | `<PROJECT_ENV_PREFIX>_COORDINATOR_TOKEN` |

Do not make one project depend on another project's state directory.

### Reusing the Google Cloud OAuth client

The same Google Cloud **Desktop app OAuth client JSON contents** may be securely copied into multiple trusted project/PC credential directories when those projects intentionally use the same Google OAuth client.

Recommended:

```text
%LOCALAPPDATA%\ProjectA\credentials\drive-oauth-client.json
%LOCALAPPDATA%\ProjectB\credentials\drive-oauth-client.json
```

Both files may contain the same downloaded client definition, but each project/PC should normally maintain its own generated `drive-oauth-token.json`.

Do not point Project B at `%LOCALAPPDATA%\ProjectA\...`; independent paths make projects removable and recyclable without hidden coupling.

## 4. Validate and merge the project configuration

```powershell
python scripts\lint.py
python scripts\validate_content.py
python -m unittest discover -s tests -v
git diff --check
```

Commit the project configuration and related project-owned Gem text, push the branch, and merge it through review. Every PC should receive the same non-secret project authority through Git rather than copied local files.

## 5. Initialize each workstation

After the new project configuration reaches the intended branch/main:

```powershell
python -m scripts.sync_configured_workstation --init-settings-only
```

Place the Google Desktop OAuth client JSON at the new project's derived credential path, then run:

```powershell
.\sync-workstation.cmd
```

The synchronizer prints the exact generated local config filename. A default new workstation normally uses `project.local.toml`; an existing/customized machine may use another allowed name such as `generator.shared.local.toml`.

For direct CLI commands, pass `--config` whenever the printed filename is not `project.local.toml`.

## 6. Validate one specific source first

Example:

```powershell
$py = (Resolve-Path ".\.venv\Scripts\python.exe").Path
$config = ".\<generated-local-config>.toml"

& $py -m app_generator doctor --config $config --selection-mode specific --pdf-subchapter-path 8.2
& $py -m app_generator run --config $config --selection-mode specific --pdf-subchapter-path 8.2
```

A new project can initially keep:

```toml
git_publish = false
git_auto_merge = false
```

for a controlled specific-mode validation.

## 7. Enable repository-managed coordination for auto/distributed work

Current `main` supports repository-managed coordinator infrastructure.

For managed mode leave:

```toml
[automation]
coordinator_url = ""
```

An empty URL selects the managed GitHub Actions/Google Apps Script lifecycle. An explicit valid Apps Script URL selects backward-compatible external coordinator mode.

Continuous `auto` and `distributed` modes require:

```toml
[git]
git_publish = true
```

because a globally successful job must have durable generated artifacts, not files stranded on one PC.

After the new project configuration is merged and synchronized, use one trusted administrator PC:

```powershell
gh auth status
& $py -m app_generator coordinator-status --config $config
```

If the managed coordinator is missing, bootstrap it once for that **project identity**:

```powershell
& $py -m app_generator coordinator-bootstrap --config $config
```

This may request additional Google Apps Script/Drive administration consent and stores the refreshable administrator credential in the repository's private GitHub Actions secret. Ordinary worker PCs do not repeat the bootstrap.

A newly recycled `project_name` requires its own one-time bootstrap even when it reuses the same
Google Cloud project, OAuth Desktop client, and administrator account. A second PC joining an
already bootstrapped project does not repeat bootstrap.

### First-project web-app recovery

If bootstrap reports no reachable `WEB_APP` entry point:

1. Open only the exact Apps Script editor URL printed by the failure. Do not choose a project by
   display title because older projects may have the same name.
2. Reload the editor, run `initializeCoordinator`, and wait for **Execution completed**.
3. Create one **Web app** deployment with **Execute as: Me** and
   **Who has access: Anyone**.
4. Copy its complete `/exec` URL and register it:

```powershell
gh workflow run ensure-coordinator.yml --ref main -f project_name=<project_name> -f web_app_url=<web-app-url>
& $py -m app_generator coordinator-ensure --config $config
```

The workflow verifies that the deployment belongs to the expected generated script before writing
runtime metadata. If Google has not finished propagating a new deployment, wait briefly and rerun
the same command; do not create or archive another deployment just to retry.

Verify worker readiness with:

```powershell
& $py -m app_generator coordinator-ensure --config $config
```

Each recycled `project_name` has a distinct managed-coordinator identity/metadata scope even if several projects use the same Google account or OAuth Desktop client.

## 8. Start continuous auto mode

Preview without claiming work:

```powershell
& $py -m app_generator doctor --config $config --selection-mode auto
```

Run:

```powershell
& $py -m app_generator run --config $config --selection-mode auto
```

Multiple PCs may run the same project concurrently after synchronization and coordinator readiness. Leases prevent double-claiming; recoverable interrupted work is prioritized according to coordinator policy; checkpoints and Git handoff make recovery cross-PC capable.

## Intentional application contracts

These remain generic/versioned application behavior rather than textbook identity:

- one controlled PDF per generated package;
- numeric `chapter.section` source folders;
- the current activity/type/difficulty contract;
- English/Malay/Simplified-Chinese learner contract;
- calculator-free conceptual-activity policy;
- deterministic validation/provenance rules;
- source PDFs and credentials outside Git;
- generated content remains draft until qualified human review.

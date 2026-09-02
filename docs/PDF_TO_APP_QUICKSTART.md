# PDF textbook section to live review app: Windows quickstart

This is the canonical beginner-facing installation and operating guide for the current `main` branch. It covers one controlled `source.pdf`, workstation setup, Google authentication, specific generation, managed continuous-auto mode, review, and optional static deployment.

**Documentation freshness rule:** use this file from the same `main` revision that you are running. Operational changes must update the relevant documentation in the same PR; see `docs/DOCUMENTATION_MAINTENANCE.md`.

Specialist references:

- `docs/WORKSTATION_SYNC.md` — workstation synchronization and machine-local state;
- `docs/GENERIC_PROJECT_SETUP.md` — recycling the repository for another textbook/project;
- `docs/CONTINUOUS_AUTO_TESTING.md` — continuous auto-mode and multi-PC verification;
- `app_generator/README.md` — generator technical reference;
- `config/README.md` — configuration field reference.

Generation does **not** mean that content is approved, publishable, merged, or publicly deployed.

## 1. Supported source layout

The generator processes one PDF per subchapter. A supported Google Drive tree looks like:

```text
Textbook-or-source-root/
└── 8/
    ├── 8.1/
    │   └── source.pdf
    ├── 8.2/
    │   └── source.pdf
    └── 8.5/
        └── source.pdf
```

The immediate parent folder must look like `8.5`; the controlled filename is normally `source.pdf`.

Never commit source PDFs, OAuth files, tokens, browser profiles, cookies, raw Gemini responses, or generator run directories to Git.

## 2. Install prerequisites on each Windows PC

Install:

- Python 3.12;
- Git;
- Node.js;
- current Google Chrome;
- GitHub CLI (`gh`) for managed coordinator bootstrap and GitHub operations;
- VS Code or another editor if desired.

Check:

```powershell
py -3.12 --version
git --version
node --version
gh --version
```

For GitHub operations also check:

```powershell
gh auth status
```

## 3. Clone or refresh the repository

For a new PC:

```powershell
cd <projects-folder>
git clone https://github.com/tlyoon/brilliant.org-style-learning-apps.git
cd brilliant.org-style-learning-apps
git fetch origin
git status -sb
```

A freshly cloned current checkout normally shows:

```text
## main...origin/main
```

For an existing PC:

```powershell
git switch main
git fetch origin
git status -sb
```

If it shows `[behind N]`, update safely:

```powershell
git pull --ff-only origin main
```

`git fetch origin` updates the PC's knowledge of GitHub without changing working files. `git pull --ff-only origin main` updates local `main` only when a clean fast-forward is possible.

## 4. Understand the tracked project authority

The normal tracked project authority is:

```text
config/configure_project.toml
```

It contains non-secret project identity, Drive source root, Gemini Gem/account, automation policy, project-derived path templates, and Git handoff policy.

For a new recycled project, preview the configurator:

```powershell
python scripts\configure_project.py `
  --project-name "NewLearningProject" `
  --source-root-url "https://drive.google.com/open?id=SOURCE_FOLDER_ID" `
  --gem-url "https://gemini.google.com/gem/GEM_ID" `
  --login-name "authorized@example.com" `
  --gem-name "subject content generator"
```

Review the diff, then repeat with `--apply` when correct. Validate and merge that configuration through the normal PR workflow before distributing it to other PCs.

For a conservative first **specific-mode** project test, `git_publish = false` and `git_auto_merge = false` are valid. Continuous `auto` and `distributed` modes require durable Git publication and therefore require `git_publish = true`.

## 5. Project name determines the machine-local state root

On Windows, the project name determines the default local state root:

```text
%LOCALAPPDATA%\<project_name>\
```

For the current project:

```toml
[project]
project_name = "BrilliantContentGenerator"
```

so the default state root is:

```text
C:\Users\<user>\AppData\Local\BrilliantContentGenerator\
```

Important derived locations are:

```text
%LOCALAPPDATA%\<project_name>\workstation-sync.toml
%LOCALAPPDATA%\<project_name>\credentials\drive-oauth-client.json
%LOCALAPPDATA%\<project_name>\credentials\drive-oauth-token.json
%LOCALAPPDATA%\<project_name>\chrome-profile\
%LOCALAPPDATA%\<project_name>\runs\
```

A different project name, for example `something_else`, gets its own state root:

```text
%LOCALAPPDATA%\something_else\
```

### Google Cloud OAuth client JSON

Create/download a Google Cloud **Desktop app** OAuth client with the Drive API enabled. Place a secure copy at:

```text
%LOCALAPPDATA%\<project_name>\credentials\drive-oauth-client.json
```

The same Google Cloud Desktop OAuth client JSON contents may be securely copied into multiple trusted PCs and multiple project-scoped credential directories when those projects intentionally use the same Google OAuth client. Keep each project's path independent rather than making one project point into another project's state directory.

Each PC/project should normally maintain its own generated `drive-oauth-token.json`. Do not copy OAuth token files into Git or a shared project checkout.

## 6. Initialize and synchronize a workstation

To initialize only the machine-local settings:

```powershell
python -m scripts.sync_configured_workstation --init-settings-only
```

Then run the normal synchronizer:

```powershell
.\sync-workstation.cmd
```

A successful first run may create `.venv`, install dependencies, render the local generator configuration, run repository tests, and run generator doctor.

Watch the line:

```text
Installed config/configure_project.toml as <generated-local-config>.toml (...)
```

**Use the filename printed by `sync-workstation.cmd` as the authority for direct CLI commands on that PC.** The default new setting is normally `project.local.toml`, but existing machine-local workstation settings may deliberately use another allowed ignored filename such as `generator.shared.local.toml`.

Set a PowerShell variable after sync. Example:

```powershell
$config = ".\generator.shared.local.toml"   # replace with the filename printed on your PC
$py = (Resolve-Path ".\.venv\Scripts\python.exe").Path
```

If the printed file is `project.local.toml`, direct CLI commands can omit `--config`; otherwise pass it explicitly.

For routine synchronization after a successful full check:

```powershell
.\sync-workstation.cmd --quick
```

Use the full command again after generator/configuration/dependency changes:

```powershell
.\sync-workstation.cmd
```

## 7. Run a non-uploading doctor check

With an explicit local config variable:

```powershell
& $py -m app_generator doctor --config $config
```

For a specific section:

```powershell
& $py -m app_generator doctor --config $config --selection-mode specific --pdf-subchapter-path 8.5
```

Doctor checks configuration, Drive authorization, PDF discovery/download, checksum, and provenance. It does not upload a PDF to Gemini.

The first Drive authorization on a PC may open a Google browser consent flow and create that PC/project's `drive-oauth-token.json`.

## 8. Generate one selected subchapter

Start with a controlled specific-mode run when validating a new project:

```powershell
& $py -m app_generator run --config $config --selection-mode specific --pdf-subchapter-path 8.5
```

The generator opens the configured Gem/account, reconciles project-owned Gem fields, opens a fresh conversation, uploads the controlled PDF, generates/repairs the package, validates it, and installs the generated artifacts.

A successful package remains a structurally validated **draft** awaiting qualified human review.

## 9. Managed coordinator: one-time project bootstrap

Continuous `auto` and `distributed` modes use a coordinator. Current `main` supports repository-managed coordinator infrastructure.

In `config/configure_project.toml`:

```toml
[automation]
coordinator_url = ""
```

an empty URL selects repository-managed infrastructure. An explicit valid Google Apps Script URL remains backward-compatible **external** coordinator mode.

Check current managed status:

```powershell
& $py -m app_generator coordinator-status --config $config
```

If it reports a current version and URL, do not bootstrap again.

If it reports, for example:

```text
Managed coordinator: missing (required v2)
```

perform the **one-time project-wide bootstrap on one trusted administrator PC**:

```powershell
gh auth status
& $py -m app_generator coordinator-bootstrap --config $config
```

The bootstrap may open Google consent for additional Apps Script/Drive administration scopes. It verifies the configured Google account, stores the refreshable administrator credential in the private GitHub Actions secret used by this repository, requests the serialized managed deployment, and waits for a live health check.

Ordinary worker PCs do **not** repeat `coordinator-bootstrap` and do not need the administrator token locally. They discover the private managed runtime through their normal Drive authorization.

Any worker can verify readiness with:

```powershell
& $py -m app_generator coordinator-ensure --config $config
```

## 10. Continuous multi-PC auto mode

Auto mode requires:

- Google Drive source discovery;
- a healthy managed or explicit external coordinator;
- `git_publish = true` so generated artifacts become durable/shared;
- a clean/synchronized Git checkout;
- working GitHub/Git credentials appropriate to the configured publication policy.

Preview the queue without claiming a generation job:

```powershell
& $py -m app_generator doctor --config $config --selection-mode auto
```

Start a continuous worker:

```powershell
& $py -m app_generator run --config $config --selection-mode auto
```

The worker repeatedly claims globally eligible jobs, prioritizes recoverable interrupted work according to coordinator policy, renews leases, uses durable checkpoints, publishes validated artifacts through Git, and continues until the global source inventory is successful. If remaining work is currently leased by other PCs, it waits/polls instead of falsely declaring completion.

Use `Ctrl+C` to stop a worker. The current CLI reports interruption and returns an active auto lease safely when possible; abandoned leases also become recoverable through expiry.

See `docs/CONTINUOUS_AUTO_TESTING.md` for a two-PC recovery/concurrency verification procedure.

## 11. Generated repository artifacts

For Section 8.5, expect:

```text
content/chapter-8/section-8-5/
├── README.md
├── learning-design.md
├── package.json
└── review-record.md

content/source-manifests/
└── chapter-8-section-8-5.json
```

The five artifacts serve learner content, learning-design rationale, review status, section provenance/status, and controlled-source identity/checksum. No source PDF should enter Git.

Validate:

```powershell
& $py scripts\lint.py
& $py scripts\validate_content.py
node --check app\app.js
node tests\test_app_loading.js
node tests\test_app_rendering.js
node tests\test_interaction_rendering.js
& $py -m unittest discover -s tests -v
git diff --check
```

## 12. Review, PR, and human approval

If a specific-mode run did not publish automatically, create a short-lived content branch, add only intended artifacts, validate, push, and open a PR:

```powershell
git switch -c content/section-8-5-draft
git add content/chapter-8/section-8-5 content/source-manifests/chapter-8-section-8-5.json
git diff --cached --check
git commit -m "Add Section 8.5 generated draft"
git push -u origin content/section-8-5-draft
gh pr create --base main --fill
```

Green CI is not subject/pedagogical approval. Complete the required qualified reviews recorded in `review-record.md` before treating content as approved.

## 13. Build and preview a minimal static review app

Build one selected package into an empty directory:

```powershell
$release = "..\section-8-5-release"
New-Item -ItemType Directory -Path $release
& $py scripts\build_public_release.py `
  content/chapter-8/section-8-5/package.json `
  $release
```

Preview:

```powershell
& $py -m http.server 8001 --directory $release
```

Open `http://127.0.0.1:8001/`. The bundle contains the learner app and selected package, not PDFs, credentials, review records, source manifests, or development files.

For public review deployment, prefer a separate minimal GitHub Pages repository and verify the built bundle locally before pushing it.

## 14. Routine multi-PC operating pattern

On every worker PC before use:

```powershell
git switch main
git fetch origin
git status -sb
```

If behind:

```powershell
git pull --ff-only origin main
```

Then:

```powershell
.\sync-workstation.cmd --quick
```

Use the generated local config filename printed by synchronization for all direct commands. Do not assume a filename copied from another PC.

For specific mode:

```powershell
& $py -m app_generator doctor --config $config --selection-mode specific --pdf-subchapter-path <chapter.section>
& $py -m app_generator run --config $config --selection-mode specific --pdf-subchapter-path <chapter.section>
```

For continuous auto mode after project-wide coordinator bootstrap:

```powershell
& $py -m app_generator doctor --config $config --selection-mode auto
& $py -m app_generator run --config $config --selection-mode auto
```

## 15. Common troubleshooting

### `Configuration file does not exist: project.local.toml`

Your workstation may use a different allowed generated config filename. Read the latest `sync-workstation.cmd` output and rerun with:

```powershell
& $py -m app_generator <command> --config .\<printed-generated-config>.toml
```

### `Managed coordinator: missing`

If this project has never been bootstrapped, run `coordinator-bootstrap` once on a trusted administrator PC. If it was already bootstrapped, check the worker's Drive authorization/account and run `coordinator-ensure`.

### Dirty or diverged Git checkout

Do not reset blindly. Inspect `git status -sb`; commit/stash/remove intended local changes before synchronization. The workstation synchronizer intentionally refuses to overwrite local-only work.

### Documentation uncertainty

Refresh `main` and read the docs from that same checkout. `docs/DOCUMENTATION_MAINTENANCE.md` defines the same-PR documentation rule and CI gate.

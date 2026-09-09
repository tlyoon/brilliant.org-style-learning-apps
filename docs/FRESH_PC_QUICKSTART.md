# Fresh Windows PC quickstart

This is the short setup checklist for using an existing project. For the complete workflow, including coordinator setup, review, and deployment, use `docs/PDF_TO_APP_QUICKSTART.md`.

## 1. Install and clone

Install Python 3.12, Git, Node.js, current Google Chrome, and GitHub CLI. Then open PowerShell:

```powershell
git clone https://github.com/tlyoon/brilliant.org-style-learning-apps.git
cd brilliant.org-style-learning-apps
git status -sb
```

The checkout should be on current `main` with no local changes.

## 2. Create this PC's settings

```powershell
python -m scripts.sync_configured_workstation --init-settings-only --branch main
```

The command prints the settings path. For the current project it is normally:

```text
%LOCALAPPDATA%\BrilliantContentGenerator\workstation-sync.toml
```

Open it with an editor, for example:

```powershell
notepad $env:LOCALAPPDATA\BrilliantContentGenerator\workstation-sync.toml
```

Edit only values that differ on this PC:

- `[repository]`: Git remote and branch;
- `[drive]`: OAuth client/token paths; `login_name` must match the shared project setting;
- `[output]`: ignored local config filename;
- `[checks]`: whether synchronization runs tests and Drive doctor.

Keep `project.project_name` and `drive.login_name` equal to their values in `config/configure_project.toml`. Keep OAuth files outside the repository. Do not edit `project.local.toml` (or another generated `*.local*.toml`) because synchronization replaces it.

Place the Google Cloud Desktop OAuth client JSON at the configured `drive.oauth_client_file`; by default:

```text
%LOCALAPPDATA%\BrilliantContentGenerator\credentials\drive-oauth-client.json
```

Never commit the client JSON or generated OAuth token.

## 3. Synchronize and check

```powershell
.\sync-workstation.cmd
```

The first run creates `.venv`, installs the package, renders the ignored local configuration, runs checks, and may open Google authorization. Note the generated config filename printed after `Installed config/configure_project.toml as ...`.

Use that filename in direct commands:

```powershell
$config = '.\project.local.toml' # replace if sync printed another name
& .\.venv\Scripts\python.exe -m app_generator doctor --config $config
& .\.venv\Scripts\python.exe -m app_generator run --config $config --selection-mode specific --pdf-subchapter-path 8.5
```

Replace `8.5` with the required Drive subchapter folder. Generated content is a draft until qualified human review. Later, refresh the PC with `.\sync-workstation.cmd --quick`.

## Editing shared project settings

Workers joining an existing project should normally leave shared settings unchanged. A project owner can change non-secret shared values in `config/configure_project.toml`; use the guarded configurator shown in `docs/PDF_TO_APP_QUICKSTART.md` and review its dry-run diff before adding `--apply`. Commit shared changes through the normal review workflow, then rerun `.\sync-workstation.cmd` on each PC.

See `config/README.md` for the field reference and `docs/WORKSTATION_SYNC.md` for troubleshooting.

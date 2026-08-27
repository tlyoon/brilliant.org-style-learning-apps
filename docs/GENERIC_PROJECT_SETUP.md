# Recycle the generator for another textbook project

The package has one active, tracked project authority: `config/project.toml`. A recycled project should use its own repository, Drive source root, Gemini Gem, coordinator deployment, OAuth client, Chrome profile, and run state.

## 1. Create a project branch

Start from a clean, current `main` branch:

```powershell
git switch main
git pull --ff-only
git switch -c config/new-textbook-project
```

## 2. Preview and apply the core identity

Run the configurator without `--apply` first:

```powershell
python scripts\configure_project.py `
  --project-name "NewPhysicsProject" `
  --source-root-url "https://drive.google.com/open?id=SOURCE_FOLDER_ID" `
  --gem-url "https://gemini.google.com/gem/GEM_ID" `
  --login-name "authorized@example.com" `
  --gem-name "physics content generator"
```

Review the unified diff. Repeat with `--apply`; the command refuses a dirty worktree and atomically changes only the approved keys in `config/project.toml`.

Then edit the remaining controlled metadata in that same file, especially edition, reviewer, rights note, learning boundary, and any desired source ID prefix. Keep token values, credentials, PDFs, browser data, and run data out of Git.

## 3. Review and merge configuration

```powershell
python scripts\lint.py
python scripts\validate_content.py
python -m unittest discover -s tests -v
git diff --check
git add config\project.toml
git commit -m "Configure new textbook project"
git push -u origin config/new-textbook-project
```

Open and merge a pull request. Every PC then receives the same non-secret project authority through Git.

## 4. Initialize each workstation

After pulling `main`:

```powershell
python scripts\sync_workstation.py --init-settings-only
```

Provision the Google Desktop OAuth client at the derived path shown below, then run `sync-workstation.cmd`.

| Derived item | Formula |
|---|---|
| State root | `%LOCALAPPDATA%\<project_name>` |
| Workstation settings | `<state root>\workstation-sync.toml` |
| OAuth client | `<state root>\credentials\drive-oauth-client.json` |
| OAuth token | `<state root>\credentials\drive-oauth-token.json` |
| Chrome profile | `<state root>\chrome-profile` |
| Runs | `<state root>\runs` |
| Generator overrides | `<PROJECT_ENV_PREFIX>_GENERATOR_*` |
| Coordinator token | `<PROJECT_ENV_PREFIX>_COORDINATOR_TOKEN` |

The synchronizer writes ignored `project.local.toml`; generation commands use that file.

## 5. Configure distributed coordination

Deploy a separate coordinator for the project. Set `PROJECT_NAME` and `JOB_SPREADSHEET_ID`, run `initializeCoordinator`, and copy the generated `WORKER_TOKEN` into the project-derived coordinator environment variable on authorized PCs. The coordinator rejects another project name and scopes every ledger row by project.

## 6. Validate before live generation

```powershell
python -m app_generator doctor --config .\project.local.toml
python -m app_generator run --config .\project.local.toml
```

Start with one specific-mode PDF. Enable distributed selection and Git publication only after that controlled run succeeds.

## Intentional boundaries

- Section folders must currently be numeric `chapter.section`, such as `15.1`.
- Each package uses exactly one PDF.
- Gemini web automation still depends on the authenticated Chrome UI and may require selector maintenance.
- Generated work remains draft and requires human review; workers do not merge or publish it.
- Legacy Brilliant environment/property compatibility ends after 31 December 2026.

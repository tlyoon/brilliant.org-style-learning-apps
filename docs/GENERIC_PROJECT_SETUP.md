# Recycle the generator for another textbook project

The normal tracked project authority is `config/configure_project.toml`. A recycled project should use its own project identity, Drive source root, Gemini Gem/account, coordinator deployment where needed, OAuth client, Chrome profile, and run state. Machine-local values are materialized by `sync-workstation.cmd` rather than copied between PCs.

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
  --project-name "NewLearningProject" `
  --source-root-url "https://drive.google.com/open?id=SOURCE_FOLDER_ID" `
  --gem-url "https://gemini.google.com/gem/GEM_ID" `
  --login-name "authorized@example.com" `
  --gem-name "subject content generator"
```

Review the unified diff. Repeat with `--apply`; the command refuses a dirty worktree and atomically changes only the approved identity/source/Gem keys in `config/configure_project.toml`.

Then review the remaining project-dependent values in that file: default subchapter selector, source filename/pattern, Gem edit URL, coordinator policy, edition/provenance wording, Git handoff policy, and any project-specific model-selection preference. Keep `${PROJECT_SLUG}`, `${PROJECT_ENV_PREFIX}`, `${REPO_ROOT}`, and `${STATE_ROOT}` tokenized so workstation sync derives them automatically.

Section title and the effective learning boundary are derived from validated PDF analysis; unidentified edition metadata and the automated-draft actor are recorded truthfully without blocking generation. Keep token values, credentials, PDFs, browser data, and run data out of Git.

## 3. Review and merge configuration

```powershell
python scripts\lint.py
python scripts\validate_content.py
python -m unittest discover -s tests -v
git diff --check
git add config\configure_project.toml
git commit -m "Configure new textbook project"
git push -u origin config/new-textbook-project
```

Open and merge a pull request. Every PC then receives the same non-secret project authority through Git.

## 4. Initialize each workstation

After pulling `main`:

```powershell
python -m scripts.sync_configured_workstation --init-settings-only
```

Provision the Google Desktop OAuth client at the derived path shown below, then run `sync-workstation.cmd`.

| Derived item | Formula |
|---|---|
| Project slug | derived from `<project_name>` as lowercase kebab-case |
| Environment prefix | derived from `<project_name>` as uppercase underscore form |
| State root | `%LOCALAPPDATA%\<project_name>` |
| Workstation settings | `<state root>\workstation-sync.toml` |
| OAuth client | `<state root>\credentials\drive-oauth-client.json` |
| OAuth token | `<state root>\credentials\drive-oauth-token.json` |
| Chrome profile | `<state root>\chrome-profile` |
| Runs | `<state root>\runs` |
| Generator overrides | `<PROJECT_ENV_PREFIX>_GENERATOR_*` |
| Coordinator token | `<PROJECT_ENV_PREFIX>_COORDINATOR_TOKEN` |

The synchronizer writes ignored `project.local.toml`; generation commands use that file by default.

## 5. Configure distributed coordination

Deploy a separate coordinator for the project when distributed mode is needed. Set the coordinator's project identity and job spreadsheet, initialize its worker token, and place that token in the project-derived coordinator environment variable on authorized PCs. The coordinator scopes ledger work by project.

## 6. Validate before live generation

```powershell
python -m app_generator doctor
python -m app_generator run --pdf-subchapter-path 8.2
```

Start with one specific-mode PDF. Enable distributed selection and Git publication only after that controlled run succeeds.

## Intentional application contracts

These are not textbook identity variables and remain generic/versioned code or schema contracts:

- Section folders currently use numeric `chapter.section`, such as `15.1`.
- Each package currently uses exactly one PDF.
- The current package contract uses 18 activities with the defined type/difficulty distribution.
- The current learner contract uses English, Malay and Simplified Chinese and calculator-free conceptual activities.
- Gemini web automation depends on the authenticated Chrome UI and may require selector maintenance.
- Generated work remains draft and requires qualified human review.

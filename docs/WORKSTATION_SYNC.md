# One-click workstation synchronization

`sync-workstation.cmd` safely updates an existing Windows checkout, prepares its Python environment, renders the repository-tracked generator configuration for that PC, and validates the workstation.

## Configuration authority

The active shared configuration is:

```text
config/generator.shared.toml
```

It is versioned with the generator code and reaches every authorized PC through the normal Git pull. Changes to shared generator behavior therefore use the same branch, pull-request review, and rollback history as the code that consumes them.

`config/generator.shared.example.toml` remains a reusable template. It is not the active workstation configuration.

The tracked file contains only approved, non-secret, machine-independent settings. It retains `${REPO_ROOT}` exactly. The synchronizer accepts only an explicit allow-list of generator fields and refuses unknown fields, oversized files, symbolic links, invalid TOML, or an invalid repository-root token.

## Security boundary

Never place any of these items in Git or in the tracked shared configuration:

- Google OAuth client JSON or OAuth token JSON;
- Google, GitHub, or coordinator token values;
- passwords, cookies, or `.env` files;
- Chrome profiles;
- controlled source PDFs or generator run directories.

Each PC must provision its own Google Desktop-app OAuth client outside the repository. By default, place the newly issued file at:

```text
%LOCALAPPDATA%\BrilliantContentGenerator\credentials\drive-oauth-client.json
```

The first generator `doctor` run opens Google's read-only Drive authorization flow and writes that PC's OAuth token beside the client file. Google Drive remains the controlled source-PDF service; it is no longer used to distribute `generator.shared.toml`. Git and GitHub authentication also remain local to each PC.

## First run on each PC

Prerequisites are Python 3.12, Git, current Chrome, Node.js, network access, and an existing repository checkout. For the private GitHub repository, authenticate Git locally before running the synchronizer.

Double-click `sync-workstation.cmd`. Its editable defaults provide the expected Google account and `main` branch. To use different values, edit the defaults in the batch file or define the corresponding `BRILLIANT_SYNC_*` environment variables before running it.

The first run saves the effective machine-local values outside the repository in:

```text
%LOCALAPPDATA%\BrilliantContentGenerator\workstation-sync.toml
```

Later runs require only a double-click. To change the branch or expected Google account, edit that machine-local, non-secret file.

## Safety and behavior

The synchronizer:

1. refuses a dirty worktree;
2. fetches the configured remote and switches to the configured branch;
3. fast-forwards only and refuses local-only or diverged commits;
4. creates or updates `.venv` with Python 3.12 and installs the repository package;
5. reads `config/generator.shared.toml` from the synchronized checkout;
6. validates it, renders `${REPO_ROOT}`, adds that PC's OAuth paths from `workstation-sync.toml`, and atomically writes the ignored `generator.shared.local.toml`;
7. verifies that the shared and machine-local expected Google accounts agree;
8. runs lint, content validation, unit tests, the JavaScript syntax check, and generator `doctor`.

`doctor` verifies Drive authorization, source discovery/download, checksums, and provenance, but does not upload a PDF to Gemini. A live run must be explicitly requested from a terminal:

```powershell
.\sync-workstation.cmd --run-generator
```

That option uploads the controlled source to Gemini and starts generation after all checks pass. Leave `git_publish = false` in the shared configuration until automated publishing and the distributed coordinator are intentionally enabled.

## Migration from the Drive Projects folder

Existing `workstation-sync.toml` files may still contain `projects_folder_url` and `shared_config_name`. The synchronizer ignores those obsolete fields so already configured PCs continue to work after pulling this change.

Validate the new flow on one PC and then a second PC. After every active PC has successfully installed the tracked configuration, the old Drive `Projects/generator.shared.toml` copy may be removed manually. This code change does not delete or modify any Drive file.

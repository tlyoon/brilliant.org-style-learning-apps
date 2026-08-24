# One-click workstation synchronization

`sync-workstation.cmd` safely updates an existing Windows checkout, prepares its Python environment, downloads a sanitized generator configuration from a private Google Drive `Projects` folder, and validates the workstation.

## Security boundary

The Drive `Projects` folder is configuration distribution, not a credential store. Never put any of these items in it:

- Google OAuth client JSON or OAuth token JSON;
- Google, GitHub, or coordinator tokens;
- passwords, cookies, or `.env` files;
- Chrome profiles;
- controlled source PDFs or generator run directories.

Each PC must provision its own Google Desktop-app OAuth client outside the repository. By default, place the newly issued file at:

```text
%LOCALAPPDATA%\BrilliantContentGenerator\credentials\drive-oauth-client.json
```

The first run opens Google's read-only Drive authorization flow and writes that PC's token beside the client file. Git and GitHub authentication must also be configured locally. The synchronizer never reads or transfers raw Chrome-profile data.

## Shared Drive folder contents

Place exactly one required file directly inside the private `Projects` folder:

```text
generator.shared.toml
```

Create it from `config/generator.shared.example.toml`, replace every instructional placeholder with approved non-secret metadata, and retain `${REPO_ROOT}` exactly. Do not add machine-specific paths or secret fields. The downloader accepts only an explicit allow-list of generator settings and refuses duplicate files, unknown fields, oversized files, or an invalid repository-root token.

The file does not need to contain the Drive OAuth paths, Chrome-profile path, state directory, or worker ID. The application derives those independently on every PC under `%LOCALAPPDATA%\BrilliantContentGenerator`.

## First run on each PC

Prerequisites are Python 3.12, Git, current Chrome, Node.js, network access, and an existing repository checkout. For a private GitHub repository, authenticate Git locally before running the synchronizer.

Double-click `sync-workstation.cmd`. On the first run it asks for:

1. the private Drive `Projects` folder URL;
2. the expected Google account email;
3. the Git branch, normally `main` after the pull request is merged.

The answers are saved outside the repository in:

```text
%LOCALAPPDATA%\BrilliantContentGenerator\workstation-sync.toml
```

Later runs require only a double-click. To change the branch or Drive folder, edit that machine-local, non-secret file.

## Safety and behavior

The synchronizer:

1. refuses a dirty worktree;
2. fetches the configured remote and switches to the configured branch;
3. fast-forwards only and refuses local-only or diverged commits;
4. creates or updates `.venv` with Python 3.12 and installs the repository package;
5. authorizes Drive locally and downloads `generator.shared.toml`;
6. renders `${REPO_ROOT}` and writes the ignored `generator.shared.local.toml`;
7. runs lint, content validation, unit tests, the JavaScript syntax check, and generator `doctor`.

`doctor` verifies Drive access, source discovery/download, checksums, and provenance, but does not upload a PDF to Gemini. A live run must be explicitly requested from a terminal:

```powershell
.\sync-workstation.cmd --run-generator
```

That option uploads the controlled source to Gemini and starts generation after all checks pass. Leave `git_publish = false` in the shared configuration until automated publishing and the distributed coordinator are intentionally enabled.

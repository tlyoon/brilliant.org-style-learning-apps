# PDF textbook section to live review app: Windows quickstart

This is the canonical beginner-facing path for taking one controlled textbook subchapter PDF through generation, human review, static bundling, and optional GitHub Pages deployment.

Use this guide for the normal happy path. Specialist references remain available for deeper details:

- `docs/GENERIC_PROJECT_SETUP.md` — recycling the repository for another textbook/project;
- `docs/WORKSTATION_SYNC.md` — workstation synchronization and machine-local state;
- `app_generator/README.md` — generator internals, distributed workers, recovery, and Git handoff;
- `config/README.md` — project configuration field reference.

The workflow is deliberately split into distinct gates:

```text
controlled source.pdf
        ↓
generated draft package
        ↓
qualified human review
        ↓
static review bundle
        ↓
optional GitHub Pages deployment
```

Generation does **not** by itself mean that content is approved, merged, publishable, or publicly deployed.

## 1. Understand the supported input

The current generator processes **one PDF per subchapter**. It does not automatically split or process one complete textbook PDF.

A supported Google Drive source tree looks like:

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

The immediate parent directory must be a numeric subchapter identifier such as `8.5`, and the controlled file is normally named `source.pdf`.

**Expected result:** you can identify one specific subchapter, such as `8.5`, whose Drive folder contains exactly one controlled `source.pdf`.

### Safety boundary

Never commit or copy these into Git:

- source PDFs;
- Google OAuth client or token JSON files;
- passwords, cookies, `.env` files, or coordinator token values;
- Chrome profiles;
- generator run directories or raw Gemini response transcripts.

Generated repository artifacts contain source provenance and checksums, not the source PDF itself.

## 2. Install the workstation prerequisites

Install on Windows:

- Python 3.12;
- Git;
- Node.js;
- current Google Chrome;
- GitHub CLI (`gh`) if you want command-line PR/repository operations;
- VS Code or another editor of your choice.

Confirm the main tools from PowerShell:

```powershell
py -3.12 --version
git --version
node --version
gh --version
```

**Expected result:** Python reports 3.12 and Git/Node are available. `gh` is optional for generation but useful for PR and Pages steps.

## 3. Clone and prepare the repository

Use a normal local development folder rather than storing Git metadata or virtual environments in a cloud-synchronized folder when possible.

```powershell
cd $HOME\Projects
git clone https://github.com/tlyoon/brilliant.org-style-learning-apps.git
cd brilliant.org-style-learning-apps
py -3.12 -m venv .venv
$py = (Resolve-Path ".\.venv\Scripts\python.exe").Path
& $py -m pip install --upgrade pip
& $py -m pip install -r requirements-dev.txt
```

Confirm the checkout is clean:

```powershell
git status -sb
```

**Expected result:** the checkout is on `main`, the working tree is clean, and `.venv` can import the development dependencies.

## 4. Configure the project for the textbook/source collection

On the current `main` branch, the normal tracked project authority is:

```text
config/configure_project.toml
```

Do not place machine-local paths or secrets in that file.

For a new textbook/project, start from current `main` and create a configuration branch:

```powershell
git switch main
git pull --ff-only
git switch -c config/new-textbook-project
```

Preview the core project changes first:

```powershell
& $py scripts\configure_project.py `
  --project-name "NewLearningProject" `
  --source-root-url "https://drive.google.com/open?id=SOURCE_FOLDER_ID" `
  --gem-url "https://gemini.google.com/gem/GEM_ID" `
  --login-name "authorized@example.com" `
  --gem-name "subject content generator"
```

Review the printed diff. If correct, repeat with `--apply`:

```powershell
& $py scripts\configure_project.py `
  --project-name "NewLearningProject" `
  --source-root-url "https://drive.google.com/open?id=SOURCE_FOLDER_ID" `
  --gem-url "https://gemini.google.com/gem/GEM_ID" `
  --login-name "authorized@example.com" `
  --gem-name "subject content generator" `
  --apply
```

Then review `config/configure_project.toml`, `config/gem_description.txt`, and `config/gem_instructions.md`. In particular, confirm the Drive root, Gemini Gem/editor values, expected account, default subchapter selector, source filename/pattern, provenance wording, and Git policy.

For the first controlled run, keep Git publication disabled unless you deliberately want the generator to create/push branches:

```toml
git_publish = false
git_auto_merge = false
```

Validate the configuration change:

```powershell
& $py scripts\lint.py
& $py scripts\validate_content.py
& $py -m unittest discover -s tests -v
git diff --check
```

Commit the project configuration through your normal PR workflow before distributing it to other PCs.

**Expected result:** the repository contains one reviewed, non-secret project configuration that every workstation can receive through Git.

## 5. Initialize machine-local workstation settings

After the project configuration is available on your working branch or `main`, initialize the local settings:

```powershell
& $py -m scripts.sync_configured_workstation --init-settings-only
```

The project name determines the default machine-local state root:

```text
%LOCALAPPDATA%\<project_name>\
```

Important derived locations include:

```text
%LOCALAPPDATA%\<project_name>\workstation-sync.toml
%LOCALAPPDATA%\<project_name>\credentials\drive-oauth-client.json
%LOCALAPPDATA%\<project_name>\credentials\drive-oauth-token.json
%LOCALAPPDATA%\<project_name>\chrome-profile\
%LOCALAPPDATA%\<project_name>\runs\
```

Create a Google Cloud **Desktop app** OAuth client with the Google Drive API enabled and save the downloaded client JSON as:

```text
%LOCALAPPDATA%\<project_name>\credentials\drive-oauth-client.json
```

Do not add that file to the repository.

Run the normal workstation synchronizer:

```powershell
.\sync-workstation.cmd
```

For later routine updates, after one full validation has succeeded, use:

```powershell
.\sync-workstation.cmd --quick
```

**Expected result:** ignored `project.local.toml` is materialized for this PC, dependencies are usable, and machine-local credentials/state remain outside Git.

## 6. Run doctor before uploading anything to Gemini

Run:

```powershell
& $py -m app_generator doctor
```

`doctor` checks configuration, Drive authorization, PDF discovery/download, checksum, and provenance compatibility. It does **not** upload the PDF to Gemini.

The first Drive authorization may open a browser for the configured Google account.

**Expected result:** doctor identifies the requested Drive source and reports a valid controlled PDF without modifying Gemini.

## 7. Generate one selected subchapter

Start with one explicit subchapter in specific mode. Example:

```powershell
& $py -m app_generator run --pdf-subchapter-path 8.5
```

The live run uses the configured Gemini Gem/account, converges the project-owned editable Gem fields as implemented by the current generator, opens a fresh conversation, attaches the selected PDF, generates the package, validates/repairs it, and installs the repository artifacts.

A successful run prints the generated paths and keeps the package in `draft` status.

**Expected result:** the target section appears under `content/chapter-8/section-8-5/` (or the corresponding chapter/section for your source).

## 8. Inspect the generated artifacts

For a generated Section 8.5, expect:

```text
content/chapter-8/section-8-5/
├── README.md
├── learning-design.md
├── package.json
└── review-record.md

content/source-manifests/
└── chapter-8-section-8-5.json
```

Purpose of each file:

| File | Purpose |
|---|---|
| `package.json` | learner-facing structured content consumed by the app |
| `learning-design.md` | concept coverage, prerequisite, misconception, and pedagogy notes |
| `review-record.md` | review checklist/status and required human sign-offs |
| section `README.md` | section-level provenance/status summary |
| source manifest | controlled source identity, location, checksum, and provenance metadata |

Only the selected `package.json` is copied into the generic public static bundle; internal review records and source manifests stay out of that bundle.

**Expected result:** all five artifacts exist, the package is still marked `draft`, and no PDF has entered Git.

## 9. Validate the generated draft before committing it

Run the repository checks:

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

Then inspect the working tree:

```powershell
git status -sb
```

**Expected result:** all deterministic checks pass and only the intended generated artifacts are uncommitted/changed.

## 10. Commit the draft and use a pull request

If Git publication was disabled for the controlled run, create a normal short-lived branch and commit only the generated artifacts:

```powershell
git switch -c content/section-8-5-draft
git add content/chapter-8/section-8-5 content/source-manifests/chapter-8-section-8-5.json
git diff --cached --check
git commit -m "Add Section 8.5 generated draft"
git push -u origin content/section-8-5-draft
```

Open a PR with GitHub or:

```powershell
gh pr create --base main --fill
```

Do not interpret a green CI result as scientific/pedagogical approval. The generated package remains a draft until the required qualified reviews are complete.

**Expected result:** the generated draft is reviewable in a PR and `main` remains unchanged until the PR is deliberately merged.

## 11. Perform human review before treating content as approved

Use the section `review-record.md` and repository content rules. The automated generator does not replace qualified review of subject correctness, instructional quality, English/Malay/Simplified-Chinese quality, accessibility, and provenance.

If corrections are needed, edit/regenerate on the same review branch, rerun validation, and update the PR.

**Expected result:** reviewers can distinguish a structurally valid generated draft from content that has actually received the required human sign-offs.

## 12. Build a minimal static review app

The generic builder requires one explicit package and an empty output directory.

Example:

```powershell
$release = "..\section-8-5-release"
New-Item -ItemType Directory -Path $release
& $py scripts\build_public_release.py `
  content/chapter-8/section-8-5/package.json `
  $release
```

If the output directory already contains files, choose a new empty directory; the builder intentionally refuses to overwrite a non-empty bundle.

The bundle contains only:

```text
index.html
.nojekyll
app/app.js
app/styles.css
content/package.json
```

It excludes Git history, tests, source PDFs, review records, source manifests, development scripts, credentials, and run diagnostics.

**Expected result:** the release directory is a self-contained static review app with one explicitly selected package.

## 13. Preview the static bundle locally

Serve the release directory:

```powershell
& $py -m http.server 8001 --directory $release
```

Open:

```text
http://127.0.0.1:8001/
```

Verify at minimum:

- the page loads without console errors;
- the intended section/package title appears;
- the package status is still `draft` when appropriate;
- the expected activity count and language controls are present;
- navigation/interactions work.

Stop the local server with Ctrl+C.

**Expected result:** the exact static bundle intended for deployment works locally before any public upload.

## 14. Deploy the review bundle to GitHub Pages

For draft/review material, prefer a **separate minimal Pages repository** rather than exposing the development repository. This keeps internal specifications, source manifests, tests, and review records out of the public site.

### A. First deployment to a new Pages repository

Create a clean deployment folder and copy the built bundle into it:

```powershell
$pages = "..\section-8-5-pages"
New-Item -ItemType Directory -Path $pages
Copy-Item -Path "$release\*" -Destination $pages -Recurse -Force
Set-Location $pages
git init -b main
git add .
git commit -m "Publish Section 8.5 draft review app"
```

If GitHub CLI is authenticated, create and push a repository using your chosen owner/repository name:

```powershell
gh repo create OWNER/REVIEW_REPO --public --source=. --remote=origin --push
```

In GitHub, open **Settings → Pages**, choose **Deploy from a branch**, select `main` and `/(root)`, then save.

GitHub will show the resulting Pages URL, normally:

```text
https://OWNER.github.io/REVIEW_REPO/
```

### B. Add another section without breaking existing routes

Build each new section into its own empty staging directory, then place that bundle in a new subdirectory of the existing Pages repository. For example:

```powershell
$nextRelease = "..\section-8-6-release"
New-Item -ItemType Directory -Path $nextRelease
& $py scripts\build_public_release.py `
  content/chapter-8/section-8-6/package.json `
  $nextRelease

Set-Location "..\REVIEW_REPO"
git pull --ff-only
New-Item -ItemType Directory -Path ".\section-8-6"
Copy-Item -Path "$nextRelease\*" -Destination ".\section-8-6" -Recurse -Force
git add section-8-6
git commit -m "Add Section 8.6 draft review app"
git push
```

The existing routes remain untouched. The new route becomes approximately:

```text
https://OWNER.github.io/REVIEW_REPO/section-8-6/
```

Do not delete or replace existing section directories merely to add a new route.

### C. Verify the deployed site

Open the live URL and verify the same properties checked locally: correct section/package, draft labelling, expected activity count, language controls, and interactive behavior.

**Expected result:** only the static review bundle is public, while source PDFs, credentials, manifests, review records, and development files remain private to their intended locations.

## 15. Normal repeat workflow for the next subchapter

Once the workstation/project is configured, the common repeat cycle is much shorter:

```powershell
git switch main
git pull --ff-only
.\sync-workstation.cmd --quick
& $py -m app_generator doctor
& $py -m app_generator run --pdf-subchapter-path <chapter.section>
& $py scripts\validate_content.py
& $py -m unittest discover -s tests -v
```

Then repeat the review → PR → human review → static bundle → preview → optional deployment gates.

## Troubleshooting and deeper references

Use:

- `docs/WORKSTATION_SYNC.md` for dirty/diverged checkout, dependency caching, first-run settings, and validation stamps;
- `app_generator/README.md` for Drive ambiguity, Selenium/Gemini UI issues, distributed worker leases, recovery, and Git handoff;
- `config/README.md` for the project fields and machine-local token boundary;
- `docs/GENERIC_PROJECT_SETUP.md` when recycling the repository for a different textbook/project;
- `docs/SECURITY_AND_PRIVACY.md` for data-handling constraints.

If the repository's tracked project-authority filename changes in the future, update this quickstart and its documentation acceptance test in the same pull request rather than allowing the normal workflow to become ambiguous again.

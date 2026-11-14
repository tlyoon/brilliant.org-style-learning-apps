# PDF textbook section to live review app: Windows quickstart

This is the canonical beginner-facing installation and operating guide for the current `main` branch. It covers a controlled topic corpus rooted in `source.pdf`, workstation setup, independent Google OAuth and Gemini accounts, specific generation, managed continuous-auto mode, review, and optional static deployment.

**Documentation freshness rule:** use this file from the same `main` revision that you are running. Operational changes must update the relevant documentation in the same PR; see `docs/DOCUMENTATION_MAINTENANCE.md`.

Specialist references:

- `docs/WORKSTATION_SYNC.md` — workstation synchronization and machine-local state;
- `docs/GENERIC_PROJECT_SETUP.md` — recycling the repository for another textbook/project;
- `docs/CONTINUOUS_AUTO_TESTING.md` — continuous auto-mode and multi-PC verification;
- `app_generator/README.md` — generator technical reference;
- `config/README.md` — configuration field reference.

Generation does **not** mean that content is approved, publishable, merged, or publicly deployed.

## 1. Supported source layout

The generator processes one topic corpus per subchapter. Each subchapter has a primary `source.pdf`; any sibling PDFs are supplementary sources and are attached in the same fresh Gem conversation. A supported Google Drive tree looks like:

Before reusing this workflow for a textbook from a **different discipline**, read `docs/DOMAIN_PROFILES.md`. Stage 0 now automatically classifies representative PDFs from the complete Source Root and binds the source inventory to a compatible installed profile before any generation job is claimed. A chemistry, mathematics, biology, history, or other textbook with no compatible active profile stops safely with `DOMAIN_PROFILE_REQUIRED`; onboard/activate that domain before generation. The selected profile then governs the subject-specific generation instructions. New packages record its ID/version, and validation/public release use that recorded identity; older packages without it retain default-profile compatibility.

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

### Source corpus discovery and manifest identity

For an explicitly selected topic, the generator now locates the controlled
source.pdf anchor and all sibling PDFs in a **single bounded metadata walk**
of the configured Source Root. The optional separate textbook-domain inventory
scan and coordinated queue scan still perform their own legitimate discovery.
No source PDF is downloaded during metadata discovery itself.

Sibling filenames are checked case-insensitively before any download, and
ambiguous topic folder matches fail closed rather than selecting whichever
folder happens to appear first. When validating an existing source manifest,
the CLI doctor and normal generation path select the configured primary
source.pdf by name, **not** the alphabetically first sibling PDF. Multi-PDF
corpora without exactly one primary cannot be installed or reused as if the
first supplementary PDF were primary.

The ordering of attached source files and the existing topic-corpus
coordinator job key remain unchanged. This prevents unnecessary requeueing of
already completed/claimed jobs solely because of this software correction.
All verification of the new behaviour uses synthetic metadata; this update
does not authorize new Gemini requests, source-download retries, public release
or re-opening a terminal campaign.

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

It contains non-secret project identity, Drive source root, Gemini Gem/account, automation policy, project-derived path templates, and Git handoff policy. `google.oauth_login` identifies the Drive/coordinator OAuth account; `gemini.login_name` identifies the Gemini browser account. They may differ. The Gem display name is not managed.

For a new recycled project, preview the configurator:

```powershell
python scripts\configure_project.py `
  --project-name "NewLearningProject" `
  --source-root-url "https://drive.google.com/open?id=SOURCE_FOLDER_ID" `
  --gem-url "https://gemini.google.com/gem/GEM_ID" `
  --gem-edit-url "https://gemini.google.com/gems/edit/EDIT_ID" `
  --oauth-login "authorized@example.com" `
  --gemini-login-name "gemini@example.com"
```

Review the diff, then repeat with `--apply` when correct. **Changing the project name automatically sets Git publication/auto-merge and public Pages deployment/auto-merge to `false`**, preventing the old project's active release settings from carrying into the new project. A same-project configuration edit retains its existing release policy. Review the output repository and deployment URL before any later, explicitly authorized enabling of publication. Validate and merge the configuration through the normal PR workflow before distributing it to other PCs.

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

This step records a machine-local repository binding: the current PC hostname and the absolute checkout path. Run it once on each intended worker checkout. Existing older workstation settings must be rebound once after this upgrade. Later synchronization and direct generator runs fail closed if the bound settings/configuration are used from another PC or repository path.

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

### Optional per-PC Gemini account and Gem

Only the `[local_gemini]` table in the generated local TOML is intended for manual editing:

```toml
[local_gemini]
login_name = ""
gem_url = ""
gem_edit_url = ""
```

Blank values inherit tracked `[gemini]` defaults. A nonblank login changes only the Gemini browser account, not `google.oauth_login`. When selecting another Gem, set both URLs together; a lone URL override is rejected. This table survives later full and quick syncs; other generated fields are replaced. Ensure the local Gemini account can edit the selected Gem. Changing local overrides invalidates cached full validation.

For direct CLI commands, `--login-name` overrides the Gemini browser account and `--oauth-login` independently overrides the Drive/coordinator account. Keep workstation `[drive].login_name` consistent with tracked `google.oauth_login` for synchronization.

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

Doctor checks configuration, Drive authorization, Source-Root/domain binding, PDF discovery/download, checksum, and provenance. If the current Source Root has no valid domain binding, doctor may upload only the bounded representative textbook PDFs needed for Stage-0 Gemini API domain discovery; it does not start activity/content generation or claim an auto content job.

The first Drive authorization on a PC may open a Google browser consent flow and create that PC/project's `drive-oauth-token.json`.

### Gemini API key selection on Windows

For a workstation explicitly permitted to access the existing local
`%LOCALAPPDATA%\Microvid\.env`, the Gemini API backend discovers
`GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, additional numbered keys and
`GEMINI_API_KEY` without placing any credential in a command argument.
An explicitly provided process-level `GOOGLE_API_KEY`/`GEMINI_API_KEY`
retains precedence. Duplicate keys are skipped; at most eight distinct
candidates are considered. No secrets are copied to the Git repository.
The shared Gemini API client factory **automatically** performs a minimal
**source-free** probe whenever a production caller creates a model client;
no call site needs to opt into fallback. It also probes when only one key
is configured, before any controlled PDF generation. With multiple
keys, a failed candidate automatically advances to the next distinct key
only after an explicit HTTP 401, 402, 403, 503 or 504. HTTP 429 (rate/quota),
HTTP 400 (malformed request), unknown or ambiguous errors stop; do not use
key rotation to evade project-level quota. HTTP 402 may reflect a shared
billing account with depleted credits, in which case no key will work until
the legitimate billing prerequisite is restored. `doctor` never performs
this generation probe, so its success alone does not prove API readiness.

Source-bearing generation makes **one** SDK request per stage. Any timeout, connection interruption, HTTP 408/409/5xx, empty answer or other ambiguous outcome latches the current API client; do not reissue the request through another key or the same instance. Reconcile the private run-state before a new authorized attempt. `gemini_api_max_attempts` and `gemini_api_retry_backoff_seconds` are legacy settings and cannot enable source-bearing retries.

An **already-submitted PDF request** is not automatically replayed after
any provider failure, even if another key is present. Inspect its private
stage/receipt first; new source-bearing attempts require independent
authorization. Do not widen Desktop Commander permissions or substitute
a different credential path if the default folder is unavailable.
This change does not reopen Decision 0029's exhausted two-round campaign
or justify additional document-specific science fixes.

## 8. Generate one selected subchapter

Start with a controlled specific-mode run when validating a new project:

```powershell
& $py -m app_generator run --config $config --selection-mode specific --pdf-subchapter-path 8.5
```

If that section already has generated repository artifacts, the command stops **before content generation** with `PACKAGE_ALREADY_EXISTS`; it will not silently overwrite reviewed work or waste a full Gemini generation run. To deliberately regenerate that exact section, use:

```powershell
& $py -m app_generator run --config $config --selection-mode specific --pdf-subchapter-path 8.5 --regenerate
```

`--regenerate` is intentionally available only in `specific` mode. The generator fully builds and validates the candidate before replacement, backs up all existing destination artifacts, validates the repository after replacement, and restores the originals if installation/verification fails. Do not use this as an auto-mode retry mechanism; coordinated auto mode continues to treat existing valid packages as completed/skipped work.

The default controlled launcher opens an independent ordinary Chrome window directly on the configured Gemini `gem_url` with no Selenium or remote-debugging connection. Its separate `<chrome_profile_dir>/gemini-browser` profile starts signed out on first use and can retain your Gemini login afterward. The run displays the configured Gemini `login_name` and both the Gem and Gem editor URLs. Finish sign-in, confirm the Gem page loads, close that dedicated Chrome window, and then press Enter in the terminal. The app reopens the same signed-in profile for Selenium, navigates to the configured `gem_edit_url`, and verifies the exact active account before editing or generating. This keeps the Google sign-in flow outside browser automation. Gemini login may differ from Drive OAuth. Existing personal and legacy generator profiles are left untouched. The launcher uses a new local debug connection and reports a connection-readiness failure after 15 seconds rather than silently waiting for an absent browser. When the generator Python environment lacks Selenium, automation now fails before opening the Chrome profile. Use the configured project Python environment with the declared `requirements-generator.txt` dependencies rather than assuming system Python has them. Explicit `attach` mode is different: it requires an already-open browser and does not launch a window or clear its login.

The generator verifies the exact configured Gemini email on visible Google Account controls, reconciles project-owned Description and Instructions without renaming the Gem, opens a fresh conversation, uploads the controlled topic PDFs, generates/repairs the package, validates it, and installs the generated artifacts.

A structurally validated package is **not** automatically approved or publishable. The exact package must satisfy independent, evidence-backed academic acceptance gates for source/answer correctness, scientific semantics, multilingual equivalence and visual/interaction meaning, as well as applicable privacy and rights requirements; unresolved findings remain `REVIEW_REQUIRED` or `FAIL`. The workflow does not require manual sign-off for every question when independent evidence is admissible, but technical CI alone cannot authorize publication. For the current consolidated draft (Decision 0029), `git_publish=false`, `git_auto_merge=false` and `public_deploy=false`; the terminal C3/C4 disposition is `BLOCKED_EXTERNAL`, not permission to run a third PDF campaign or to deploy. See [finite global disposition](FINITE_GLOBAL_CODEBASE_DISPOSITION_20261104.md).

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

The bootstrap may open Google consent for additional Apps Script/Drive administration scopes. It verifies `google.oauth_login` (not the Gemini browser account), stores the refreshable administrator credential in the private GitHub Actions secret used by this repository, requests the serialized managed deployment, and waits for a live health check.

### First-project web-app recovery

If bootstrap reports that no reachable `WEB_APP` entry point exists, complete this once on the
trusted administrator PC:

1. Open the exact Apps Script editor URL printed by the failure. Do not select a script by display
   title; an older project can have the same name.
2. Reload the editor, select `initializeCoordinator`, click **Run**, and wait for
   **Execution completed**.
3. Click **Deploy > New deployment**, select **Web app**, set **Execute as: Me** and
   **Who has access: Anyone**, then click **Deploy**.
4. Copy the complete URL ending in `/exec`.
5. Register that URL and recheck live health:

```powershell
gh workflow run ensure-coordinator.yml --ref main -f project_name=<project_name> -f web_app_url=<web-app-url>
& $py -m app_generator coordinator-ensure --config $config
```

The recovery workflow rejects a deployment that does not belong to the generated managed script.
If a newly published URL is initially reported as unreachable, wait briefly for Google deployment
propagation and rerun the same command. Do not create or archive another deployment merely to
retry validation.

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

### Chapter-scoped auto mode

To run several PCs in parallel on one chapter without changing the canonical Drive source root, give every worker the same chapter scope:

```powershell
& $py -m app_generator doctor --config $config --selection-mode auto --chapter 10
& $py -m app_generator run --config $config --selection-mode auto --chapter 10
```

Each PC still uses the shared Drive-native lease system, but its candidate inventory contains only `10.*` sections. A worker claims any eligible Chapter 10 section, writes only into its own bound local `repo_root`, publishes/merges the deterministic Git handoff, then claims another Chapter 10 section. When all Chapter 10 jobs are globally successful, chapter-scoped workers exit with `AUTO_CHAPTER_COMPLETE` instead of continuing into Chapter 11. `--chapter` and `--pdf-subchapter-path` are mutually exclusive in auto mode.

### Targeted auto mode

To generate exactly one section while retaining coordinator protection, add an explicit subchapter path:

```powershell
& $py -m app_generator doctor --config $config --selection-mode auto --pdf-subchapter-path 8.6
& $py -m app_generator run --config $config --selection-mode auto --pdf-subchapter-path 8.6
```

This is different from `specific` mode. Targeted auto mode restricts the candidate inventory to the requested section **and still acquires a coordinator lease**. If another worker already owns that section, the targeted worker waits and does not fall through to another section. If the section is already globally successful, it exits successfully. If the target is terminally failed, it reports the blocked state. After the requested section succeeds, the targeted worker exits instead of continuing to the next section.

Expected queue-control outcomes such as an already globally successful target are reported cleanly (for example, `AUTO_TARGET_COMPLETE`) without a generation-failure traceback. Genuine generation, lease, validation, or publication failures still retain error diagnostics.

This form is recommended when a human wants to choose the exact section while other PCs may also be running auto mode.

Use `Ctrl+C` to stop a worker. The current CLI reports interruption and returns an active auto lease safely when possible; abandoned leases also become recoverable through expiry.

If an abandoned or repeatedly interrupted target exhausts its automatic attempt budget, targeted `doctor` reports `failed=1` plus the target status, attempt count, and last error code; auto mode refuses to claim it. Review those diagnostics first. To grant a new bounded attempt budget to exactly one verified Drive source, use the explicit recovery command:

```powershell
& $py -m app_generator coordinator-retry-failed --config $config --pdf-subchapter-path 9.1 --confirm
& $py -m app_generator doctor --config $config --selection-mode auto --pdf-subchapter-path 9.1
```

The command synchronizes the Git base, resolves the exact current Drive source identity, and succeeds only when that one coordinator row is terminally failed and still matches the source version. It returns the row to `interrupted`, resets its attempt count, and preserves the last error until the next atomic claim. It does not download or upload the PDF, claim a lease, generate content, or mark unfinished work complete. Do not use `coordinator-complete` as failure recovery.

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
node --check app\visual-renderers.js
node tests\test_app_loading.js
node tests\test_app_rendering.js
node tests\test_visual_renderers.js
node tests\test_visual_player_integration.js
node tests\test_interaction_rendering.js
& $py -m unittest discover -s tests -v
git diff --check
```

## 12. Validation, PR, and publication

If a specific-mode run did not publish automatically, create a short-lived content branch, add only intended artifacts, validate, push, and open a PR:

```powershell
git switch -c content/section-8-5-draft
git add content/chapter-8/section-8-5 content/source-manifests/chapter-8-section-8-5.json
git diff --cached --check
git commit -m "Add Section 8.5 generated draft"
git push -u origin content/section-8-5-draft
gh pr create --base main --fill
```

Green CI and metadata/semantic validation alone are **not** publication permission. Automatic merge/public deployment requires the exact-package source-bound academic PASS and visual-value product gate enforced by `app_generator.runtime.academic_release`, plus the configured deployment and owner-authorization controls. Human academic review is optional; independent automated evidence is not. The `review-record.md` file remains an audit/traceability record.

## 13. Explicit local static preview or academic-gated public bundle

**Unreviewed packages cannot be silently packaged as a public release.**
The standalone `scripts/build_public_release.py` now has two mutually
exclusive modes. To preview drafts locally, choose `--local-preview`:

```powershell
$preview = "..\section-8-5-local-preview"
& $py scripts\build_public_release.py `
  content/chapter-8/section-8-5/package.json `
  $preview --local-preview
& $py -m http.server 8001 --bind 127.0.0.1 --directory $preview
```

Open `http://127.0.0.1:8001/`. This generated preview has a **visible unapproved
draft notice** and a `noindex` instruction. Neither provides access control;
keep the local server loopback-only and do not upload, publish or share the
bundle. Only runtime files and that selected package are copied, not PDFs,
source manifests, review records or credentials.

Public bundle mode (no `--local-preview`) requires a distinct, private
`--academic-validation-dir` **outside the repository and the bundle**:

```powershell
& $py scripts\build_public_release.py `
  content/chapter-8/section-8-5/package.json `
  ..\reviewed-public-bundle `
  --academic-validation-dir $privateAcademicReceiptDir
```

The command independently reuses the same exact-byte academic and visual
release gate as the configured publisher; a draft with missing proof **stops
before writing a bundle**. Supplying a fake PASS JSON does not override
the underlying verifier, and this command does not itself authorize Git
merge or external publication. The automation's publisher also rechecks
the gate and remains subject to its separate deployment authorization.

For GitHub Pages or other public hosting, **manual review is optional**, but independent, automated source-bound academic verification and explicit publication authorization are mandatory. Never upload a local preview bundle as a public release; a static `noindex` notice is not an access-control mechanism.

The historical `scripts/build_section_8_1_public_release.py` containing
multiple unverified variants is now **local-preview only**, requiring an
explicit `--local-preview` flag. It includes visible unapproved-draft notices
on every page and cannot serve as a release authorization path.

## 14. List generated apps and deployment URLs

The tracked public-deployment registry is:

```text
config/deployments.json
```

From the repository root, run:

```powershell
& $py -m app_generator deployments
```

No workstation TOML, Google authorization, coordinator connection, or Gemini browser session is required. The command reports each tracked app's generated/deployed state and public URL. Any generated package under `content/chapter-*/section-*/package.json` that is missing from the registry is still listed with `DEPLOYED = no` and URL `-`.

Update `config/deployments.json` in the same source-repository PR whenever a public route is created, changed, or removed. See `docs/DEPLOYMENTS.md`.

## 15. Routine multi-PC operating pattern

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

For one coordinator-protected target section:

```powershell
& $py -m app_generator doctor --config $config --selection-mode auto --pdf-subchapter-path <chapter.section>
& $py -m app_generator run --config $config --selection-mode auto --pdf-subchapter-path <chapter.section>
```

## 16. Common troubleshooting

### `Configuration file does not exist: project.local.toml`

Your workstation may use a different allowed generated config filename. Read the latest `sync-workstation.cmd` output and rerun with:

```powershell
& $py -m app_generator <command> --config .\<printed-generated-config>.toml
```

### `Managed coordinator: missing`

If this project has never been bootstrapped, run `coordinator-bootstrap` once on a trusted administrator PC. If it was already bootstrapped, check the worker's Drive authorization/account and run `coordinator-ensure`.

### Transient GitHub connection resets

Automated Git synchronization/publication retries recognized transient transport failures such as `Recv failure: Connection was reset`, temporary connection/DNS failures, timeouts, and selected 502/503/504 responses. The generator retries with bounded backoff (2, 5, then 10 seconds after the first attempt). Authentication failures, dirty/diverged repositories, non-fast-forward updates, and other deterministic Git errors still fail immediately.

If all transient attempts are exhausted, the run stops safely with a `GIT_PUBLISH_FAILED` error. Resolve the network path and rerun; auto mode does not treat the job as successfully generated when durable Git publication could not be established.

### Automatic public deployment and stalls

This project's auto mode publishes validated source packages to `https://tlyoon.github.io/section-8-1-learning-app/section-{section_slug}/` through a deterministic public-repository PR. Human sign-off is not required. If a worker stops after source merge, the next auto worker skips Gemini and completes the same public PR.

Each auto attempt is a supervised child. Default checks are every 600 seconds and terminate after three consecutive stale checks; heartbeats do not count as content progress. Parsed Drive checkpoints are retained, so recovery begins at the last parsed stage rather than mid-token.

### Dirty or diverged Git checkout

Do not reset blindly. Inspect `git status -sb`; commit/stash/remove intended local changes before synchronization. The workstation synchronizer intentionally refuses to overwrite local-only work.

### Documentation uncertainty

Refresh `main` and read the docs from that same checkout. `docs/DOCUMENTATION_MAINTENANCE.md` defines the same-PR documentation rule and CI gate.

### Fresh-only independent academic review from private source evidence

Use `scripts/run_private_fresh_source_bound_review.py` only after a newly completed **source-free two-context neutral Gemini probe** and a private source-bound academic priority queue. Pass `--config`, `--package`, `--pdf`, `--packets`, `--priority-queue`, `--neutral-receipt`, `--private-evidence-root`, `--run-id`, `--activity-id`, and `--claim-prefix`, and optionally `--preflight-only` to check admission without opening Chrome or sending any prompt. All referenced inputs, reviewer receipts and run directories must reside outside Git, under an authorized private evidence root. Use distinct, never-reused run IDs and claim prefixes. Existing submitted, ambiguous, in-flight or skipped claims must be reconciled, **never replayed**; the code scans known private immutable claim directories independently of the possibly stale work queue. Only a previously unreviewed activity is eligible. The command verifies original source/package SHA and specific PDF anchors before browser use, requires controlled existing-login Chrome ownership and creates one new private five-gate immutable review. This does **not** authorize publication or confer academic PASS; fresh model consensus is advisory until independent deterministic academic evidence is complete.

Fresh-only source-bound academic review admission additionally rejects any two-context Gemini neutral receipt older than 30 minutes or dated beyond 60 seconds in the future, an incomplete or malformed role response SHA, a source-bearing probe, a missing original model role, or any purportedly approved or account-independent probe. Browser readiness can expire even though its old receipt remains complete. A blocked neutral probe must never be replaced with an older successful one. Re-run a separate source-free probe only when the browser account is actually available, and preserve immutable failed receipts.


## Offline six-subchapter pilot candidate preflight (source-free)

For the class-only six-subchapter pilot, prepare an **explicit candidate roster**
in a private authorized workspace. This is not instructor approval, PDF
acquisition or an authorization to run source-bearing model requests.

The strict JSON manifest has exactly these fields:

- `scopeId`: a fresh `sourcefree-pilot-...` identifier.
- `baselineGitSha`: the exact 40-character Git revision.
- `chapterNumber`: a positive integer chapter number.
- `mode`: `OFFLINE_EXISTING_PACKAGES_ONLY`.
- `modelCallsAllowed`, `pdfReadsAllowed`, `publicationAllowed`: all `false`.
- `cases`: exactly six objects, each with `sectionNumber` (positive integer),
  `packagePath` (e.g. `content/chapter-9/section-9-1/package.json`) and
  `packageSha256` (SHA-256 of the exact JSON file bytes).

Each path must identify a distinct section of the same chapter and bind to
a distinct digest. Do not invent hashes or designate the first six packages
as an instructor-approved pilot roster.

On a checkout at that **same exact revision** run:

```powershell
python scripts/audit_course_pilot_readiness.py `
  --manifest <private-roster.json> `
  --repo-root . `
  --observed-git-sha <exact-40-character-commit>
```

This reads each existing package once and reuses the Stage-0 roster gate:
18 original activities, 9 MCQ/9 interactive, three per type/difficulty,
EN/MS/ZH declarations, chapter/section identity, canonical source-manifest
reference and exact package digest. Unsafe/duplicate paths, changed source
identity, and model/PDF/publication-enabled flags fail closed before file reads.
No provider, PDF, browser, source text, student records or publishing is used.

Exit 0 means only **six structurally valid source-free candidates**. It never
means classroom or academic readiness. Even 18 declared visual plans do not
prove their quality. Instructor selection, original-source/figure rights,
independent physics and EN/MS/ZH meaning, diagram semantics, authentic learner
browser interactions, institution-specific privacy consent and release
authorization remain separate gates. Every report keeps
`classroomPilotReady=false`, `academicQA=REVIEW_REQUIRED` for every case and
`publicationAuthorized=false`. Exit 1 means incomplete/invalid candidates;
exit 2 means an invalid/unreadable scope. This step cannot reopen exhausted
Decisions 0029/0030/0031 or change course diagnostic/prerequisite progression.

## Local-only six-section instructor preview (not classroom release)

### Source-free real-browser engineering smoke

The private full existing-package browser auditor now waits for the actual question and enabled locale selector after each navigation, since the learner deliberately disables language switching during asynchronous package load. Do not replace this readiness check with a fixed sleep or repeat a consumed one-shot candidate to force PASS. Failures retain sanitized phase and Python module/function identity for targeted root-cause classification, without storing raw tracebacks, private paths, original source texts, or credentials. These are harness-integrity checks, not independent academic approval.

The CI job executes `python scripts/check_course_preview_browser.py`
in headless Chrome. It stages only disposable synthetic packages in a
loopback-only temporary directory and tests three interface languages at
390 px and 1280 px, section selection, localized hints, screenshot capture,
responsive overflow and fail-closed rejection of tampered JSON bytes.
It does not read original source PDFs, reach Gemini/ChatGPT, use student
accounts or publish a course. A missing or failing Chrome dependency is a
technical blocker, not permission to skip an acceptance gate.

**This is an engineering smoke only:** six observations on synthetic
activities do not establish actual 18-activity-per-subchapter browser
coverage, independent scientific/visual correctness, source/figure rights,
EN/MS/ZH meaning equivalence, institutional privacy or classroom readiness.
Existing private source-bound browser audit denials and finite C3 campaigns
remain terminal and are not retried through this source-free test.


### One-command local roster preparation

The repo includes a **source-free** helper to avoid manually calculating six
package hashes or hand-writing a JSON roster. In an authorized clean checkout
of draft PR #223, select six **explicit** existing sections from one chapter.
For example, the following is a *test-only candidate selection*, NOT a
record of instructor approval:

```powershell
python scripts/prepare_course_preview.py --chapter 9 --sections 1 2 3 4 5 6 --scope-id sourcefree-pilot-local-instructor-demo
```

This helper reads only the six existing tracked JSON files and Git HEAD.
A clean Windows Git checkout may transform committed LF JSON into CRLF. The tool now compares the path-normalized Git blob with HEAD; genuine content changes remain rejected. The local roster digest still hashes the actual served package bytes.
It refuses modified/untracked packages, invalid activity distributions,
duplicate or mismatched identities, and missing gitignore protection.
It creates `local-pilot/roster.json` exactly once; it will **not overwrite**
an existing local roster. The roster remains ignored by Git, and all science,
translation, visual, rights, browser and institutional approval gates remain
unverified. An instructor must separately confirm the intended pilot roster
before any real class use. Never treat the example sections as approved.

After an authorized candidate check, use `python scripts/serve.py` and visit
`http://127.0.0.1:8000/app/course-preview.html` in the same local checkout.


The separate `app/course-preview.html` provides **manual navigation** among
exactly six existing draft packages from one explicit roster. It uses the
existing single-package learner (no course unlocking or adaptive routing).
This page is **not** included in `scripts/build_public_release.py` output.

Use the **same strict JSON manifest** described in the preceding offline
candidate preflight. First run `scripts/audit_course_pilot_readiness.py`
against exact package bytes and the matching code revision. After a structural
candidate check, place a copy of the private/sanitized manifest at
`local-pilot/roster.json` inside an authorized **local testing checkout**.
`local-pilot/` is excluded by `.gitignore`; never add real student identities,
source passages, private PDF contents, or credentials to that directory.
Then run the documented local server from the repository root:

```powershell
python scripts/serve.py
```

Open `http://127.0.0.1:8000/app/course-preview.html`. The preview loads only
`../local-pilot/roster.json`, accepts six exact same-chapter repository
`content/.../package.json` references, and checks the selected package's
actual response bytes against its manifest SHA-256 in the existing learner
loader before displaying activities. It refuses duplicates, unsafe paths,
changed package bytes, invalid scopes, and unavailable cryptographic hashing.
Nothing auto-selects a first section: the instructor chooses each draft.

The local instructor page intentionally starts **without** an activity package; this is a waiting-for-selection state, not a configuration error. Clearing the section menu invalidates any outstanding package fetch, removes the previous activity, and clears its anonymous session-only practice evidence. While a new section loads, the preceding activity and evidence are hidden; stale `?activity=` deep links are removed so another section starts at its first exercise, and a failed load cannot restore the old section. Selecting another draft starts a fresh in-memory session. This changes neither the public single-package learner nor any course-wide progression/mastery policy.

The menu supports EN/MS/ZH, uses no account or learner persistence and
never calls an AI provider. An absent/invalid roster disables the menu.
**Successful navigation is an engineering/local UI preview, not an academic
PASS, learner mastery evaluation, class authorization, or source-rights
approval.** Do not deploy the page publicly, include it in public bundles,
or use it with real students until the independent source, visual, translation,
browser, privacy and release gates are separately met. The exact-version
SHA check is an integrity guard, not independent physics verification.

## V3 native Gemini API review: automatic SDK recovery (14 November 2026)

After verifying the frozen candidate and independently authorizing the
generated-text-only operation, invoke the normal source-free reviewer CLI:

```powershell
python scripts/run_v3_native_gemini_review.py --execute --allow-generated-text-transfer --batch-size 1 --max-batches 1
```

The default without these flags is **read-only** and cannot transmit content.
An explicit execution first checks the frozen package, existing private role
claims and no-replay state. If the current Python environment lacks the
Google SDK's `HttpRetryOptions` (which is needed to disable implicit model
request retries), the normal CLI now checks the repository's ignored `.venv`
or creates it and makes **one bounded installation** of the project's already
pinned dependencies from `pyproject.toml`. It delegates to that interpreter
once, with a recursion guard. A failed install, unavailable package index,
missing credentials or unresolved model claim stops the run; no model call
can be reported successful from an SDK-installation attempt. It never
installs or upgrades packages in the system-wide Python installation.

A live test of Section 9.1 activity 1 on HP completed both Gemini API
reviewer contexts and recorded one `AI_CONSENSUS_PASS` on the earlier
frozen code revision. See `docs/V3_NATIVE_GEMINI_LIVE_PILOT_20261114.md`
for the exact evidence and separation from later SDK-repair code. This
does not certify all 108 activities, independently validate physics or
EN/MS/ZH, authorize release or merge draft PR #223. Reviewers that
return an uncertain response still stop before any attempted replay.

### V3 Gemini ServerError: safe automatic independent continuation

A genuine Gemini `ServerError` **after submission** is uncertain, not a
proven unsent request. The native runner never resends that activity, even
with a second API key or different model. It preserves the exact private
`AMBIGUOUS` reviewer claim and `AI_UNCERTAIN` aggregate.

For the normal native CLI (with both original execution/transfer flags),
the read-only planner now **quarantines the affected frozen section** and
selects a different unblocked section when one exists. For example, a
Section 9.1 ambiguous assessment can lead to a *new*, independently
authorized Section 9.2 activity; it cannot cause the original Section 9.1
activity to be reported as passed. An existing active review lock prevents
starting another section while a prior request may still be in flight.

The runner enforces a minimum 30-minute cooldown after a recent ambiguous
`ServerError` before any *new* independent model request. Two provider
capacity failures in a rolling hour open the circuit until the window
and cooldown are satisfied. A cooldown or circuit stop is a truthful
status, not an invitation to repeatedly relaunch the same request.
The default read-only CLI shows `quarantinedSections`, `providerCapacity`,
`nextSection` and the unchanged real review counts without model calls.
No automatic merge, release receipt, source-PDF upload or academic PASS is
created. See `docs/decisions/0040-v3-server-error-quarantine.md`.

# Automated learning-content generator

The generator core is domain-independent. Subject-specific instructions, renderer/simulation assets, validators, and verification policy are resolved through `domains/registry.json`; the current default profile is `university-level-physics` at `domains/university-level physics/`. See `docs/DOMAIN_PROFILES.md` before pointing a recycled project at a textbook from another discipline.

This Python 3.12 package turns a controlled Google Drive topic corpus (`source.pdf` plus supplementary sibling PDFs) into one repository-compatible subchapter draft. It supports controlled specific-subchapter generation and coordinated multi-PC operation, including continuous `auto` mode.

For the current installation/operating procedure, start with `docs/PDF_TO_APP_QUICKSTART.md`. Documentation is versioned with the code; `docs/DOCUMENTATION_MAINTENANCE.md` defines the same-PR update rule.

Generated content may be published automatically after repository validation and configured deployment checks succeed. The package `status` remains metadata and does not create a human-review publication gate. Source PDFs, credentials, browser profiles, coordinator tokens, and raw Gemini responses never belong in Git.

## Project authority and machine-local configuration

The tracked project authority is:

```text
config/configure_project.toml
```

Project-owned Gemini text is:

```text
config/gem_description.txt
config/gem_instructions.md
```

`sync-workstation.cmd` renders a machine-local ignored TOML into the repository root. A default new workstation normally uses `project.local.toml`, but the filename is machine-local configuration and may be another allowed name such as `generator.shared.local.toml`.

The synchronization output is authoritative:

```text
Installed config/configure_project.toml as <generated-local-config>.toml (...)
```

Direct CLI commands must use `--config <that-file>` when it is not the default `project.local.toml`.

Google API authorization uses `google.oauth_login`; the Gemini browser independently uses `gemini.login_name`. CLI `--oauth-login` and `--login-name` override those identities separately. The generated file's `[local_gemini]` table supports preserved per-PC `login_name`, `gem_url`, and `gem_edit_url` overrides. Blank values inherit tracked defaults; alternate Gem URLs must be supplied together. Other generated fields remain managed. See `config/README.md`.

## Project-derived state

The Windows state root is derived from `project.project_name`:

```text
%LOCALAPPDATA%\<project_name>
```

It contains workstation settings plus project-scoped credential/token paths, Chrome profile paths, and run state. Changing `project_name` for a recycled project creates a separate state root and environment namespace. Controlled Chrome uses the separate `gemini-browser` child of `chrome_profile_dir`, not the legacy profile's saved sign-ins.

The Google Cloud Desktop OAuth client JSON may be securely copied into multiple trusted project/PC credential directories if those projects intentionally use the same OAuth client. Each project/PC should normally keep its own generated Drive OAuth token.

## Source identity

The Drive scanner recursively finds:

```text
.../<subchapter-id>/source.pdf
```

where the immediate parent looks like `8.1`. Jobs are ordered numerically by chapter/section and tied to stable Drive file/version identity. Replacing a source PDF therefore creates a new source version.

Source-manifest version 1.1 records primary/supplementary PDFs and corpus provenance. Drive generation discovers sibling PDFs beneath the selected topic; direct local `source_files` configuration still accepts only one PDF.

## Stage-0 textbook domain gate

Every Google Drive run resolves a textbook-level subject domain before content generation. The gate always inventories the complete configured Source Root first; an explicit target such as `--chapter 9` or `--pdf-subchapter-path 9.2` is applied only after the textbook domain is verified. The inventory fingerprint covers all topic corpora, and each topic corpus key covers every sibling PDF in that topic folder.

With `[domain] domain_id = "auto"`, Stage 0 deterministically selects representative subchapters (three by default), downloads only those representative PDFs to temporary state storage, and sends them to the configured Gemini API model using the strict `domain-discovery` response schema. A whole-textbook decision must meet `domain_min_confidence` and agree with the per-sample evidence. The result is matched only against active entries in `domains/registry.json`.

A successful result is cached at `${STATE_ROOT}/domain-binding.json` with the whole-root fingerprint and selected profile version. The cache is reused only while both identities remain current. An explicit `domain_id`/`--domain-id` is a deliberate override and is recorded as such. An unsupported textbook exits with `DOMAIN_PROFILE_REQUIRED`; ambiguous/inconsistent/low-confidence evidence exits with `DOMAIN_DISCOVERY_FAILED`. Diagnostic state is stored at `${STATE_ROOT}/domain-discovery-status.json`. No content lease is claimed before this gate passes.

The selected profile now follows the run into the generation pipeline. Source analysis, activity planning/batches, semantic audit, and repair prompts are composed with the matching repository-owned domain instruction while the generic JSON/schema/security contract remains authoritative. The composition map also reserves `visual-*` stages for the profile's `visualGeneration` instruction; this PR does not itself activate a new visual-plan/spec authoring stage.

Newly generated packages carry a `domain` identity (`id`, `profileVersion`, `subject`, `academicLevel`). Parsed auto-mode checkpoints are fenced by the same identity so a profile change cannot reuse stages authored under a stale domain version. Deterministic validation and public release resolve domain validators/registries/runtime assets from the package identity. Existing packages without a `domain` field remain backward-compatible and use the registry default.

## Selection modes

Three modes are supported:

| Mode | Purpose |
|---|---|
| `specific` | Generate an explicitly selected subchapter; no central job claim is required. |
| `auto` | Continuously discover, Drive-claim, recover, publish, and continue through globally eligible Drive jobs. The default backend is Drive-native and needs no Apps Script/Sheet coordinator. An explicit `--pdf-subchapter-path` creates a Drive-lease-protected targeted auto run. |
| `distributed` | Claim coordinated jobs one at a time for advanced/external orchestration. |

CLI examples using an explicit local config:

```powershell
python -m app_generator doctor --config .\<generated-local-config>.toml --selection-mode specific --pdf-subchapter-path 8.5
python -m app_generator run --config .\<generated-local-config>.toml --selection-mode specific --pdf-subchapter-path 8.5
# Existing generated sections fail fast by default. Regenerate only when replacement is deliberate:
python -m app_generator run --config .\<generated-local-config>.toml --selection-mode specific --pdf-subchapter-path 8.5 --regenerate
python -m app_generator doctor --config .\<generated-local-config>.toml --selection-mode auto
python -m app_generator run --config .\<generated-local-config>.toml --selection-mode auto
python -m app_generator doctor --config .\<generated-local-config>.toml --selection-mode auto --pdf-subchapter-path 8.6
python -m app_generator run --config .\<generated-local-config>.toml --selection-mode auto --pdf-subchapter-path 8.6
```

### Existing-package safety and explicit regeneration

Specific mode never overwrites an existing generated section implicitly. If any destination artifact already exists, the run stops before content generation with `PACKAGE_ALREADY_EXISTS`. `--regenerate` is an explicit specific-mode-only replacement request: the candidate is generated and validated first, existing artifacts are backed up, replacement is performed atomically, repository validation runs against the replacement, and the originals are restored if installation or verification fails. Auto/distributed modes do not accept this flag and retain their existing completed/skip semantics.

### Targeted auto semantics

Targeted auto is activated only when the operator explicitly supplies `--pdf-subchapter-path` together with `--selection-mode auto`. The tracked/configured default `placeholders.pdf_subchapter_path` remains useful for specific-mode defaults and does **not** silently pin ordinary auto mode.

For a target such as `8.6`, Stage 0 first verifies the domain against the **complete Source Root**. Only after that textbook-level gate passes does the runtime filter the inventory to exact section `8.6` for queue preview, durable-handoff reconciliation, and Drive claim election. The worker:

- acquires the normal Drive-native lease for 8.6;
- waits if another worker currently owns 8.6;
- never substitutes 8.7 or another section;
- can restore compatible interrupted checkpoints for 8.6;
- exits successfully without generation when 8.6 is already globally successful;
- reports a missing/terminally failed target instead of falling through;
- exits after 8.6 succeeds rather than continuing through the global queue.

This is the preferred operator-selected mode when other auto workers may be running concurrently. Ordinary `specific` mode remains intentionally uncoordinated.

## Gemini behavior

With `browser_mode = "controlled"`, the launcher opens independent ordinary Chrome directly on the configured `gem_url` with no Selenium or remote-debugging connection. A new separate profile at `<chrome_profile_dir>/gemini-browser` starts signed out and can retain the Gemini login for later launches. The app displays the configured Gemini `login_name` (or `[local_gemini].login_name` override) and both Gem URLs. The operator finishes sign-in, confirms the Gem loads, closes that dedicated window, and presses Enter. The launcher then reopens the same signed-in profile with a local debug connection, Selenium attaches, and the client navigates to `gem_edit_url` and verifies the active account. Gemini login is independent of Drive's OAuth account. Personal and legacy generator profiles are neither read nor cleared. The local-only debug connection uses a Chrome-assigned port and waits at most 15 seconds for a matching endpoint with an open page; driver setup can take longer, but the Chrome window is already launched.

`ChromeSession.open_window()` opens ordinary Chrome without debugging, `wait_for_manual_sign_in()` requires that window to close, and `start()` relaunches the same profile before connecting Selenium. Closing a connected controlled session closes only this independent browser and preserves its on-disk login. If automation cannot connect, the window remains available for manual sign-in. Explicit `attach` mode remains advanced: it connects only to the supplied existing browser, does not launch a window or reset its login, and leaves that browser open on cleanup. Account verification applies in both modes; a saved login is never assumed correct.

Verification requires the exact configured email on visible Google Account controls. Hidden account-chooser entries, generic email buttons, and ambiguous multiple visible identities do not prove the active account.

Before live generation, the client reads the authoritative Gem values:

- Description from `config/gem_description.txt`;
- Instructions from `config/gem_instructions.md`.

The Gem editor is opened under the verified Gemini browser account. The configured Gem URLs identify the target; its display name is left untouched. The generator compares Description and Instructions, changes only values that differ, saves only when needed, reopens, and verifies persistence. A fresh Gem conversation is then used for each controlled topic corpus.

## Generated artifacts

Each successful section writes:

```text
content/chapter-*/section-*/README.md
content/chapter-*/section-*/learning-design.md
content/chapter-*/section-*/package.json
content/chapter-*/section-*/review-record.md
content/source-manifests/<package-id>.json
```

Artifacts are staged and validated before installation. Existing section artifacts are not silently overwritten.

## Drive-native auto coordination

`auto` mode now defaults to `automation.coordination_backend = "drive"`. It creates small JSON marker/event files directly in the existing Drive subchapter folder beside that topic corpus; no shared state folder has to be bootstrapped. Claim election, heartbeat fencing, parsed-stage checkpoints, failure history, retry resets, and durable success are all represented there. No Google Apps Script deployment, Google Sheet, coordinator token, or administrator bootstrap is required for normal auto operation.

The winning claim's Drive file ID is a fencing token. Ownership is elected by Drive server `createdTime` and file ID, while expiry uses the Drive HTTP server time and marker `modifiedTime`; PC clocks do not decide ownership. Checkpoints are append-only and source-corpus-bound. See `docs/DRIVE_NATIVE_AUTO_COORDINATION.md`.

The older managed/external Apps Script coordinator remains in the repository for `distributed` mode and legacy administration. Commands such as `coordinator-bootstrap`, `coordinator-ensure`, and `coordinator-status` apply to that compatibility path, not to default auto mode.

## Continuous auto-mode contract

Auto mode requires writable Google Drive access plus `git_publish=true`. It does not require a managed/external cloud coordinator when `coordination_backend = "drive"`.

The continuous worker:

1. synchronizes/reconciles durable Git state;
2. derives the current full-corpus job identity for each source section;
3. creates a unique Drive claim and wins only after deterministic two-pass election;
4. prioritizes recoverable interrupted work before untouched queued work;
5. restores source-version-bound parsed-stage checkpoints when available;
6. generates/repairs/validates remaining stages;
7. publishes validated artifacts through the configured Git handoff;
8. when configured, publishes/reuses the deterministic public Pages PR;
9. writes a Drive `success` marker only after every required durable publication;
10. claims another job;
11. waits when remaining work is leased elsewhere and exits successfully only when global work is successful.

When `target_subchapter_id` is supplied through the explicit auto CLI target, the same lease/checkpoint/publication contract applies to the filtered one-section inventory, and the worker exits after that target succeeds.

`Ctrl+C` stops the worker; active leases are returned safely when possible and expired leases remain recoverable. If repeated interruption exhausts the configured attempt budget, inspect the failure and explicitly recover only that target with `python -m app_generator coordinator-retry-failed --config <generated-local-config> --pdf-subchapter-path <chapter.section> --confirm`. The command verifies the current Drive source identity and terminal Drive coordination state, resets the bounded attempt budget, and returns the target to `interrupted`; it neither claims the job nor marks it complete. Run targeted auto `doctor` again before restarting generation.

See `docs/CONTINUOUS_AUTO_TESTING.md` for a two-PC verification procedure.

## Git handoff

When `git_publish=true`, the worker requires a clean/non-diverged checkout and uses deterministic/recoverable job branches. It can reuse valid pushed handoffs/open PRs, recognize merged results, and recover under an exact Drive lease instead of rerunning Gemini unnecessarily.

`auto` and `distributed` modes require durable publication. Specific mode can be operated conservatively with Git publication disabled.

Generation, automated validation, source merge, and public deployment remain separate machine-enforced gates.

The repository project enables automatic public deployment to the shared Pages repository after automated validation succeeds. Each auto attempt is supervised in a child process: default 600-second meaningful-activity checks terminate after three stale checks while preserving Drive parsed-stage checkpoints for a later lease reclaim.

## Deployment inventory

Public routes are tracked separately from generation state in:

```text
config/deployments.json
```

List the current inventory from the repository root:

```powershell
python -m app_generator deployments
```

This command does not load workstation configuration or contact Drive/GitHub. It compares the tracked registry with generated `content/chapter-*/section-*/package.json` files, reports `GENERATED` and `DEPLOYED` independently, prints each tracked public URL, and includes generated packages that have no deployment entry yet. See `docs/DEPLOYMENTS.md`.

## Validation

Deterministic repository checks include:

```powershell
python scripts\lint.py
python scripts\validate_content.py
python -m unittest discover -s tests -v
node --check app\app.js
node tests\test_app_loading.js
node tests\test_app_rendering.js
node tests\test_interaction_rendering.js
python scripts\check_documentation_impact.py
```

`doctor` exercises configuration/Drive/provenance and coordinated queue inspection where relevant. When no current Source-Root/domain binding exists, doctor may upload only the bounded representative textbook PDFs required for Stage-0 domain discovery to the configured Gemini API; it does **not** start activity/content generation or claim an auto content job.

## Failure handling

Drive ambiguity, wrong accounts, bad downloads, domain-profile absence/ambiguity, dirty/diverged Git, invalid generated content, lease loss, coordinator health failure, or unsafe publication stop the affected operation. Auto mode preserves recoverable state/checkpoints where possible and does not claim global success when terminal failures remain.

Network-facing Git synchronization/publication operations use bounded retries for recognized transient transport failures such as connection resets, temporary DNS/connectivity failures, timeouts, selected HTTP 502/503/504 responses, and common curl/TLS transport errors. Retry backoff is 2, 5, then 10 seconds after the initial attempt. Deterministic failures such as authentication errors, dirty worktrees, non-fast-forward updates, invalid refs, or merge conflicts still fail immediately. Read-only GitHub CLI checks may use the same transient retry path; non-idempotent PR actions retain their existing explicit reconciliation behavior rather than being blindly retried.

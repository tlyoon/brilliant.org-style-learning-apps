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

Visual-plan and visual-spec generation is schema-gated. Specification prompts
embed the exact repository visual-spec schema. For specification-only validation
errors, the generator reuses the valid planning checkpoint and makes one bounded
specification retry with the deterministic findings. A failed pilot can be
resumed using --resume RUN_ID in specific mode only when Git publication is
disabled; check the preserved run/candidate and unchanged source identity
before resuming. Do not delete saved stage responses or overwrite the
previously installed package to bypass a failed visual gate.

## Failure handling

Drive ambiguity, wrong accounts, bad downloads, domain-profile absence/ambiguity, dirty/diverged Git, invalid generated content, lease loss, coordinator health failure, or unsafe publication stop the affected operation. Auto mode preserves recoverable state/checkpoints where possible and does not claim global success when terminal failures remain.

Network-facing Git synchronization/publication operations use bounded retries for recognized transient transport failures such as connection resets, temporary DNS/connectivity failures, timeouts, selected HTTP 502/503/504 responses, and common curl/TLS transport errors. Retry backoff is 2, 5, then 10 seconds after the initial attempt. Deterministic failures such as authentication errors, dirty worktrees, non-fast-forward updates, invalid refs, or merge conflicts still fail immediately. Read-only GitHub CLI checks may use the same transient retry path; non-idempotent PR actions retain their existing explicit reconciliation behavior rather than being blindly retried.

Visual-spec generation also reads physics renderer guidance in the active domain profile, retains individually validated specifications, and retries failed activity IDs only. The two-attempt visual batch cap remains. The original package is not replaced until all repository checks pass.

### Offline visual pilot audit

Run `python scripts/audit_visual_run.py --run-root PATH_TO_SAVED_RUN` to inspect saved plans and visual specifications without invoking Gemini or changing files. For a COMPLETE run, it verifies the installed package recorded by the run state, independently reconstructing and comparing visual fields against current renderer contracts. An offline `contract_pass` is NOT proof of source accuracy, visual pixel quality, browser accessibility, or publication readiness. Non-complete or inconsistent runs exit with a failure status and diagnostics.

### Semantic visual-render smoke test

Run `node scripts/audit_visual_rendering.js --package PATH` to instantiate every visual in en/ms/zh through the trusted JavaScript renderer without modifying the package. The test checks semantic SVG/figure output, accessible descriptions, expected template identities and finite geometry attributes. It deliberately does **not** verify actual browser pixels, academic correctness, device layout or WCAG compliance. Use real browser, source-grounding, and accessibility review before release.

### Visual pilot technical gate

Run `python scripts/visual_pilot_gate.py --run-root PATH_TO_SAVED_RUN` to combine the read-only installed-package audit with semantic renderer tests. Output `technicalEvidenceReady=true` means only deterministic contract and synthetic DOM checks passed, not that the app is release-ready. The report *always* leaves actual browser/pixel, classroom accessibility, source-grounded academic review, and learner review as pending; publication is never authorized by this tool.

### Isolated browser-level visual smoke test

For a complete local teaching package, run `python scripts/audit_browser_visual.py --package PATH`. The tool copies only needed static assets to a temporary local directory, launches a private-profile headless Chrome, serves content on 127.0.0.1, and tests every visual in en/ms/zh at desktop/mobile viewport sizes. It checks SVG nodes, aria descriptions, response controls and visual horizontal overflow, then destroys its temporary browser/profile and server. A browser DOM smoke pass is not proof of final pixel quality, WCAG screenreader compliance or academic correctness, and cannot authorize publication. Selenium and a compatible Chrome driver are needed only for this optional QA tool.

### Visual review evidence capture

Pass `--evidence-root NEW_PRIVATE_DIRECTORY` to `scripts/audit_browser_visual.py` to capture element-level PNGs for all real-browser locale/viewport checks. Evidence files are stored outside the repository and original production package; the manifest retains package SHA-256, individual PNG SHA-256, and explicit `unreviewed` status. This is evidence for later academic/pixel/accessibility inspection, **not** an automated pass of those review gates. The directory must not already exist and the tool refuses evidence paths inside the source repository or installed package folder.

### Keyboard focus continuity

MCQ button activation regenerates the activity card; the player now restores keyboard focus to the selected replacement button. The headless Chrome visual pilot checks Enter-key selection, `aria-pressed`, check-answer enablement, and focus continuity for every visual MCQ in three locales at two viewport widths. This is a bounded keyboard smoke check, not a full screen-reader/WCAG audit.

### Interactive answer-button focus after rerender

For classification, matching and multi-selection activities, the player records stable item/target IDs on answer buttons and restores focus to the corresponding control after updating the activity card. This complements the MCQ focus repair. Test coverage checks actual re-rendered focus, not just answer correctness; keyboard and screenreader validation in a real browser remains a separate acceptance gate.

### Keyboard focus after ordering moves

Moving an item up or down replaces its entire ordering row. The player now maintains semantic item/direction identifiers and focuses the new enabled direction control for that item. When the original move direction becomes disabled at a list boundary, the opposite enabled move button receives focus. DOM tests exercise repeated reorders, focus continuity and this boundary fallback without changing ordering answer scoring.

### Autonomous academic QA decision policy

Academic verification gates use PASS, FAIL, or REVIEW_REQUIRED. PASS requires explicit independent deterministic or source-verified evidence, never only the original generation model report. Missing evidence remains REVIEW_REQUIRED; a verified failure takes precedence. This evaluation never marks human review as performed or authorizes publication. See app_generator/validation/academic_qa.py.

### Independent academic QA triage (Section 9.4 pilot)

Run `python scripts/audit_academic_qa.py --package PATH_TO_INSTALLED_PACKAGE`. An optional `--source-pdf PRIVATE_CONTROLLED_PDF_PATH` permits read-only SHA-256 identity checking; it does NOT upload or publish the PDF. The tool checks source-file identity, structural answer integrity, numerical collision witness availability, multilingual completeness and visual renderer contracts. PASS requires independently verified evidence for every academic gate; incomplete evidence is REVIEW_REQUIRED. A verified contradiction is FAIL. The report explicitly preserves humanReviewed=false and publicationAuthorized=false. It does not claim that syntactic validation, file hashes or model-based semantic reviews establish textbook accuracy. Next development work must provide trusted source-bound crosschecks and independent scientific/translation verification before academic PASS can be claimed.


### Academic public-release gate

Normal generation, local installation and draft GitHub review remain possible
while independent academic evidence is REVIEW_REQUIRED. Automatic Git merge
and public deployment now invoke the academic release guard only after
the installed package has been revalidated. It recomputes the academic report
for the exact installed package SHA-256, saves a durable
validation/academic-release-gate.json record and fails closed unless every
academic gate has trusted independent PASS evidence. This supersedes the
older assumption that Gemini semantic review and green structural checks
alone warrant public release. A false/ambiguous QA result never grants
publication permission. See the continuation checkpoint and failure ledger.


### Direct public publisher release safety

The public Pages publisher is also called from auto-recovery, not only the
normal generation orchestrator. Its publish entrypoint now independently
requires matching, trusted academic PASS for the exact installed package.
A private SHA-bound academic validation receipt is saved in the configured
state directory. A missing state directory or unresolved result blocks public
merge *before* remote Git operations. Test-only fake publisher/recovery
fixtures may mock independently validated academic evidence to isolate Git
idempotency, but production may never substitute such fixtures for proof.


### Academic gate for source-branch handoff recovery

An interrupted distributed run can leave a committed source job branch without
a completed publish phase. Automatic Git merge is now gated at the common
PR-finalization path, not just at the normal generator or Pages publisher. Both
the candidate branch's package and source-manifest Git blobs must match local
files before independent academic QA is consulted. Unresolved or mismatched
source handoffs cannot be auto-merged. Draft review branches remain available.
Blocked recovery must not blindly regenerate an ambiguous Gemini request.

## Autonomous academic AI review after package generation

The generator now runs source-bound academic review after final package
verification and before protected release. It reads the private
academic-review-source-packets.json in the owned validation run directory.
The source packet must match the generated package SHA and controlled local
PDF SHA. Literal page evidence is independently re-extracted from the PDF.

When pre-provisioned dedicated controlled Gemini reviewer profiles exist
for the physics and semantics roles, the stage uses independent browser
sessions with version-bound claims. The authoring browser and Gem are not
reused, and source passages and credentials never go into Git.

When evidence or independent reviewer authentication is unavailable, the
stage writes autonomous-academic-queue.json to the private validation
directory with AUTO_SOURCE_CHECK or AUTO_RETRY instructions. Missing
learner-facing activities produce a PACKAGE follow-up rather than
breaking legacy local generation. No manual academic reviewer approval is
required.

This stage is not an academic PASS or public-release authorization.
Unresolved evidence stays REVIEW_REQUIRED; protected publication and
merge permissions remain unchanged. See docs/AUTONOMOUS_AI_ACADEMIC_QA.md
and docs/decisions/0024-autonomous-ai-academic-review.md.
## Automatic private academic repair

After independent reviewers identify a concrete contradiction, the runtime
may dispatch a limited AI repair in a dedicated controlled browser context.
The correction is restricted to existing three-language learner-facing text
and answer explanations. It cannot alter grading keys, visual structure,
other activities, or the installed package. Attempts are checkpointed prior
to submitting the model request. The successful result is a private candidate
requiring fresh independent verification, never academic PASS.
A missing reviewer or repair profile creates a recoverable automatic task
without requiring manual academic sign-off. Publication remains separately
disabled unless authorized.

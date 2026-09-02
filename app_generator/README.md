# Automated learning-content generator

This Python 3.12 package turns one controlled Google Drive `source.pdf` into one repository-compatible subchapter draft. It supports controlled specific-subchapter generation and coordinated multi-PC operation, including continuous `auto` mode.

For the current installation/operating procedure, start with `docs/PDF_TO_APP_QUICKSTART.md`. Documentation is versioned with the code; `docs/DOCUMENTATION_MAINTENANCE.md` defines the same-PR update rule.

Generated content remains `draft` until qualified human review is complete. Source PDFs, credentials, browser profiles, coordinator tokens, and raw Gemini responses never belong in Git.

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

## Project-derived state

The Windows state root is derived from `project.project_name`:

```text
%LOCALAPPDATA%\<project_name>
```

It contains workstation settings plus project-scoped credential/token paths, Chrome profile, and run state. Changing `project_name` for a recycled project creates a separate state root and environment namespace.

The Google Cloud Desktop OAuth client JSON may be securely copied into multiple trusted project/PC credential directories if those projects intentionally use the same OAuth client. Each project/PC should normally keep its own generated Drive OAuth token.

## Source identity

The Drive scanner recursively finds:

```text
.../<subchapter-id>/source.pdf
```

where the immediate parent looks like `8.1`. Jobs are ordered numerically by chapter/section and tied to stable Drive file/version identity. Replacing a source PDF therefore creates a new source version.

The current source-manifest contract represents one controlled PDF per package.

## Selection modes

Three modes are supported:

| Mode | Purpose |
|---|---|
| `specific` | Generate an explicitly selected subchapter; no central job claim is required. |
| `auto` | Continuously discover, claim, recover, publish, and continue through globally eligible Drive jobs until the source inventory is successful. |
| `distributed` | Claim coordinated jobs one at a time for advanced/external orchestration. |

CLI examples using an explicit local config:

```powershell
python -m app_generator doctor --config .\<generated-local-config>.toml --selection-mode specific --pdf-subchapter-path 8.5
python -m app_generator run --config .\<generated-local-config>.toml --selection-mode specific --pdf-subchapter-path 8.5
python -m app_generator doctor --config .\<generated-local-config>.toml --selection-mode auto
python -m app_generator run --config .\<generated-local-config>.toml --selection-mode auto
```

## Gemini behavior

Before live generation, the client reads the authoritative Gem values:

- Name from `config/configure_project.toml`;
- Description from `config/gem_description.txt`;
- Instructions from `config/gem_instructions.md`.

The Gem editor is opened under the configured Google account. The generator compares fields, changes only values that differ, saves only when needed, reopens, and verifies persistence. A fresh Gem conversation is then used for each controlled PDF.

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

## Repository-managed coordinator

Current `main` supports a managed coordinator lifecycle for `auto` and `distributed` modes.

An empty configured URL:

```toml
[automation]
coordinator_url = ""
```

selects repository-managed infrastructure. The runtime consists of a private Google Sheet/Apps Script deployment plus private Drive metadata/checkpoint storage managed through the repository's serialized GitHub Actions deployment workflow.

An explicit valid Apps Script URL remains backward-compatible external coordinator mode.

### One-time bootstrap

Check:

```powershell
python -m app_generator coordinator-status --config .\<generated-local-config>.toml
```

If managed infrastructure is missing, one trusted administrator PC runs:

```powershell
gh auth status
python -m app_generator coordinator-bootstrap --config .\<generated-local-config>.toml
```

Bootstrap obtains the additional Google administration authorization, verifies the configured account, stores the refreshable administrator credential in a private GitHub Actions secret, triggers the serialized deployment, and waits for live health.

Other worker PCs do not repeat bootstrap. Verify readiness with:

```powershell
python -m app_generator coordinator-ensure --config .\<generated-local-config>.toml
```

Workers discover managed runtime metadata with their ordinary Drive authorization; they do not need the administrator OAuth token locally.

## Continuous auto-mode contract

Auto mode requires Google Drive discovery, a healthy managed/external coordinator, and `git_publish=true` so a job is not marked globally successful while its artifacts exist only on one PC.

The continuous worker:

1. synchronizes/reconciles durable Git state;
2. inspects the globally coordinated source inventory;
3. atomically claims an eligible lease;
4. prioritizes recoverable interrupted work according to coordinator policy;
5. restores source-version-bound parsed-stage checkpoints when available;
6. generates/repairs/validates remaining stages;
7. publishes validated artifacts through the configured Git handoff;
8. marks the coordinated job generated only after durable publication;
9. claims another job;
10. waits when remaining work is leased elsewhere and exits successfully only when global work is successful.

`Ctrl+C` stops the worker; active leases are returned safely when possible and expired leases remain recoverable.

See `docs/CONTINUOUS_AUTO_TESTING.md` for a two-PC verification procedure.

## Git handoff

When `git_publish=true`, the worker requires a clean/non-diverged checkout and uses deterministic/recoverable job branches. It can reuse valid pushed handoffs/open PRs, recognize merged results, and recover under an exact coordinator lease instead of rerunning Gemini unnecessarily.

`auto` and `distributed` modes require durable publication. Specific mode can be operated conservatively with Git publication disabled.

Generation, human approval, merge, and public deployment remain separate gates.

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

`doctor` exercises configuration/Drive/provenance and coordinated queue inspection where relevant, but does not upload a PDF to Gemini.

## Failure handling

Drive ambiguity, wrong accounts, bad downloads, dirty/diverged Git, invalid generated content, lease loss, coordinator health failure, or unsafe publication stop the affected operation. Auto mode preserves recoverable state/checkpoints where possible and does not claim global success when terminal failures remain.

# Project configuration boundary

Start with `docs/PDF_TO_APP_QUICKSTART.md` for the current operating workflow. This file is the field/reference guide for project configuration. Documentation is versioned with code; see `docs/DOCUMENTATION_MAINTENANCE.md`.

## Tracked authority

`config/configure_project.toml` is the normal tracked authority for non-secret values that vary by project.

Project-owned Gemini text is also tracked:

- `configure_project.toml` → Gem Name through `gemini.gem_name`;
- `gem_description.txt` → Gem Description;
- `gem_instructions.md` → Gem Instructions.

Before live generation, the generator reconciles the editable Gem fields with these authoritative values and verifies persistence.

## Important project-dependent values

Review these when creating/recycling a project:

- `project.project_name`;
- `placeholders.sourcepath`;
- `placeholders.gemini-gem`;
- `placeholders.loginname`;
- `placeholders.pdf_subchapter_path`;
- `placeholders.target_filename` and `target_file`;
- `gemini.gem_edit_url` and `gem_name`;
- source/provenance metadata;
- automation selection/coordinator policy;
- Git publication/PR/merge policy;
- model preference policy.

## Project-derived tokens

Do not replace these with copied machine-specific values:

- `${PROJECT_SLUG}`;
- `${PROJECT_ENV_PREFIX}`;
- `${REPO_ROOT}`;
- `${STATE_ROOT}`.

On Windows `${STATE_ROOT}` resolves to:

```text
%LOCALAPPDATA%\<project_name>
```

and is reused for workstation settings, OAuth client/token paths, Chrome profile, and run state.

Changing `project_name` gives the recycled project an independent local state root and environment namespace.

## OAuth client and token policy

The configured OAuth paths resolve under:

```text
%LOCALAPPDATA%\<project_name>\credentials\
```

The Google Cloud Desktop OAuth **client JSON contents** may be securely copied into multiple trusted project/PC directories if they intentionally use the same Google OAuth client. Do not make one project reference another project's state directory. Each project/PC should normally maintain its own generated Drive OAuth token.

Credentials and tokens never belong in the tracked TOML or Git.

## Machine-local rendered configuration

`sync-workstation.cmd` renders the tracked project authority into an ignored local TOML in the repository root.

A default newly initialized workstation normally uses:

```text
project.local.toml
```

but `workstation-sync.toml` may specify another allowed ignored basename such as:

```text
generator.shared.local.toml
```

The synchronizer prints the exact filename it installed. Direct `app_generator` commands must pass `--config <printed-file>` when that filename differs from the CLI default.

## Selection modes

Current values are:

```text
specific
auto
distributed
```

- `specific` selects one explicit subchapter and does not require a central job claim;
- `auto` continuously claims/recover/publishes jobs until the globally coordinated inventory is successful;
- `distributed` provides coordinated one-job selection for advanced/external orchestration.

`auto` and `distributed` require Google Drive discovery and `git_publish=true`.

## Managed versus external coordinator

Current default coordinator management is repository-managed GitHub Actions infrastructure.

When:

```toml
[automation]
coordinator_url = ""
```

is empty, the project uses repository-managed coordinator infrastructure. The CLI can report/bootstrap/ensure it with:

```powershell
python -m app_generator coordinator-status --config <local-config>
python -m app_generator coordinator-bootstrap --config <local-config>
python -m app_generator coordinator-ensure --config <local-config>
```

`coordinator-bootstrap` is a **one-time project-wide administrator action**, not a per-PC setup step. Worker PCs discover the managed runtime through their ordinary Drive authorization.

If `coordinator_url` is explicitly set to a valid Google Apps Script URL, that URL is authoritative and the project remains in backward-compatible external coordinator mode.

Coordinator protocol, lease, heartbeat, and attempt settings remain project policy. Token values remain outside Git.

## Git policy

For controlled specific-mode testing, a project may use:

```toml
git_publish = false
git_auto_merge = false
```

Continuous `auto`/`distributed` operation requires `git_publish=true` so globally completed jobs have durable shared artifacts.

Auto-merge is a separate policy choice and never turns a generated draft into qualified human approval.

## Generic application contracts

The following are application/schema contracts rather than textbook identity:

- one PDF per package;
- supported interaction modes;
- deterministic validation/provenance rules;
- current activity/type/difficulty distribution;
- current English/Malay/Simplified-Chinese contract;
- calculator-free conceptual policy;
- credentials/PDFs/run state outside Git;
- generated work remains draft until qualified human review.

## Compatibility file

`config/project.toml` remains only for compatibility with older tooling/tests during the current migration. Normal workstation operation enters through `sync-workstation.cmd`, which selects `config/configure_project.toml`.

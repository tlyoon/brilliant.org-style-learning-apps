# Project configuration boundary

Start with `docs/PDF_TO_APP_QUICKSTART.md` for the current operating workflow. This file is the field/reference guide for project configuration. Documentation is versioned with code; see `docs/DOCUMENTATION_MAINTENANCE.md`.

## Tracked authority

`config/configure_project.toml` is the normal tracked authority for non-secret values that vary by project.

## Single Source Root

`placeholders.sourcepath` is the **one authoritative project-level source-root placeholder** for Stage 0 and every later blueprint stage. For the present project it is:

```toml
[placeholders]
sourcepath = "https://drive.google.com/drive/folders/1xiYsp3pe3bcWV9W_ikarnjo_i_EsAPaA"
```

This Google Drive folder is the source universe for Chapters 8 through 14. `pdf_subchapter_path`, `target_filename`, CLI target arguments, and future chapter/topic selectors select material **beneath** `sourcepath`; they are not alternative source roots. `target_file` is a derived locator template and must continue to derive from `{sourcepath}`.

Do not add another project-level source-root placeholder for Stage 1 or later stages. When recycling the repository for another course/source tree, change `placeholders.sourcepath` through the project configurator and keep downstream stages rooted in that value.

Public deployment metadata is tracked separately in `config/deployments.json`. It records public review routes and URLs; it is not a workstation configuration file and contains no credentials. Query it with `python -m app_generator deployments`. See `docs/DEPLOYMENTS.md`.

Project-owned Gemini text is also tracked through `configure_project.toml`, `gem_description.txt`, and `gem_instructions.md`. Before live generation, the generator reconciles editable Gem fields with these authoritative values and verifies persistence.

## Important project-dependent values

Review these when creating/recycling a project:

- `project.project_name`;
- `placeholders.sourcepath` — the single Source Root;
- `placeholders.gemini-gem`;
- `placeholders.loginname`;
- `placeholders.pdf_subchapter_path` — a selector beneath the Source Root;
- `placeholders.target_filename` and derived `target_file`;
- `gemini.gem_edit_url` and `gem_name`;
- source/provenance metadata;
- automation selection/coordinator policy;
- Git publication/PR/merge policy;
- model preference policy.

## Project-derived tokens

Do not replace `${PROJECT_SLUG}`, `${PROJECT_ENV_PREFIX}`, `${REPO_ROOT}`, or `${STATE_ROOT}` with copied machine-specific values. On Windows `${STATE_ROOT}` resolves to `%LOCALAPPDATA%\<project_name>` and is reused for workstation settings, OAuth client/token paths, Chrome profile, and run state.

## OAuth client and token policy

The configured OAuth paths resolve under `%LOCALAPPDATA%\<project_name>\credentials\`. The Google Cloud Desktop OAuth client JSON contents may be securely copied into multiple trusted project/PC directories if they intentionally use the same Google OAuth client. Each project/PC should normally maintain its own generated Drive OAuth token. Credentials and tokens never belong in tracked TOML or Git.

## Machine-local rendered configuration

`sync-workstation.cmd` renders the tracked project authority into an ignored local TOML in the repository root. The synchronizer prints the exact filename it installed. Direct `app_generator` commands must pass `--config <printed-file>` when that filename differs from the CLI default.

## Selection modes

Current values are `specific`, `auto`, and `distributed`.

- `specific` selects one explicit subchapter beneath the Source Root;
- `auto` continuously claims/recover/publishes jobs from the inventory beneath the Source Root;
- `auto` plus explicit `--pdf-subchapter-path <chapter.section>` becomes targeted auto;
- `distributed` provides coordinated one-job selection for advanced/external orchestration.

The tracked `placeholders.pdf_subchapter_path` is a default selector and does not redefine or replace `placeholders.sourcepath`. Auto targeting is activated only when the operator explicitly supplies `--pdf-subchapter-path` on an auto command.

`auto` and `distributed` require Google Drive discovery and `git_publish=true`.

## Managed versus external coordinator

When `[automation].coordinator_url` is empty, the project uses repository-managed coordinator infrastructure. An explicit valid Google Apps Script URL remains backward-compatible external coordinator mode. Coordinator configuration is independent of the Source Root and must not introduce another content root.

## Git policy

For controlled specific-mode testing, a project may use `git_publish=false` and `git_auto_merge=false`. Continuous `auto`/`distributed` operation requires `git_publish=true` so globally completed jobs have durable shared artifacts. Auto-merge is a separate policy choice and never turns a generated draft into qualified human approval.

## Stage-0 application contracts

The current Stage-0 baseline retains these contracts while establishing the single-root invariant:

- one configured Google Drive Source Root;
- one selected PDF per generated package;
- selectors resolve beneath the Source Root;
- supported interaction modes;
- deterministic validation/provenance rules;
- current activity/type/difficulty distribution;
- current English/Malay/Simplified-Chinese contract;
- calculator-free conceptual policy;
- credentials/PDFs/run state outside Git;
- generated work remains draft until qualified human review.

Multi-PDF topic synthesis belongs to Stage 1; Stage 0 does not need to implement it. Stage 1 must, however, reuse the same `sourcepath` rather than introducing another root.

## Compatibility file

`config/project.toml` remains only for compatibility with older tooling/tests during the current migration. It is not a second project configuration authority. Normal workstation operation enters through `sync-workstation.cmd`, which selects `config/configure_project.toml`.

# Decision 0008: Repository-tracked shared generator configuration

**Status:** Accepted 27 August 2026

## Context

The Windows workstation synchronizer previously downloaded `generator.shared.toml` from a private Google Drive `Projects` folder after updating the repository. That split code and configuration across two version systems, added a second availability dependency, and allowed a workstation to combine a Git revision with an independently changed Drive configuration.

The shared generator settings contain no credentials or source documents. Machine-specific OAuth paths, tokens, Chrome profiles, worker state, and run data are already derived or provisioned separately on every PC.

## Decision

- Track the active non-secret shared configuration as `config/generator.shared.toml` in the private GitHub repository.
- Distribute it through the same fast-forward Git synchronization used for generator code.
- Render `${REPO_ROOT}` and the PC's locally configured OAuth paths into the ignored root file `generator.shared.local.toml`.
- Continue enforcing the shared-field allow-list, size limit, TOML validation, repository-root check, account consistency check, and atomic local installation.
- Keep OAuth clients and tokens, coordinator token values, Chrome profiles, source PDFs, run state, logs, and worker identity outside Git.
- Continue using Google Drive for controlled source-PDF discovery and download; remove only the Drive `Projects` configuration-distribution dependency.
- Tolerate obsolete `projects_folder_url` and `shared_config_name` fields in existing machine-local settings during migration.
- Remove the old Drive copy only after the tracked flow has been verified on more than one PC.

## Consequences

- A code revision and its shared configuration are reviewed, rolled back, and synchronized together.
- New PCs need Git access plus locally provisioned credentials, but no configuration file in a separate Drive folder.
- Configuration changes now require a repository branch and pull request.
- The private repository contains the configured account email and Gem/source folder URLs, but no credential capable of granting access to them.
- Decision 0006 remains unchanged: each generation job still uses one claimed PDF in a fresh Gem conversation with central leasing for distributed work.

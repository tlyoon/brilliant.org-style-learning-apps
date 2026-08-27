# Decision 0009: Single project configuration authority

**Status:** Accepted 27 August 2026

## Context

Decision 0008 moved non-secret generator settings from a Google Drive Projects folder into the repository. The next genericization step needs one clearly named project-level authority rather than an active generator-specific file alongside several examples.

## Decision

- Make `config/project.toml` the sole active editable authority for non-secret, machine-independent project settings.
- Add `project.project_name`, initially `BrilliantContentGenerator`, and validate it as a safe portable identifier.
- Keep credentials, token values, OAuth files, Chrome profiles, controlled PDFs, run data, and worker state outside Git.
- Continue rendering `${REPO_ROOT}` and machine-local OAuth paths into the ignored runtime configuration.
- Reject missing required sections, unknown sections or keys, unsafe project names, oversized files, symbolic links, invalid TOML, and invalid runtime configuration.
- Retain legacy generator example TOMLs temporarily as non-authoritative migration material; remove duplicated project defaults in a later phase.
- Defer derivation of machine paths and environment-variable names from `project_name` to Phase 2.

## Consequences

- A person recycling the package has one active tracked file to edit.
- Project configuration changes remain reviewable and versioned with their consuming code.
- Existing machine-local settings and the ignored generated runtime configuration continue to work.
- The package is not yet fully generic: current Section 8.1 values and fixed local-state naming remain until later phases.

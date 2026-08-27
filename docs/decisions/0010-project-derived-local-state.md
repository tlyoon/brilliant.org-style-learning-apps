# Decision 0010: Project-derived local state and environment names

## Status

Accepted, 27 August 2026.

## Context

The generator must be recyclable for another textbook project by editing one tracked file. Machine-local directories and coordinator environment-variable names previously embedded the Brilliant project name in code and the Windows entrypoint.

## Decision

`config/project.toml` remains the single active, repository-tracked authority. Its `project.project_name` is validated and deterministically derives:

- the uppercase environment namespace;
- the machine-local state root;
- workstation settings, OAuth client and token paths;
- the dedicated Chrome profile; and
- generator run storage.

For the existing default, `BrilliantContentGenerator` maps to `BRILLIANT_CONTENT_GENERATOR` and `%LOCALAPPDATA%\BrilliantContentGenerator`. Token names are derived, but token values remain secret and external to Git.

The synchronizer renders only approved tokens (`PROJECT_NAME`, `PROJECT_ENV_PREFIX`, `STATE_ROOT`, and `REPO_ROOT`) and rejects unknown tokens. The batch entrypoint contains no project-specific environment-variable defaults.

## Consequences

- A renamed project receives an isolated local state directory and environment namespace.
- Two recycled projects can coexist on one PC without sharing credentials, profiles, or run data.
- Existing settings without a project table remain readable during migration, while a settings file explicitly naming another project is rejected.
- This phase does not generate secret token values or migrate existing local files; those concerns remain in later phases.

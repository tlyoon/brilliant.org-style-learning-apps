# Decision 0011: No duplicate project configuration

## Status

Accepted, 27 August 2026.

## Context

After `config/project.toml` became the active authority, legacy example TOMLs and application defaults still duplicated the current project's Drive URL, Gem URL, account, local path name, and token environment names. Editing only the project file could therefore leave hidden old values active.

## Decision

- Remove the three legacy generator example TOMLs.
- Require all project-specific values to come from `config/project.toml` or an explicit higher-precedence override.
- Retain defaults only for generic operational behavior such as timeouts, retry bounds, logging, and safe Git behavior.
- Derive the generator environment override prefix from `project.project_name`.
- Name the rendered ignored configuration `project.local.toml`.

## Consequences

- Recycling a project cannot silently inherit the current Drive root, Gem, account, paths, or token names from Python defaults.
- Documentation and workstation commands refer to one active configuration flow.
- Existing hand-written legacy TOMLs require the bounded migration support planned for a later phase.

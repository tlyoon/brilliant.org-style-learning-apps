# Decision 0012: Guarded project and workstation initialization

## Status

Accepted, 27 August 2026.

## Context

Recycling the package by manually editing several TOML values is error-prone, while automatically overwriting a tracked configuration or a dirty worktree would be unsafe.

## Decision

- Provide `scripts/configure_project.py` for the five core project inputs.
- Make the configurator a dry run by default and show a unified diff.
- Require `--apply`, a clean Git worktree, valid project identity, and valid Drive/Gem hosts before an atomic write.
- Preserve all other project configuration, including token placeholders and derived paths.
- Provide `sync_workstation.py --init-settings-only` to create or verify machine-local settings without fetching, installing, authorizing Drive, or starting Gemini.

## Consequences

- A user can initialize a recycled project without copying an example TOML.
- Configuration changes remain ordinary reviewable Git changes.
- The command does not create credentials, tokens, Drive files, Gems, commits, or pull requests.

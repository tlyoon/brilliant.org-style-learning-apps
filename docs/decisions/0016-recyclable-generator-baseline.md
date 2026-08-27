# Decision 0016: Recyclable generator baseline

## Status

Accepted, 27 August 2026.

## Context

The genericization is complete only if two differently configured textbook projects can materialize from the same code without sharing identifiers, local state, credentials, browser profiles, source roots, Gems, coordinator variables, or output metadata.

## Decision

- Maintain an automated two-project materialization test using the active project template and real configuration loaders.
- Assert separate environment namespaces, local paths, Drive/Gem settings, coordinator token names, and source IDs.
- Scan runtime Python for the current project's Drive ID, Gem ID, and account so they cannot re-enter hidden defaults.
- Document one clean-branch recycling procedure and the remaining intentional constraints.

## Consequences

- Editing the single project authority, provisioning per-project external credentials, and deploying a project-scoped coordinator is sufficient to recycle the package for a similarly structured textbook.
- A future change that reintroduces current-project service identifiers into runtime code fails tests.
- Numeric section folders, one-PDF packages, Gemini UI fragility, and human review remain explicit constraints rather than hidden assumptions.

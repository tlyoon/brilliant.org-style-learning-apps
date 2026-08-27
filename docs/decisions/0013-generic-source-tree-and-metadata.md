# Decision 0013: Generic source tree and section metadata

## Status

Accepted, 27 August 2026.

## Context

Different textbook projects may use different grouping folder names while retaining the same `<chapter>/<chapter.section>/source.pdf` shape. Fixed Section 8.1 output metadata would make that otherwise generic discovery unusable.

## Decision

- Continue recursively traversing every folder beneath the configured Drive root.
- Treat grouping and chapter ancestor names as opaque; require only the immediate PDF parent to be a numeric `chapter.section` identifier.
- Keep the target PDF basename configurable.
- Template package IDs, content directories, titles, boundaries, headings, page labels, and source IDs from the resolved subchapter.
- Add a configurable lowercase `source_id_prefix`, derived from `project_name` by the guarded configurator.

## Consequences

- A tree such as `AnyBook_15_17/15/15.1/source.pdf` works without source-specific code.
- Distributed claims materialize stable repository paths for every discovered section.
- Projects needing a non-numeric section naming scheme still require an explicit future schema decision.

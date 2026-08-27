# Decision 0014: Project-scoped coordinator and generated worker token

## Status

Accepted, 27 August 2026.

## Context

The original Apps Script property name was Brilliant-specific, and ledger job keys did not include project identity. Reusing a coordinator or spreadsheet could therefore mix unrelated projects whose Drive versions happened to produce the same job key.

## Decision

- Use generic Apps Script properties `PROJECT_NAME`, `JOB_SPREADSHEET_ID`, and `WORKER_TOKEN`.
- Require every coordinator request to carry the exact configured project name.
- Store project name in every row and scope lookup keys by project plus job key.
- Provide `initializeCoordinator`, which creates a SHA-256-derived, web-safe random worker token only when one does not already exist.
- Continue storing the matching worker-side value only in the project-derived coordinator environment variable.

## Consequences

- Wrong-project workers fail before reading or changing leases.
- Existing ledgers require the explicit migration implemented in the next phase.
- Token rotation remains an intentional administrator action; redeploying or rerunning initialization does not silently change an existing token.

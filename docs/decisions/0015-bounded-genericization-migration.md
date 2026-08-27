# Decision 0015: Bounded genericization migration

## Status

Accepted, 27 August 2026.

## Context

Existing PCs and the pilot Apps Script deployment may still hold names created before project-derived configuration. Silently accepting arbitrary old forms would weaken project isolation, while rejecting every old form immediately would make the rollout unnecessarily disruptive.

## Decision

Recognize only these exact legacy forms for `BrilliantContentGenerator`:

- `BRILLIANT_GENERATOR_*` environment overrides, when the corresponding new variable is absent;
- `BRILLIANT_COORDINATOR_TOKEN`, when the configured new coordinator variable is absent;
- workstation settings without `[project]` and the old ignored generated-config basename;
- Apps Script property `BRILLIANT_WORKER_TOKEN`, copied only when `WORKER_TOKEN` is absent; and
- the exact previous ledger header, migrated by inserting the configured project name.

Python emits deprecation warnings. Renamed projects receive none of these fallbacks. Compatibility is scheduled for removal after 31 December 2026.

## Consequences

- Existing authorized PCs can update without moving secrets immediately.
- New projects cannot inherit the default project's variables, token, or ledger rows.
- Malformed or unrecognized legacy configuration still fails closed.

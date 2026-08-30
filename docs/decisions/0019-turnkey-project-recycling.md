# Decision 0019: Turnkey project recycling and restored single authority

## Status

Accepted 30 August 2026 by explicit project-owner request.

## Context

The recyclable-generator baseline designated `config/project.toml` as the sole tracked project authority. A later transitional wrapper introduced `config/configure_project.toml`, duplicating current-project service identifiers and creating contradictory workstation and generator instructions. The guarded configurator also changed the Gem conversation URL without clearing the previous Gem editor URL and preserved enabled publishing and auto-merge settings. A syntactically valid recycled configuration could therefore target the old Gem editor or inherit an unsafe repository handoff policy.

## Decision

- Restore `config/project.toml` as the only tracked project configuration authority.
- Remove the transitional configuration file and configured-workstation wrapper; `sync-workstation.cmd` invokes `scripts.sync_workstation` directly.
- Keep bounded legacy environment compatibility only in the single authority's optional `[compatibility]` table.
- Make guarded project initialization replace or clear both the Gem conversation and editor URLs, clear the legacy environment prefix, and reset `git_publish` and `git_auto_merge` to `false`.
- Continue deriving project slug, environment namespace, local state, OAuth paths, Chrome profile, coordinator token name, run directories, and source ID prefix from `project_name`.
- Require the two-project isolation test to distinguish both Gem URLs and to verify safe publishing defaults.
- Treat checked-in learning packages as current-project data and keep the Chapter 8 comparison-release builder under `project_extensions/brilliant_content_generator/`, outside reusable runtime defaults. The generic learner and `scripts/build_public_release.py` continue to require an explicitly selected package.

## Consequences

- A similarly structured textbook project can be initialized through one guarded configuration command and one reviewed TOML authority without inheriting another project's Gem editor or automatic Git handoff.
- A project may deliberately enable publishing or auto-merge only in a later reviewed configuration change after its controlled first run succeeds.
- Existing project-specific content remains available for historical review but is not selected automatically by the generator, learner runtime, workstation sync, or generic public-release builder.
- Numeric `chapter.section` source folders, one controlled PDF per package, schema 1.1 activity/language contracts, external credentials, and qualified human-review gates remain intentional application constraints.

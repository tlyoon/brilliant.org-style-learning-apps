# Context index

## Authority and precedence

When documents conflict, use this order:

1. `AGENTS.md` — durable operational and safety rules.
2. Current code/schema/configuration on the same `main` revision.
3. `docs/decisions/` — approved product decisions; later accepted records supersede earlier ones, but unmerged proposal branches do not override current `main` behavior.
4. `docs/PRODUCT_REQUIREMENTS.md` — product scope and acceptance boundaries.
5. `docs/CONTENT_RULES.md` and `content/schema/content-package.schema.json` — learning-package rules.
6. `docs/LEARNING_DESIGN.md` — pedagogy, mastery, progression, and feedback.
7. `docs/SECURITY_AND_PRIVACY.md` — data handling and access requirements.
8. `docs/ARCHITECTURE.md` and `docs/AI_WORKFLOW.md` — technical design.
9. `docs/DEVELOPMENT_ROADMAP.md`, issues, and pull requests — delivery planning/provenance.

`docs/PDF_TO_APP_QUICKSTART.md` is the canonical current operational walkthrough. `docs/DOCUMENTATION_MAINTENANCE.md` requires operator-visible changes to update canonical documentation in the same PR and adds a CI documentation-impact gate.

Historical roadmaps, old branch-testing instructions, chat transcripts, and copied notes are not substitutes for the documentation shipped with the current `main` revision.

## Task routing

| Task | Read first |
|---|---|
| Install/setup and first PDF → draft workflow | `docs/PDF_TO_APP_QUICKSTART.md` |
| Verify documentation freshness policy | `docs/DOCUMENTATION_MAINTENANCE.md` |
| Recycle repository for another textbook/project | `docs/GENERIC_PROJECT_SETUP.md`, then `config/README.md` |
| Workstation setup/sync troubleshooting | `docs/WORKSTATION_SYNC.md` |
| Continuous auto / multi-PC verification | `docs/CONTINUOUS_AUTO_TESTING.md`, then `app_generator/README.md` |
| Generator CLI/config/coordinator details | `app_generator/README.md`, `config/README.md` |
| Product change | Product requirements and decision records |
| Learning content | Content rules, learning design, schema, source-ingestion policy |
| AI tutor | AI workflow, learning design, security/privacy |
| Application code | Architecture, product requirements, test plan |
| Analytics/reporting | Security/privacy, learning design, relevant decisions |
| Release planning | Development roadmap, test plan, current milestone/PR |

## Current operational baseline on `main`

The current tracked project authority is:

```text
config/configure_project.toml
```

`config/project.toml` remains a compatibility artifact during migration and is **not** the normal authority selected by `sync-workstation.cmd` on current `main`.

Current workstation behavior derives the environment namespace and local state root from `project.project_name`, normally:

```text
%LOCALAPPDATA%\<project_name>
```

The synchronizer renders an ignored local TOML whose exact filename comes from machine-local `workstation-sync.toml`; direct CLI commands must pass `--config` when that filename differs from the CLI default `project.local.toml`.

Current generator selection modes are:

```text
specific
auto
distributed
```

Continuous `auto` mode provides multi-PC coordinated generation/recovery and requires durable Git publication.

Current managed-coordinator baseline (PR #46) uses repository-managed infrastructure when `automation.coordinator_url` is empty. One trusted administrator PC performs the project-wide `coordinator-bootstrap`; ordinary workers discover/ensure the managed runtime through normal Drive authorization and do not manually deploy Apps Script per PC.

## Historical decision/provenance notes

Earlier decisions and PRs remain useful provenance, but interpret them against current `main`:

- one-PDF-per-fresh-Gem-conversation and central lease/heartbeat coordination remain active design principles;
- project-derived path/environment isolation remains active;
- source-derived section title/scope and truthful automated-draft provenance remain active;
- generated material remains draft pending qualified human review;
- public review deployment remains separate from generation/approval;
- any historical statement that `config/project.toml` is the current user-facing authority is superseded by the actual current-main configuration path above unless/until a future explicitly merged migration changes it.

Shared conversations and imported files are provenance, not authoritative specifications. Accepted operational behavior must be represented in the repository code/configuration and same-revision canonical documentation.

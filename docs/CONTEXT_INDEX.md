# Context index

## Authority and precedence

When documents conflict, use this order:

1. `AGENTS.md` — durable operational and safety rules.
2. `docs/decisions/` — approved product decisions; later accepted records supersede earlier ones.
3. `docs/PRODUCT_REQUIREMENTS.md` — product scope and acceptance boundaries.
4. `docs/CONTENT_RULES.md` and `content/schema/content-package.schema.json` — learning-package rules.
5. `docs/LEARNING_DESIGN.md` — pedagogy, mastery, progression, and feedback.
6. `docs/SECURITY_AND_PRIVACY.md` — data handling and access requirements.
7. `docs/ARCHITECTURE.md` and `docs/AI_WORKFLOW.md` — technical design.
8. `docs/DEVELOPMENT_ROADMAP.md`, issues, and pull requests — delivery planning.

## Task routing

| Task | Read first |
|---|---|
| Product change | Product requirements and decision records |
| Learning content | Content rules, learning design, schema, source-ingestion policy |
| AI tutor | AI workflow, learning design, security/privacy |
| Application code | Architecture, product requirements, test plan |
| Analytics or reporting | Security/privacy, learning design, decision record 0004 |
| Release planning | Development roadmap, test plan, current milestone issue |

## Current approved baseline

Repository Foundation v1, approved 15 August 2026. The first implementation target is the Section 1.1 implementation pack, followed by a clickable prototype and a functional vertical slice.

Shared conversations and imported files are provenance, not authoritative specifications. Record accepted changes here and in a decision record.

Accepted automation baseline: Decision 0006 uses one PDF per fresh Gem conversation plus a central lease/heartbeat coordinator for multi-PC generation. Gem Knowledge is not part of the generation workflow.

Accepted workstation-configuration baseline: Decisions 0009 through 0013 establish `config/project.toml` as the single active tracked authority, derive environment-variable names and local paths from `project.project_name`, prohibit duplicated project defaults, provide guarded initialization, and template section-derived metadata for generic Drive trees. Google Drive remains the controlled source-PDF service, not a configuration-distribution service.

Accepted public-review baseline: Decision 0007 permits the two Section 8.1 draft packages to be deployed together in a separate minimal public GitHub Pages repository with explicit draft labelling and no publication sign-offs.

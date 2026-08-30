# Project configuration boundary

`project.toml` is the sole tracked authority for non-secret values that can change when this repository is reused for another subject, textbook, source tree, Gemini Gem, or deployment policy.

The `config/` directory also owns the project-specific Gemini Gem text:

- `project.toml` → Gem **Name** through `gemini.gem_name`;
- `gem_description.txt` → Gem **Description**;
- `gem_instructions.md` → Gem **Instructions**.

Before every live generation, the generator opens the configured Gem editor under the configured Google account and compares all three editable fields with these authoritative values. It changes only fields that differ, saves once when any value changed, reopens the editor, and verifies all three persisted. If all three already match, no Save/Update is issued.

## Project-dependent values

Review these when creating a new project:

- `project.project_name`
- `placeholders.sourcepath` — Google Drive source root
- `placeholders.gemini-gem` — project Gem URL
- `placeholders.loginname` — expected Google account
- `placeholders.pdf_subchapter_path` — controlled default source selector
- `placeholders.target_filename` and `target_file` — source-tree naming/pattern
- `gemini.gem_edit_url` and `gem_name`
- `gem_description.txt` and `gem_instructions.md`
- coordinator URL/policy when distributed execution is used
- run metadata/provenance wording such as edition, reviewer and rights note
- Git publishing/PR/merge policy
- model preference policy when a project needs a different model-selection rule

## Values automatically materialized by `sync-workstation.cmd`

Do not replace these tokens with machine-specific or copied project values:

- `${PROJECT_SLUG}` — lowercase kebab-case project identifier derived from `project_name`
- `${PROJECT_ENV_PREFIX}` — uppercase environment namespace derived from `project_name`
- `${REPO_ROOT}` — checkout path on the current PC
- `${STATE_ROOT}` — project-scoped machine-local state root

The derived values are then reused for the coordinator-token environment variable, OAuth client/token paths, Chrome profile, workstation settings, and generator run state. This prevents paths and environment namespaces from leaking between projects or PCs.

## What should stay generic in code/schema

The following are application contracts rather than textbook identity and therefore should not be copied into per-textbook configuration merely to remove constants:

- schema version and JSON field names;
- supported interaction modes;
- deterministic validation and provenance rules;
- the current 18-activity / MCQ-interactive / difficulty distribution contract;
- the current English/Malay/Simplified-Chinese localization contract;
- calculator-free conceptual-activity policy;
- security boundaries that keep credentials, source PDFs and run data outside Git.

If the product itself later changes one of these contracts, make a versioned schema/design change rather than silently changing a textbook project file.

## Compatibility values

The optional `[compatibility]` table holds only bounded migration names for the existing default project. `scripts/configure_project.py` clears those names when recycling the repository. Do not create another tracked project TOML or add project-dependent defaults to Python modules.

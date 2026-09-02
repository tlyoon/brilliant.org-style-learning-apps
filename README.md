# Interactive Learning App

A reusable foundation for interactive, concept-first learning packages generated from instructor-provided source material.

## Pilot

The first pilot uses undergraduate physics source material, but the generator/runtime are intended to be reusable across subjects and textbook projects. Under the current learning-app contract, each complete subchapter contains 18 calculator-free activities:

- 9 multiple-choice questions and 9 interactive activities;
- 3 easy, 3 moderate, and 3 challenging activities of each type;
- formative hints, retries, and prerequisite routing;
- separate evidence for independent and assisted success.

The repository contains specifications, schemas, validation scripts, tests, project-management templates, and a dependency-free learner-app scaffold. It intentionally does not contain copyrighted source PDFs, student records, credentials, browser state, or production secrets.

## Start here

For the **current installation and operating workflow** from one controlled subchapter PDF to a generated draft, managed multi-PC generation, review bundle, and optional deployment, use:

**`docs/PDF_TO_APP_QUICKSTART.md`**

Operational documentation is versioned with the code. Read the docs from the same `main` revision you are running. `docs/DOCUMENTATION_MAINTENANCE.md` defines the same-PR documentation-update rule and CI documentation-impact gate so operator-visible changes do not silently reach `main` with obsolete instructions.

Specialist references:

1. `AGENTS.md` — durable operational/safety rules;
2. `docs/CONTEXT_INDEX.md` — authoritative-document order;
3. `docs/WORKSTATION_SYNC.md` — workstation synchronization and machine-local state;
4. `docs/GENERIC_PROJECT_SETUP.md` — recycling the package for another project;
5. `docs/CONTINUOUS_AUTO_TESTING.md` — current continuous-auto/multi-PC verification;
6. `config/README.md` — configuration reference;
7. `app_generator/README.md` — generator technical reference.

## Workstation baseline

A normal Windows workstation starts from current `main`:

```powershell
git switch main
git fetch origin
git status -sb
```

If behind:

```powershell
git pull --ff-only origin main
```

Then:

```powershell
.\sync-workstation.cmd
```

The synchronizer prints the exact ignored local config filename generated for that PC. Direct `app_generator` commands must pass `--config <printed-file>` when it differs from the CLI default `project.local.toml`.

The project name determines the default state root:

```text
%LOCALAPPDATA%\<project_name>
```

OAuth client/token files, Chrome profile, run state, and other machine-local material stay there rather than in Git.

## Run the learner scaffold

Python 3.12, Node.js for JavaScript checks, and a modern browser are required.

1. Run `python scripts/serve.py` from the repository root.
2. Open `http://127.0.0.1:8000/app/`.
3. Supply the package URL through the host page's `data-package-url` or call `loadPackage(packageUrl)` from an embedding/release page.
4. Stop the server with Ctrl+C.

The learner scaffold is project-neutral. Learner-facing strings follow the current English (`en`), Malay (`ms`), and Simplified Chinese (`zh`) contract. Draft examples may contain fewer activities; complete review/publishable packages must satisfy the required activity distribution.

## Development checks

Run before review:

```text
python scripts/lint.py
python -m json.tool content/schema/content-package.schema.json
python -m json.tool content/schema/source-manifest.schema.json
python scripts/validate_content.py
python -m unittest discover -s tests -v
python scripts/check_documentation_impact.py
node --check app/app.js
node tests/test_app_loading.js
node tests/test_app_rendering.js
node tests/test_interaction_rendering.js
```

Node.js is development-time only; the learner application has no runtime package dependency/build step.

## Public review-prototype bundle

The generic builder requires an explicit package:

```text
python scripts/build_public_release.py content/<chapter>/<section>/package.json <empty-output-directory>
```

It creates a minimal static bundle containing the entry page, learner assets, selected package, and `.nojekyll`. It excludes repository history, tests, source PDFs, review records, source manifests, credentials, and development scripts.

## Automated draft generator

`app_generator/` contains the Python 3.12/Google Drive/Selenium workflow. Current selection modes are `specific`, `auto`, and `distributed`.

Continuous `auto` mode coordinates multiple PCs, recovers interrupted jobs from durable checkpoints, requires durable Git handoff, and uses repository-managed coordinator infrastructure when `automation.coordinator_url` is empty. One trusted administrator PC performs the project-wide `coordinator-bootstrap`; ordinary worker PCs do not repeat it.

Generated content remains draft until qualified human review.

## Configuration authority

The tracked project authority is:

```text
config/configure_project.toml
```

`sync-workstation.cmd` derives project slug/environment namespace, checkout path, state root, OAuth/token locations, Chrome profile, coordinator identity, and run-state paths per PC.

Credentials, source PDFs, browser profiles, tokens, and run data remain outside Git.

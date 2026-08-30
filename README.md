# Interactive Learning App

A reusable foundation for interactive, concept-first learning packages generated from instructor-provided source material.

## Pilot

The first pilot uses undergraduate physics source material, but the generator/runtime are intended to be reusable across subjects and textbook projects. Under the current learning-app contract, each complete subchapter contains 18 calculator-free activities:

- 9 multiple-choice questions and 9 interactive activities
- 3 easy, 3 moderate, and 3 challenging activities of each type
- formative hints, retries, and prerequisite routing
- separate evidence for independent and assisted success

The repository contains specifications, schemas, validation scripts, tests, project-management templates, and a dependency-free learner-app scaffold. It intentionally does not contain copyrighted source PDFs, student records, credentials, or a production database.

## Start here

For the complete normal workflow from one controlled subchapter PDF to a generated draft, reviewed static bundle, and optional GitHub Pages deployment, use **`docs/PDF_TO_APP_QUICKSTART.md`**.

Then use the specialist references only when needed:

1. Read `AGENTS.md` for durable operational/safety rules.
2. Read `docs/CONTEXT_INDEX.md` for the authoritative-document order.
3. Read `config/README.md` for the project/configuration boundary.
4. Read `docs/GENERIC_PROJECT_SETUP.md` when recycling the repository for another textbook/project.
5. Read `docs/WORKSTATION_SYNC.md` for workstation internals and troubleshooting.

For a quick repository health check, run `python scripts/validate_content.py` and `python -m unittest discover -s tests -v`.

## Run the learner scaffold

Python 3.12, Node.js for JavaScript checks, and a modern browser are required. Install the pinned validation dependency with `python -m pip install -r requirements-dev.txt`.

1. Run `python scripts/serve.py` from the repository root.
2. Open `http://127.0.0.1:8000/app/`.
3. Supply the package URL through the host page's `data-package-url` or call `loadPackage(packageUrl)` from an embedding/release page.
4. Stop the server with Ctrl+C.

The learner scaffold is project-neutral and no longer silently selects Section 1.1. Generated/release pages select the package explicitly. Learner-facing strings currently follow the application contract of English (`en`), Malay (`ms`), and Simplified Chinese (`zh`). Draft examples may contain fewer activities; complete review/publishable packages must contain the required 18-activity distribution.

Content package schema 1.1 distinguishes MCQs from genuine interactions. MCQs use `answerKey`; interactive activities use `interactionMode`, mode-specific `interaction` response data, and `diagnosticRules` that connect recognizable incorrect responses to declared misconceptions. The learner scaffold renders classification, matching, ordering, and multiple-selection modes with native keyboard-operable controls.

## Development checks

Run all local checks before review:

```text
python scripts/lint.py
python -m json.tool content/schema/content-package.schema.json
python -m json.tool content/schema/source-manifest.schema.json
python -m json.tool content/templates/subchapter.template.json
python -m json.tool content/source-manifests/source-manifest.example.json
python scripts/validate_content.py
node --check app/app.js
node --check tests/test_app_loading.js
node --check tests/test_app_rendering.js
node --check tests/test_interaction_rendering.js
node tests/test_app_loading.js
node tests/test_app_rendering.js
node tests/test_interaction_rendering.js
python -m unittest discover -s tests -v
```

Node.js is used only for development-time syntax and regression checks. The application has no runtime package dependencies or build step.

## Public review-prototype bundle

The generic builder requires an explicit package instead of embedding a textbook section:

```text
python scripts/build_public_release.py content/<chapter>/<section>/package.json <empty-output-directory>
```

It creates a small static bundle containing only the root entry page, learner-app assets, the selected package (normalized to `content/package.json`), and `.nojekyll`. It excludes repository history, tests, specifications, review records, source manifests, and development scripts.

`scripts/build_section_8_1_public_release.py` remains an explicitly named historical/specialized comparison builder for the existing Chapter 8 review site. It is not used by the generic generator or learner runtime and must not be treated as a project default.

Implementation work should use short-lived branches and pull requests. `main` remains the stable baseline.

## Automated draft generator

`app_generator/` contains an isolated Python 3.12/Google Drive/Selenium workflow for generating one repository-compatible draft per controlled PDF. Each job attaches its PDF to a fresh Gemini Gem conversation; Gem Knowledge is not modified. Distributed workers can use a central lease/heartbeat coordinator, validate and repair the generated package, and hand work to Git according to the configured publishing policy. Generated content remains draft until qualified review.

The normal tracked project-specific authority is `config/configure_project.toml`. `sync-workstation.cmd` derives project slug/environment namespace, checkout path, state root, OAuth/token locations, Chrome profile, coordinator token environment name, and run-state paths to produce machine-local `project.local.toml`. See `config/README.md`, `docs/WORKSTATION_SYNC.md`, and `docs/GENERIC_PROJECT_SETUP.md`. Credentials, source PDFs, browser profiles, tokens, and run data remain outside Git.

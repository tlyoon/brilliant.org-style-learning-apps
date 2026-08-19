# Interactive Learning App

A reusable foundation for interactive, concept-first learning packages generated from instructor-provided source material.

## Pilot

The first pilot covers six subchapters of an undergraduate physics chapter. Each publishable subchapter contains 18 calculator-free activities:

- 9 multiple-choice questions and 9 interactive activities
- 3 easy, 3 moderate, and 3 challenging activities of each type
- formative hints, retries, and prerequisite routing
- separate evidence for independent and assisted success

The repository contains specifications, schemas, validation scripts, tests, project-management templates, and a dependency-free learner-app scaffold. It intentionally does not contain copyrighted source PDFs, student records, credentials, or a production database.

## Start here

1. Read `AGENTS.md`.
2. Read `docs/CONTEXT_INDEX.md` for the authoritative-document order.
3. Run `python scripts/validate_content.py`.
4. Run `python -m unittest discover -s tests -v`.

## Run the learner scaffold

Python 3.12, Node.js for JavaScript checks, and a modern browser are required. Install the pinned validation dependency with `python -m pip install -r requirements-dev.txt`.

1. Run `python scripts/serve.py` from the repository root.
2. Open `http://127.0.0.1:8000/app/`.
3. Stop the server with Ctrl+C.

The scaffold reads `content/examples/conceptual-forces.json`. To try another subchapter, create a schema-compatible draft package and change `DEFAULT_PACKAGE` in `app/app.js`. Learner-facing strings must include English (`en`), Malay (`ms`), and Simplified Chinese (`zh`). Draft examples may contain fewer activities; publishable packages must contain the required 18-activity distribution.

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

Implementation work should use short-lived branches and pull requests. `main` remains the stable baseline.


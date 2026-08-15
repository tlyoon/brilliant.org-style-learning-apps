# Brilliant-Style Learning App

A reusable foundation for interactive, concept-first learning packages generated from instructor-provided source material.

## Pilot

The first pilot covers six subchapters of an undergraduate physics chapter. Each publishable subchapter contains 18 calculator-free activities:

- 9 multiple-choice questions and 9 interactive activities
- 3 easy, 3 moderate, and 3 challenging activities of each type
- formative hints, retries, and prerequisite routing
- separate evidence for independent and assisted success

The repository contains specifications, schemas, validation scripts, tests, and project-management templates. It intentionally does not contain copyrighted source PDFs, student records, credentials, or a production database.

## Start here

1. Read `AGENTS.md`.
2. Read `docs/CONTEXT_INDEX.md` for the authoritative-document order.
3. Run `python scripts/validate_content.py`.
4. Run `python -m unittest discover -s tests -v`.

Implementation work should use short-lived branches and pull requests. `main` remains the stable baseline.


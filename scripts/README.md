# Validation scripts

`validate_content.py` validates packages and referenced source manifests against their authoritative JSON Schemas using the pinned development dependency, then checks repository content packages for required fields, multilingual completeness, exact publishable activity distribution, calculator-free flags, numerical-answer prohibition, and suspicious prompt wording.

`lint.py` checks repository text files for UTF-8 encoding, tabs, trailing whitespace, valid JSON, and valid Python syntax. CI also uses `node --check` for the browser JavaScript.

`build_public_release.py` is the generic explicit-package review-bundle builder. Current-project-only historical/review builders live under `project_extensions/`, outside the reusable scripts namespace.


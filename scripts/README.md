# Validation scripts

`validate_content.py` validates packages and referenced source manifests against their authoritative JSON Schemas using the pinned development dependency, then checks repository content packages for required fields, multilingual completeness, exact publishable activity distribution, calculator-free flags, numerical-answer prohibition, and suspicious prompt wording.

`lint.py` checks repository text files for UTF-8 encoding, tabs, trailing whitespace, valid JSON, and valid Python syntax. CI also uses `node --check` for the browser JavaScript.

`build_section_8_1_public_release.py` builds the minimal Chapter 8 static review site. It retains immutable and current Section 8.1 routes, adds the current Section 8.3 draft, and copies no manifests, review records, source files, run diagnostics, or development material.


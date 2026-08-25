# Validation scripts

`validate_content.py` validates packages and referenced source manifests against their authoritative JSON Schemas using the pinned development dependency, then checks repository content packages for required fields, multilingual completeness, exact publishable activity distribution, calculator-free flags, numerical-answer prohibition, and suspicious prompt wording.

`lint.py` checks repository text files for UTF-8 encoding, tabs, trailing whitespace, valid JSON, and valid Python syntax. CI also uses `node --check` for the browser JavaScript.

`build_section_8_1_public_release.py` builds the minimal dual-version Section 8.1 static review site. Version 1 is read from its immutable introducing Git commit, Version 2 is read from the current validated package, and no manifests, review records, source files, run diagnostics, or development material are copied.


# Validation scripts

`validate_content.py` uses only the Python standard library. It checks repository content packages for required fields, multilingual completeness, exact publishable activity distribution, calculator-free flags, numerical-answer prohibition, and suspicious prompt wording.

`lint.py` checks repository text files for UTF-8 encoding, tabs, trailing whitespace, valid JSON, and valid Python syntax. CI also uses `node --check` for the browser JavaScript.


## What changed

<!-- Describe the smallest coherent change. -->

## Why

<!-- Link the issue or approved decision. -->

## Validation

- [ ] `python scripts/validate_content.py`
- [ ] `python -m unittest discover -s tests -v`
- [ ] `python scripts/check_documentation_impact.py`
- [ ] No source PDFs, student data, credentials, raw transcripts, or generated temporary files
- [ ] Content is original and calculator-free

## Documentation impact

- [ ] I reviewed the canonical operational docs against this change.
- [ ] If CLI/config/workstation/OAuth/coordinator/auto-mode behavior changed, I updated the relevant canonical docs in this same PR.
- [ ] If no documentation wording changed, the PR description explains why the current instructions remain correct.

Canonical operational docs are listed in `docs/DOCUMENTATION_MAINTENANCE.md`.

## Review evidence

<!-- Add screenshots, test output, or sample validation results when relevant. -->

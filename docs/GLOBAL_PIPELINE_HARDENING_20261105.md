# Global generator hardening campaign — 5 November 2026

**Project:** `tlyoon/brilliant.org-style-learning-apps` (Bosla), draft [PR #223](https://github.com/tlyoon/brilliant.org-style-learning-apps/pull/223).

**Scope:** Three reusable, domain-independent source-free development priorities after the already closed two-round physics generalization evaluation (Decision 0029). These changes do **not** reopen that campaign, repair or regenerate any of its PDFs, contact an AI provider, run protected source material, claim independent academic success, authorize Git merge or publish an app.

## Priority A — Explain activity-repair failures without loosening the contract

**Code:** `app_generator/generation/repair_diagnostics.py`, `app_generator/generation/protocol.py`.

- Stable activity fields, misconception identities, prerequisites and internal item/target/option IDs now raise typed, bounded categories. Incomplete interaction solutions receive a separate category; schema and plan failures remain distinct. Previously all reasons were collapsed into one generic final error.
- The existing **three attempts maximum** and invalid-stage discard are unchanged. On each rejected attempt a run-scoped `diagnostics/<stage>-repair-attempts.json` stores only attempt ordinal, stable activity ID, category and field; it never copies raw provider errors, source text, AI responses, prompts or credentials.
- On exhaustion the existing `ResponseContractError` remains fail-closed while reporting the **enumerated categories**. A discarded draft is never silently installed. Negative fixtures test ordering solution omissions, stable identifier changes, schema rejection and error-text privacy across multiple attempts.

**Limit:** These diagnostics identify a family of failure, not the physics truth or actual correctness of a model's proposed repair. The old traveling-waves attempt is **not replayed** or re-certified.

## Priority B — Require meaningful browser/learner coverage

**Code:** `app_generator/validation/learner_coverage_gate.py`, `scripts/audit_browser_visual.py`, `scripts/audit_learner_coverage.py`.

- A visual browser audit with **zero visual activities** now fails before opening Chrome. Counts are checked against expected EN/MS/ZH and 390/1280 visual coverage; missing keyboard exercises or mandatory screenshots fail the visual-audit scope.
- The existing DOM smoke label remains a **smoke-only** observation when screenshots were not requested. New results carry an explicit `scopeCoverage` status; they never imply scientific visual semantics, accessibility or full learner acceptance.
- A separate full-roster, source-free coverage gate requires **per-activity, per-locale, per-viewport** recorded interaction, rendering, responsive and keyboard checks. Aggregate `checks: 0` or `browser_dom_smoke_pass` alone cannot pass. Even complete self-reported metadata remains `COMPLETE_COVERAGE_METADATA_UNVERIFIED` until independent browser receipts are checked.

**Offline example (no browser or provider call):**

```text
python scripts/audit_learner_coverage.py --package <EXACT_CANDIDATE_JSON> --receipt <PRIVATE_BROWSER_RECEIPT_JSON>
```

The receipt must carry the exact package's SHA-256 and `publicationAuthorized=false`. The CLI returns nonzero for incomplete, malformed or unbound evidence. This is a **general codebase acceptance mechanism**, not a claim that the two old draft packages now satisfy new keyboard/mobile criteria.

## Priority C — Make independent academic evidence gaps explicit

**Code:** `app_generator/validation/academic_coverage_gate.py`, `scripts/audit_academic_coverage.py`.

- Consume **actual candidate JSON bytes**, compute its SHA-256, and verify a QA matrix's package digest, original-source digest, activity count, exact activity IDs and canonical per-activity SHA-256 hashes.
- Check all five academic gates (`source_fidelity`, `answer_correctness`, `physics_consistency`, `visual_semantics`, `multilingual_meaning`) and reject missing gates, inconsistent aggregate statuses, unbound claimed original passages and release-enabled evidence.
- Report counts and **fixed next-action categories** for missing original passages/rights, independent answer proofs, domain science, diagram meanings and EN/MS/ZH equivalence.
- A matrix is **not itself independently verified academic evidence**. Even if its rows all claim PASS, this source-free inventory returns `academicQA=REVIEW_REQUIRED` and `formalAcademicPassCount=0`; a confirmed deterministic FAIL remains FAIL. No user review is required merely to run the inventory, but actual source-bound independent proof must still be acquired through separately authorized verification.

**Offline example (no original PDF or AI request):**

```text
python scripts/audit_academic_coverage.py --package <EXACT_CANDIDATE_JSON> --matrix <PRIVATE_QA_MATRIX_JSON> --source-sha256 <ORIGINAL_SOURCE_SHA256>
```

## Regression and completion boundary

- New negative fixture suites: `tests/test_repair_failure_observability.py`, `tests/test_learner_coverage_gate.py`, `tests/test_academic_coverage_gate.py`. These are registered in the permanent recurrence contract as `BSA-20261105-112`, `-113` and `-114`.
- The development outcome is **GLOBAL CODEBASE DIAGNOSTICS AND FAIL-CLOSED QA GATES IMPLEMENTED**, subject to exact-HEAD CI. This **does not** mean real current Gemini rotation through the new shared gateway was observed, source-verified science/translation PASS was attained, or the closed C3 campaign was successful.
- Next legitimate work: independently verify the technical coverage observations from a new authorized cross-topic candidate set, then establish source-backed scientific and multilingual proof receipts; report a finite disposition under an explicit **new** development/evaluation contract rather than repeatedly repairing a selected PDF.

**Release boundary:** No PDF regeneration, provider invocation, auto-merge or public deployment is authorized by this campaign.

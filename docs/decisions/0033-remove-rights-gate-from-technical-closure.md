# Decision 0033 — Owner removes edition, rights-holder and rights gate from BOSLA technical completion

**Status:** Explicit owner-directed binding amendment, 11 November 2026. Supersedes Decision 0032 only where it treated source/figure rights, identification of textbook edition or identification of rights holder as a *technical project acceptance precondition*. Historical results remain unchanged.

## Decision

The following **must not be prerequisites** to declaring BOSLA's software engineering work technically complete:

- Identifying the source textbook's edition.
- Identifying the source textbook's legal rights holder.
- Passing a separate `sourceAndFigureRights` clearance/approval gate.

There must be **no disguised replacement gate** asking the same questions before technical closure. The Chapter 9 closure charter has been versioned to `FINAL_ACCEPTANCE_NO_REPEAT_V2` and its nine-gate registry **omits** `sourceAndFigureRights`; `policy.excludedTechnicalAcceptanceGates` makes that choice explicit and machine-validated. CI tests fail if the excluded gate is reinserted or this exclusion is silently removed. Rights-related language in earlier Decision 0032 and the historic 11 November rights-clearance handoff is superseded *for technical acceptance*. Those documents remain available for provenance.

## What remains required

Technical and learning-quality acceptance still require independently evidenced physics, correct answers, EN/MS/ZH equivalence, useful visuals and interactions, learner viewport/accessibility, adaptive/privacy/operations, source identity/location as applicable, and exact-head CI. Terminal original Chapter 9 campaigns and finite no-repeat limits remain terminal; no previously failed source or browser receipt becomes PASS merely because the rights gate was removed. Engineering completion, acceptance of actual learning content, and public distribution remain distinct.

**Technical completion ≠ legal permission.** This decision does not assert ownership of any textbook or figure, grant third-party redistribution rights, authorize external transmission of protected PDF/passages/figures, alter service data-handling restrictions, or authorize Git auto-merge, publication or deployment. The existing explicit no-unauthorized-transfer and public-release controls remain protective *operation policies*, **not** technical acceptance gates. A fully original, independently evidenced learning activity may be assessed without requiring the identity of the earlier source textbook's publisher/edition. If real protected third-party assets are proposed for an external model or public release, handle their use lawfully; never record the absence of an internal gate as a license.

## Implementation and permanence

1. `docs/acceptance_closure_chapter9.json`: V2 contract; nine gates; three excluded administrative conditions; no rights-based terminal label. Source SHA and package Git-object identity unchanged.
2. `app_generator/validation/final_acceptance_closure.py`: requires V2 exclusion permanently and refuses reintroduction of the tenth gate; academic review's historic terminal-campaign stop uses a neutral code, not a rights-gate status.
3. `tests/test_final_acceptance_closure.py`: adversarial tests reproduce the prior rights-gate requirement, assert all three omissions, reject silent reintroduction, and retain the protection against unauthorized campaigns, source transmission and publication.
4. `AGENTS.md`, `docs/CONTEXT_INDEX.md` and the latest continuation checkpoint: later sessions read this decision before planning completion. Do **not** propose acquiring edition/rightsholder or rights-gate PASS as a prerequisite for BOSLA *technical closure*.

The only remaining technical gates are the nine machine-listed in the V2 register; their statuses must still be based on evidence. This is a deliberate, permanent project-governance change; it does not manufacture missing independent academic or learner-pilot evidence.

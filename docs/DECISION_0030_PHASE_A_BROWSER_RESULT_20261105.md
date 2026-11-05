# Decision 0030 — Phase A finite browser acceptance result (5 November 2026)

**Outcome: `PASS_LOCAL_BROWSER_BASELINE_WITH_LIMITED_SCOPE`.** This is a one-shot existing-package browser result, **not** C3 generalization, C4 science, independent screenshot interpretation, visual-interactive pedagogy approval, merge, or release.

## Precommitted intent and immutable identity

- Protocol: [Decision 0030](decisions/0030-final-bounded-acceptance-and-release-closure.md), committed and pushed **before** the browser run at `980194f8057e1de61740c07611aeb1105975d10a`.
- Inspected software baseline: consolidated draft PR #223, commit `767dfb382c8af10d9806b3bd0744b91d36dae363`. Decision 0030 changed documentation only before the run.
- Existing tracked candidate: `content/chapter-1/section-1-1/package.json`; SHA-256 `c5460f8417e7d451205a6fd911f096b46cd5e665c01b9ccda58172b0ba8ffb96`. Exact bytes verified before and after the run.
- Browser harness `scripts/audit_full_learner_browser.py` SHA-256 `00158b354cc33530ee73d0faf24071c4829dae7131503696d5945630d6a646a8`.
- Learner player `app/app.js` SHA-256 `4f797ab5ddc09f890804d796374a180f6cb1986a5b8ebcdd07aadc78b5ae9993`.
- Package roster: **18 activities**, 9 MCQ, 9 interactive; **0 `visualSpec` activities**. This is an existing codebase baseline, not a new held-out PDF, not the two previously audited round-two private candidates and not a third Decision 0029 campaign.

## Executed private one-shot acceptance

- **One** isolated local headless-Chrome audit on Yoga 6, staging trusted player assets and exact candidate bytes on localhost. No model/provider call, PDF acquisition/generation, production deployment, real student record, merge, or external browser interaction.
- **108/108** expected observations executed: 18 activities × 3 locales (EN, MS, ZH) × 2 viewport widths (390, 1280).
- **108/108** row checks showed successful localized prompt rendering, no detected document horizontal overflow, keyboard-operable hint and response, plus answer feedback. **0 failed checks, 0 missing checks.**
- **108/108** browser screenshot PNGs captured in a private location, not in Git.
- A separate **read-only offline integrity verification** checked each unique activity/locale/viewport triple, every positive field in the per-check receipt, actual screenshot existence, PNG signature/geometry and exact SHA-256 matching, zero duplicates, and matching package/harness/player hashes. **All 108 screenshot hashes verified.**
- Private result receipt SHA-256 `0bb836fa30873815ef255ed0b4ddf2b6937c09d495893abdf670617570886e75`; summary SHA-256 `531ca5001778ef1cb6b05f1cc28a919264e807862a692d9a1474b310a3b8e396`; one-shot start record SHA-256 `3c05cff0ee18759f4e9c09e0eb06e08da5b3a3030d0807016234be7282b97875`. These are hashes of **private artifacts**, not claims of third-party browser authenticity.
- Returned status `COMPLETE_BROWSER_COVERAGE_UNDER_INDEPENDENT_REVIEW`; terminal code `0`.

## What the PASS means — and does not

**Closed for this one known package:** the *local technical keyboard, localized-rendering and mobile/desktop overflow baseline* at the declared check count. The exercise supports the general player's ability to render all 18 interaction formats in a real browser with the observed test assertions.

**NOT independently closed:** provenance of actual browser-session execution against a trusted external verifier; screenshot visual-quality interpretation; substantive physics correctness; effectiveness or need for diagrams, animations or manipulations; semantic equivalence of EN/MS/ZH text; original-source and third-party figure rights; full accessibility/reduced-motion/touch; any real pilot with students.

Specifically, **0 visualSpec** means the required visual-interactive pedagogy gate still has *no case-level evidence* in this candidate. The success of keyboard checks cannot be promoted into visual-semantic PASS. Independent reviewer/material-based academic QA remains `REVIEW_REQUIRED`.

The existing private round-two C3 campaign remains **`FAILED_LIMITED_CAMPAIGN`** (two drafts and a failed waves repair); the old 104/108 browser receipts for the two private drafts were not overwritten or rerun. Historical Section 9.4 remains 0/18 formal independent academic PASS. No release or merge was attempted.

## Binding disposition and next gate

**Phase A: complete with a narrow local technical PASS; no retry or source-specific correction required.**

**Phase B: NOT AUTHORIZED / NOT STARTED.** A genuinely fresh, rights-cleared, independently precommitted three-source cross-topic evaluation would require a **separate, explicit authorization** and the five independent academic proof categories. The new sources cannot be copies of Decision 0029's exhausted PDFs. Do not create synthetic `visualSpec` content solely to make this baseline appear visual.

**Phase C current global assessment:** `NOT_COMPLETE_WITH_NAMED_BLOCKERS`, limited by C3 failed generalization, missing source-grounded academic/scientific/trilingual/visual proof and no release approval. Draft PR #223 remains **unmerged** and publication remains **disabled**.

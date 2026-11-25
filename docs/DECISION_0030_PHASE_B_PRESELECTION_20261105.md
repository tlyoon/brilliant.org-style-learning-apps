# Decision 0030 Phase B — pre-acquisition source-selection witness

**Status:** FROZEN_SELECTION_BEFORE_SOURCE_ACQUISITION. Decision 0030, owner request "Proceed as recommended", 5 November 2026.

This document is to be committed and pushed to the consolidated draft PR **before** downloading any selected source PDF or initiating any model or generator call. It fixes the three distinct topic families and exact public source URLs, so PDF-specific difficulty or generated output cannot influence selection.

## Frozen source selections

| Case ID | Topic family | Source identity | Exact MIT OCW PDF URL |
|---|---|---|---|
| `phaseb-momentum` | `mechanics` | 8.01SC Classical Mechanics, Chapter 10, *Momentum, System of Particles, and Conservation of Momentum* (22 pages listed by public source) | `https://ocw.mit.edu/courses/8-01sc-classical-mechanics-fall-2016/mit8_01scs22_chapter10.pdf` |
| `phaseb-gauss` | `electromagnetism` | 8.02T Electricity and Magnetism, Chapter 4, *Gauss's Law* (39 pages listed) | `https://ocw.mit.edu/courses/8-02t-electricity-and-magnetism-spring-2005/16ff64d64187374a61c28a1f9f16f348_chapte4gauss_law.pdf` |
| `phaseb-first-law` | `thermodynamics` | 3.020 Thermodynamics of Materials, Lecture 3, *Process Variables and the First Law* (7 pages listed) | `https://ocw.mit.edu/courses/3-020-thermodynamics-of-materials-spring-2021/mit3_020s21_l03.pdf` |

**Selection references:** public MIT OCW mechanics online textbook; 8.02T lecture notes; 3.020 lecture notes; official MIT OCW privacy and terms of use.

**Historical exclusions:** prior Decision 0029 round-one original source SHA-256 `a8bd3d0b24251600124e09c894d8f495c4e013397ecb77bb03f09b6aeba0dfc4`, `158328ca4d43958c4b8add3c98f4279e8dfea56acde60aa084ecc5ea20d5dd9c`, `a37ba03ab6d67940e36c06a2355cb93336cc4b61f63d58a74865cb137e90fe4f`. Round-two exclusions `443ab307f70ae053dfe1110ca2167c000ec184f0724c533ab4f64d9789f80ef6`, `d6c21d0cf0e29ebfd47d84913ee852bce024513f31057c7afee52b96367393a0`, `e2e080d037a316b5b501dc79a4289cdaf6019bf434f05974161f34d8ed504ac1`. This is a known six-source exclusion set, **not independently proven absence across all historical private corpora**. Compare exact fetched PDF hashes against these six prior values and each other before ingestion.

## Licensing, private-use boundary and attribution

MIT OpenCourseWare identifies a **CC BY-NC-SA 4.0** license for OCW-authored material and explicitly permits noncommercial educational adaptation with attribution and share-alike. This frozen evaluation is **private, noncommercial technical research**, with source citations and attribution retained as metadata. MIT course pages identify original instructors/notes; site-level licensing does **not** independently clear every embedded figure or external third-party image. Never copy a third-party figure into a released app without separate clearance. Never copy protected source bytes, figures, or raw model output into Git or CI. **Rights for public redistribution and all diagrams are NOT VERIFIED**; this is only a conditional private-use rights review, not release clearance.

Official license/terms: `https://ocw.mit.edu/pages/privacy-and-terms-of-use/`. Attribution: © MIT OpenCourseWare; course descriptions and PDFs above; CC BY-NC-SA 4.0, `https://creativecommons.org/licenses/by-nc-sa/4.0/`.

## Software and campaign freeze

- Repo `tlyoon/brilliant.org-style-learning-apps`, consolidated **draft PR #223**.
- Frozen source-generation baseline **`2c35da46490061d92ba7f61558cabbc65d4e13c8`** from the last exact-head passing validation; future metadata-only witness/receipt commits do **not** update this generator baseline.
- Domain profile: `university-level-physics`; version must be inspected and pinned in the separate pre-ingestion private manifest.
- Number of sources **exactly 3**; one new source-bearing generation invocation per source **maximum**, no automatic replay of ambiguous source requests, no reusing round-one/round-two PDFs. No extra run when an outcome is unsatisfactory.
- Source PDFs and generated packages live **outside the repository** in a new private read/write campaign root. SHA-256, page count, page-text viability, rights boundaries and source/engine identities are attested **after** download and **before** the first model call.
- Provider source-free preflight allowed only if connected and authorized. On explicit execution denial, stop; do not reroute to another machine or transport. Only approved Gemini/ChatGPT; **no local models**.
- Source-bound academic/EN/MS/ZH/visual QA requires independent proof; schema/CI/provider-access or any AI self-rating does **not** grant academic PASS.
- `git_publish=false`, `git_auto_merge=false`, `public_deploy=false`, `public_deploy_auto_merge=false`; **no merge and no publication**.
- Terminal disposition: if all 3 cannot be independently proven across five C3/C4 gates, stop with named **FAIL / REVIEW_REQUIRED / BLOCKED_EXTERNAL**, not a fourth PDF.

**Witness timing invariant:** This tracked document's authenticated Git commit must precede the first acquisition of any of these three PDFs. If that cannot be verified, report `PRECOMMIT_NOT_ATTESTED` and **do not call a model**.

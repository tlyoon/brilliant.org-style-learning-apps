# Finite private learner-browser evidence audit — 5 November 2026

**Repository:** `tlyoon/brilliant.org-style-learning-apps`; draft PR #223. This audit does not reopen Decision 0029, generate a PDF, contact Gemini/ChatGPT, merge, publish, or authorize new source-bearing retries.

## Pre-existing round-two private candidates

Two *already generated* draft packages, located in the owner-authorized Yoga 6 continuity directory, were examined without modifying their bytes:

| Topic | Exact package SHA-256 | Activity roster | Declared visualSpec count |
|---|---|---|---:|
| Circular motion / mechanics | `f7d3687fb26a6ddc5f895a5a992e3f949d9c38b82c2a7d76229dd0a81610829f` | 18 (9 MCQ / 9 interactive) | 0 |
| Coulomb's law / electromagnetism | `3a55da0dbcc84fff898f82ba1bcd1150ba25b729775834c3e040201472bb4316` | 18 (9 MCQ / 9 interactive) | 0 |

The absence of visual specifications **does not automatically violate the text-first exception** in the product requirements; an independent pedagogical/physics review is still required to determine whether visuals should have been authored. It **does mean visual-semantic coverage cannot be demonstrated from these two package bytes alone**.

## Actual private browser observations

A new private one-shot localhost-only headless Chrome audit inspected the immutable candidates without any PDF/model calls. Each test required a localized prompt, mobile/desktop layout without horizontal overflow, keyboard-accessible hint, keyboard answer interaction, and feedback. Screenshots and per-activity metadata were saved **privately**, not in Git.

- Mechanics: 108 of 108 expected checks recorded; 104 screenshots captured; four failed checks (selection interactions at two activities, in Malay, at both widths). Exact package remains `INCOMPLETE_BROWSER_COVERAGE`.
- Electromagnetism: 108 of 108 checks recorded; 104 screenshots; four failed checks (selection interactions at two activities, in Malay, at both widths). Exact package remains `INCOMPLETE_BROWSER_COVERAGE`.
- Cause found in the *new QA harness*: it reused the same page across EN/MS/ZH checks. The real application intentionally retained prior selected answers when the locale changed; pressing a selected option again **deselected it**. The harness incorrectly required that first option to be pressed after every locale change. Consequently, the failures are **not sufficient evidence of an app-side keyboard defect**, nor can they be retroactively marked PASS without a correctly isolated verification.
- Original one-shot receipts, including incomplete status and all four false-negative-looking observations per package, are **preserved**. Their evidence was not overwritten or replayed.

## General reusable code correction, without repeating PDF generation

New `scripts/audit_full_learner_browser.py` supports an isolated, bounded full-roster run for a separately authorized **existing package**. It stages only the local trusted player and candidate bytes, runs ephemeral localhost Chrome without external requests, records a SHA-256 for each screenshot, refuses reused per-package output directories, stops after a bounded number of errors and emits sanitized categories. No model, original PDF, student ID, or publication action is involved.

The harness now performs a fresh page load **before each language**. A wholly synthetic single-selection fixture covered three locales and two widths with **6/6 successful checks and 6 screenshots**, and four source-free regression tests protect page isolation, missing localization, unsafe output directories and duplicate one-shot evidence. Each new receipt binds the exact audit-script and learner-player SHA-256 in addition to the package. Synthetic success is not a new result for the two old candidates.

For a **new, separately authorized existing package** (not the already inspected drafts), the bounded read-only command is:

```powershell
python scripts/audit_full_learner_browser.py --package "C:\\private\\candidate\\package.json" --output-root "C:\\private\\existing-review-folder"
```

The output directory must preexist outside the checkout and must not already contain evidence for that package digest. The command has **no replay/overwrite option**.

## Remaining external acceptance dependencies

1. The existing finite C3 generalization campaign is **FAILED_LIMITED_CAMPAIGN** (two drafts plus a failed waves repair). Its trial budget cannot be silently reset.
2. A new explicitly authorized, finite real-candidate/browser acceptance contract and separately trusted receipts are needed to clear the remaining interactive/responsive evidence gap. Do not reissue an old source-bearing request or disguise a rerun with another output folder.
3. Independent source-rights, mathematical/physics reasoning, diagram semantics and EN/MS/ZH equivalence require separately authorized automated source-bound evidence. Metadata and browser screenshots alone cannot grant formal academic PASS.
4. Draft PR #223 remains unmerged with `git_publish=false`, `git_auto_merge=false`, `public_deploy=false`. No release authorization is inferred from source-free CI or this private check.

**Regression incident:** `BSA-20261105-116`. The accepted engineering disposition is **BROWSER ACCEPTANCE TOOL IMPLEMENTED; OLD PRIVATE RECEIPTS STILL INCOMPLETE; ACADEMIC AND RELEASE GATES BLOCKED**.

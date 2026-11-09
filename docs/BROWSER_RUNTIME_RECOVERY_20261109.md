# BOSLA browser-runtime recovery — 9 November 2026

## Root cause and general correction
A Chapter 9 pilot run invoked `scripts/audit_full_learner_browser.py` with
the Windows shell's default Python, which lacked Selenium. The run raised
`ModuleNotFoundError: No module named 'selenium'` before creating an audit
directory or contacting Chrome. This is an environment-selection fault, not a
physics-content defect and not a consumed browser acceptance run.

The shared full-learner-browser entrypoint now calls
`app_generator/runtime/browser_runtime_selection.py` **before** any one-shot
receipt or local browser session. If Selenium imports in the current runtime,
normal operation is unchanged. Otherwise, it checks only a preexisting
`.venv` in the current BOSLA checkout or the owning Git common checkout for
detached worktrees. It probes the candidate interpreter with a source-free
`import selenium` and relaunches the exact original command once.

There is no package installation, arbitrary path scan, cross-project runtime,
PDF access, Gemini request, source-bearing replay, Chrome-profile reuse,
permission change, modification of completed receipts or hidden retry. If
no suitable runtime is found, an explicit sanitized
`BOSLA_BROWSER_RUNTIME_UNAVAILABLE` result exits before any audit begins.
A process-local guard prevents recursive re-launch.

## Evidence and reproducibility
- Two previously unattempted, owner-approved Chapter 9 real packages were
  audited once each in the existing private Yoga 6 evidence root with the
  existing BOSLA virtualenv, on the frozen code head `0a901e4d194c`.
- Section 9.4: 108/108 observations, zero failures/missing, 108 screenshots;
  package SHA-256 `1f6e2568fb6cbd5a82a7563c12f627779644ef3a991eb861e791849c49abc4d2`.
- Section 9.6: 108/108 observations, zero failures/missing, 108 screenshots;
  package SHA-256 `1620d15e1d645c81301997f0e42d0efbad0a7b2d123eb6b11cba9ec8c04b027f`.
- Prior Section 9.5: 108/108 observations, zero failures, with frozen receipt
  and screenshot hashes kept privately. Sections 9.1–9.3 remain one-shot
  incomplete records and are **not** replayed.
- Seven new source-free tests prove automatic same-repository runtime routing,
  fail-closed missing dependencies, recursion guard and CLI integration.
  Existing seven browser-audit regression tests remain green.

The browser reports always say `independentBrowserReviewComplete=false`,
`technicalAcceptanceGranted=false`, `academicAcceptanceGranted=false`
and `publicationAuthorized=false`. These tests cover browser operation,
**not** original-source rights, scientific meaning, EN/MS/ZH equivalence,
responsive assistive accessibility, visual pedagogy or academic C4 acceptance.
All six original packages declare zero visualSpec activities. Do not equate
324 successful browser observations with six-section pilot acceptance.
No new PDF/model generation, source upload, student data, publication or merge.

## Recurrence and continuation
Incident `BSA-20261109-130` links earlier environment-preflight
`BSA-20261031-055` and browser async readiness `BSA-20261107-128` to the
specific remaining automatic-recovery gap. Permanent tests run with normal CI.
This amendment belongs to consolidated draft PR #223 only; source code
remains unmerged until applicable merge controls and final checks permit it.

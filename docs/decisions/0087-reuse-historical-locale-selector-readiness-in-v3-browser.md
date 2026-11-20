# Decision 0087 — Reuse the historical enabled-locale readiness guard

**20 November 2026 — owner Yoga 6, BOSLA BSA-20261120-231.**

## Actual blocker and historical recurrence

The genuine source-free V1–V10 worker on clean source
`f3a6985539d42b32cb5142d0e045424db06f5adf`
stopped with exit 3 in the original Chapter 9 candidate-browser child,
before completing V10. The child returned
`STOP_ACTUAL_CHAPTER9_BROWSER_QA` with `NotImplementedError`;
it did not produce a signed V10 receipt. GitHub Actions
#44669663186 passed, so passing hosted CI alone did not establish
real Yoga 6 acceptance.

Historical BSA-20261107-128 had already identified this failure:
the app disables the language selector while fetching an activity.
Selenium 4.47 `Select._set_selected` may raise
`NotImplementedError` if a target option is temporarily disabled.
The historical shared `scripts/audit_full_learner_browser.py` waits
for the language selector to become enabled AND for an actual question
heading to render. That fix was never consistently applied to the
separate `scripts/check_v3_real_chapter9_browser.py` entrypoint.
Historical BSA219 also identified failed child-error propagation,
but BSA230 correctly returned nonzero and retained the failure
classification instead of falsely reporting PASS.

## Targeted reusable repair

Reuse the historical BSA128 readiness predicate in the actual
Chapter 9 source-bound browser script, at every language-selection
site. A new `_select_loaded_locale` waits for both the enabled
language selector and the genuine `#app h1.question` element before
calling Selenium Select, without fixed sleeps or blind retries.
The existing strict prompt, locale, activity, viewport and privacy
checks remain in force. An unavailable selector times out and fails;
it is never treated as acceptance.

Add regression controls for a disabled selector with a rendered
question, an enabled selector with no rendered question, a
slow-loading selector eventually becoming ready, a selector that
never becomes ready, and proof that the active browser path uses
the shared guarded selection rather than direct Selenium selection.

This is a normal production worker repair because the unmodified
`scripts/run_v3_yoga6_acceptance.py` already dispatches that
source-bound script. Do not replay paid Gemini requests, source
PDFs, uncertain historical C3 campaigns or unrelated public pushes.

## Verification sequence

Follow the v7.1 contract: historical review → targeted repair →
real owner Yoga 6 test → fault injection and regressions →
executable registry integration → normal pipeline restart. The
first 31 focused local regressions passed. Do not mark BSA231
or BSA230 complete until exact new-head hosted CI and authentic
normal source-free V1–V10 acceptance have been observed. Preserve
the existing V9 private 24-file SHA scope and continue to a
non-merging release proposal only when a genuine V10 signed
receipt exists. No public branch push, public PR, merge or
deployment is part of this browser repair.

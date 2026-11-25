# Decision 0068 — Repeated hosted Chrome integrity smoke must see changed fixture bytes

**Date:** 18 November 2026. **Incident:** BSA-20261118-210. **Trigger:** GitHub Actions run 44294173539 on commit 03add0486687a09a9b5ec4aeacbc61d2d046bd89 failed in source-free real Chrome instructor preview smoke, at script line 311, waiting 10 seconds for the learner-visible invalid-signed-package result after mutating Section9.2 synthetic package bytes. All Python content, lint, recurrence and broader unittest gates had already passed on that CI run, as had the genuine 108/698 browser run on Yoga 6.

## Historical review, diagnosis and scope

BSA194/197 established the difference between hosted synthetic browser smoke and Yoga6 genuine Chapter9 browser acceptance. BSA205 established reusing the pinned Selenium environment. This newly observed failure is at an additional **HTTP-fixture byte-change boundary** rather than content generation or provider availability. The local test uses Python `SimpleHTTPRequestHandler` and rewrites a previously requested `package.json` during the same Chrome session. Without explicit no-cache headers, the browser may return a cached old valid payload or use conditional request metadata, which would invalidate the negative-control test. Cached response reuse is a plausible cause, not proved to be the only possible cause of the observed timeout. A repeated arbitrary delay or suppressing the negative-control assertion would not resolve the mechanism.

## Targeted executable repair

`scripts/check_course_preview_browser.py` contains the local-only disposable `QuietHandler`. Override `send_head` to ignore stale `If-Modified-Since` and `If-None-Match` request conditionals and `end_headers` to emit `Cache-Control: no-store, max-age=0` and `Pragma: no-cache`. This forces the synthetic package-integrity check to fetch the **actual modified bytes**, preserving rejection rather than masking the expected failure. The formerly bare Selenium TimeoutException now records a small **synthetic only** learner-visible app state if the expected package-integrity warning does not appear; it still fails closed and never passes after a timeout. No production app code, genuine source package, private reviewer evidence, live credentials, browser privacy policy, academic assessment or release gate was changed.

`tests/test_course_preview_cache_integrity.py` makes a real loopback HTTP request, mutates the fixture bytes, then sends a stale conditional request and requires status200 with modified content and no-store headers. It also supplies both ETag and a future If-Modified-Since negative control to ensure 304 cannot hide new fixture bytes.

## Evidence and closure

Actual Yoga6 existing pinned .venv ran both network-level fake-cache regression tests, 2 PASS; real Selenium Chrome `scripts/check_course_preview_browser.py` succeeded with 6 locales/viewports, 6 screenshot digests, `tamperedPackageRejected=true`, academicQA still REVIEW_REQUIRED and publication false. The CI repair must pass the full normal regression contract, tests and a fresh hosted exact-head GitHub CI before BSA210 can be marked resolved. This is a source-free test-only repair; **no Gemini API call is authorized or issued by it**. The new owner-authorized four original Section9.2 reviews remain blocked on hosted CI success, preserving the eight-call budget.

# Autonomous Academic QA: no mandatory human sign-off

Authoritative owner contract: docs/decisions/0024-autonomous-ai-academic-review.md.

The previous decision 0023 already made manual approval optional for
publication. Decision 0024 explicitly removes mandatory *human academic*
approval from generation, corrections, tests and development continuation.
Source-bound science checks, independently verifiable proof and separate
protected-branch/public-release permission remain necessary.

## Execution interface
app_generator/validation/autonomous_ai_review.py requires two distinct
fresh reviewer sessions, tied to the exact package SHA, PDF SHA, activity
version, independently obtained source passage, and authorized PDF pages.
Both model responses are structured and checked against the requested gate;
neither AI agreement nor language-keyword matching alone proves full
academic correctness.

app_generator/runtime/autonomous_academic.py accepts an owned RunContext,
exact package/source SHA, authorized source evidence per activity and a
reviewer_factory supplying two fresh independent sessions. Before each
request it persists an IN_FLIGHT claim. COMPLETE responses are cached.
After ambiguous potentially-submitted requests, the claim stays AMBIGUOUS
and is not re-sent blindly. A deterministic follow-up queue chooses
AUTO_REPAIR, AUTO_SOURCE_CHECK, AUTO_RETRY after reconciliation, or
AUTO_CONTINUE to independent mathematical and source-specific validation.

All recorded AI findings use humanReviewed=false and
humanReviewRequired=false. Distinguish aiReviewAttempted from aiReviewed
for uncertain or in-flight claims. Academic PASS still requires independent
real mathematical/source/visual evidence under existing quality gates.

## Reproduction
Run python -m unittest tests.test_autonomous_ai_review -q with the approved
project venv. Full repo tests and GitHub Actions are additional gates.
Tests are simulated; they make NO paid model calls.

## Explicit limitation
The review API is provider-neutral and not automatically activated in the
normal generator pipeline by this PR. A separate live integration must
provision independent Gemini browser sessions, verify source passages,
reconcile in-flight requests and independently validate reviewed responses.
The existing generation Gem is NOT an independent academic reviewer.
Do not label simulated tests as real AI academic review.

## Next real milestone
Wire authorized, independent Gemini browser reviewer sessions into the
normal run coordinator, run one original-source Section 9.4 v3 private
pilot, retain private receipts, validate physical and translated meanings,
then independently audit visual meaning before complete academic PASS.
Keep git_publish=false and git_auto_merge=false without separate consent.

# Decision 0035 — RC1 provisional six-section draft learner integration

**Date:** 11 November 2026. **Status:** owner-directed engineering integration,
source-free evidence only; not academic acceptance or public release.

The owner requested immediate connection of the verified RC1 routing engine to
the **existing authentic six-subchapter draft learning packages**, using actual
player answer observations, followed by independently evidenced academic,
visual, learner, and release verification. This is permission to implement an
eligible local engineering integration without waiting for the scheduled task,
**not** permission to replay the terminal original-source/browser/academic
acceptance campaigns or to collect real learner records.

## Exact existing content identities — unchanged from Decisions 0031/0032

The six original Chapter 9 package Git blob SHA-1 identities, in order:

| Section | Chapter 9 topic | Original committed package Git blob SHA-1 |
| --- | --- | --- |
| 9.1 | Linear Momentum | `6dc84d7bbc8f6944d150bb79bb26906a71e2f3f5` |
| 9.2 | Analysis Model: Isolated System (Momentum) | `779deb4e207078f9081a9de78a14226d473f9b25` |
| 9.3 | Analysis Model: Nonisolated System (Momentum) | `7b019d9502d8da7eab9f311e9c3d0830e8b30396` |
| 9.4 | Collisions in One Dimension | `f9604d795a6d8c02d2de02a5672f8cba0e4bf949` |
| 9.5 | Collisions in Two Dimensions | `aa6d34978b79a13cf26f9558c21dd8aafa08c80b` |
| 9.6 | The Center of Mass | `90b8a5e7d627de3bfcc2320428981e73022a968e` |

These are **not** new candidates, and the original Chapter 9 frozen V2
campaign statuses and terminal attempt counts are unchanged.
`docs/acceptance_closure_chapter9.json` remains FINAL_ACCEPTANCE_NO_REPEAT_V2,
with zero new original Chapter 9 campaigns. New implementation is source-free;
all browser acceptance tests use synthetic fixture packages, never the original
six package bytes in a fresh original-source/browser campaign.

## Engineering scope and actual evidence provenance

- `app/rc1-chapter9-draft.html` is a local instructor-only six-section
  **draft** course path. It reuses the existing exact-package SHA-256 verified
  `app/course-preview.js` selector and unchanged Stage-0 answer-check code.
  On Yoga6, `scripts/prepare_course_preview.py` can generate a gitignored
  `local-pilot/roster.json` from *exact tracked* package identities; no PDF,
  model, login, student data or public upload is needed.
- Only this explicit local draft page sets `data-diagnostic-events=true`.
  The real `app/app.js::recordLearningEvent` emits a minimal in-memory
  `bosla:player-evidence` CustomEvent for genuine checks, hints, skips and
  completions. The packet carries only package ID, 1-based activity ordinal,
  event kind and anonymous local counters; no selected option, answer content,
  student identity, grade, timestamp, storage key or network POST.
- `app/rc1-course-diagnostic.js` accepts only an explicitly selected,
  exact-section package ID and the first authored activity. It freezes the
  **first observed checked answer** across retries/navigation and marks
  independent only after a clean first-try correct response followed by
  explicit player completion with no hints/skips/interruptions.
  Wrong-first, retries, hints, skips or abandoning a first attempt cannot be
  inflated to independent completion. It never persists results.
- `app/rc1-course-routing.js::planDraftCourse` reuses the validated generic
  six-section DAG and session-only recommendation logic. The engineering
  predecessor graph, presently provisional, is: 9.1 -> 9.2 -> 9.3; 9.2 ->
  9.4 -> 9.5; 9.1 -> 9.6. This is **not** independently proven to be the
  optimal pedagogical sequence. Recommendations are advisory, not enforced
  gate locks; learners can still inspect any draft section.
- `app/rc1-chapter9-bridge.js` merges genuine answer evidence and route
  advice on the new local-only page. The diagnostic prominently says
  the key-scored counts are provisional and independently UNVERIFIED.
  Answer-check integrity is distinct from correctness of academic answer keys.
  No institutional standing, retention, student record, verified course
  mastery, grade, privacy consent or public release is asserted.
- All UI source and executable tests remain in the ordinary repo/PR; original
  textbook PDFs, extracted passages and third-party figure assets are not
  added to Git, the tests or an external service.

## Exact bounded testing authority

- Existing source-free JavaScript tests, supported six-synthetic-package
  local-only Chrome stage site, 390x844 mobile and 1280x800 desktop viewports;
  test the **real** player answer/next UI and untrusted response refusal.
- New synthetic fixtures have no original Chapter 9 source content, so these
  are engineering regressions, not repeats of terminal original-source,
  original-browser, or independent academic campaigns.
- No source PDFs, Gemini/API calls, original-content external review,
  real learners/identities, class pilot, production authentication,
  deploy, publication, or Git merge.
- An exact-head green workflow and source-free recurrence regression establish
  only the integrity and integration of the code. They cannot certify the
  scientific correctness or multilingual meaning of old authored answers.

## Completion and remaining independent gates

**This milestone closes only** real-answer-event -> first-check evidence ->
provisional six-section routing within an authentic, digest-verified *draft*
learning interface. Trustworthy **measurement of observed answer events** is
implemented; trustworthy **educational interpretation and scoring** remain
unverified while the underlying author keys and translations are unreviewed.

Independent source-grounded answer and EN/MS/ZH correctness, meaningful visual
semantics, an original-source permitted viewport/browser acceptance campaign,
real learner accessibility and institutional privacy/pilot evidence, and explicit
release authorization are STILL REQUIRED for publishable completion. They must
be established in an independently admissible **new authorized scope** or
genuinely newly available evidence; do not assign PASS from synthetic tests or
reopen previously exhausted Chapter 9 campaigns.

Binding Decision 0033's removal of textbook edition, rights-holder discovery
and a rights gate as *technical* completion requirements remains permanent.
Operationally, this decision does not grant rights to transmit or redistribute
protected third-party content. Git merge/public deployment remains prohibited
without distinct explicit release permission.

This owner-authorized **technical** bridge is distinct from Decision 0034's
six synthetic RC1 demonstration scope. The original six package identities
are referenced but not reissued as fresh academic candidates.

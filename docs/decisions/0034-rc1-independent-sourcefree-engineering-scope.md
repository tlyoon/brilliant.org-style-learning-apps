# Decision 0034 — BOSLA RC1 independent source-free engineering scope

**Status:** Owner-directed RC1 engineering authorization, 11 November 2026.
**Authority:** The owner explicitly instructed "Proceed as recommended" after the
RC1 release-candidate proposal. This authorizes a genuinely distinct, bounded
**source-free engineering slice** now. It is not an approval to restart terminal
Chapter 9 acceptance attempts, use protected source PDFs in external models,
collect student data, merge PRs, or publish an unaccepted learning course.

## Frozen input identity and non-replay boundary

- **Repository:** `tlyoon/brilliant.org-style-learning-apps`; existing consolidated
  draft PR #223, no separate PR stack, no automatic merge.
- **Engineering baseline:** `a6bc4dac35b6fb0a157ac0261bfe3474b2b1a78b`
  (pre-RC1 source tree; later source-free commits are permitted with new exact-head CI).
- **Independent input:** `docs/rc1_engineering_scope.json`, six **synthetic original**
  concept nodes and versioned, explicit graph edges. Canonical JSON
  `JSON.stringify(parsedScope)` SHA-256:
  `13c5234f5f22d7904c7a78f7d7927605a3e2ff4fbc9609ec66dfe34560619d76`.
  This identity is asserted by normal executable CI tests; any change requires
  a new explicitly reviewed versioned scope, not silent reuse.
- No source PDFs, original Chapter 9 candidate hashes, textbook passages or
  frozen Chapter 9 browser/source/academic review receipts are inputs to RC1.
- **Chapter 9 V2 remains authoritative and unchanged:** the former
  `sourceAndFigureRights`, textbook-edition, and rights-holder identification
  conditions are NOT BOSLA technical-completion gates (Decision 0033).
- This authorization is **engineering-only**. It does not pretend to be the
  instructor-approved original six-section learner pilot, independent scientific
  review, real learner data, or a release grant.

## Frozen finite execution budget

The machine scope sets `maxSourceCampaigns=0`,
`maxAcademicExternalReviews=0`, `maxSyntheticBrowserSmokes=1`,
`externalModelCallsAllowed=false`, `sourcePdfReadsAllowed=false`,
`realLearnerRecordsAllowed=false`, `publicPublicationAllowed=false`
and `gitAutoMergeAllowed=false`.

The one independently reviewed engineering smoke uses **only the six synthetic
nodes** and source-free code on an isolated loopback Chrome session.
Repeating these lightweight source-free tests in ordinary CI is regression
verification, NOT a renewed original-content academic or learner acceptance
campaign; it does not reset or expand the one-shot manual smoke budget.
No identity, grades, session persistence, exports, cloud APIs or paid calls.

## First executable vertical slice

1. `app/rc1-course-routing.js`: a subject-neutral, deterministic, versioned
   pure route planner. Reject unknown/missing/duplicate/cyclic prerequisites,
   changed protected action budgets, invalid or duplicate synthetic outcomes.
   Only independent completion satisfies an explicit prerequisite; assisted
   practice does not. A simulated review-due flag takes priority without
   claiming a real scheduling algorithm or retention evidence.
2. `app/rc1-course-journey.html` with local `rc1-course-demo.js` and CSS:
   visibly demonstrate the route using only synthetic session observations;
   label it clearly non-publishable, no PII, no storage. A missing or invalid
   frozen scope renders no route.
3. `tests/test_rc1_course_routing.js` and
   `scripts/check_rc1_routing_browser.py`: source-free adversarial tests,
   version binding, assisted-vs-independent negative controls, stale/malicious
   scope rejection and exact responsive 390x844/1280x800 Chrome interactions.
   CI must invoke these normal controls.
4. Retain default Stage-0 player and six-subchapter instructor preview
   unchanged; no automatic inference of educational prerequisites from a PDF
   or claims that synthetic routing is a classroom-ready adaptive system.

**Success for this first RC1 slice** means deterministic routing and safe
synthetic browser behavior with green CI. It does **not** mean BOSLA's overall
six-section teaching application is academically accepted or publishable.

## Subsequent gated progression toward publishable completion

Advance through the remaining actual learner-course integration, independent
EN/MS/ZH science-answer review, meaningful visual semantics, authentic
viewport/touch/accessibility, approved privacy/retention/rollback and real
learner-pilot evidence, integration and explicit public-release authorization,
**only when fresh source/scope-specific admissible inputs are available**.
Never use synthetic simulations to certify real mastery or privacy consent.
Report `NOT_COMPLETE_WITH_NAMED_BLOCKERS` until the mandatory V2 evidence is
actually passed. Do not invent another academic gate or restart previous
terminal Chapter 9 campaigns.

This separate source-free engineering decision neither edits
`docs/acceptance_closure_chapter9.json` nor expands
`newCampaignsAuthorized` there. A future genuinely distinct original-content
pilot needs its own versioned exact-package scope and legitimate rights of use
for the intended operations. These are operational content-use decisions, not
a reinstated technical rights-PASS gate.

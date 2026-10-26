# Reviewers using existing authorized Gemini login

## Decision 0024 interpretation
Manual academic sign-off is not a gate. The first-party authorized Gemini
login must be checked before asking the owner to authenticate new profiles.
Do not copy passwords, browser cookies, OAuth tokens or authoring context.

## Verified Yoga6 real account, 26 October 2026
- Existing controlled Chrome profile at
  %LOCALAPPDATA%/BrilliantContentGenerator/chrome-profile/gemini-browser
  opened Gemini. The existing project GoogleAccountVerifier independently
  VERIFIED the expected signed-in account via visible web UI.
- No new Google login was needed. No cookies or credentials read.
- First source-free neutral role probe saved privately at
  academic-source-evidence/existing-login-neutral-probe-20261026-pr147-01/state.json.
  Physics request became POSSIBLY_SENT, then AMBIGUOUS with
  ResponseContractError. No valid response captured; second probe role
  not submitted. No PDF or protected teaching content uploaded.
- DO NOT blindly retry this ambiguous prompt; reconcile prior provider
  transaction first. It did not yield a scientific reviewer report.
- Original authorized Chrome profile remained active after reported
  Browser.close/driver.quit. A process scan found an associated process
  tree; its precise remaining process ownership was not durably proven.
  Do not kill/steal that browser in order to continue work.

## Independent conversation implementation
New ExistingLoginReviewerFactory uses a single pre-authorized controlled
Chrome profile, checks Google signed-in account LIVE, and creates two
separate brand-new neutral Gemini chat tabs. Every academic prompt switches
to its own reviewer tab and refuses other pages or nonacademic stages.
Original/authoring browser tabs are never navigated, used as reviewer
contexts, or closed explicitly. The existing generator configuration
and its customized Gem are not overwritten or synchronized.

Two fresh conversations do NOT equal two independently authenticated
Google accounts or independent model providers. Independent source-bound
exact-arithmetic, distractor, translated-meaning and visual correctness
tests remain mandatory. Two AI opinions alone can never grant PASS.

The private Section9.4 academic pilot now supports --existing-login and
uses gemini_browser in memory, never the configured paid Gemini API.
The original legacy dedicated-profile mode remains available.
A profile path and Preferences file are not evidence of authentication.
Actual sign-in must be verified via GoogleAccountVerifier before attaching
the controlled PDF or submitting academic requests.

## Source-free recovery
scripts/probe_existing_gemini.py creates a new private immutable report
directory and writes POSSIBLY_SENT before any UI model submission.
It checks only structured generic JSON, not textbook information.
A possibly sent request times out to AMBIGUOUS; replaying the same report
folder is prohibited. No publication, humanReview or academic PASS inferred.

## Permanent browser lifecycle hardening
A Windows read-only Chrome process scan detects use of the old original
profile before reviewer startup; do not take over another owner.
ChromeSession now retains its own launched automation process handle,
so close may terminate only that specific owned process. Attach-mode
Chrome and unrelated normal login windows are never terminated.
If a prior process still runs with uncertain ownership, fail closed;
do not kill it by looking up a matching path or guessed PID.

## Next action
Reconcile the original source-free Gemini ambiguity and exclusive browser
ownership. Then perform genuinely captured two-conversation academic review
for the exact original Section9.4 PDF and v3 candidate, compare model claims
against original passage, deterministic physics and visual tests, and
expand only after one activity is fully independently verified.
All 18 activities stay REVIEW_REQUIRED until reliable complete evidence;
no human academic approval is required. Public release, protected merges,
paid API use, and edits to original source remain unauthorized.

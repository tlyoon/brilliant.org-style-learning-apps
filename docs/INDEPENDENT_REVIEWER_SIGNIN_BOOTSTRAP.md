# Independent reviewer readiness on authorized Yoga6

## Goal
Unblock source-bound Section 9.4 academic review using two physically
separate, controlled Chrome user-data profiles, with no paid Gemini API,
no copied Google cookies, and no reuse of the protected authoring profile.

The current regular generator configuration may specify the Gemini API.
The private academic pilot runner explicitly selects the browser-only backend
in memory without modifying the user's configuration or token files.
Both reviewer sign-in windows use neutral https://gemini.google.com/app,
not the customized authoring Gem or Gem editor.

## Safe owner controls
On Yoga6 only, from the owned development checkout:

  python -I scripts/prepare_academic_reviewers.py --config PRIVATE_CONFIG.toml

Read-only mode verifies the profile directory and normal Chrome Preferences
metadata **by existence only**, without opening cookies, tokens or stored
credentials. This is not proof of authentication.

  python -I scripts/prepare_academic_reviewers.py --config PRIVATE_CONFIG.toml --open-missing-windows

This opens ONLY absent role windows for physics and semantics. Existing
browser profiles are skipped; owner account credentials must be entered
solely in Google's normal Chrome sign-in UI, never through assistant logs,
arguments or Git. Chrome windows MUST be fully closed after completed
sign-in, before starting the controlled Selenium reviewer. Repeat the
readiness command; it never reports authentication based on directory
presence. A real neutral, no-source prompt/response probe must follow,
then the exact original-PDF one-activity source-bound pilot.

Private pilot CLI:

  python -I scripts/private_section94_gemini_pilot.py --config PRIVATE_CONFIG.toml --v3 PRIVATE_V3 --v2 PRIVATE_V2 --pdf CONTROLLED_SOURCE.pdf --proofs PRIVATE_SOURCE_PROOFS.json --out NEW_PRIVATE_REPORT_DIR

Do not use --execute until normal Google sign-in was independently
completed in BOTH roles, the windows have closed, current worktree is
owned, the source receipts and hashes are verified, and an explicit
request-claim idempotency workflow is prepared. --execute submits model
requests and may create in-flight provider claims; never blindly repeat
it after an ambiguous timeout.

## Actual Yoga6 preflight, 26 October 2026
- Both academic-reviewer profiles were initially ABSENT.
- This invocation opened ordinary neutral sign-in windows separately for
  physics and semantics using new on-disk role profiles.
- Subsequent read-only verification found both role directories and Chrome
  Preferences metadata initialized. No cookies or sensitive files were read.
- No login was independently verified. No actual Gemini response captured.
- No model request, textbook PDF upload, public publication or paid API made.
- Reviewer status: AWAITING_GOOGLE_SIGNIN, not academic PASS.
- Latest source-packet stage as of PR145: 18/18 original PDF passages
  verified, 18 AUTO_RETRY and zero genuine AI reviewer requests.
- Original working trees, protected textbook and GIT publication flags
  remain unchanged.

## Regression targets
Adversarial tests assert no source upload during bootstrap, independent
role paths, neutral URL, no inherited authoring Gem, no paid API calls,
idempotent existing role windows, fail-closed unexpected preexisting
directories, protection against profiles within the public Git checkout,
and explicit NOT-AUTHENTICATED even after Chrome initialization.
CLI test verifies a configured Gemini API backend is overridden ONLY for
the source-bound, private one-activity no-API pilot.

## Next owner action and normal automated continuation
If Google asks for login in the TWO separate Yoga6 Chrome windows, perform
normal sign-in into each, close both windows, then resume the no-source
prompt roundtrip and exact original-PDF one-activity academic review.
No human academic quality review is required by this process. The
publication authorization and all five academic acceptance gates
remain separate and fail closed. Do not count browser launch as live
Gemini review or as completed learning content.

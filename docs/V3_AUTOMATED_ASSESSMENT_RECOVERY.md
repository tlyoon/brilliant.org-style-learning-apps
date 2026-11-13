# V3 autonomous assessment: durable progress and verified blockers

**Scope:** BOSLA PR #223, current Decision 0036, 12 November 2026.
This document describes the actual source-free assessment runtime, not
independent scientific certification or proof of a real learner pilot.

## Why the assessment remained pending

The owner-approved V3 policy replaced manual educational, visual, learner
pilot and manual release-approval gates with complete two-context LLM review
and automated software evidence. But **the assessment engine did not itself
save and reload a full multi-invocation summary**. Only six activities were
reviewed per call, with individual claim checkpoints. Starting the next call
without externally supplying an `existing` aggregate could repeat the first
six, even when all six model role claims had previously completed.

The current shared `assess_with_models` function now:
- Uses a package-hash-bound `v3-assessment-<sha256>` aggregate checkpoint.
- Saves the aggregate after each fully classified activity, not just after
  the entire six-activity call.
- Loads that checkpoint automatically on the next invocation with the same
  controlled checkpoint port; no manual assembly of prior model results.
- Rejects stale, fabricated or inconsistent cached results. The validator
  checks every activity's exact identity, consensus reconstruction, both
  reviewer contexts, schema-complete verdicts, and the role-specific prompt
  SHA-256 for the exact generated activity.
- Never retries an ambiguous request; role-level `IN_FLIGHT` or
  `AMBIGUOUS` claims remain non-replayable until valid reconciliation.
- Returns `AI_ASSESSED_PASS` only when **all actual activities** in a package
  have complete two-context unanimous reviews, not after the first six.
  An AI response is model opinion, not independent external validation.

The source-free synthetic regression tests demonstrate 18 activities
progressing in exactly three bounded calls of six without caller-provided
prior results, followed by an idempotent fourth call with no more model
requests. Counterfeit prompt hashes, false statuses and removed reviewers
are rejected before sending another request.

## Read-only assessment progress

The normal status script is `scripts/check_final_acceptance_closure.py`.
It supports a package-specific option without submitting any model request:

```powershell
python scripts/check_final_acceptance_closure.py --package content/chapter-9/section-9-1/package.json
```

Pass `--assessment-file <PRIVATE_CHECKPOINT_JSON>` to inspect a real
package-matching aggregate checkpoint saved by the normal model assessment
port. Optionally pass `--release-receipt <PRIVATE_V3_RECEIPT_JSON>`
to validate a private locally attested full release receipt. The script
reports only counts and statuses, never model rationale, prompts, credential
contents, student identifiers or original source PDF passages. The
`--historical-v2` flag remains separate for the frozen attempt archive.
A missing or changed checkpoint never counts as reviewed.

Status meanings:
- `PENDING_AUTOMATED_ASSESSMENT`: at least one activity not yet assessed
  (or no model responses exist).
- `AUTO_REPAIR_REQUIRED`: one or more model-reviewed activities contain a
  model-flagged contradiction/repair need; original content remains unchanged.
- `RECONCILE_AMBIGUOUS_REVIEW`: every activity has been attempted, but at
  least one model result is uncertain or unreconciled.
- `PENDING_DETERMINISTIC_RELEASE_EVIDENCE`: all activities have two-context
  consensus, but no fully verified private release receipt exists.
- `AUTOMATED_TECHNICAL_ELIGIBLE`: a package-specific full model assessment
  and private attested automatic release decision were validated. This is not
  independent scientific proof, a classroom pilot or a source-license grant.

## What has NOT yet happened

**No genuine V3 Gemini/ChatGPT review of the original six Chapter 9
packages has been performed in this work.** The synthetic tests supply
fabricated model responses for controlled regression purposes only. The
direct authenticated Gemini runner creation was blocked in the previous
session; do not retry or disguise the same denied operation. On
12 November 2026 Yoga6 was also offline. No source-bearing model call,
protected PDF/figure upload, or real student data use was authorized.

Once a *permitted* existing reviewer transport and Yoga6 availability are
confirmed, the already shared `assess_with_models` function can run over
generated activity JSON only with a private `RunContext` checkpoint.
Until genuine model responses and machine evidence exist, report
`PENDING_AUTOMATED_ASSESSMENT` and do not merge or publicly deploy.

The current V3 contract has **no mandatory human academic review, independent
visual certification, approved real learner pilot, or separate human release
approval**. Decision 0033's technical rights gate remains removed. The
archived original Chapter 9 V2 source/browser/academic review campaigns are
not reset or restarted.

## Canonical authorized-session integration (BSA-20261112-152)

Previous BOSLA source-PDF reviewer code already supplied the
`ReviewerSession(reviewer_id, session_id, conversation)` shape and a
`conversation.ask(prompt, stage=...)` interface. The current V3 engine
must not use those historical PDF-upload factories, but can reuse the
interface **only when another permitted transport has independently provided
two valid model sessions**.

The provider-neutral entrypoint is now
`app_generator/runtime/v3_authorized_review.py::advance_v3_generated_text`.
Its parameters are the exact generated package bytes, two independently
supplied and authorized reviewer sessions, an absolute **off-repository**
private checkpoint root, explicit permission to transfer generated activity
text, and `max_activities` from 1 to 6.

A previously authorized runtime can first invoke
`advance_v3_generated_text(raw, sessions, private_root=private_root,
generated_content_transfer_allowed=True, max_activities=1)` for a single
activity; later invocations use the same private root with a maximum of six.
This is an API interface, **not a CLI that logs into Gemini or launches a
browser**. The flag documents the external caller's established transfer
permission; setting it does not itself authorize an account, browser action,
provider connection or paid service.

The service creates
`<PRIVATE_ROOT>/v3-generated-<full-package-sha256>/batches/
v3-assessment-<full-package-sha256>.json` as the stable private checkpoint.
An exclusive `.active-review.lock` is held for each bounded invocation to
prevent two concurrent processes from submitting the same model prompt.
If a process terminates while holding the lock, the system stops for
ownership reconciliation rather than silently deleting it or re-sending
ambiguous model requests. No real model response is printed by the service;
its return value is the source-free `assessment_progress` summary.

The permanent synthetic tests in
`tests/test_v3_authorized_execution_bridge.py` cover one-activity startup,
durable 1+6+1 progression, zero-repeat completion, missing authorization,
stale or conflicting checkpoint, unsafe private root, invalid batch size
and exclusive lock refusal. All real Chapter 9 packages are protected by a
no-model-session negative test, not reviewed by a fake transport. The separate
history-to-milestones evidence map is
`docs/V3_HISTORICAL_REUSE_MILESTONES.md`.

**Remaining external dependency is unchanged:** a genuinely permitted and
operational Gemini/ChatGPT generated-text-only reviewer source. Do not
call the old denied authenticated browser runner, bypass a host restriction,
attach protected PDFs, or count fake unit-test answers as actual model verdicts.

## Course-wide V3 readiness (BSA-20261112-153)

The Chapter 9 tracked content directory contains **nine** section packages
(9.1–9.9), but the approved current RC1/V3 scope covers **only 9.1–9.6**.
Never infer the frozen six-section roster from a whole-directory scan or
silently truncate extra packages. The *existing normal status script* now runs
with the automatically approved frozen-candidate selection (BSA-154):

```powershell
python scripts/check_final_acceptance_closure.py --course-dir content/chapter-9
```

Without a frozen scope manifest, a nine-section directory against the default expected
six fails closed. The generic `--expected-sections` parameter permits
separately authorized different engineering scopes; it does NOT amend the
current owner-approved Chapter 9 V3 campaign. The `--course-dir` and
`--package` modes are mutually exclusive. No source PDFs are read and no
external provider request, private source campaign or original-content browser
test is initiated by the new status path.

Optionally provide `--private-assessment-root ABSOLUTE_OFF_REPO_DIRECTORY`
to read the already-defined V3 `v3-generated-<full SHA>/batches/
v3-assessment-<full SHA>.json` checkpoints. This is strictly read-only:
missing evidence means zero model verdicts, stale/forged/mismatched evidence
fails closed, and scope/package digests cannot be substituted. The course
report uses `activitiesAssessedRows` separately from actual recorded
`activitiesFullyModelReviewed` and `modelConsensusPassActivities`.
It always reports `courseReleaseReceiptValidated=false` and
`publicationAuthorized=false`; separate exact-package full receipt,
deterministic browser/privacy/CI and genuine model evidence remain necessary.
The output exposes no original generated activity texts, private file paths,
model rationales, credentials or learner information.

Dedicated source-free regressions in `tests/test_v3_course_readiness.py`
cover the exact frozen six authentic repository packages, ambiguous broader
directory, bad scope, optional private checkpoint, tampering, and normal CLI
contract. They do not claim a real student pilot or AI review PASS.

## On-the-fly frozen course-scope recovery (BSA-20261113-154)

The earlier BSA-153 course-level checker required operators to repeat
`--sections 1,2,3,4,5,6`. That repaired an unsafe nine-section directory
scan, but introduced a recurring manual selection step and still allowed
another existing six-number set to replace the approved campaign.

**The normal command now automatically resolves the frozen scope:**

```powershell
python scripts/check_final_acceptance_closure.py --course-dir content/chapter-9
```

For any `content/chapter-N` with a tracked, compatible immutable candidate
roster `docs/acceptance_closure_chapterN.json`, the shared
`v3_course_readiness._approved_frozen_scope` reads only its
`frozenCandidates` **section identities**, **activity counts**, and
**package SHA-256** values. It rejects a malformed/unfrozen manifest,
duplicate/unknown candidates, missing package, changed bytes/count,
wrong chapter/section directory name, and an explicit `--sections` override
that differs from the approved roster. This ensures recovery works for new
approved chapter rosters of the same type without hardcoding 9.1–9.6.

The Chapter 9 file currently contains precisely six frozen candidate
identities, all **6/6 matching** the original unchanged package bytes, while
the directory contains nine tracked sections. The scoped read-only report
covers 9.1–9.6 and **108 activities only**. If a later authorized repair
changes the bytes or versioned campaign, the checker must fail closed and
require a separately established **new version-bound approved roster**.
It must NOT self-update the approved hash, import a previous PASS, or silently
expand to 9.7–9.9. With no approved roster, an overcomplete directory is
not magically treated as approved.

The legacy archive is used strictly as a **machine-readable immutable
selection/identity source**, NOT as historical V2 academic, learner-pilot,
visual, rights or manual-approval requirements. Decision 0036 remains the
current V3 acceptance authority; only genuine two-context model verdicts
and deterministic current-evidence receipts can establish eligibility.

Permanent regressions cover automatic normal CLI recovery, real original
package identities, an independent synthetic Chapter 7 with a nine-section
directory and approved six-candidate manifest, changed SHA/bytes, invalid
frozen manifest, wrong folder naming and conflicting overrides. They are
source-free and do not submit a prompt or trigger a browser.

## Cross-platform immutable package identity (BSA-20261113-155)

The first BSA-154 implementation did not pass hosted Linux CI. Its two
failed tests did not indicate a changed authored question or scope: the
frozen `packageSha256` came from controlled Windows Yoga 6 working files
with CRLF newlines, while GitHub Actions checked out the **same tracked
Git blobs** with LF. This is the established BSA-20261107-127 failure
family, previously fixed in the course-preview roster path.

The shared V3 `_verify_frozen_package_identity` now automatically applies
the read-side remedy for every normal course-status call: the existing
`packageGitBlobSha1` must match the exact LF-normalized Git blob
identity, and the archived SHA-256 must match **either** actual bytes
**or** the deterministic all-newlines-only alternate LF/CRLF bytes.
No other byte changes are tolerated. If the source manifest lacks a
Git blob identity, only exact SHA-256 bytes can pass; do not infer Git
permission or fill a missing hash. Changed content, partial/mixed newline
transformations, forged archival digests, wrong counts and renamed
sections still fail closed. Per-section `frozenIdentityBasis` names
`EXACT_PACKAGE_SHA256` or `EOL_NORMALIZED_GIT_BLOB`, not model PASS.

This action neither modifies the frozen archival roster nor accesses
protected source PDFs, a live browser, reviewer credentials or student
records. The scope remains 9.1–9.6 and 108 activities. New synthetic
regressions reproduce a CRLF-origin frozen SHA with an LF checkout and
reject semantic alteration and altered Git blob identity on an
independent Chapter 7 fixture. Hosted CI failure #43333798461 is
retained as reproducible negative evidence; closure requires successful
exact-head hosted Linux tests.

## Finite generated-text course review dispatcher (BSA-20261113-156)

Earlier incident BSA-20261105-115 established that recurring manual
cross-topic inspection and selection must be replaced by bounded, existing-
evidence-aware orchestration. BSA-152 provided a safe **single-package**
generated-text V3 model-review adapter for externally authorized sessions;
BSA-153/154/155 integrated immutable six-section status. A missing bridge
between them still required manually choosing Sections 9.1–9.6 and each
follow-up review batch.

The shared, normal V3 implementation now consists of:

- `app_generator/runtime/v3_course_review.py::plan_v3_course_review`
  (strictly source-free **read-only** plan): recovers only the frozen
  approved section roster, checks existing signed/exact package identity
  and private V3 progress, and returns one `nextSection` or a terminal
  `dispatchStatus`, without writing a private checkpoint or contacting
  Gemini/ChatGPT. Any unresolved or failed model finding prevents
  launching a fresh course batch until reconciled/repaired under a
  separately versioned, legitimately authorized path.
- `advance_v3_course_review`: with **already authorized, independent**
  model reviewer sessions and explicit generated-text transfer permission
  *externally supplied*, invokes the existing `advance_v3_generated_text`
  for only the next 1–6 activities in one approved package, then
  re-verifies the resulting state. It uses existing private package-SHA
  checkpoints, lock, role circuit and no-replay policy. No API key,
  browser, account, model context or PDF is bootstrapped by this service.
  Without model access it returns `BLOCKED_EXTERNAL_REVIEW_TRANSPORT`
  with no write or external request. A complete course remains
  `PENDING_DETERMINISTIC_RELEASE_EVIDENCE`, not publishable.
- The **existing normal status CLI**
  `python scripts/check_final_acceptance_closure.py --course-dir content/chapter-9`
  calls the read-only planner. It surfaces `nextSection` and
  `dispatchStatus` (and correct source-free coverage) automatically.
  This is a planning signal, not a live transport health probe or an
  assertion that the next external request is permitted.

The source-free six-section dispatcher test uses **synthetic** separate
reviewers and 12 synthetic activities to exercise bounded 1-activity
passes, exact round-robin progression, true idempotent completion,
stop-on-uncertain, stale immutable source refusal and no-provider/no-
transfer side-effect refusal. Real Chapter 9 packages are inspected
read-only **only**; no fake V3 review appears in the authentic private
state. Historical source-PDF campaigns remain frozen under Decision 0028.
The independently established authorized Gemini/ChatGPT two-context
transport remains the external completion dependency.

## Source-free historical Gemini existing-login provider (BSA-20261113-158)

The existing course-level entrypoint `advance_v3_course_review` now accepts
an **optional** `session_factory` and the default-false
`external_operation_authorized` admission guard. When a reviewer operation
has been independently approved by the external execution authority, a caller
can provide `V3ExistingLoginSessions` with the same approved intent,
verified generated-content-only transfer and an existing already-authenticated
controlled Gemini profile on Yoga 6. The normal dispatcher validates the
frozen next section, package identity, permissions and batch limit BEFORE
entering the provider, then receives two fresh `ReviewerSession` contexts,
invokes the unchanged immutable V3 assessment engine, and closes only newly
owned browser tabs in a finite context. The provider **never** attaches any
source PDF, uses an author Gem, extracts cookies, copies model responses to
Git or retries possibly submitted requests.

**Do not run it under the previous rejected tool operation or assume that a
local Boolean, history of Gemini success, existing login, user approval or
this code change is a platform authorization grant.** The historical source-PDF
reviewer factory is *not* the V3 factory. If the external operation has not
been separately authorized, leave the factory unavailable and pass no
sessions; normal dispatch returns `BLOCKED_EXTERNAL_REVIEW_TRANSPORT`
without opening Chrome. No automatic account swapping, alternative device,
permission-policy changes, request replay or model-health probe are implied.
The new regression tests use fake browsers and synthetic verdicts; they are
not genuine Section 9.1 evidence.

The safe approved-operation constructor is
`app_generator.gemini.v3_existing_login_sessions.V3ExistingLoginSessions`;
the normal entrypoint is
`app_generator.runtime.v3_course_review.advance_v3_course_review`.
Existing `sessions=(...,...)` injection remains compatible. Do not publish
until the actual external authorization decision and real two-context receipts
have been independently verified.

## Decision 0038 — Gemini exclusively for both V3 reviewers

The owner explicitly removed ChatGPT from the V3 two-context assessment
mechanism. Two distinct `gemini_browser` sessions (physics adversary and
language/learner adversary) are mandatory. Mixed Gemini/ChatGPT, ChatGPT-only,
unknown or unlabelled reviewer contexts are rejected BEFORE any model request
or private checkpoint. Existing approved-session injectors must provide
`provider_id="gemini_browser"`; `V3ExistingLoginSessions` supplies that
metadata automatically. New per-role claims and aggregate review rows persist
`providerId="gemini_browser"`, which is checked during bounded resume,
read-only course status and private automated release verification. Older
unattributed receipts cannot be recast as Gemini reviews.

The owner guessed that the prior external tool denial might have originated
from ChatGPT, but the historical evidence does **not** verify that cause.
Changing the model-provider contract cannot itself authorize a denied
authenticated-browser operation. The existing strictly finite, permission-
gated source-free Gemini transport remains dormant unless independently
authorized. All actual Chapter 9 reviews remain pending until real Gemini
receipts exist. Regression coverage includes policy mutation, ChatGPT-only,
mixed pair, missing provider, tampered saved evidence and no-state/no-call
negative controls.

## BSA-160 — automatic Gemini browser frame normalization

The historical shared `GemConversationPage.ask` yields a complete
`BEGIN_JSON` ... `END_JSON` frame, but the strict V3 four-dimension
assessment parser accepts a bare JSON object only. Earlier V3 fake browser
tests returned bare JSON and did not catch this genuine integration failure.
`V3OwnedGeneratedConversation.ask` now unwraps **exactly one completed
frame** locally before returning, and the existing V3 schema checker
still validates every property. It rejects malformed, incomplete,
multiple or prose-wrapped frames; no Gemini request is resent. The
normal `advance_v3_course_review` path exercises this automatically.
Source-free negative controls first failed on the real-format frame,
then passed after the fix. This closes a code-format blocker, not the
independent host execution authorization or missing real V3 assessments.

## External execution dependency: one-time support escalation, not another model recovery loop

The owner authorized pursuit of a reusable approved Gemini-only execution
path. No internal code change or model/prompt retry can grant external
platform authorization. The current appropriate escalation is the account
holder's OpenAI Support chat at https://help.openai.com/ using the
**prepared, not submitted** private Yoga 6 file
`V3_GEMINI_ONLY_OPENAI_SUPPORT_SUBMISSION_20261113.md` (private Yoga 6 project-continuity folder).
The request explicitly asks for the exact operation, platform decision ID,
permitted execution tool and whether permission may persist for subsequent
bounded batches. When a *new* Remote Desktop Commander tool call itself is
client-blocked and an unchanged retry is also blocked, use the first-party
`review_device_call` with those precise arguments/error instead. Never
invent an original blocked-call payload or invoke a similar operation in an
attempt to obtain that payload. Until a real decision arrives, keep
`BLOCKED_EXTERNAL_REVIEW_TRANSPORT`, 0/108 genuine V3 reviews and no public
release. See `docs/EXTERNAL_EXECUTION_RUNBOOK.md`.

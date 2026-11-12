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
silently truncate extra packages. Use the *existing normal status script*
with an explicit selection:

```powershell
python scripts/check_final_acceptance_closure.py --course-dir content/chapter-9 --sections 1,2,3,4,5,6
```

Without `--sections`, a nine-section directory against the default expected
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

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

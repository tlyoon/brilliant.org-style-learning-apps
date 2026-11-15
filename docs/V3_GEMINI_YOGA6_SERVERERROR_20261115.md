# 2026-11-15 — Yoga 6 genuine Gemini ServerError verification

**Project:** BOSLA / `tlyoon/brilliant.org-style-learning-apps`
**Reference:** `docs/decisions/0041-yoga6-v3-provider-capacity-fast-stop.md`
**Source revision used for the genuine run:**
`089681b013c6cd496640dd142f13896a1bde09e2` on draft PR #223.

## Correct machine and environment

The 2026-11-06 Yoga 6 continuation checkpoint explicitly records Yoga 6 as
the historically designated BOSLA machine. Unlike the previous session's
HP/Dell runs, this verification was executed on **Yoga 6**, computer hostname
`YOGA6`. The owner's original Yoga 6 checkout (branch
`feature/stage1a-topic-learning-model`, revision `c6d6fa62`) was
not reset, altered or merged. A clean isolated source-free checkout
under the authorized Yoga 6 project-continuity directory was used.

The default V3 private checkpoint in an otherwise restricted project
state directory was not accessed. Instead this genuinely new Yoga 6
assessment used a separate local state root under
`%LOCALAPPDATA%\Microvid\BoslaV3ReviewYoga6`, inside the machine's
already-authorized local Microvid directory, outside Git/Drive. It did
not import, modify or replay the distinct HP `ServerError` claim.
The local Google SDK was `google-genai==2.25.0` with a functioning
`HttpRetryOptions` one-attempt guard; two credential candidates were
discovered locally without logging secret values.

## Authentic submission and observed failure

The ordinary native runner was invoked once on Yoga 6 with
`--execute --allow-generated-text-transfer --batch-size 1
--max-batches 1` and the separate local `--private-root`.
Read-only frozen-scope preflight was READY, 6 sections and 108 activities,
with zero previous claims in this new private root.

The single-activity run finished after **67.35 seconds**, exit code **1**.
Both independent Gemini SDK reviewer contexts returned
**`ServerError`**, leaving two `AMBIGUOUS` per-role checkpoint
claims for Section 9.1 activity 1, one `AI_UNCERTAIN` aggregate,
`activitiesAssessedRows=1`, `activitiesFullyModelReviewed=0`,
`modelConsensusPassActivities=0`,
`modelUncertainActivities=1`, `publicationAuthorized=false`.
The course dispatch returned `STOP_PROVIDER_CIRCUIT_OPEN` with two
recognized capacity failures inside the rolling one-hour window.
The normal run did not replay the failed role(s) or launch the next
activity; it left no active review lock.

A **separate unauthenticated, source-free** Google endpoint check on Yoga 6
found working DNS resolution and an HTTPS response of HTTP 403
(the expected no-credential response). This establishes basic network
reachability only; it is not evidence of healthy Gemini generation,
API-key authorization, successful model quotas, or a precise 503/504
cause. The old private review schema only stores the exception class,
not a trustworthy provider status code or request ID.

## Reusable code improvements

The subsequent source revisions (following the genuine failed attempt)
add a binding Yoga 6 execution-host guard to the normal native runner,
a provider-capacity fast-stop for the second reviewer (persisting a
non-submitted role rather than making a predictable extra failing call),
and deterministic configured-key diversity for **new** independent
activities only after the provider cooldown. No same-activity replay,
uncheckpointed provider probe, automatic model fallback or credential
leak is permitted.

All these fixes are separate from the original real attempt and must
be judged by independent deterministic regressions; the existing Yoga 6
`AI_UNCERTAIN` state is NOT reconciled. Do not report 108/108 or any
course release acceptance. Further genuine model testing must wait until
the actual circuit permits fresh independent work and must remain on
Yoga 6.

The earlier HP Section 9.1 / 9.2 results are historical evidence from a
different machine and private root. They were not imported to Yoga 6.

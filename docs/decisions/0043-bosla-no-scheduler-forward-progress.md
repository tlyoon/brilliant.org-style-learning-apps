# Decision 0043 — in-process automatic recovery and forward progress

Date: 16 November 2026. Project: Bosla. Authorized host: Yoga 6.

Owner directive: remove the Yoga 6 30-minute scheduled task, and make six-step automatic recovery / forward progress an executable normal-workflow property. This supersedes Decision 0042 Step 2's scheduler approach. All older schedule observations remain historical only.

## Executable implementation

1. The actual Windows task BoslaYoga6V3Recovery was disabled and unregistered, with an independent absence check. scripts/install_yoga6_v3_recovery.ps1 now refuses -Install; its inspection and -Uninstall paths remain.
2. The existing normal scripts/run_v3_yoga6_recovery_worker.py now accepts --auto-advance. It uses app_generator/runtime/v3_forward_progress.py to loop through independently eligible frozen activities during ONE running authorized invocation. Each step calls the unchanged one-activity reviewer with its Gemini-only reviewers, host guard, immutable role claims, source-free metadata diagnostic, cooldown/circuit and existing content/QA/authorization gates.
3. Each attempted dispatch is preceded by a durable PRE_CALL checkpoint. It contains only sanitized counters, exact frozen six-section package roster SHA256, stage, monotonically numbered update and checksum. No keys, prompts, source passages, model text, student records or transferable authorization are persisted. Atomic file replacement and an OS-released run lock protect process restarts and concurrency.
4. After an interruption, an existing PRE_CALL can advance only if validated independent model checkpoints show one new assessed activity, OR if the existing frozen course planner quarantines the old section and independently selects a different eligible section. The old possibly accepted request is never replayed. If neither proof exists, it stops closed.
5. Known provider capacity, quota, ambiguous role, content repair, release QA and unknown statuses are classified before any new provider request. Content-specific FAIL never becomes PASS. The original frozen package and earlier decisions remain unchanged. The normal stage may move to another independent section.
6. Each invocation requires both explicit --execute and --allow-generated-text-transfer flags. The maximum is 1–6 newly attempted activities per invocation with a 30–3600-second elapsed check BETWEEN calls; underlying SDK timeouts still apply to each model call. The worker does not automatically merge, publish, refill a paid budget, create a scheduler or run forever.

The new mode is invoked explicitly from the standard normal entrypoint:
    python scripts/run_v3_yoga6_recovery_worker.py --auto-advance --execute --allow-generated-text-transfer --max-forward-activities 4 --max-forward-seconds 900

Without both execution and text-transfer authorization flags, this mode exits before any paid request or private checkpoint. A time-bound or budget-bound invocation ends cleanly; there is no background time-based restart.

## Recovery evidence and outstanding blockers

Incident BSA-20261116-172 links BSA-20261115-168, BSA-20261115-166 and BSA-20261115-171. The previous scheduled mechanism performed one activity per invocation, forcing another timed tick after success and leaving no crash-safe in-process forward progression. The new code directly addresses that failure rather than requiring another user prompt.

The source-free adversarial test suite covers one-invocation multi-activity completion, simulated full six-section 108-activity progression across finite sessions, restart reconciliation, lost provider response, old ambiguous claim, safe cross-section quarantine, false-next-section evidence rejection, trilingual content FAIL, 429/circuit budget, concurrency lock, forged checkpoint, no publication and no paid operation without explicit permission. A Windows symlink test may skip when the OS does not permit symlink creation. A genuine read-only Yoga 6 course snapshot was 52/108 assessed, 51 fully reviewed, 50 Gemini consensus PASS, one historical Section 9.1 uncertain, one Section 9.2 trilingual repair required, and Section 9.5 next. No additional live API call was initiated in this milestone.

Current final V3 completion remains open. Successful model assessment of all required revised activities, correct versioned repair, deterministic browser/privacy/QA and release checks must pass on real evidence. The Batch API keyed-file adapter has source-free tests but no live provider result-to-review-checkpoint acceptance yet.

## 16 November 2026 — BSA-174 source-free repair handoff

The existing normal auto-advance worker now includes app_generator/runtime/v3_auto_repair.py as an executable source-free stage before new reviewer dispatch. It reuses the exact-identity Section 9.2 correction rule confirmed under BSA-173, checks both genuine historical Gemini reviewer identities and the frozen original SHA, and stages the versioned private candidate idempotently. The forward controller persists the recovery stage, confirms original review counters remain unchanged, and continues to the next independent eligible activity in the same explicitly authorized bounded process. This avoids another user-driven repair instruction. Unknown/revised content, ambiguous original requests and cost/QA boundaries remain fail-closed; no public release or scheduled task is created. See docs/V3_AUTOMATIC_REPAIR_FORWARD_HANDOFF_20261116.md and BSA-20261116-174.

## v6.0 persistent-recognition amendment (16 November 2026)

BSA-20261116-177 replaces direct hardcoded Section 9.2 repair selection at the normal Yoga 6 entrypoint with an allowlisted, version-controlled recurrence registry dispatcher. For the known verified locale failure it reads active BSA-173/174/175/176 records, validates exact handler identities, executes the existing idempotent private repair, persists an integrity-checked source-free incident/remedy receipt, and hands off immediately to the next eligible stage under the same finite, explicitly authorized runner. A retired remedy stops that repair but does not falsely block unrelated safe sections. A new unknown failure gets a classified, non-PASS, source-free decision for future engineering, never arbitrary code execution. Crash-after-repair-before-review, tampered checkpoint and regressed historical entrypoint tests are mandatory. The no-scheduler/no-unbounded-paid-operations contract remains unchanged. Full V3 scientific review and release evidence are still required.

## 16 November 2026 — exact-slice corrective reviewer boundary (BSA-179)

After BSA-178's metadata-only private reviewer handoff, normal v3_recovery_policy now creates an immutable one-activity source-free slice of the corrected Section 9.2 candidate (new SHA, separate role prompt identities) before resuming independent original Section 9.5 work. This avoids a needless 18-activity re-review. An explicit separate scripts/run_v3_revised_activity_review.py command has a source-free dry-run default and reuses the existing Yoga 6-only two-Gemini checkpoint reviewer only when BOTH paid-execution and generated-text-transfer authorizations are active, provider capacity and metadata diagnostic succeed, and no old role claim can be replayed. Corrected-content AI consensus, if later genuinely produced, is NOT the full course's release authorization. See docs/V3_ISOLATED_REVISED_REVIEW_20261116.md and BSA-179. Owner-retired scheduled task stays absent.

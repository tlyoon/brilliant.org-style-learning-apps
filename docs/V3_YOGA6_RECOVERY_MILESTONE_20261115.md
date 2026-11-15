# BOSLA Yoga 6 — scheduled Gemini recovery acceptance, 2026-11-15

**Scope:** owner-approved Steps 1 and 2 in Decision 0042. **Branch:** draft PR #223, unmerged. **Execution source head:** `8f830b39d2ee89389267df6245829c188740b400`. **Machine:** Yoga 6, OS hostname `YOGA6`.

## Historic evidence and protection

On the same Yoga 6 private frozen-course root
`%LOCALAPPDATA%\Microvid\BoslaV3ReviewYoga6`, Section 9.1 activity 1
had two independent `AMBIGUOUS` Gemini `ServerError` role claims from
the earlier real failed run and one `AI_UNCERTAIN` aggregate.
Those claims were NEVER deleted, rewritten, promoted, credential-rotated
in place, or resubmitted. They remain quarantined on identical package
SHA-256 `aa7b82fa8f256d02e7af1bb0ddfa8b91020b82d100175c14a37834eedb51ff7e`.

## Actual source-free model metadata diagnostic

The new one-tick worker's source-free `models.get` request for
`gemini-3.8-flash` returned HTTP **200** using existing configured
candidate index **1** (zero-based). It did not send the activity JSON
or a source PDF. The receipt explicitly classifies
`READY_SOURCE_FREE_ONLY`: metadata reachability is NOT evidence
that `generate_content` has recovered.

## Authenticated scheduled-task live test

Windows Scheduled Task `BoslaYoga6V3Recovery` was actually registered,
with current-user interactive logon, fixed full-path Python executable,
frozen-code worker path, 30-minute recurrence, single-instance ignore-new
setting and 60-minute execution deadline. Initial scheduled time:
**2026-11-15 11:13:22 Asia/Kuala_Lumpur**.

After the durable circuit's `retryNewWorkAfterUnix=1794711153`
(2026-11-15 10:52:33 Asia/Kuala_Lumpur), the **registered Windows
Scheduled Task itself** was manually triggered at
**2026-11-15 10:52:38 Asia/Kuala_Lumpur**. This was a bounded
end-to-end test of the real scheduler action, not a direct Python
substitute for the task. Windows Task Scheduler recorded
`LastTaskResult=0` and `LastRunTime=10:52:38`.

The real private machine-local status report (Unix timestamp
`1794711180`) recorded:

- `status=NEW_ACTIVITY_COMPLETED`, `nativeExitCode=0`;
- `activitiesAssessedRows=2` out of **108**;
- `activitiesFullyModelReviewed=1`;
- `modelConsensusPassActivities=1`;
- `modelUncertainActivities=1`;
- `quarantinedSections=["section-9-1"]`;
- `dispatchStatus=READY_FOR_AUTHORIZED_REVIEW_SESSIONS`;
- `nextSection=section-9-2`, `publicationAuthorized=false`.

Private role-claim metadata confirms Section **9.2 activity 1** added
two fresh `COMPLETE` `gemini_api` reviewer claims (physics and
multilingual semantics), with no leftover per-package review locks.
The **original Section 9.1 activity** retains its two
`AMBIGUOUS ServerError` claims. A separate read-only normal CLI
planning run immediately afterward reported identical course-level
counts, quarantined section and next eligible Section 9.2.

## Deterministic acceptance and what is not proven

- **94/94 focused Python tests** on Yoga 6 passed, including shared
  provider error diagnosis, credential selection, workstation guard,
  immutable V3 role claims, OS-owned coordinator lock, finite campaign
  budget, SDK compatibility bootstrap, and workstation-sync tests.
- Source-free Windows/Chrome learner preview smoke passed for six
  EN/MS/ZH viewport/locale combinations, six screenshot hashes,
  tampered package rejection, 12 source-free pilot-readiness tests
  and one Node multilingual preview suite.
- Lint, recurrence registry/normal-path contract, documentation-impact
  gate and 16 tracked learning-package content-validation checks passed.
- **Not established:** old ambiguous provider request reconciliation,
  complete 108/108 real content assessment, independent scientific and
  translation correctness, learner-pilot evidence, hosted exact-head
  GitHub Actions or release authorization. PR remains draft/unmerged.

The scheduled worker is an actual OS task, which can run without another
ChatGPT request **while the owner's Yoga 6 Windows session is logged in**.
Its first **unprompted** 11:13 scheduled recurrence is not established
by this manually triggered acceptance test. Its normal checks may stop
if future provider capacity, authorization, campaign budget, changed
package, or another live worker prevents new work. This worker performs
review execution/recovery; it does not autonomously merge code or
invent independent educational acceptance.

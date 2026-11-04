# Test plan

## Foundation gates

- All JSON files parse.
- Content packages satisfy structural and semantic validation.
- Publishable subchapters contain the exact required activity distribution.
- Calculator-required and numerical-answer activities are rejected.
- Required multilingual fields are present.
- Course-specific legacy naming is absent.
- Documentation links and protected-file expectations remain valid.

## Vertical-slice gates

- Responsive keyboard-accessible activity player.
- First-attempt and assisted evidence remain distinct.
- Offline submission queue is idempotent.
- Mastery/progression changes have deterministic unit tests.
- Tutor is grounded, bounded, and falls back safely.
- Teacher and student views enforce role boundaries.
- Automated accessibility checks plus manual screen-reader and mobile checks.

## Pilot evidence

Measure immediate understanding, delayed retention, participation/completion, tutor accuracy/usefulness, and teacher-management workload. Do not optimise solely for time in app, streak length, or activity volume.

## Held-out codebase generalization exit (Decision 0029)

The technical app is **not** declared complete merely because a tuned PDF passes, or because synthetic tests or GitHub CI pass. After integrated code and reusable validators are proven, independently precommit three unseen rights-cleared physics PDFs from three distinct topic families. Run all three on the same frozen revision and collect real source/domain, validated-draft, learner-interaction and EN/MS/ZH browser evidence without PDF-specific code changes. Use the source-free metadata evaluator only to audit receipt/identity completeness, never to synthesize real execution proof.

Permitted evaluation: one initial campaign, and at most one additional fresh three-PDF campaign **only after** a documented general code defect and permanent cross-document regression fix. After that record TECHNICALLY_COMPLETE, NOT_COMPLETE_WITH_NAMED_BLOCKERS or BLOCKED_EXTERNAL. Any content with unresolved scientific, translation or diagram meaning stays quarantined regardless of software completion. Preserve separate accessibility, privacy, institutional pilot and publication gates.

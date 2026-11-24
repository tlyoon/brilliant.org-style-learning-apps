# Bosla autonomous development continuation contract — v1.0

Authoritative execution identity: **Bosla**, the Brilliant.org-style learning app, on
the authorized owner **Yoga 6**. This is not MicroGen_AI_Web.

## No avoidable handoff stops

Once any verified step finishes, the normal worker must **immediately execute
the next already-implemented, source-free, eligible milestone**. Reporting
"the next priority is ..." is not itself progress. A conversation interruption
does not change this executable requirement on subsequent worker invocations.

The standard repair/continuation loop is:
historical failure scan -> classify -> reuse registered remedy or add a tested
repair -> real owner-machine test -> adversarial regression -> register permanent
remedy -> checkpoint -> **automatically restart and advance**.

Implemented handoff: `scripts/run_v3_yoga6_recovery_worker.py --source-free-advance`
calls `app_generator.runtime.v3_auto_development_handoff` after signed V28.
The dispatcher has a bounded, explicit allowlist of real source-free successor
stages, currently V29, and continues through additional registered successors
without further prompting. Add further stages to `_TRANSITIONS`, with actual
fixtures and signed receipts, not standalone prose or manual instructions.
A normal worker exit code 0 is allowed only after all registered eligible
successors ran successfully.

## Safe autonomous decisions

- **Advance automatically:** exact source and candidate hashes match; owner
  Yoga 6 source-free test passes; the next stage is implemented, registered,
  authorized, bounded, and has no new rights, cost, or publication side effect.
- **Recover automatically:** classify recurring failure, search the
  `docs/FAILURE_TO_FIX_LEDGER.md` and
  `docs/recurrence_registry.json`, re-run existing fixed repair and regression
  before restarting. Never replace a failed signed receipt or silently replay
  uncertain paid work.
- **Bounded stop:** source identity/version mismatch, failed independent
  academic evidence, untrusted or unrecoverable provider identity, external
  authorization/cost not already granted, remote machine inaccessible,
  forbidden public write/merge, unregistered successor, genuine dependency
  missing, or recursion/cycle/budget violation. Persist a precise reason and
  exact next executable action; **never mislabel this as the whole development
  being completed**.
- **Evidence policy:** textbook fidelity, scientific explanation accuracy,
  incorrect MCQ proposition truth, EN/MS/ZH meaning, and exact rendered
  diagrams are separate. A mathematical model, text quotation, label
  consistency, or SVG DOM geometry never grants full academic PASS by itself.
- **Boundaries:** one chosen textbook; no mandatory external source PDFs;
  original frozen candidate immutable; no publication or PR merge without
  separate release acceptance; no model/API calls in the source-free pipeline.
  Do not claim work continues asynchronously between chat sessions unless an
  actual operating scheduled task exists.

## Quality gate for every newly registered stage

New stages must carry independent source hashes, signed immutable
restart-safe receipts, adversarial mutation tests, failure-to-fix registry
entries, normal-worker integration tests, exact-head GitHub CI, genuine owner
Yoga 6 execution and independent evidence readback. No status `RESOLVED`
without these.

## Current bounded frontier (BSA257)

V29 makes a private, non-released Serway Section 9.1 velocity-vector draft for
the existing MCQ, with abstract markers explicitly identified as a pedagogical
simplification rather than a copied textbook figure. Its new deterministic
renderer exposes only given velocity directions and magnitudes, not the
momentum answer, and compares actual SVG geometry across EN/MS/ZH. The
released candidate and source PDF are unchanged. Full rendered screenshot
scientific meaning, natural-language explanation truth, and remaining
academic proof gates are next; a private draft is **not** the finished app.

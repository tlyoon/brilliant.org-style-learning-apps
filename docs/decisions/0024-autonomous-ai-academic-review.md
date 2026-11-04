# 0024 ? Autonomous AI Academic Review Without Mandatory Human Approval

## Status

Accepted owner amendment, 25 October 2026. Applies to this learning-app project.

## Decision

1. No academic generation, review, correction, QA, or development-continuation
   task requires **manual academic sign-off**, human reviewer credentials,
   or the owner's recurring approval. Human review is optional, not a gate.
2. Independent AI evaluation, preferably using the project's authorized
   Gemini browser workflow instead of paid APIs, performs mathematical,
   scientific, source-alignment, distractor, multilingual and visual review.
   Review contexts are distinct from the authoring session. AI findings
   remain explicitly attributed to AI, not human approval.
3. Exact-source PDF and exact-package fingerprints, independent calculations,
   answer-mapping tests, source-page receipts, visual and interaction tests,
   and falsifiable semantic crosschecks remain mandatory wherever applicable.
   AI model consensus alone does not prove factual truth or textbook fidelity.
4. When an AI reviewer finds a contradiction, the system creates a versioned
   targeted repair and independently rechecks it. When the evidence is
   ambiguous, it preserves a recoverable review/claim and continues other
   eligible work without requesting human academic approval. Ambiguous
   possibly-sent requests must not be blindly resubmitted.
5. Preserve the tri-state academic acceptance ledger: PASS only for adequately
   verified claims; FAIL for demonstrated contradictions; REVIEW_REQUIRED
   for insufficient evidence. REVIEW_REQUIRED describes an **automated
   follow-up queue**, never a requirement for manual sign-off. Never
   fabricate AI agreement, independent proofs, or human consent.
6. Do not weaken the distinct public release gate or infer permission to
   merge, publish, change protected originals, spend on APIs, or disclose
   private source PDFs. Existing git_publish=false and git_auto_merge=false
   remain in force until separately authorized.
7. Preserve exact version-bound private evidence and reproducible handoffs
   across development sessions. No live remote AI invocation is required
   merely to exercise offline contracts and regression tests.

## Compatibility

This clarifies decision 0023, which already makes human review optional for
publication. Older historical decisions requiring qualified human academic
review no longer govern the current academic workflow. Model evaluations
are recorded under aiReviewed, not humanReviewed. Source/semantic evidence
remains necessary for any claim of academically correct content.

## Code paths

- app_generator/validation/autonomous_ai_review.py: independent, bounded
  AI reviewer contracts, source-page and version checking, action classification.
- app_generator/runtime/autonomous_academic.py: per-activity resumable,
  machine-actionable review queue, source/version-bound checkpoints.
- The existing app_generator/gemini/client.py supports reviewer conversations;
  callers must arrange separate fresh sessions and reconcile ambiguous sends.
- Academic publication guard remains in app_generator/runtime/academic_release.py.

## Next acceptance milestone

Execute a genuine authorized two-context Gemini academic-review pilot on the
private v3 Section 9.4 activity, retain receipts outside Git, reconcile any
ambiguous requests, then run deterministic crosschecks. No result may be
promoted to full academic PASS merely because two language models agree.

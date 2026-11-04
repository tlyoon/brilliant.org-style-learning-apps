# Evidence-based 18-activity academic acceptance

## Policy
There is NO mandatory human academic review or sign-off. Each generated
activity gets five separate automated academic gates: original-source
fidelity, answer correctness, physics consistency, rendered visual/scientific
semantics, and English/Malay/Chinese meaning equivalence.

Academic PASS requires genuine independent evidence for every gate.
Successful JSON schema, English/Malay/Chinese text presence, AI consensus,
or an independently located textbook quote alone **never** grants PASS.
Deterministic answer-key defects or invalid visual contracts are FAIL.
Insufficient evidence is REVIEW_REQUIRED with a machine-actionable follow-up,
not a request for manual review.

## Commands and private output
Use scripts/audit_activity_acceptance_matrix.py with the exact private
generated package, exact original PDF, controlled PDF SHA256, optional
private source-packet file and a NEW private output path outside Git.
The audit fingerprints the package and original source. It checks every
MCQ answer-key structure, selection/order/matching/classification answer
mapping, all localized labels, multilingual surface and declarative
visual specification. A private source passage, if available, is
independently located AGAIN in the controlled original PDF. It never
treats an obsolete source packet for another package version as approved.

Only authenticated, in-process, independently written science/source/
visual verifier functions may provide a positive academic PASS finding.
A model statement from JSON, even if both reviewers agree, cannot
fabricate that verifier. Manual reviewer approval is never required.

## Genuine Yoga6 original-source v3 pilot, 25 October 2026
- Exact PDF SHA256: 08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578.
- v3 package exact file SHA256: cd2c17864e155cc870e5ba8f6d3013a0c73e3bf3aa2d22a91834030eaf047fbc.
- All 18 activities audited: 9 MCQs and 9 interactions.
- Correct choice and interaction mapping structure defects: 0.
- Declarative visual-contract defects: 0. These are NOT proof that every
  diagram visually represents the underlying scientific phenomenon.
- One current-v3 private textbook quote independently re-located on PDF
  physical page 2 for int-select-isolated-conditions. The other 17
  source locations remain unverified for this exact package.
- Full academic PASS: 0/18; REVIEW_REQUIRED: 18/18; FAIL: 0.
- Real multilingual *semantic equivalence* and scientific diagram
  correctness have not been demonstrated. No model agreement was invented.
- Original content, private PDF and historical generated assets unchanged.
  No public publishing, protected merges or paid APIs.

Private report location:
%LOCALAPPDATA%/BrilliantContentGenerator/academic-source-evidence/
section94-v3-full-activity-matrix-source1-20261025.json

## Next autonomous work
Acquire and verify original-source passages for the remaining 17 activities,
perform independent proof/falsification for every answer/distractor and
interaction, and use separate Gemini reviewer sessions for complete
trilingual meaning and rendered scientific diagram checks. Retry or correct
individual failures without halting unrelated development. Keep
publicationAuthorized=false unless all protected release gates are
separately met.

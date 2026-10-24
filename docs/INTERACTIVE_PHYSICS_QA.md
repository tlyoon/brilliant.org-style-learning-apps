# Section 9.4: bounded independent interactive physics QA

The independent reference models are in app_generator/validation/interactive_physics.py.
They check nine *installed* Section 9.4 activities, not the distinct checked-in
repository fixture. Source PDF, original content and private receipts are not committed.

A model computes exact rational-number physical examples to test each generated
classification, matching, ordering or selection answer key. A positive result
means the bounded physical answer model agrees with the key. It does not prove
the correctness of all answer wording, distractors, visuals or translations.

Each private witness must bind the exact controlled PDF SHA, page-indexed
textbook excerpt, canonical installed package SHA and unchanged question/
localized item labels. Fixed SHA values for localized narratives prevent
recertification of changed content by simply regenerating a receipt.
Missing/unmatched evidence stays REVIEW_REQUIRED; an incorrect physical mapping
becomes FAIL. No model alone can grant full activity academic PASS.

Reproduce with python -I scripts/audit_academic_qa.py --repo-root REPO
--package PRIVATE_INSTALLED_PACKAGE --source-pdf PRIVATE_CONTROLLED_PDF
--physics-receipts PRIVATE_MCQ_WITNESSES
--interaction-receipts PRIVATE_INTERACTION_WITNESSES.

## Actual pilot verified 24 October 2026
- Controlled source SHA-256:
  08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578.
- Installed package canonical SHA-256:
  2ffe799784c5492b5b8cf2062f7ffaa40264e3933820349b506c39fb651a01f7.
- Nine bounded MCQ subclaims verified in PR #131.
- Nine interactive activities audited: eight bounded physics answer models verified,
  one QUALIFIER_REVIEW_REQUIRED, zero answer-mapping discrepancies.
- The held item int-select-isolated-conditions uses the phrase
  'strictly conserved' for collision momentum under the impulse approximation,
  although small nonzero external impulse gives only approximate conservation.
  Exact conservation requires net external impulse zero.
- No full activity passes: 0/18 academic PASS, publicationAuthorized=false.
  English/Malay/Chinese meaning, distractors, visual semantics and complete
  source-grounded interpretation still require independent evidence.

Private receipts and combined report stay outside Git:
%LOCALAPPDATA%/BrilliantContentGenerator/academic-source-evidence/
section94-integrated-physics-mcq-interactions-20261024.json.

Next: independently investigate the held wording and produce a candidate repair
without changing the installed production package; then verify localized meaning
and every activity's non-numerical semantics.

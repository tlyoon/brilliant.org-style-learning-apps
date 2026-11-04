# Exact-version activity evidence dossier (private)

Purpose: reconcile the independently generated original-PDF academic acceptance
matrix with a bounded-physics witness report for the **same original source,
candidate package and all activities**. This is a prerequisite to independent
semantic/visual review, **not** proof of complete academic correctness.

Example in an authorized Windows checkout:

```powershell
python scripts/audit_activity_evidence_dossier.py `
  --package <private-candidate-package.json> `
  --pdf <controlled-source.pdf> `
  --matrix <private-verified-activity-matrix.json> `
  --physics <private-recomputed-bounded-physics.json> `
  --activity-id int-select-isolated-conditions `
  --out <new-private-report.json>
```

The destination must not exist or be inside the repository. Source quotations,
options, original PDF contents and account information are not written to
GitHub or copied into the dossier. The script checks SHA-256 identities,
per-activity canonical hashes, all-activity coverage, consistent academic
status and non-publication flags. Its inputs must themselves come from
independently executed source and mathematical checks; mere alignment does
not authenticate a forged receipt.

The next action can be AUTO_SOURCE_CHECK, AUTO_REPAIR, or
AUTO_INDEPENDENT_SEMANTIC_VISUAL_REVIEW. Every result remains
`publicationAuthorized: false` and `fullAcademicPass: false` until
separately justified substantive semantic, translation, diagram and learner
behavior checks have passed. AI consensus alone does not certify them.

## Verified Yoga6 example (27 October 2026)

Original controlled Section 9.4 PDF SHA:
`08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578`.
Private corrected v3 package SHA:
`cd2c17864e155cc870e5ba8f6d3013a0c73e3bf3aa2d22a91834030eaf047fbc`.

Fresh matrix inspected the actual PDF: 18/18 source locations verified,
0/18 academic PASS, 18 REVIEW_REQUIRED. The selected
`int-select-isolated-conditions` activity reconciled against all 18
bounded-physics witness receipts and was routed to
AUTO_INDEPENDENT_SEMANTIC_VISUAL_REVIEW. Private reports remain outside Git.
No Google session was attached, no Gemini or paid API called, no public
release or human academic action was necessary.
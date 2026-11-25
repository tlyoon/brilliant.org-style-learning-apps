# Section 9.4: Independent multilingual and distractor QA

## Bounded review contract

The QA engine in app_generator/validation/impulse_semantics.py and CLI
scripts/audit_impulse_semantics.py use exact arithmetic and independently
specified concept checks for English, Malay, and Chinese. This is a bounded
review, not a claim of complete translated semantic equivalence.

Exact original PDF SHA256:
08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578.

Exact private corrected v2 candidate SHA256:
31a52ab461c62d0d9c7e244290b8ec94f3dd105f8056f2a8bb7db2b61cd5967a.

The exact impulse theorem equates change in total momentum with net external
impulse. A small but nonzero external impulse permits approximate, not exact,
momentum conservation. A sticking collision conserves system momentum while
kinetic energy falls. Large external forces can cancel each other: negligible
net external impulse does not imply every individual external force is smaller
than the collision contact force. Nonzero external forces before and after
impact do not determine the net impulse during impact.

## Verified 2026-10-25 Yoga6 pilot

- All five choices examined with independent physical witness checks and
  localized proposition markers.
- Four bounded answer/distractor models verified, one selected item
  REVIEW_REQUIRED: item-large-internal-forces uses a universal individual-force
  comparison that does not follow from negligible net external impulse.
- All 21 localized narrative checks found expected concepts or formulas
  across seven fields and three languages.
- Full translation-semantic equivalence is NOT proven: the concept markers
  are a fail-closed screening tool, not human or independent AI consensus.
- Original candidate remains REVIEW_REQUIRED; publicationAuthorized=false.
  Five academic gate categories remain unresolved and 0/18 activities
  have complete academic QA approval.
- No PDF, textbook source excerpt, auth token or private candidate was
  committed or publicly published.

## Reproduce

Use the authenticated Yoga6 checkout with a new private output path:
python -I scripts/audit_impulse_semantics.py --package PRIVATE_V2/package.json
--review PRIVATE_V2/review.json --source-pdf PRIVATE_CONTROLLED_PDF
--out NEW_PRIVATE_REPORT.json

Private verified report:
%LOCALAPPDATA%/BrilliantContentGenerator/academic-source-evidence/
impulse-v2-multilingual-distractor-audit-20261025.json

The full academic triage supports an optional --impulse-review path, never
turning pre-existing FAIL or unresolved findings into academic PASS.

## Next action

Create an immutable private v3 candidate for the overbroad selected
force-comparison statement with controlled English/Malay/Chinese wording.
Keep its answer key and visual plan intact, rebind the proof hashes and
retest the source-bounded meaning of all five choices. Full semantic
equivalence and visual fidelity must be validated before release.

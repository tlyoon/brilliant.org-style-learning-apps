# Section 9.4 Source-Bound v3 Impulse Correction

## Evidence and provenance
- Repository: tlyoon/brilliant.org-style-learning-apps; parent PR #134, head 97414a70eb52a1e989c51c2c3cb7030ed2e7917a (GitHub CI passed).
- Authorized test machine: Yoga6; isolated worktree: %LOCALAPPDATA%/BrilliantContentGenerator/impulse-v3-stack-20261025.
- Original controlled source PDF SHA256: 08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578.
- Previous private v2 file SHA256: 31a52ab461c62d0d9c7e244290b8ec94f3dd105f8056f2a8bb7db2b61cd5967a.
- New private v3 file SHA256: cd2c17864e155cc870e5ba8f6d3013a0c73e3bf3aa2d22a91834030eaf047fbc.
- New private v3 canonical SHA256: 33828329938512a661fbebd71ef04a830545981878555173bab50c86c3bb5f56.
- Private candidate folder: %LOCALAPPDATA%/BrilliantContentGenerator/academic-source-evidence/review-candidate-impulse-20261025-v3.
- Private audit: %LOCALAPPDATA%/BrilliantContentGenerator/academic-source-evidence/impulse-v3-bounded-audit-20261025.json.
- Raw source textbook, source quotations and all private learning packages remain outside Git.

## Scientific correction
The original selected force-comparison assertion that all individual external forces
must be much smaller than collision forces was not entailed by the impulse approximation.
The exact two-body momentum change equals NET EXTERNAL IMPULSE over the interval.
Opposing large external forces can cancel; small nonzero net impulse permits
approximate, not exact, system momentum conservation.

The reviewed v3 changes only the original item-large-internal-forces label and
matching answerLogic in English, Malay and Chinese. It retains 18 activities,
17 other activities unchanged, original objective, original visual plan,
five choice IDs, and all correctSelections. Exact rational opposing external
forces +1000 and -1000 yield zero net external force despite being individually
larger than a representative contact force of magnitude 1.

## Boundaries and real verification
- Reconstructed exact private v3 from exact private v2 and source PDF, not
  from regenerated Gemini output or a previously attached unverified archive.
- v3 stored with exact UTF8 LF bytes and immutable per-file/parent SHA receipts;
  no existing folders were overwritten.
- Separate verifier reconstructs v3 from trusted parent, not merely compares
  re-signed hashes, checks all five answer choices and three language markers.
- Actual private v3 pilot: FIVE OF FIVE bounded answer models verified,
  TWENTY-ONE OF TWENTY-ONE multilingual concept/formula markers found,
  zero visual-contract errors, seventeen untouched activities.
- Full semantic equivalence, complete distractor semantics, source-to-answer
  textbook interpretation and physical drawing accuracy remain unverified.
  Academic PASS 0/18, academicQA REVIEW_REQUIRED, publicationAuthorized false.
  No human or AI semantic consensus is asserted.
- Existing academic FAIL is never overwritten; submitting both v2 and v3
  receipts is explicitly rejected before either versioned audit.
- Do not merge, auto-install, upload original textbook or publish.

## Reproduction (authorized Yoga6 only)
Run Python in isolated mode with:
  scripts/make_impulse_v3_candidate.py
    --v2-package PRIVATE_V2/package.json --v2-review PRIVATE_V2/review.json
    --source-pdf PRIVATE_SOURCE.pdf --out NEW_PRIVATE_V3_DIR

Then:
  scripts/audit_impulse_v3.py
    --package PRIVATE_V3/package.json --review PRIVATE_V3/review.json
    --v2-package PRIVATE_V2/package.json --v2-review PRIVATE_V2/review.json
    --source-pdf PRIVATE_SOURCE.pdf --out NEW_PRIVATE_REPORT.json

The new directory and report must not exist and must be outside the repo.
Always verify latest branch, source hashes and that there is no competing
writer before running. Do not treat math and lexical markers as a full
translation-quality or visual-semantic certificate.

## Next safe action
Pursue independently verified complete EN/MS/ZH equivalence and source-bound
visual scientific interpretation for the exact v3 output SHA before any full
academic activity PASS. Preserve separate release authorization.

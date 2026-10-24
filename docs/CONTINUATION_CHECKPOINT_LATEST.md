# Latest Continuation Checkpoint — Brilliant-style learning apps

Updated: 2026-10-24 (Malaysia, UTC+08). Verify against live devices, GitHub and run state before any new work.

## Identity, ownership and contract
- Repository: tlyoon/brilliant.org-style-learning-apps. Workstation: Yoga6 via Remote Desktop Commander; no paid API/Work/Codex credits authorized.
- Target: source-grounded multilingual physics learning activities; exact source provenance, deterministic/browser QA, evidence-backed PASS/FAIL/REVIEW_REQUIRED academic QA.
- Contracts: docs/PRODUCT_REQUIREMENTS.md, docs/CONTENT_RULES.md, docs/SECURITY_AND_PRIVACY.md, docs/VISUAL_GENERATION_PROMPT_SPEC.md, app_generator/README.md, and owner-approved academic QA contract.
- PASS must have independent evidence. Missing academic source, answer-semantic or multilingual evidence remains REVIEW_REQUIRED, not automatically human-approved. Public release permission is separate.

## Latest verified development and branching
- GitHub PRs #108–#124 formed the previous unmerged draft stack. PR #124 head 128b618e6dbb6288bda788b66bccb9f3c88a8723, based on #123 head 6b2f57fe3c5349a1ead88ad92e08b6b6ef42dd30; GitHub Actions validation succeeded.
- Current isolated worktree on Yoga6: %LOCALAPPDATA%/BrilliantContentGenerator/academic-qa-stack-20261024. Branch feature/block-unverified-academic-release-20261024 is stacked on #124. Verify new PR/head SHA from GitHub after push; avoid hardcoding a presumed future PR number.
- Protected generation worktree: %LOCALAPPDATA%/BrilliantContentGenerator/feature-test-repo-20260922 (locally modified by generated content); do not reset, checkout, clean, or overwrite.
- Separate older PR worktree: %LOCALAPPDATA%/BrilliantContentGenerator/pr-series-20261023. No competing generation/academic process observed at the start of this segment; recheck before every write.

## Section 9.4 real pilot and acceptance matrix
- Durable run 20261022T132815Z-d248c31122: COMPLETE at 2026-10-23T11:19:07.812188Z; no retry or duplicate generation initiated here.
- Actual installed package: content/chapter-9/section-9-4/package.json, SHA-256 cc45e32383da53ecad4457418a234e54c6f70ae5ba3506203b13b79c717d9620.
- Count: 18 activities, 18 visual plans, 5 validated visual specs. 30 real Chrome desktop/mobile/localization smoke checks passed in previous segment.
- Screenshot evidence: 30 private PNG files plus review-manifest.json in %LOCALAPPDATA%/BrilliantContentGenerator/section94-visual-review-evidence-20261023. Not independently pixel-reviewed.
- Controlled primary PDF source declared SHA-256 08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578, Drive ID 1qFtZ7ZR5RFqLSkVl3VExo_-z9rXzNP0j. Original PDF bytes were not found in the saved run folder: identity and semantic content not proven in this segment.
- Academic QA on actual installed package: 18/18 activities triaged, all five gate types REVIEW_REQUIRED (0/5 PASS, zero proven FAIL). Structural and hash metadata are not textbook accuracy or independent translation equivalence.
- Technical/regression: local 470 Python unit tests passed, one intentionally skipped; 16 content packages pass; Node visual renderer/player/interaction checks pass. No new live published application.
- Governance: git_publish=false, git_auto_merge=false in original pilot config. No public merge or deployment performed; human review not presumed.

## Current hardening unit
- Incident BSA-20261024-001: runtime previously entered Git auto-merge / public deployment after technical/semantic validation without consulting #124 independent academic QA.
- New code: app_generator/runtime/academic_release.py plus integration into app_generator/runtime/orchestrator.py BEFORE Git publisher/public deploy. The adjacent standalone public publisher entrypoint is also guarded in the following stacked draft. Unresolved academic QA blocks automatic merge/public release, preserves draft review and local installation, writes per-run academic-release-gate.json, and rejects stale artifact hashes.
- Focused regression tests: tests/test_academic_publication_gate.py (real Section 9.4 denial, missing evidence, digest mismatch, mode matrix). Full regression 470 tests OK, 1 skip. CI/PR to be verified after push.
- Containment limitation: source-grounded independent answers/translation still missing. Standalone PublicPagesPublisher.publish now has an independent exact-package academic guard. Audit source-branch auto-recovery Git auto-merge as the next adjacent bypass risk.

## Failure and acceptance records
- See docs/FAILURE_TO_FIX_LEDGER.md for dated incident/root-cause records and pending generalizations.
- Acceptance status: source identity PENDING, technical generation PASS, automated schema PASS, browser smoke PASS bounded, academic gates 0/5 PASS / 5/5 REVIEW_REQUIRED, human evaluation NOT CLAIMED, deployment NOT DONE.

## Next executable action
1. Verify Yoga6 connectivity/process ownership, exact GitHub stack/CI and unmodified dirty original checkout; preserve owners' work.
2. Verify draft PR for the current branch, exact head/base SHA, changed files and GitHub CI. Fix CI failures before further descendants.
3. When authorized source bytes are available, implement strict source-anchored physics and translation evidence, with adversarial false-positive checks, and reduce REVIEW_REQUIRED only for independently proven activities.
4. If PDF unavailable, examine direct publisher bypass and exact-version receipts offline; do not falsely pass QA or issue paid Gemini requests.
5. No protected merge, public publication, original-content overwrite or silent background work. Latest owner authorization permits autonomous ordinary coding and draft PRs only.


## Next stack unit: standalone public publisher boundary
- Parent draft PR #125: branch feature/block-unverified-academic-release-20261024, head 61e6de7a0f4750a73df2eb9c55e65d18a1c90c7e, parent 128b618e6dbb6288bda788b66bccb9f3c88a8723. GitHub Actions Validate repository: success.
- This descendant branch: feature/guard-direct-public-pages-publisher-20261024. PublicPagesPublisher.publish enforces academic QA before even looking up an existing merged release PR or invoking any external Git command, using state_dir/academic-publication-gates/{package_digest} for private receipts. A missing state_dir fails closed.
- Actual Section 9.4 negative direct-publisher test proves rejection before remote command and records exact-package QA status; success-path PR-recovery fixture explicitly mocks independent QA to isolate PR idempotency logic.
- Local full suite: 472 Python tests, one skipped; lint and 16-package validation pass. This branch was developed with publication disabled, no original package edits and no remote merge.
- Source-branch recovery path in app_generator/runtime/auto.py may auto-merge source content through GitPublisher.recover_handoff before the later public publisher guard; inspect separately, do not claim it resolved.


## New owned unit: source-handoff merge guard (24 Oct 2026)
- Parent: PR #126, head 62f4f6b42bfdd9298de4f959f9d41656dd6509cc; CI successful.
- New isolated descendant: feature/guard-source-handoff-automerge-20261024. Verify draft PR and hosted CI after push; no original teaching or public assets changed.
- Incident BSA-20261024-004: GitPublisher.recover_handoff converges into _finalize_pr, potentially auto-merging a previously generated source branch before academic verification. The guard now runs at the normal and recovery source PR finalization boundary.
- For automatic source merge, exact local package and manifest must match Git blob identities on the candidate branch (remote tracking ref preferred). Enforce academic PASS for that package before any create/reopen/merge PR call. Absent, mismatched or REVIEW_REQUIRED evidence blocks.
- Draft-only handoffs remain possible. Recovery without a locally available exact package remains safely blocked and may require branch-bound verification; never blindly repeat the Gemini request or declare generated.
- Targeted temporary-Git corruption and missing-evidence tests pass. Full suite: 476 Python tests OK, one intentional skip; lint and 16 packages passed.
- Controlled Section 9.4 Drive source ID 1qFtZ7ZR5RFqLSkVl3VExo_-z9rXzNP0j is accessible as source.pdf (985648 bytes according to metadata); exact bytes, SHA and academic claims remain to be independently checked.
- Next: obtain exact source PDF read-only, verify SHA and develop independent source-grounded academic checks. Preserve source outside public repository.


## Source retrieval and page anchor verification (24 Oct 2026)
- Source PDF recovered **read-only** from exact manifest Drive file ID 1qFtZ7ZR5RFqLSkVl3VExo_-z9rXzNP0j using existing authorized account/session (noninteractive memory-only refresh; no token file overwritten). Private Yoga6 path: %LOCALAPPDATA%/BrilliantContentGenerator/academic-source-evidence/section94-08c450e780e95aab.pdf.
- Actual PDF size 985648 bytes and computed SHA-256 08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578 exactly match the controlled source manifest. This proves source identity, **not the correctness of any activity**.
- Local pdftotext extraction: 9 pages (some font warnings), no source text was committed. Additional semantic/photo verification is still necessary for equations and figures.
- The next stacked draft branch feature/source-passage-anchor-qa-20261024 adds exact-hash and 1-based PDF-page quotation matching in app_generator/validation/source_passages.py and scripts/audit_source_passages.py, with negative tests and no raw book text in standard output.
- Real installed pilot assessment: 18 activities, **0 passage anchors available**, 18 REVIEW_REQUIRED for source passage verification, 0 proved citation FAIL; no academic pass. Future autonomous generation should provide source-specific evidence without public copyrighted quotations.
- Parent PR #127 head 79bfc3105391958a43303b747eb769149392a181. Verify new PR and hosted CI after push; normal release still off.


## Source-page retrieval pilot and direct-CLI regression (24 Oct 2026)
- Descendant branch feature/private-source-page-candidates-20261024 stacked on PR #128 head e91a1b15c2f54e7185ed5d8fc9471ef07583d18c.
- Source-page suggester uses the exact SHA-verified private Section 9.4 PDF, per-page lexical overlap and deterministic ranking; saves hints outside Git. All 18 activities received page suggestions; zero academic verdicts passed. No quoted textbook excerpts, source content or credentials written into the repository.
- Incident BSA-20261024-006: directly invoking new scripts by filename loaded an older editable package rather than current checkout and failed with ModuleNotFoundError. Both source-audit CLIs now prepend current repository root to sys.path; isolated (-I) direct execution regression added. Actual private output produced successfully after fix.
- Private report: %LOCALAPPDATA%/BrilliantContentGenerator/academic-source-evidence/section94-page-candidates-20261024.json. Use only for navigation; never treat lexical similarity as source or academic PASS.
- Verify new draft PR URL/head/CI after commit and push. Continue toward independently verified source passages and mathematical/translation proofs.


## Bounded independent Section 9.4 mathematical evidence (24 Oct 2026)
- New isolated branch: feature/physics-proof-receipts-section94-20261024, based on PR #129, head 52fba0e4cc52b34bbabbe155a0a91baec07a3aef; verify descendant PR and hosted CI after push.
- Controlled original 985648-byte PDF matched SHA 08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578. Actual installed package was bound by canonical JSON SHA 2ffe799784c5492b5b8cf2062f7ffaa40264e3933820349b506c39fb651a01f7.
- Private witness file in academic-source-evidence/section94-independent-physics-witnesses-20261024.json contains 6 curated numeric cases with page-localized original PDF quotations; it must NOT be committed.
- app_generator/validation/physics_proofs.py uses exact rational numbers, validates model inputs, source quotations and package/content identities, and computes independent claims for equal-mass sticking and elastic exchange, Newton cradle, extreme mass ratio embedding, ballistic pendulum two-phase mechanics, and ideal spring energy transfer.
- Actual run: **6/18 bounded propositions verified, 0 failed witnesses, 0/18 full academic PASS**. This is evidence of mathematical consistency of selected propositions only, not validation of every answer, distractor, translation or visual, and does not change release authorization.
- scripts/audit_physics_proofs.py and optional --physics-receipts on scripts/audit_academic_qa.py reproduce and integrate bounded results. CLI output and saved report never expose textbook excerpts.
- Portable adversarial tests cover invalid masses, numeric limits, altered source hashes, changed exact package, wrong source page and broken witnesses. Integrated real QA report remains academicQA REVIEW_REQUIRED and publicationAuthorized=false.
- Remaining substantive work: independently verify remaining 12 activities and complete source-backed English/distractor, visual-semantic and Malay/Chinese meaning checks. Do not infer any activity-wide PASS from these bounded proofs.


## Remaining Section 9.4 MCQ proposition proofs (24 Oct 2026)
- New draft branch feature/remaining-mcq-physics-checks-20261024 is stacked on PR #130, head 527b09b3e05db39bad6fbfa4cb76bce7fd498103. Verify PR and hosted CI after pushing.
- Added independent exact-restitution inelastic example, nonzero-external-force impulse approximation (correctly APPROXIMATE momentum conservation) and one-dimensional elastic relative-velocity exact-identity proof. Verifies three remaining multiple-choice subclaims.
- Reused controlled source PDF SHA 08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578 and exact immutable installed package binding. Private versioned witness path academic-source-evidence/section94-independent-physics-witnesses-v2-20261024.json (never Git commit).
- Actual private report source: academic-source-evidence/section94-bounded-physics-report-v2-20261024.json, 9/9 MCQ propositions verified, 0 failed witnesses, 0/18 full academic activity PASS. Nine interactive questions remain to be model-verified.
- Main safety invariant: no model self-certification or domain-wide PASS. All five academic QA gate categories remain REVIEW_REQUIRED; protected release disabled.


## Interactive model verification milestone ? 24 October 2026
- Branch feature/interactive-physics-model-audit-20261024 on Yoga6, descendant of PR #131 head 9415760becfc1228954b0da5130698c6872eae75. Verify new draft PR/head SHA and hosted CI after push. Isolated checkout only; original materials unchanged.
- Exact controlled PDF SHA 08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578; installed package canonical SHA 2ffe799784c5492b5b8cf2062f7ffaa40264e3933820349b506c39fb651a01f7.
- Reference engine app_generator/validation/interactive_physics.py computes exact collision models and checks all nine installed classification, selection, matching, ordering keys. Real private receipts verify exact PDF page/source passage and localized narrative text hash.
- Real evidence: 8/9 bounded interaction model agreements, 1/9 physics qualifier REVIEW_REQUIRED, 0 mapping discrepancies; nine earlier MCQ bounded subclaims pass. All 18 installed activities remain REVIEW_REQUIRED for complete academic approval, publicationAuthorized=false.
- Private integrated QA output: %LOCALAPPDATA%/BrilliantContentGenerator/academic-source-evidence/section94-integrated-physics-mcq-interactions-20261024.json. Do not commit private quotes/source/credentials.
- Incident BSA-20261024-007: checked-in repository Section9.4 fixture IDs do not match installed pilot. Synthetic test fixtures constructed independently; actual installed evidence checked separately.
- Incident BSA-20261024-008: impulse approximation question feedback says momentum strictly conserved despite nonzero external impulses; exact counterexample gives impulse 1/100000. Candidate fix is pending, not a full academic PASS.
- Incident BSA-20261024-009: potential recertification of changed multilingual wording via newly signed receipts is blocked by immutable localized narrative SHA reference digests; new wording requires new review.
- Next smallest safe action: source-grounded review-only candidate for qualifier and meaningful EN/MS/ZH/visual QA. Preserve installed package and release restrictions.

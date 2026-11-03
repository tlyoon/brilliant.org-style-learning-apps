# Bounded held-out PDF generalization campaign

Decision 0029 replaces repeated PDF-specific code hardening with a **finite test of the general generator**. This is an operator procedure. The new evaluator reads private **metadata only** and never downloads a PDF, invokes Gemini/ChatGPT, browses protected pages, alters a workstation, merges a PR or publishes content.

## Before the first campaign

1. Establish the authorized original-textbook and rights policy; do not upload protected PDF pages or student records to GitHub. Keep original PDF, package, credentials, screenshots and raw reviewer output in private authorized storage.
2. Freeze one exact **40-character Git commit SHA**, active physics domain profile and regression baseline. Record an independent, immutable **source-selection witness** before generating any output. Source SHA-256 and witness SHA-256 values may be recorded, but raw source content stays private.
3. Independently select **three unseen PDFs from three distinct topic families** such as mechanics, electromagnetism and waves/optics. Avoid selecting three sections of the same previously tuned content. The code must already support their subject domain; unsupported-domain results remain blockers, not excuses for PDF-specific exception code.
4. Record the source metadata in a private JSON manifest conforming to the module's strict v1 contract. Every source entry has caseId, sourceSha256, topicFamily, declaredUnseen=true and rightsCleared=true; the manifest has round=1, priorCampaign=null, baselineGitSha, profileId, campaignId and selectionWitnessSha256. **The boolean declarations and witness hash are not independent proof**; preserve external attestations.
5. Run ordinary source acquisition, domain binding, generation, deterministic validation, real interactive learner/browser testing and source-bound academic review under separately authorized permissions. Use the same frozen commit for all three PDFs, and do not alter general code or validators for an individual source. Do not repeat a potentially submitted Gemini or ChatGPT request when its outcome is ambiguous.

## Exactly five technical stage receipts for each PDF

| Stage key | Evidence required for a truthful PASS |
|---|---|
| domain_binding | Actual textbook-level supported domain/profile selection and source-root fingerprint |
| source_ingestion | Exact original source corpus fingerprint and independently checked source provenance |
| draft_schema | Actual generated draft package, content/schema validation and bounded answer-model consistency |
| interactive_learner | Real learner interaction and responsive/keyboard functional evidence, not merely generated HTML |
| trilingual_render | Actual English, Malay and Chinese learner rendering across supported layouts, with localized explanations |

Each PASS has a genuine immutable evidenceSha256. A failed/blocked/not-run stage uses evidenceSha256=null and retains its true state. For a fully completed draft also record exact packageSha256; every case carries the frozen engineGitSha, sourceSha256, academicQA=PASS/FAIL/REVIEW_REQUIRED, bespokeCodeChanges=false and publicationAuthorized=false. This is still *receipt metadata* until independent proof.

The metadata-only evaluation program is:

    python scripts/assess_heldout_generalization.py --manifest <PRIVATE_FROZEN_MANIFEST.json> --results <PRIVATE_VERIFIED_STAGE_RECEIPTS.json> --out <NEW_PRIVATE_EVALUATION.json>

It writes a **new** file only, refuses repository-contained inputs/outputs and never overwrites a previous receipt. Its technicalResult is one of:
- READY_FOR_TRUSTED_PROVENANCE_AUDIT — all three report full stages, but external receipts/source truth/unseen selection have **not** been independently audited by this program
- FAILED_LIMITED_CAMPAIGN — at least one stage FAIL; investigate the general cause rather than add a source-specific test
- BLOCKED_EXTERNAL — at least one stage was explicitly denied (and there was no FAIL); see Decision 0028
- INCOMPLETE — one or more stages not run

It always returns technicalAcceptanceGranted=false, academicAcceptanceGranted=false and publicationAuthorized=false. These are *deliberate* safety boundaries. A separate authorized witness must independently verify PDFs, source provenance, code-frozen execution and real browser records before claiming C3/C4 completion.

## One finite repair opportunity

If campaign 1 exposes a **general software defect** with cross-PDF evidence, allow one reusable code correction protected by a negative regression. Freeze a **new** commit and select three different unseen PDFs for round 2. Round-2 manifests require priorCampaign.receiptSha256, priorCampaign.genericFixRegressionSha256 and a list of prior source SHA256s; any reused PDF is rejected. Do not add document-specific ID or SHA branches to general code.

There is no round 3. After round 2, the campaign is either evidence-backed complete, NOT_COMPLETE_WITH_NAMED_BLOCKERS or BLOCKED_EXTERNAL. Do not extend it automatically. Missing academic acceptance for a *particular* PDF keeps that package private; it is not a perpetual reason to rewrite the generator.

## Closing criteria and next decision

- C1: consolidated technical integration and all standard CI gates (draft PR #222/#223 are not merged merely by passing CI)
- C2: general verifier, reusable tests, private content quarantine and independent academic evidence workflow
- C3: three genuinely unseen PDFs, fixed code, five technical stages each, no bespoke edits, verified external evidence; round 2 only if legitimately required
- C4: independent provenance, browser/accessibility/privacy acceptance and a **recorded finite disposition**

Content-specific independent science, answer, EN/MS/ZH meaning and diagram checks remain mandatory **before publishing that content**. The academic 18x5 matrix for historical Section 9.4 remains distinct; 0/18 formal academic PASS cannot be represented as 18 completed source-semantic approvals. No human academic signoff is forced by this procedure.

## Privacy and truthfulness

Never place the private manifest (which may identify protected sources), original PDFs, screenshots, student details or model responses into the public GitHub repository. The example values in tests are synthetic and **do not constitute a successful real hold-out run**. The run is only complete after an authorized execution actually produces trusted evidence.

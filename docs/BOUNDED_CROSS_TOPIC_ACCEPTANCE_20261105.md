# Bounded cross-topic acceptance workflow — 5 November 2026

**Repository:** `tlyoon/brilliant.org-style-learning-apps`, consolidated draft [PR #223](https://github.com/tlyoon/brilliant.org-style-learning-apps/pull/223).

## Goal and finite stopping condition

Connect the existing source-free learner-coverage and academic-coverage gates in **one one-shot three-topic evidence audit** that reports exactly what was observed and what is missing. No PDF replay, no Gemini/ChatGPT call, no online browser automation, no new held-out C3 campaign, no per-PDF corrections, no merge and no publication.

- The run accepts **exactly three distinct** predeclared topic families (such as mechanics, electromagnetism and thermodynamics) and exactly three uniquely identified source/package digests.
- Code revision is pinned to the **actual inspected 40-hex Git commit**, and each candidate file must match its declared SHA-256.
- The declared caps are `maxCases=3` and `maxChecksPerCase=1`, with `modelCallsAllowed=false`, `pdfReadsAllowed=false`, `publicationAllowed=false`. These values are enforced, not advisory.
- Each case is inspected at most once through the already developed learner and academic evidence validators. A case with invalid evidence is recorded as a fail-closed **category**, not retried. Later cases get their own single inspection.
- The script writes a private, exclusive `started.json` and `disposition.json` under a manifest-hash-specific run directory. A repeat using the same manifest and output root is rejected, even if the previous results are incomplete.
- Every outcome is **terminal**. No `retry`, `resume`, `force`, `next-round`, `auto-fix`, `provider` or `publish` action exists in this command.

## Entry points

- `app_generator/validation/bounded_cross_topic_acceptance.py`: strict schema and pure, deterministic three-case evaluator.
- `scripts/run_bounded_cross_topic_acceptance.py`: private local-file runner, validates paths and digests, enforces commit pin, refuses oversized or linked evidence, creates one exclusive result directory and prints a minimal sanitized summary.
- `tests/test_bounded_cross_topic_acceptance.py`: independent synthetic fixtures across **mechanics**, **electromagnetism** and **thermodynamics**; includes positive metadata-only coverage and adversarial negative cases.

## Required manifest

The manifest is a JSON object with **exactly** the following keys:

```json
{
  "campaignId": "sourcefree-cross-topic-pilot-20261105",
  "baselineGitSha": "0000000000000000000000000000000000000000",
  "mode": "OFFLINE_EXISTING_EVIDENCE_ONLY",
  "maxCases": 3,
  "maxChecksPerCase": 1,
  "modelCallsAllowed": false,
  "pdfReadsAllowed": false,
  "publicationAllowed": false,
  "cases": [
    {
      "caseId": "case-mechanics",
      "topicFamily": "mechanics",
      "sourceSha256": "<64-hex-source-digest>",
      "packageSha256": "<64-hex-candidate-digest>",
      "package": "case-1/candidate.json",
      "learnerReceipt": "case-1/learner.json",
      "academicMatrix": "case-1/academic.json"
    },
    {
      "caseId": "case-electromagnetism",
      "topicFamily": "electromagnetism",
      "sourceSha256": "<64-hex-source-digest>",
      "packageSha256": "<64-hex-candidate-digest>",
      "package": "case-2/candidate.json",
      "learnerReceipt": "case-2/learner.json",
      "academicMatrix": "case-2/academic.json"
    },
    {
      "caseId": "case-thermodynamics",
      "topicFamily": "thermodynamics",
      "sourceSha256": "<64-hex-source-digest>",
      "packageSha256": "<64-hex-candidate-digest>",
      "package": "case-3/candidate.json",
      "learnerReceipt": "case-3/learner.json",
      "academicMatrix": "case-3/academic.json"
    }
  ]
}
```

The zero commit and angle-bracket digest values above are **illustrative placeholders**; they are deliberately invalid until replaced with exact real values. The manifest is not an authorization for new source processing. Paths are **relative** to the chosen private input root and may not contain traversal, Windows drive references, absolute paths or symlinks.

### Invocation for existing, explicitly authorized private evidence

```powershell
python scripts/run_bounded_cross_topic_acceptance.py --manifest "C:\private\cross-topic\manifest.json" --input-root "C:\private\cross-topic" --output-root "C:\private\acceptance-results"
```

Output root must already exist and be **outside the repository**. The command reads the exact candidate JSON and corresponding learner and academic evidence, but does not read, upload or open the original source PDF, and never invokes a model or browser. Restricted private source/evidence data stays out of Git and stdout.

## Disposition taxonomy

| Terminal disposition | Meaning |
|---|---|
| `STOP_INDEPENDENT_VERIFICATION_REQUIRED` | All three case matrices and per-activity learner observations have internally consistent **metadata**, but none has independently verified learner behavior, scientific correctness, EN/MS/ZH equivalence or visual semantics |
| `STOP_INCOMPLETE_OR_INVALID_EVIDENCE` | At least one declared case lacks coverage or carries stale/invalid receipt identity; no auto-repair or replay |
| `STOP_REPORTED_DEFECTS` | At least one accepted academic matrix declares a deterministic FAIL; no further generation |
| `REJECTED_SOURCE_FREE_ACCEPTANCE_RUN` | The manifest, code SHA, paths, prior-run directory or root boundaries fail before any new report can be accepted |

Each case's `status`, `learnerScope`, `academicEvidence`, missing-check count and per-gate outstanding count are included. The terminal receipt always sets `interactiveLearnerAcceptanceGranted=false`, `technicalAcceptanceGranted=false`, `academicAcceptanceGranted=false`, and `publicationAuthorized=false`. A historical self-reported `PASS` is never upgraded into independent academic proof.

## Stage-0 product roster regression closed ? 6 November 2026

The earlier three-case positive fixtures used only **two activities per case**
(one MCQ plus one interactive). They proved the *coverage-metadata loop*
but **not the required publishable learning-product roster**. As a result a
small but internally consistent package could appear as
`METADATA_COMPLETE_PROOF_UNVERIFIED`; this symptom resembles the historical
BSA-20261105-113 and BSA-20261105-115 omissions.

The **same existing** `assess_cross_topic_evidence` evaluator now validates
`inspect_stage0_product_roster` **before** reading learner and academic
receipts. The current product contract is **18** activities:
9 MCQ and 9 interactive; 3 each of easy, moderate and challenging **for
each type**; all unique activity IDs. A mismatched roster is reported as
`INVALID_PRODUCT_ROSTER` with a sanitized
`STAGE0_ACTIVITY_QUOTA_OR_IDENTITY_MISMATCH` category and terminal
`STOP_STAGE0_PRODUCT_CONTRACT_VIOLATION`. This is a product-contract
stop, **not** an invitation to regenerate the old source PDF.

The positive synthetic fixtures now contain all **18** required activities
per topic. Adversarial tests reject two-item packages, wrong difficulty
quotas, missing/wrongly typed data and duplicate IDs even when external
browser counters appear complete. Each report also includes
`declaredVisualSpecCount` and `visualPedagogyStatus`, but **does not
impose an arbitrary visual count** or mistake a declared visual for
independently verified diagrams. The existing academic, technical and
publication flags remain false.

A **read-only, source-free scan of 15 tracked content packages** on the
inspected repository head showed **15/15 matching Stage-0 counts** and
**0/15 with a declared nonempty `visualSpec`**. Consequently the
unresolved visual-interactive educational value is now explicit and
still needs genuine independent evidence, rather than another quota
loophole or decorative image generation. No source PDF/model/browser
request was made. Incident: `BSA-20261106-120`, linked to 113/114/115.

## What this does and does not complete

**Completed in code:** the finite, source-free **orchestration** of the two previously developed gates; evidence identity checking; a strict, bounded, one-shot stopping condition; and three-topic simulated integration and negative tests.

**Not completed or claimed:** independently captured real browser interactions, source-bound physics proof, original-source rights, bilingual/trilingual semantic equivalence, scientific diagram verification, technical C3 acceptance, C4 academic acceptance, project merge or release. The old two-round Decision 0029 pilot remains exhausted and its reported generalization result **FAILED_LIMITED_CAMPAIGN**.

A subsequent **separately authorized, finite real-world acceptance campaign**, if warranted, must begin with fresh non-replayed candidates and independently trusted evidence. This CLI cannot initiate that campaign by itself; avoid reconstructing a third campaign by rerunning the old mechanics/Coulomb/waves PDFs.

**Regression incident:** `BSA-20261105-115`.

# Decision 0030 Phase B — first and terminal acquisition disposition

**5 November 2026. Result: `NOT_COMPLETE_WITH_NAMED_BLOCKERS`.** This report is not a failed physics generation verdict or a new Gemini outage.

## Owner authorization and authenticated precommit

The owner authorized Phase B following [Decision 0030](decisions/0030-final-bounded-acceptance-and-release-closure.md). Exact public MIT OpenCourseWare source identities were committed on consolidated draft PR #223 at `0d1823f8e9a75a48f0b4026d52047737ad7e6768`; GitHub confirmed the commit date `2026-11-05T11:39:32Z`. See [frozen selections](DECISION_0030_PHASE_B_PRESELECTION_20261105.md).

The code baseline remained `2c35da46490061d92ba7f61558cabbc65d4e13c8`. No repository generator code changes were made. The witness preceded the **private campaign downloads and all generator attempts**, although the publicly available PDF landing pages and PDF previews had been checked during selection. Thus this does not establish *blind* independent historical unseen provenance. Original rights are limited to MIT OCW noncommercial, attributed reuse; independent rights to any third-party diagrams are **not** verified, so no public reproduction or deployment is permitted.

## What actually executed

A private, one-shot three-source downloader with `maxPublicPdfDownloads=3` and `noSourceRetries=true` was started on authorized Yoga 6 **after** the witness had been pushed. Its finite result was:

| Frozen case | Public source acquisition | Private source identity and preflight | Generation |
|---|---|---|---|
| `phaseb-momentum` — mechanics | One transfer completed; private 3,012,546-byte PDF retained | SHA-256 `d6c8907971c0678128defc79ccf8d6e7c7c3c2a44761e7b046794716763eed83`; 22 pages, about 3,445 extracted words, no listed rights warning patterns | **Not attempted** |
| `phaseb-gauss` — electromagnetism | Transfer completed, but bytes were discarded by a subsequent preparation-script exception | No retained PDF, no trustworthy source digest receipt | **Not attempted** |
| `phaseb-first-law` — thermodynamics | Not attempted; preparation stopped before third source | No source bytes or digest | **Not attempted** |

After finishing the first case, the new **private acquisition script** appended a record with key `sourceSha256`. When processing the next case, its duplicate check incorrectly looked up `row["sha256"]`, raising Python `KeyError` **before saving the second PDF**. This is a reproducible, topic-independent *local preparation harness bug*, not a model, network, academic, or generator-framework failure.

The campaign stopped immediately and did **not** redownload the second source, reselect topics, change source identities, invoke provider source-free preflight, submit any source-bearing model request, or run Gemini generation. The previously exhausted Decision 0029 campaign remains `FAILED_LIMITED_CAMPAIGN`. No third/fourth PDF was substituted.

## Safe source-free correction, *not* a repeated campaign

The failed private script was preserved byte-identical (SHA-256 `b452388d60d74d1c74770c24fd5f909a5f505b43e7afc3c192142c7eaa94c4dd`). A **nonexecuted private corrected template** fixes only the duplicate-row field lookup to `sourceSha256` (SHA-256 `ddd6a527b21bcb666cd52c1bcbe5caf67dc40a09d1c616322f8333766165a3a7`). A synthetic distinct/duplicate-hash regression and Python syntax compilation passed, without a network, source PDF or model call. The corrected template was **not used to restart or continue** this campaign.

A private exclusive stop receipt was written, SHA-256 `266fcb41c719e9be9b24be391a5519d7e0bae56e587ebb2596932c9af07279f7`. The original start marker, one retained public source PDF, and stop receipt are private; none are in Git. These hashes attest to specific private artifacts, not an independent signed review.

## Binding exit gates and next decision

- **Phase B generalization:** `NOT_COMPLETE_WITH_NAMED_BLOCKERS` — no AI generation was attempted; therefore the result says nothing about whether the frozen generator can solve momentum, Gauss's law, or the first law.
- **C3 real interactive/visual acceptance:** `NOT_RUN` for these sources; no generated learning packages or `visualSpec` to inspect.
- **C4 academic/EN/MS/ZH/source/diagram verification:** `REVIEW_REQUIRED`, zero independent academic PASS.
- **Provider connectivity:** `NOT_CHECKED_IN_THIS_CAMPAIGN`; the blocker is local `SOURCE_ROW_KEY_MISMATCH`, not Gemini HTTP 503/504.
- **Release/merge:** disabled; PR #223 remains draft/unmerged, no publication authorized.

**Stop condition honored:** The frozen one-shot source acquisition failed; this exact campaign is terminal. The one retained mechanics source is quarantined as private input, not advertised as a passing output. A *new, separately approved narrowly scoped decision* would be required to revisit the missing public source acquisition without pretending this attempt never occurred. Do not silently rerun the script, re-download as a workaround, or shift to another machine.

**Engineering interpretation:** There is no evidence of a new production-generator bug. The isolated preflight preparation tool had a mismatched metadata field. The generic corrective template and source-free negative check exist privately; do not introduce a PDF-specific rule into the shared codebase merely to clear this campaign.

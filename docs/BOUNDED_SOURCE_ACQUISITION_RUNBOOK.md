# Generic bounded private source acquisition recovery

**Scope:** finite deterministic preparation of three previously precommitted PDF sources for a *separately authorized* campaign. This reusable source module does **not** generate learning apps, call Gemini/ChatGPT, authenticate scientific content, request external permissions, merge Git branches, or publish.

## What it prevents

The original Decision 0030 private downloader had producer key `sourceSha256`, but the next iteration inspected `sha256`, failing **after** a successful HTTP transfer. The hardened `app_generator/sources/bounded_acquisition.py` now validates the **complete frozen source manifest and field names before the first fetch** and writes the same canonical `sourceSha256` through all results. It also protects against duplicate downloaded content, source swapping, existing-file digest mismatch, untrusted hosts, off-list redirects, insufficient PDF text, detected reuse restrictions and stealth repeated attempts.

**Automatic recovery is deliberately constrained:** verified existing private PDF files are reused without a second fetch; missing precommitted URLs are fetched once each within a fixed maximum. If a network call may have occurred, **no automatic replay** is allowed. Provider/authorization denials, ambiguous model calls, academic falsity and licensing conflicts cannot be automatically "fixed" by altering prompts or selecting another source.

## Preflight and non-public inputs

The private JSON manifest schema version 1 requires exact fields:

```json
{
  "schemaVersion": 1,
  "campaignId": "unique-authorized-recovery",
  "selectionWitnessCommit": "<40-hex-git-commit>",
  "selectionWitnessFile": "docs/DECISION_0030_PHASE_B_PRESELECTION_20261105.md",
  "generatorBaselineGitSha": "<40-hex-git-commit>",
  "priorStopReceiptSha256": "<64-hex-private-stop-receipt-sha256>",
  "previousSourceSha256s": ["<64-hex-previous-source-hash>"],
  "allowedSourceHosts": ["ocw.mit.edu"],
  "maxNewDownloads": 2,
  "modelCallsAllowed": false,
  "publicationAllowed": false,
  "cases": [
    {
      "caseId": "phaseb-momentum",
      "topicFamily": "mechanics",
      "filename": "momentum.pdf",
      "sourceURL": "https://ocw.mit.edu/.../momentum.pdf",
      "reuseLocalPath": "C:/private/existing/momentum.pdf",
      "reuseSha256": "<64-hex-verified-digest>"
    },
    {
      "caseId": "phaseb-gauss",
      "topicFamily": "electromagnetism",
      "filename": "gauss.pdf",
      "sourceURL": "https://ocw.mit.edu/.../gauss.pdf"
    },
    {
      "caseId": "phaseb-first-law",
      "topicFamily": "thermodynamics",
      "filename": "thermo.pdf",
      "sourceURL": "https://ocw.mit.edu/.../thermo.pdf"
    }
  ]
}
```

**The example URLs and digest placeholders are illustrative, not a runnable source selection.** The actual three URLs must already appear unchanged in the committed selection witness. The old private stop receipt must match `priorStopReceiptSha256`. Each reused file must match its declared SHA-256 before acquisition. Input and output roots must remain outside Git.

## Windows invocation

Use an **already existing, empty private output folder**, explicit metadata tool paths and the original stop receipt:

```powershell
python scripts/recover_bounded_sources.py `
  --manifest "C:\private\authorized-plan.json" `
  --prior-stop "C:\private\prior\terminal_disposition.json" `
  --output-root "C:\private\new-empty-recovery" `
  --pdfinfo "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64\pdfinfo.exe" `
  --pdftotext "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64\pdftotext.exe"
```

The tool validates the complete plan, old-stop digest and immutable Git witness. It writes an exclusive `started.json`, per-source attempt markers and success/stop receipts. If all three source hashes, pages, extracts, and rights flags pass, it emits `source_integrity.json` with `ALL_THREE_PRIVATE_SOURCES_ACQUIRED`. This confirms *source preparation only*. Every verified file is retained with an exclusive `*-acquired.json` receipt **before** its suitability check, so borderline or rejected documents are not lost. Source suitability is classified as `PASS`, `BORDERLINE_REVIEW_REQUIRED`, `INSUFFICIENT_SOURCE_CONTENT` or `RIGHTS_REVIEW_REQUIRED`; the 300-word/5-page PASS threshold is **not** lowered by a borderline outcome. Source files remain in the output folder's private `pdfs/` directory and must not be committed.

## No-loop and QA contract

- **Network attempts:** never more than the number of declared missing sources, never a second fetch of a verified reused file. Failed external transfers are terminal for their run.
- **Preflight checks:** exact keys, topic diversity, case/source identity, matching Git witness and prior stop, safe paths, HTTPS allowlist, digest uniqueness, PDF size/magic/EOF, numerical page/word count, and rights-warning flags.
- **Provenance:** no source text, credentials, original PDF bytes or raw HTTP errors enter Git/stdout. Hashes are local integrity checks; they do not certify unbiased source selection or independent source licensing.
- **Generation:** only after a separately safe, exact-code-revision preflight; no implicit model call by this script. Original Decision 0029 and Decision 0030 terminal receipts are unmodified. One source-bearing call per future frozen source is the maximum, and any timeout or ambiguous provider response halts replay.
- **Academic and release:** independent source/math/physics/visual/EN-MS-ZH rights checks remain `REVIEW_REQUIRED` without actual proof. All Git merges, auto-publication and public deployment stay disabled.

**Permanent recurrence:** BSA-20261105-117 in `docs/recurrence_registry.json` references source-free regression tests exercising canonical field names, reuse, network caps, no-replay and fail-closed invalid source and evidence.

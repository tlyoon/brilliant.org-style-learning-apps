# 0031 — Deterministic Source Acquisition Recovery and Future Immunity

**Status: owner-authorized, 5 November 2026.** This is a **new narrowly scoped recovery decision** after the terminal Decision 0030 Phase B acquisition incident. It does not retrospectively reopen or erase Decision 0030's failed one-shot record; it does not authorize retries of any *submitted Gemini source-bearing model call*.

## Failure evidence and scope

The Phase B original one-shot private downloader successfully retained one new mechanics PDF before a deterministic row-key mismatch (`sourceSha256` vs `sha256`) stopped after the Gauss's-law transfer, without saving its bytes. Thermodynamics acquisition never started. Exactly **zero Gemini/model generation requests** were made; no API ambiguity, per-PDF science failure, or third-party reproduction permission can be inferred.

Owner requests that these experiences become permanent **reusable codebase protections**, rather than one-off manual private script modifications.

## Permanent general mechanism

In `app_generator/sources/bounded_acquisition.py` and `scripts/recover_bounded_sources.py`:

1. **Prevalidate before network:** exact manifest and all per-case field keys, three unique topic families/IDs/filenames/URLs, an explicit HTTPS host allowlist and a precise `maxNewDownloads` budget. The historical `sourceSha256` metadata key is canonical in validation, receipt output, hash comparison and tests. Unknown case fields are rejected *before* the first fetch.
2. **Verify immutable preselection:** `git show` the prior committed witness and prove every candidate ID and URL matches it, confirm the frozen generator commit exists, and verify the original terminal receipt SHA-256. Do not use a mutable draft file as the authority.
3. **Automatically reuse sound prior work:** where a candidate's existing private PDF is present, verify exact SHA-256, PDF magic/EOF, bounded size and path, then copy into a fresh private run rather than re-download it.
4. **For missing PDFs only:** issue exactly one HTTPS fetch per frozen URL, never follow an untrusted redirect, enforce size/structure/text thresholds and historical SHA-256 exclusions, capture safe metadata without source text, and write exclusive per-case started/finished receipts. Fail closed on mismatched identity or rights flags.
5. **No ambiguous external replay:** if the network fails, a file is partial, a source digest repeats, upstream execution is denied or a PDF has rights warnings, record a terminal sanitized stop. Do not silently try another URL, device, key, download, model transport or source campaign.
6. **Independent gates:** completing acquisition is not completing generation. The finite Gemini generation budget remains separately bounded to one source-bearing attempt **per source**, with no replay after ambiguous calls. C3 learner and C4 five-gate academic/EN/MS/ZH/visual verification remain independent and do not gain automatic PASS.
7. **No publication:** private PDFs, source text, third-party figures, credentials, raw model output, student data or screenshots remain outside the tracked Git repository. Preserve `git_publish=false`, `git_auto_merge=false`, `public_deploy=false` and `public_deploy_auto_merge=false`. No automatic merge or release.

A test suite must verify the historical wrong-key case is rejected before downloads, one verified reuse plus only two downloads, disallowed hosts and schema, one-shot nonreplay on a second invocation, fail-closed network/duplicate/rights/size behaviors and zero model access. Incident **BSA-20261105-117** locks regression checks in CI.

## Single authorized recovery scope

- **Previous source-selection witness:** `0d1823f8e9a75a48f0b4026d52047737ad7e6768`; tracked `docs/DECISION_0030_PHASE_B_PRESELECTION_20261105.md`. Exactly the same momentum, Gauss's law and first-law MIT OCW PDF URLs; no re-selection.
- **Previously terminal source-preparation receipt:** SHA-256 `266fcb41c719e9be9b24be391a5519d7e0bae56e587ebb2596932c9af07279f7`, stored privately with the prior stopped campaign.
- **Source-generation baseline:** `2c35da46490061d92ba7f61558cabbc65d4e13c8` (not retroactively altered to accommodate individual PDFs). The acquisition protection itself is new source-preparation code, not a physics-specific generator modification.
- **Source 1 mechanics:** reuse only previously retained private `momentum.pdf` SHA-256 `d6c8907971c0678128defc79ccf8d6e7c7c3c2a44761e7b046794716763eed83`; **zero downloads**.
- **Source 2 electromagnetism:** Gauss's law, exactly **one** new public download; verify the PDF SHA-256 and pages.
- **Source 3 thermodynamics:** first law, exactly **one** new public download; verify SHA-256 and pages.
- **Total:** maximum **two** new public source transfers; no other downloads. New unique private root, exclusive durable start/attempt/terminal records. All prior original Phase B files/receipts remain immutable.
- **Provider:** zero Gemini calls during acquisition. Only **after** actual source preflight passes, separately decide whether bounded generation can safely begin; no old source replays and no local models.
- **Rights:** MIT OCW-authored content may be inspected privately and noncommercially under CC BY-NC-SA 4.0 with attribution; individual third-party graphics remain **NOT VERIFIED** and cannot be published.

**Finite terminal dispositions:** `ALL_THREE_PRIVATE_SOURCES_ACQUIRED` (source acquisition/preflight only), `STOPPED_NO_AUTO_RETRY` (with safe failure category), or `BLOCKED_EXTERNAL` (upstream execution denial). Each run is terminal and cannot overwrite or repeat its network effects. Any further preparation after this new recovery would need a distinct owner decision, not automatic looping.

**Authority boundary:** This decision expresses the owner's authorization to close the deterministic blocker with the same precommitted sources and to integrate general safeguards into draft PR #223. It does **not** authorize automatic Git merge, public app deployment, unsafe rights use, PDF-specific repair, or reissuing uncertain model requests.

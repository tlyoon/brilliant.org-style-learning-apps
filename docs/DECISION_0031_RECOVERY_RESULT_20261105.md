# Decision 0031 — verified recovery and source-suitability disposition

**Status, 5 November 2026: all three frozen PDF byte streams are retained privately; two source-suitability PASS, one borderline REVIEW_REQUIRED; no AI generation.** The strictly bounded recovery exited `STOPPED_NO_AUTO_RETRY`, and no further download or model call was made.

## Binding scope and private integrity evidence

- Original source-selection witness `0d1823f8e9a75a48f0b4026d52047737ad7e6768`, [Decision 0030 Phase B selections](DECISION_0030_PHASE_B_PRESELECTION_20261105.md): **unchanged momentum, Gauss's law and first-law URLs**.
- Original stopped one-shot Phase B receipt SHA-256 `266fcb41c719e9be9b24be391a5519d7e0bae56e587ebb2596932c9af07279f7`: **verified and left unchanged**.
- Recovery source-preparation engine committed at `82295a554e36b5b5f645d5a66034cdf2b40cea77`; its exact-head hosted CI [completed successfully](https://github.com/tlyoon/brilliant.org-style-learning-apps/actions/runs/42050511917). Original generator baseline remains `2c35da46490061d92ba7f61558cabbc65d4e13c8`.
- Recovery plan schema prevalidated all three topics and source identities **before** issuing a public request. It had a **two-new-download cap** and one existing local PDF reuse, with no model calls or publication.
- Private manifest SHA-256 `f83e764b1494e792e3419656fa969f33abc9f446ed031b6b21a39fd494bab3a6`; committed-witness file SHA-256 `3b1e799ba6797efbca58eb84ee8b3b08e99087f65930bfc337a478397cdad2df`. Raw source PDFs and receipts remain outside Git.

## Measured outcomes

| Topic | Acquisition observation | SHA-256 of private PDF | Source suitability |
|---|---|---|---|
| Mechanics: momentum | Existing source reused after verifying exact digest; **no redownload** | `d6c8907971c0678128defc79ccf8d6e7c7c3c2a44761e7b046794716763eed83` | **PASS**: 22 pages, ~3,445 extractable words, no listed rights-warning indicators |
| Electromagnetism: Gauss's law | **One** missing-source HTTP acquisition, saved with metadata receipt | `877dbeee27c807d23bdd7da48755aea8b112da3001d72d9154a013c8b0ddc822` | **PASS**: 39 pages, ~5,526 extractable words, no listed rights-warning indicators |
| Thermodynamics: first law | **One** missing-source HTTP acquisition; valid PDF retained, but its eligibility gate refused it | `e8958556f44a718dfce7013d7fe608eca9c38aaca156d490b4764fa1ab0c29c7` | **BORDERLINE_REVIEW_REQUIRED**: 7 pages, ~297 extractable words, no listed rights-warning indicators; below **predeclared 300-word gate** |

The first two accepted-source receipts were written privately. The third source bytes were saved before the suitability exception, but the original version of this runner did not create a success receipt for it. A separate *read-only* verification of all three saved files later checked each SHA-256, PDF signature/EOF and local extraction metadata, and wrote an independent private reconciliation SHA-256 `f1694a5acdc8c2c6d954667fbe370394a5e3d9501d9478ff5a1f13bb4173b9cb`.

The original recovery terminal marker is preserved: `SOURCE_STRUCTURE_OR_RIGHTS_REVIEW_STOP` after the source suitability threshold, with zero Gemini/ChatGPT calls, zero generated learning packages, zero academic approvals, zero Git merges and zero publication.

## Global codebase lesson — not a document-specific workaround

The permanent generic acquisition module now validates all source-row fields, frozen provenance, private prior-stop checksum, explicit HTTPS host allowlists, no-replay budgets and PDF identities **before** network use. It automatically reuses verified private PDFs and records a per-source attempt. It does **not** make a second source/model request after a timeout or failure.

After this run, source suitability is additionally classified as one of:
- `PASS` — satisfies the frozen minimum;
- `BORDERLINE_REVIEW_REQUIRED` — enough text to preserve evidence, but not automatically acceptable;
- `INSUFFICIENT_SOURCE_CONTENT` — below the general extraction floor or too few pages;
- `RIGHTS_REVIEW_REQUIRED` — detected possible third-party/restricted-content markers.

The strict PASS requirement **remains at 300 extracted words and at least 5 pages**. It was **not** relaxed to promote the observed 297-word thermodynamics source. A valid downloaded PDF receives a durable acquired-state receipt **before** suitability inspection in future runs. The change is generic across unrelated topics, guarded by synthetic adversarial tests under incident `BSA-20261105-117`. This prevents the previous error class and distinguishes recoverable local preparation from genuine evidence deficiencies, without an endless per-PDF correction cycle.

## Accurate completion boundary

- **PDF bytes acquired:** **3/3**, verified locally.
- **Source-suitability accepted under fixed Phase B criteria:** **2/3**; thermodynamics requires independent source-adequacy verification, not threshold manipulation.
- **New model/generator execution:** **0/3**, because the prerequisite gate did not pass. No evidence of a Gemini connectivity outage or a failure to generate correct physics has been produced by Decision 0031.
- **C3 real learner/visual acceptance on these PDFs:** not run; no packages exist.
- **C4 scientific correctness, EN/MS/ZH equivalence, diagram meaning and third-party figure rights:** still independently `REVIEW_REQUIRED`. General MIT OCW CC BY-NC-SA private noncommercial-use context is not authorization for public release.
- **Git:** consolidated PR #223 remains draft and unmerged; `git_publish=false`, `git_auto_merge=false`, `public_deploy=false`.

**Finite disposition: `ACQUISITION_CLOSED_WITH_ONE_SOURCE_ADEQUACY_BLOCKER`.** Retain all frozen sources and receipts. Do not repeat network transfers, replay source-bearing calls, silently waive the frozen threshold, or substitute a new thermodynamics PDF. A distinct, independently grounded *source-sufficiency and academic* determination is needed before another bounded generation campaign could be authorized.

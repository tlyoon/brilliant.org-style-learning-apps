# Next three priorities — bounded reconciliation and C4 readiness (4 November 2026)

> **LATER RECEIPTS SUPERSEDE THE ACCESS-BLOCKED STATUS BELOW:** See [the 4 November post-billing reconciliation](C3_POST_BILLING_RECONCILIATION_20261104.md). Actual authorized source-free Gemini requests succeeded with key 2, and the original frozen round-two campaign produced two validated drafts and a third repair-contract failure. The present C3 result is **FAILED_LIMITED_CAMPAIGN**. The source-free readiness-audit code remains valid as a general safety check, but it does not represent the latest execution history.
>
**Repository:** `tlyoon/brilliant.org-style-learning-apps`; draft [PR #223](https://github.com/tlyoon/brilliant.org-style-learning-apps/pull/223). This is **not a new held-out campaign** and does not alter the Decision 0029 terminal result `BLOCKED_EXTERNAL`.

## Priority 1 — Gemini authenticated access readiness

**Status: ACCOUNT ACCESS NOT VERIFIED; offline mechanism checked.** Source-free multi-key automatic failover is part of the shared Gemini client, and previous fake-SDK/CI regression tests establish bounded 401/402/403/503/504 key selection. HTTP 429 and transport ambiguity remain fail-closed. The user reports available credit, which rules out treating exhausted global credit as a proven diagnosis; the old project-specific HTTP 402 and the later remote-execution safety denial are distinct observations.

The prior authenticated remote probe was explicitly denied by execution controls **before execution**. This session did not bypass or reroute it. Neither the presence of key names, an SDK-import check nor public provider status proves actual Gemini account/model access. **Closure:** code mechanism reviewed; live-provider prerequisite remains `BLOCKED_EXTERNAL`.

## Priority 2 — Finite round-two C3 reconciliation

**Status: preparation tooling completed; generation still blocked.** Existing selected topic families are circular motion, Coulomb's law and traveling waves. Round-two engine SHA `7a7b146e16d719576ef7bceea6719fa4153b4a1c`, selection witness SHA256 `9d75f6979a1c20b378603c9919efc53d6540158d3bdb726ff616c48f178abdda`; historic manifest SHA256 `cf56beb7c37af258439ca0dbce727e3c5c0bdd9a4f22993126b7e35bb4fa5fcc`. Private manifest/source bytes were **not** re-opened or copied in this run.

New `app_generator/validation/reconciliation_readiness.py` plus `scripts/audit_reconciliation_readiness.py` is a read-only, source-free admission audit. It checks **explicitly false** publication flags, exact engine identity, a valid claimed round-two manifest and an owner-supplied witness digest. It can report only `OFFLINE_READY_FOR_EXTERNAL_REVIEW`, never technical approval, permission to upload a source, re-run a previously submitted model claim, start a third campaign or publish.

**Real local negative check on tracked `config/configure_project.toml`:** `BLOCKED_OFFLINE` with `PUBLICATION_FLAGS_NOT_EXPLICITLY_DISABLED`, `FROZEN_ENGINE_MISMATCH` and `PRIVATE_ROUND_TWO_MANIFEST_NOT_SUPPLIED`. The project config explicitly enables publication/auto-merge; it is **not** a safe private test config. An authorized private effective config must independently disable all four flags. New Gemini gateway improvements are at a later Git SHA; they cannot be substituted into old frozen receipts.

## Priority 3 — Independent C4 and release decision

**Status: fail-closed readiness safeguards, but no genuine C4 acceptance.** The new checker never reads original PDFs, executes Gemini, opens browsers or validates external scientific/locale meaning. It keeps `geminiAccessVerifiedHere=false`, `sourceAndBrowserEvidenceVerifiedHere=false`, `independentAcademicAcceptanceGranted=false`, `executionAuthorized=false`, `campaignReopened=false`, and `publicationAuthorized=false`, even when synthetic metadata passes all format checks.

Normal CI and prior isolated learner/renderer tests are source-free and do not replace real stage, visual-semantic, keyboard/mobile, English/Malay/Chinese or original rights evidence. No one has newly produced such evidence for the three source PDFs, and historical Section 9.4 remains 0/18 formal independent academic PASS. The branch remains **draft and unmerged**.

## Source-free technical verification

- Focused new `tests/test_reconciliation_readiness.py`: **9/9 passing** on an isolated clone on Yoga 6 inside the existing authorized `%LOCALAPPDATA%\\Microvid` directory.
- Earlier codebase head `ff1e9afa12f5c94a3bad9a35ac9725043e60d680` passed [GitHub Actions #443](https://github.com/tlyoon/brilliant.org-style-learning-apps/actions/runs/41820250603): **969 Python tests, one skipped** and standard JS/validation checks. That CI is **not** exact-head validation of these newly added source-free readiness files.
- Permanent regression incident `BSA-20261104-109` prevents silent removal of the offline release flag/version/witness checks after integration.

## Next legitimate external dependency

Obtain *new* permitted provider-account/model readiness evidence through an **approved** route that does not disguise/replay the operation previously denied. Then reconcile the original immutable round-two evidence and obtain a distinct version-bound authorization if the engine is changed. Actual real-source C3 and independent C4 can continue only under these conditions. Do not make source submission, merge, or publication contingent solely on this metadata-only audit.

**Technical gate:** offline admission checks implemented; **global completion: BLOCKED_EXTERNAL**. No original PDF requests were made, no credentials used, and no release was performed.

# Decision 0075 — Standing owner consent for necessary paid Gemini calls

**Date:** 19 November 2026. **Incident:** BSA-20261119-217. **Host:** Yoga 6.

## Historical failure review

BSA185/206/209 established successful source-bound, one-activity independent two-Gemini review campaigns. The separate 18 November four-activity grant was used exactly once with eight completed reviewer claims. Because those grants were pinned to specific sources and exhausted after the successful campaign, further unreviewed Section 9.1 work became blocked for a new owner permission despite a working Gemini provider and Chrome pipeline. The owner has now explicitly directed that necessary paid Gemini calls for BOSLA code development be continually permitted.

## Revised standing contract

The separate immutable file `docs/v3_standing_paid_gemini_authorization_20261119.json` gives standing consent for new, eligible BOSLA science reviews and new content corrections. It does not expire after any fixed total number of campaigns or paid role calls. No new owner prompt is needed for each subsequent eligible campaign. The older paid charters and all their original hashes, complete role claims, original scientific FAIL and historical uncertain requests remain unchanged.

Every individual invocation is still bounded to at most **four new source identities, eight independent Gemini reviewer roles, and 900 elapsed seconds**; there is no automatic scheduler or infinite unattended spending loop. The ordinary Yoga 6 executable still requires its explicit execution and generated-text-transfer flags. No replay of submitted/uncertain prior roles is allowed; a failed or unknown request is quarantined. Provider denial and scientific correctness are independent gates. A new content revision requires a new source identity and genuine separate reviewer evidence, not a forged PASS. Source PDFs, automatic version admission, merge, and publication remain disallowed.

## Targeted executable implementation

`app_generator/runtime/v3_standing_paid_science.py` reads and exactly checks the standing consent, validates the frozen original Section 9.1 old index 0 uncertain record, isolates eligible unchanged indices 1–17 into atomic source SHA-bound one-item review slices, and uses the existing independent Gemini review engine and durable per-role PRE_CALL mechanism. Genuine saved two-reviewer evidence is revalidated before reuse. Previously completed activities are skipped, and ambiguous prior roles remain quarantined while fresh eligible siblings may advance.

The normal `scripts/run_v3_yoga6_recovery_worker.py --standing-science --execute --allow-generated-text-transfer` first checks genuine source-free 108/698 Chrome acceptance, then submits a maximum of four distinct previously untouched activities via the real V3 two-reviewer transport. On genuine scientific PASS it immediately re-enters source-free staging, integrates the new genuine Section9.1 saved evidence into a NEW unadmitted 108-course proposal, and verifies all 108 activities/698 Chrome checks. It never reopens prior Gemini roles, modifies the original frozen 75 assessed/72 PASS ledger, or grants publication.

## Acceptance plan

Adversarial tests must cover indefinite standing consent versus per-invocation budgets, tampered authorization, no source transfer/execute flags, original index0 uncertainty, source mutation, atomic staged source tampering, fake reviewer callback with no saved actual roles, the first unknown role stop, quarantine of prior incomplete role while advancing eligible siblings, real normal worker dispatch, and refusal of unverified browser receipts. Run repository lint, executable recurrence-contract verification and cross-path suite, commit and pass exact HEAD GitHub CI, then run the genuine Yoga 6 108/698 browser before the first paid call. The first authorized Section9.1 review batch contains original indices 1–4. Successful new reviewer evidence must survive process restart and a new ChatGPT session, with the remedy integrated into the executable recovery registry. Publication and whole-course scientific acceptance remain separate and cannot be inferred from rendered browser success.

# Decision 0044 — New paid Gemini V3 review campaign

**Owner approval:** 17 November 2026, "Proceed with the suggestion. Modify the contract so that paid API call is allowed."

**Status:** Authorized for bounded V3 academic-review operations only. The previously frozen `FINAL_ACCEPTANCE_NO_REPEAT_V2` historical charter is left untouched and still controls its original campaigns and final publication rights.

The executable source of authorization is `docs/v3_paid_gemini_review_authorization_20261117.json`, validated by `app_generator/runtime/v3_paid_review_authorization.py`. The user authorizes Gemini API generation and transfer of generated learning-activity text in a new separately versioned V3 QA campaign on the designated **Yoga 6**. Each run must still opt in with `--execute --allow-generated-text-transfer`.

Allowed review targets: as-yet-unreviewed original frozen activities in Sections 9.3–9.6, plus the exact corrected Section 9.2 activity `act-int-iso-05` using its isolated package and existing original provenance. Per invocation limit: 4 original activities / 900 seconds; corrected activity 1; two distinct one-shot Gemini reviewers per activity. No replay of old uncertain Section 9.1 requests, no extra retry of possibly accepted provider calls, no PDF uploads, no new Batch POST, no scheduled unattended task, no automatic public release, no modification to frozen historical acceptance or scientific QA thresholds. The fixed per-invocation limits are operational bounds, not a guaranteed maximum invoice in any currency; model costs depend on provider billing.

Existing normal, direct and corrected review CLI entrypoints validate this new contract before sending any model request. Authentic reviewer evidence must be retained in private immutable per-role checkpoints and verified by the original four-dimensional V3 rubric. Model consensus PASS is evidence for a particular activity, not full 108-activity or release certification.

An initial REAL authorized paid two-Gemini review on Yoga 6 succeeded, raising original consensus PASS from 50 to 51 and assessed activities from 52 to 53. Bounded auto-advance is separately governed by this contract. Historic V2 policy stays frozen and release rights remain absent.

# 0030 — Final Bounded Acceptance and Release Closure

**Status:** Owner-directed protocol, 5 November 2026. Supersedes no source-replay, private-access, academic-verification, or publication restriction. Implemented as a finite *acceptance protocol*, not as permission for another PDF campaign.

## Decision

Stop feature accumulation and per-PDF optimization. Evaluate the frozen shared codebase against predefined independent evidence gates, then issue one terminal disposition. **Green CI is an engineering result, not proof of effective visual learning, source correctness, EN/MS/ZH semantic equivalence, or permission to publish.** Decisions 0024, 0027, 0028 and 0029 remain binding.

- **Software baseline:** consolidated draft PR #223, inspected starting commit `767dfb382c8af10d9806b3bd0744b91d36dae363`. Retain exact package/code digests, CI artifacts and commit ancestry in every evidence record. No automatic Git merge or deployment.
- **Legacy campaigns:** Decision 0029 round one and round two are terminal; last measured generalization result `FAILED_LIMITED_CAMPAIGN`. Mechanics and Coulomb's law private draft generation succeeded, traveling-waves repair failed. Original receipts are immutable. A fresh campaign cannot be called a continuation, replay or retrospective PASS.
- **Engineering fixes:** permit only a reproducible **cross-topic** application defect with an independently identified failure mechanism and unrelated source-free regression. No source-specific token/figure/answer exception, no fixing an old PDF until it passes, and no automatic next campaign after a failure.
- **No forced human academic review:** independent automated source-bound verification is preferred, with missing or contradictory proof fail-closed. AI claims alone or unsigned QA matrices do not establish independent PASS.
- **Student data / rights / privacy:** no real student identifiers, source PDF bytes, provider credentials, copyrighted source images or private model transcripts may be copied into Git or public CI artifacts.

## Finite Phase A — one source-free learner/browser baseline (approved now)

**Exact scope is frozen before executing:**

| Parameter | Fixed value |
|---|---|
| Candidate | Tracked `content/chapter-1/section-1-1/package.json` — existing local learning package, **not** a new PDF / held-out source |
| Candidate SHA-256 | `c5460f8417e7d451205a6fd911f096b46cd5e665c01b9ccda58172b0ba8ffb96` |
| Browser harness | `scripts/audit_full_learner_browser.py`, pinned to inspected PR #223 software baseline |
| Package roster | 18 activities: 9 MCQ, 9 interactive; 0 declared `visualSpec` |
| Requested execution | One isolated localhost-only headless Chrome run; EN/MS/ZH; width 390 and 1280; 18 x 3 x 2 = **108 independent activity observations** |
| Proof recorded | Package/harness/player hashes; per-check localized prompt, layout, keyboard hint and answer, answer-feedback observations; screenshot SHA-256 per successful check |
| Declared cap | 1 package, 1 audit attempt, 108 maximum planned cases, 8 failed checks before early stop |
| Forbidden | PDF opening/regeneration, Gemini or ChatGPT calls, browser external traffic, retries, overwrite of prior evidence, repackaging, source-specific code changes, auto-merge, publication |

**Pass for this narrow technical test:** 108/108 independently exercised activity/locale/viewport checks; 0 failed/missing checks; 108/108 captured browser screenshot hashes; no horizontal overflow, mismatched localized prompts, keyboard inoperability or missing answer feedback. The saved private receipt is immutable and bound to exact package/player/harness hashes. **Even a full technical pass does not constitute independent artifact review, full accessibility certification, visual semantics proof, scientific/trilingual meaning verification, C3 acceptance or release authorization.** With 0 `visualSpec` activities, this case cannot pass a required **visual-learning acceptance gate**.

**Failure disposition:** record `STOP_BROWSER_BASELINE_INCOMPLETE` with bounded failure categories; do not rerun the same candidate or modify its source to force PASS. A generic app defect may be referred to a *separately scoped engineering decision* only when an independent unrelated regression reproduces it.

## Phase B — one *separately approved* cross-topic acceptance (NOT authorized by Phase A)

A new evaluation, if explicitly authorized, selects three **fresh, rights-reviewed, independently precommitted** topic/source families before inspecting generator outputs: mechanics, electromagnetism and thermodynamics. New sources must not reuse any round-one/round-two originals or previously audited packages. A single fixed generator revision, domain-profile version, selection witness, candidate roster, and SHA-256 for each item must be recorded.

The proposed limits are **three distinct sources, at most one source-bearing generation attempt per source, and zero automatic retries/replays of uncertain calls**. Provider access must be checked by permitted source-free preflight. Stop on the first external execution denial; never route around controls. Do not run this phase simply because this decision exists.

**Independent acceptance conditions (all required; missing means NOT_VERIFIED):**

1. **Technical C3:** source and version identity, validated 18-activity schema, 9 MCQ / 9 interactive and relevant distinct difficulty quotas, and completed generation for all three families without document-specific engine patches.
2. **Actual learner operation:** full per-activity EN/MS/ZH keyboard/touch-equivalent response behavior and mobile/desktop responsive rendering, hint/retry/skip support, authentic screenshot receipts and independently checked browser-session provenance. Aggregate DOM-smoke and asserted counters never suffice.
3. **Visual pedagogy:** for every activity, justify the need for a visual; when useful, a meaningful deterministic `visualSpec` must render and answer-critical semantics must be independently checked. A zero-visual package cannot be called *visual-interactive* merely because its buttons work. Do not attach decorative visuals to meet an arbitrary quota.
4. **Academic C4 (per candidate):** verified right to use exact sources/figures, original-source identity, independent mathematics and physics-answer proof, physical consistency, diagram meaning and independent EN/MS/ZH equivalence. Five separate gates and original proof receipts required. AI-generated QA assertions without corroborating source evidence stay `REVIEW_REQUIRED`.
5. **Privacy and delivery:** no student data in artifacts, restricted assets stay private, no secrets or source PDFs in Git; PR/release controls remain disabled until all required gates and owner-specific release authorization are recorded.

No partial pass across sources may be called a full C3 PASS. Domain-specific academic FAIL quarantines that content without reopening development. An unavailable provider or upstream execution-denial is `BLOCKED_EXTERNAL`, not evidence of wrong physics.

## Phase C — one terminal package-level decision

Report exactly one of:

- `TECHNICALLY_COMPLETE_PENDING_ACADEMIC_OR_RELEASE`: all agreed software/learner technical gates independently evidenced, but content or launch approvals missing;
- `COMPLETE_AWAITING_EXPLICIT_RELEASE_AUTHORIZATION`: all independent technical and academic conditions met; publication still explicitly disallowed;
- `NOT_COMPLETE_WITH_NAMED_BLOCKERS`: a finite technical/academic/visual evaluation ended with exact, evidenced failures or missing receipts;
- `BLOCKED_EXTERNAL`: an external provider, authorization or evidence prerequisite prevents the bounded assessment.

Every disposition must state the exact attempted scope, source/package and engine digests, current PR and CI revision, missing/failing gates, whether any model/PDF/browser call actually occurred, and whether merge/deployment happened. No automatic threshold relaxation, retry, second campaign or PDF-specific enhancement follows. A new scope must be documented as a *new independent decision*.

**Current authorization boundary:** Phase A only is authorized by the owner's instruction to proceed with the recommended browser-first acceptance. Phase B needs separately scoped consent before selecting or processing new PDFs; Phase C reports evidence that actually exists. No release or merge is authorized.

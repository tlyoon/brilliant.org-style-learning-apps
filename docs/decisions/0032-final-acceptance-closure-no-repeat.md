# Decision 0032 — Final acceptance closure, automatic no-repeat enforcement

**Status:** Owner-directed binding BOSLA development decision, 10 November 2026.
Applies to BOSLA (`brilliant.org-style-learning-apps`), especially the frozen
Chapter 9 sections 9.1–9.6 pilot of Decision 0031. Supplements v5.0's
automatic recurrence-recovery contract without overriding original source,
figure, privacy, cost, approval, or historical finite-campaign stop rules.

## Irreversible principle: closure, not another repeated round

**No repeated acceptance campaign without materially new evidence and an
independently justified, explicitly authorized new scope.** A new chat, prompt,
filename, PR, worktree, machine, Chrome profile, browser session, package
directory, repaired harness, or an ordinary "proceed" cannot restart terminal
browser, source-location or academic campaigns, reset exhausted budgets,
or turn missing source-use/rights evidence into permission.

Freeze the set of acceptance gates **once** from approved requirements, without
inventing new gates or relaxing scientific, visual or multilingual criteria.
Each gate must have a scoped evidence-based PASS, FAIL, NOT_VERIFIED,
BLOCKED or NOT_AUTHORIZED state and a finite dependency/stop condition.
When all permitted progress is exhausted, issue
`NOT_COMPLETE_WITH_NAMED_BLOCKERS` and `CLOSURE_STALL`; do not produce another
round of patches, manual approvals, experiments or proposed repeated checks.

An independently reproduced new **shared, critical-path** defect is eligible
for a narrow general repair, which must be baked into the normal pipeline,
with automatic trigger, bounded safe remediation, cross-entrypoint tests,
CI and exact-head evidence. This exception **does not** reopen historic
source-specific campaign attempts or authorize copyrighted model submissions.

## Machine-executable policy, not just instructions

The single frozen gate register is
`docs/acceptance_closure_chapter9.json`.
Shared code `app_generator/validation/final_acceptance_closure.py` validates
the register and enforces its terminal decisions before side effects in:

1. `scripts/audit_full_learner_browser.py` — browser or screenshot run.
2. `app_generator/runtime/academic_source_provision.py` — new local source
   bootstrap; an existing private packet can still be read without replacing it.
3. `app_generator/runtime/academic_generation_stage.py` — source-bound
   academic stage, before model calls.
4. `scripts/run_private_fresh_source_bound_review.py` — external independent
   Gemini review entrypoint, before credential/configuration use.
5. `app_generator/runtime/academic_release.py` — shared autonomous
   publication gate, before academic triage, receipts or any release action.
6. `scripts/build_public_release.py` — alternate standalone public
   bundle builder, before invoking the academic gate or creating files.

Read-only closure status:
`python scripts/check_final_acceptance_closure.py`.

The candidate roster is pinned by the controlled source manifest,
historical package SHA-256 and the **original committed Git blob SHA-1**.
To recognize precisely the same package on Windows CRLF and Linux LF
checkouts, the shared Git checkout identity mechanism (BSA-127/131) computes
the canonical Git object identity from either real representation. It rejects
substantive changes. A raw Windows SHA-256 must never be used alone as a
cross-platform Git identity. Identity drift is a stop, not a new authorized
campaign. The charter
lists **zero** newly authorized campaigns. To reopen a truly fresh eligible
scope, an explicit new decision must first freeze its source/candidate identity,
rights, independent evidence, finite budgets and stop rules, and revise the
charter and tests in a reviewed change. No generic v5.0 invocation constitutes
that permission. Never overwrite or retroactively upgrade old receipts.

## Factual closure status at contract adoption

- Approved six-section scope and original PDF byte identities: verified
  **within their exact frozen versions**.
- Private original local text-location evidence: 9.4, 9.5, 9.6 each 18/18;
  9.1–9.3 source-location campaigns terminal and incomplete. This is not
  independent physics, answer, translation or diagram proof.
- Browser interactions 9.4–9.6: historic 324/324 recorded, but actual old
  screenshot width mismatches mean exact viewport acceptance is **not verified**.
  Historical 9.1–9.3 browser campaigns are terminal.
- External review source/third-party figure rights: **not verified**.
  Physics and answer correctness, EN/MS/ZH semantic equivalence, meaningful
  visual semantics, full adaptive/accessibility/privacy pilot: **not verified**.
- PR #223 is draft/unmerged. Release and deployment: **not authorized**.

An engineering CI pass never closes these domain/pilot/release gates.
Authorized autonomous academic review does not require a human reviewer,
but it must have admissible independent evidence and permitted source use.

## Cross-session continuity rule

Every future BOSLA ChatGPT session should read Decision 0032, the machine
charter, and `docs/CONTINUATION_CHECKPOINT_LATEST.md` before suggesting or
initiating acceptance work. Do **not** assume ChatGPT memory by itself will
preserve this decision. The repository, not recollection or a chat transcript,
is the authoritative durable rule. Never import the rule into unrelated
MicroGen projects.

If the project is blocked, report only the unverified/blocked gate, exact
new evidence needed, terminal disposition and one permissible next action.
The objective is final product acceptance or a truthful terminal decision,
**not another endless loop of "next academic acceptance"**.

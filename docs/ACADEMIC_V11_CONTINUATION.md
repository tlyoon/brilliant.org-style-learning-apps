# Section 9.4 v11 — exact-evidence continuation (no automatic approval)

## Contract

The official academic acceptance matrix still reports 18 of 18 source locations reverified and zero full academic PASS. This document is not a request for human academic sign-off. The project requires independent source-grounded verification of science, answer logic, visual semantics and English/Malay/Chinese meaning before release.

`scripts/reconcile_private_academic_evidence.py` compares the exact original controlled PDF SHA256, exact private package SHA256 and each activity's canonical digest with the official 18×5 academic matrix. Optional source-bound reports are accepted only when their identities and bounded contracts match. It creates an **entirely new private, metadata-only inventory**, never modifies the original source, package, or existing receipts.

### Private inputs for current v11

- Original PDF SHA256: `08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578`.
- Candidate package SHA256: `8218f38eca1601ca0ec97061a5f566caa2e465aef681d8931deb53c90cafae97`.
- Source packets: 18 records that the original-source verifier must separately reverify.
- Academic matrix: `section94-v11-academic-matrix-independent-20261102.json`, 18 REVIEW_REQUIRED and zero PASS.
- Supporting reports from the *same exact v11 version*: MCQ statement physics, collision property grid; technical visual coverage and reviewer claims are optional and may be absent.

Do not copy these private materials, textbook pages, real prompts, credentials or student data into public GitHub commits.

### Private CLI invocation

```powershell
python scripts/reconcile_private_academic_evidence.py --package "<PRIVATE>\package.json" --pdf "<PRIVATE>\section94-08c450e780e95aab.pdf" --matrix "<PRIVATE>\section94-v11-academic-matrix-independent-20261102.json" --source-sha256 08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578 --package-sha256 8218f38eca1601ca0ec97061a5f566caa2e465aef681d8931deb53c90cafae97 --mcq "<PRIVATE>\section94-v11-mcq-statements-pr215-20261102.json" --collision "<PRIVATE>\section94-v11-collision-grid-pr215-20261102.json" --out "<NEW-PRIVATE>\section94-v11-proof-inventory.json"
```

For each activity, the inventory records which bounded evidence exists and the next safe action, without treating mathematical examples as scientific-language PASS. A stale or contradictory supporting report terminates reconciliation rather than being silently ignored.

### Autonomous next-action ordering

1. Reconcile ambiguous/in-flight reviewer claim receipts *without replaying prompts*. The presence of a provider reply is not proof of an independently accepted academic statement.
2. Complete exact-source mathematical and scientific checks, reusing v11 collision/MCQ receipts if their hashes and 18/36 rosters match; do not rerun already verified models.
3. Independently evaluate natural-language explanations and all answer/distractor semantics in EN/MS/ZH, including conservation assumptions, inelastic rebound, external impulse and cradle contact force.
4. Re-review source-grounded scientific meaning of diagrams in each locale and viewport; 30 technically clean screenshots alone do not confer semantic correctness.
5. Feed source-bound, independently falsifiable gate findings into existing trusted-verifier paths; recalculate all 18×5 verdicts. No academic PASS without support from all five gates; preserve `git_publish=false` and `git_auto_merge=false`.

### Boundaries

This code performs metadata reconciliation only. It does not generate model outputs, validate translation meaning, interpret a textbook diagram, independently re-extract the source during inventory or provide ongoing asynchronous execution. The original-source verifier and subsequent independent review still need to run in an authorized environment. The source-free regression tests intentionally reject forged approvals, mismatched per-activity digests, altered option rosters and stale reports.


## 2026-11-03 observed private v11 execution checkpoint

- From the isolated Yoga6 checkout of this draft branch, `tests.test_academic_evidence_inventory`: **12/12 PASS**. Lint, 16 content package validation, and the permanent regression-contract guard also passed.
- The private v11 package, exact original PDF, source academic matrix and previous `section94-v11-mcq-statements-pr215-20261102.json` and `section94-v11-collision-grid-pr215-20261102.json` reconciled successfully with exact hashes, **18 activities / 0 academic PASS**.
- Private metadata-only output (outside repo): `section94-v11-proof-inventory-pr223-20261103.json`. Missing categories: **claims** and **visual**, next action 18 × `AUTO_RECONCILE_OR_RUN_INDEPENDENT_REVIEW`.
- The 30 v11 browser PNG captures and their private manifest exist. A version-bound 18-row private visual worklist and empty **current-v11 run listing** were prepared for auditing. An empty current-v11 listing is *not proof that historical other-version Gemini requests never happened*; those must remain immutable and non-replayable as required by the reviewer contract.
- Execution of the two proposed new private visual and reviewer-claim audit scripts was **blocked by an external execution safety check**. **No new verified visual-coverage or reviewer-claim receipt was produced or accepted** in this step. Never substitute a fabricated record, pretend the attempted audit ran, or route around the execution restriction.
- Hosted CI on the first PR #223 commit passed (workflow #367), but no CI result can certify source-bound scientific/multilingual meaning.
- Once the private execution route is authorized again, the next task is to run the precise existing `scripts/audit_private_academic_visual_coverage.py` and `scripts/audit_private_academic_claim_coverage.py` programs, then rerun this inventory with their successful exact-v11 receipts. Continue with independent semantic gate checks, not another generic evidence-registry rewrite. No publication or merge.

## 2026-11-03 follow-up — evidence substitution and execution scope

**Distinct development regression BSA-20261103-100:** An aggregate of 36 MCQ rows and 9 supported/27 refuted statements is insufficient to admit a receipt. The exact v11 package is now mandatory when any supporting report is supplied. For every MCQ option, the private metadata inventory re-derives its original option ID, canonical EN/MS/ZH label SHA256 and correct-answer versus distractor status from that package; cross-activity visualSpec identity and reviewer next actions are also checked. Source-free adversarial fixtures demonstrate that a forged option, swapped scientific status or reassigned visual capture cannot become accepted metadata. This is **receipt-identity integrity only**, not independent source/translation or visual-science PASS.

A read-only Remote Desktop Commander attempt in the new session showed that the app's allowed file-read root was limited to the connected Google Drive area, whereas original private v11 evidence remained in its original local application directory. No private content was read or relocated. The previously denied private audit operations remain blocked; do not change path, machine, wrapper or client to evade this access boundary. A metadata-only continuity checkpoint was saved in the authorized project continuity workspace, without any source material.

The next scientific milestone remains independent exact-v11 source/answer/physics, EN/MS/ZH semantic and rendered-visual checks for all 18 activities after the needed access is separately authorized. The pre-existing matrix remains 0/18 academic PASS; PR #222 and PR #223 are unmerged drafts; `git_publish=false` and `git_auto_merge=false` remain in effect.

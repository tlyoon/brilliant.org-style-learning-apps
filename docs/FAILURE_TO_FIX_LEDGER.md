# Failure-to-Fix Ledger

| Incident | Symptom and evidence | Root-cause class / permanent mitigation | Status and next action |
|---|---|---|---|
| BSA-20261023-001 | Run 20261022T132815Z-d248c31122 rejected energy-bar relative_amount despite correct numbers | PR #108 aligns renderer schema/prompt with relativeAmount and adds adversarial tests | Resolved in original replay and complete resumed run; retain tests |
| BSA-20261023-002 | Repeated visual generation risk and incomplete saved sibling specs | PR #108 checkpoint reuse with bounded targeted repair, original run now COMPLETE | Reference case resolved; interrupted/ambiguous external responses still need review |
| BSA-20261023-003 | Chrome Enter activation lost MCQ focus; 30 browser failures | PR #116 restored focus; 30 passing browser checks; #117–#118 expanded focus across interaction modes | Tested modes resolved; screen-reader review still pending |
| BSA-20261024-001 | Academic QA #124 returned 5 REVIEW_REQUIRED gates while runtime still allowed automatic publisher path | New academic_release guard before publisher; exact SHA match and real-Section-9.4 regression | Pending new draft PR/hosted CI; audit direct publisher invocations next |
| BSA-20261024-002 | Section 9.4 source PDF bytes not present in saved run and 18 activities lack independent academic meaning checks | #119–#124 conservative evidence triage and status report | BLOCKED ON EVIDENCE, not on mandatory human approval; obtain authorized source and verify claims without fabricated PASS |

## Recovery receipts and protected state
- Latest source manifest SHA: 08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578; package SHA: cc45e32383da53ecad4457418a234e54c6f70ae5ba3506203b13b79c717d9620.
- The completed generation was historical, with no new request submitted in this continuation. No owned active generator seen at start.
- The original generation checkout has uncommitted produced artifacts; use isolated new worktrees only.
- Authorization: Yoga6 RDC + GitHub draft PRs, no paid API calls or public release without verified project gate.

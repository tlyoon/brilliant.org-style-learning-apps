# Context index

## Native Gemini V3 full-course stress and process-loss hardening (13 Nov 2026)

**BSA-20261113-162** corrects a genuinely reproduced normal-runtime defect: a
crashed API worker left a per-role `IN_FLIGHT` request claim but no aggregate
review row, causing the course planner to return false READY. The normal
`app_generator/validation/v3_course_readiness.py` now checks exact orphan
role claims, and `advance_v3_course_review` stops before a new SDK session
when `unreconciledRoleClaims` is nonzero. See
`docs/V3_NATIVE_GEMINI_STRESS_REPORT_20261113.md` and
`tests/test_v3_native_gemini_stress.py` for source-free full 108-activity
campaign, simulated 216 calls, simultaneous-worker, power-loss and failure
matrix tests. No authentic Chapter 9 Gemini model requests were executed.


## Native local Gemini API reviewer — default independent V3 route (13 November 2026)

**Decision 0039 / BSA-20261113-161** (binding) adds
`app_generator/gemini/v3_native_api_reviewers.py` and
`scripts/run_v3_native_gemini_review.py`. Owner-run local execution uses
two stateless Gemini API clients and the **same immutable normal V3 course
dispatcher**, with no ChatGPT remote tool or browser required for each review.
The strict active policy allows `gemini_api` and `gemini_browser` only.
No ChatGPT model is a reviewer; no PDF/student data is sent.
Default CLI is dry-run; real local API work requires explicit two-flag opt-in
and legitimate provider credentials. No model calls were run during this
code-development milestone. Old reported connector-denied operations
remain forbidden to bypass. See
`docs/decisions/0039-native-gemini-api-review-worker.md` and
`docs/V3_AUTOMATED_ASSESSMENT_RECOVERY.md`.

## External Gemini-only reviewer authorization — official support route (13 November 2026)

The exact external-execution approval is still **pending**. See the permanent
`docs/EXTERNAL_EXECUTION_RUNBOOK.md` escalation addendum and the Yoga 6
private prepared-but-unsubmitted support request
`V3_GEMINI_ONLY_OPENAI_SUPPORT_SUBMISSION_20261113.md` (private Yoga 6 project-continuity folder).
A support packet, code PASS or app-level permission setting does not grant
platform approval. A current client-side stopped call, with its exact
unchanged retry also blocked, can use the connector's first-party review
panel. Otherwise the signed-in account holder must submit via
`https://help.openai.com/`. Do not repeat the historically denied operation
with another model, tool, script or device.

## Gemini-only V3 assessment provider (13 November 2026)

**Decision 0038** (`docs/decisions/0038-gemini-only-v3-reviewers.md`)
supersedes Decision 0036 only for the permitted reviewer provider: two
fresh role-isolated **Gemini** browser conversations, no ChatGPT or mixed
provider fallback. Both sessions and durable V3 review evidence must identify
`gemini_browser`, verified by normal review, status and release paths; no
provider attribution may be inferred from unlabeled historical receipts.
This does not override Decision 0028's platform-denied authenticated operation.

## V3 existing authorized Gemini account recovery (13 November 2026)

BSA-20261113-158 connects the historically proven source-free existing-login
Gemini browser ownership, visible account verification and fresh isolated
role tabs to the current `advance_v3_course_review` normal dispatcher via
`V3ExistingLoginSessions`. See `docs/V3_AUTOMATED_ASSESSMENT_RECOVERY.md`.
This is a dormant, separately-authorized generated-text-only provider. It
cannot override an earlier denied authenticated browser operation or attest
current live provider availability; no original PDF is attached.

## Latest owner binding: automatic recovery is normal pipeline behavior (13 November 2026)

Read `docs/decisions/0037-automatic-recovery-normal-pipeline.md`
and `docs/normal_pipeline_recovery_contract.json` before any further
development. Every solved recurring blocker must be detected and safely
repaired or stopped **within the already supported normal execution path**,
with regression and exact-head CI, rather than through assistant-led manual
patch cycles. The ordinary `scripts/check_regression_contract.py` CI
check enforces the machine-readable policy. Continue independently eligible
authorized work without repeated routine owner intervention; never route
around a host safety denial or fabricate genuine model evidence.

## Current binding BOSLA acceptance-closure decisions (11 November 2026)

**READ BEFORE STARTING OR RESTARTING ANY BOSLA WORK:** `AGENTS.md`,
`docs/decisions/0032-final-acceptance-closure-no-repeat.md`,
`docs/decisions/0033-remove-rights-gate-from-technical-closure.md`,
`docs/decisions/0034-rc1-independent-sourcefree-engineering-scope.md`,
`docs/decisions/0035-rc1-provisional-chapter9-draft-player-integration.md`,
`docs/decisions/0036-autonomous-ai-technical-completion.md`,
`docs/V3_AUTOMATED_ASSESSMENT_RECOVERY.md`,
`docs/autonomous_completion_v3.json`,
`docs/rc1_engineering_scope.json`,
`docs/acceptance_closure_chapter9.json` and
`docs/CONTINUATION_CHECKPOINT_LATEST.md`. The machine-executable
`scripts/check_final_acceptance_closure.py` now reports CURRENT
`AUTONOMOUS_AI_TECHNICAL_COMPLETION_V3` status (pending until actual two-model
and deterministic machine evidence). Add `--historical-v2` to inspect the
archived `NOT_COMPLETE_WITH_NAMED_BLOCKERS / CLOSURE_STALL` result.
Frozen Chapter 9 original-source/browser/external-review campaigns are terminal.
The V3 owner amendment expressly removes independent academic content review,
independently certified meaningful visual plans, approved real learner-pilot
evidence and separate manual release authorization as mandatory technical
criteria. Bounded LLM assessments and machine CI/browser/privacy verification
replace them. Decision 0033 also permanently excludes edition/rightsholder/
sourceAndFigureRights as technical gates. Missing/model-uncertain evidence
always means PENDING (not a fake PASS). Automatic release eligibility may be
generated without manual approval after complete verified machine receipts,
but no real student data, source PDF or protected third-party asset transmission
is authorized merely by this document.
RC1 Decision 0034 separately freezes **six entirely synthetic, source-free**
engineering concept nodes and safe local route simulation. It may establish
software functionality, never independent learner-pilot or academic acceptance.
Do not import these synthetic PASS results into the original frozen V2 gates.
Owner Decision 0035 additionally permits a **local draft Chapter 9 player-event bridge**
using the six existing, unchanged package identities; all fresh Chrome and
scoring tests remain synthetic. Actual first-check events are measured, but
key validity, translation equivalence and learner mastery remain NOT_VERIFIED.
No original Chapter 9 acceptance campaign is restarted.

## Authority and precedence

When documents conflict, use this order:

1. `AGENTS.md` — durable operational and safety rules.
2. Current code/schema/configuration on the same `main` revision.
3. `docs/decisions/` — approved product decisions; later accepted records supersede earlier ones, but unmerged proposal branches do not override current `main` behavior.
4. `docs/PRODUCT_REQUIREMENTS.md` — product scope and acceptance boundaries.
5. `docs/CONTENT_RULES.md` and `content/schema/content-package.schema.json` — learning-package rules.
6. `docs/LEARNING_DESIGN.md` — pedagogy, mastery, progression, and feedback.
7. `docs/SECURITY_AND_PRIVACY.md` — data handling and access requirements.
8. `docs/DOMAIN_PROFILES.md`, `docs/ARCHITECTURE.md` and `docs/AI_WORKFLOW.md` — technical design.
9. `docs/DEVELOPMENT_ROADMAP.md`, issues, and pull requests — delivery planning/provenance.

`docs/PDF_TO_APP_QUICKSTART.md` is the canonical current operational walkthrough. `docs/DOCUMENTATION_MAINTENANCE.md` requires operator-visible changes to update canonical documentation in the same PR and adds a CI documentation-impact gate.

Historical roadmaps, old branch-testing instructions, chat transcripts, and copied notes are not substitutes for the documentation shipped with the current `main` revision.

## Task routing

| Task | Read first |
|---|---|
| Short fresh-PC setup and settings editing | `docs/FRESH_PC_QUICKSTART.md`, then `docs/PDF_TO_APP_QUICKSTART.md` |
| Install/setup and first PDF → draft workflow | `docs/PDF_TO_APP_QUICKSTART.md` |
| Verify documentation freshness policy | `docs/DOCUMENTATION_MAINTENANCE.md` |
| Recycle repository for another textbook/project | `docs/GENERIC_PROJECT_SETUP.md`, `docs/DOMAIN_PROFILES.md`, then `config/README.md` |
| Workstation setup/sync troubleshooting | `docs/WORKSTATION_SYNC.md` |
| Continuous auto / multi-PC verification | `docs/CONTINUOUS_AUTO_TESTING.md`, then `app_generator/README.md` |
| Generator CLI/config/coordinator details | `app_generator/README.md`, `config/README.md` |
| Product change | Product requirements and decision records |
| Learning content | Content rules, learning design, schema, source-ingestion policy |
| Diagnose Stage-0 textbook domain selection/binding | Decision 0026, `docs/DOMAIN_PROFILES.md`, `config/README.md`, then `app_generator/README.md` |
| Add or change a subject domain | Decisions 0025-0026, `docs/DOMAIN_PROFILES.md`, then the target `domains/<domain>/` manifest/rules |
| Visual/graphic/simulation activity work | Decision 0024, `docs/VISUAL_INTERACTION_DESIGN.md`, `docs/VISUAL_GENERATION_PROMPT_SPEC.md`, `docs/VISUAL_TOOL_ORCHESTRATION.md`, content rules, learning design, architecture |
| AI tutor | AI workflow, learning design, security/privacy |
| Application code | Architecture, product requirements, test plan |
| Analytics/reporting | Security/privacy, learning design, relevant decisions |
| Release planning | Development roadmap, test plan, current milestone/PR |
| Recurring defect, interrupted run, CI/test stall, external access block or new PR work | Decision 0027, `docs/recurrence_registry.json`, failure-to-fix ledger and current continuation checkpoint before changing code |
| Explicit external operation/security denial or recovery from a denied tool call | Decision 0028, `docs/EXTERNAL_EXECUTION_RUNBOOK.md`, `app_generator/validation/execution_access_recovery.py`; no retry or bypass |
| Freeze per-PDF hardening, measure generic readiness and bounded unseen-PDF completion | Decision 0029, `docs/HELDOUT_GENERALIZATION_CAMPAIGN.md`, `docs/DEVELOPMENT_ROADMAP.md`, `scripts/assess_heldout_generalization.py` |

## Current operational baseline on `main`

The current tracked project authority is:

```text
config/configure_project.toml
```

`config/project.toml` remains a compatibility artifact during migration and is **not** the normal authority selected by `sync-workstation.cmd` on current `main`.

Google Drive/coordinator authorization uses tracked `google.oauth_login`; the Gemini browser uses independent `gemini.login_name`, `gem_url`, and `gem_edit_url`. A preserved `[local_gemini]` table in the generated local TOML permits workstation-only Gemini overrides. The Gem display name is not synchronized. Topic generation retains `main`'s multi-PDF corpus support beneath the single `sourcepath` root. Stage 0 binds the complete Source-Root fingerprint to a compatible active domain profile before any Drive generation job is claimed; automatic classification is the default and fails closed for unsupported or ambiguous textbooks. The resolved profile is then carried through live generation prompt composition, resumable-stage fencing, package identity, deterministic domain validation, and public-release runtime asset selection. Legacy packages without domain identity remain compatible with the registry default.

Current workstation behavior derives the environment namespace and local state root from `project.project_name`, normally:

```text
%LOCALAPPDATA%\<project_name>
```

The synchronizer renders an ignored local TOML whose exact filename comes from machine-local `workstation-sync.toml`; direct CLI commands must pass `--config` when that filename differs from the CLI default `project.local.toml`.

Current generator selection modes are:

```text
specific
auto
distributed
```

Continuous `auto` mode provides multi-PC coordinated generation/recovery and requires durable Git publication.

Current managed-coordinator baseline (PR #46) uses repository-managed infrastructure when `automation.coordinator_url` is empty. One trusted administrator PC performs the project-wide `coordinator-bootstrap`; ordinary workers discover/ensure the managed runtime through normal Drive authorization and do not manually deploy Apps Script per PC.

## Historical decision/provenance notes

Earlier decisions and PRs remain useful provenance, but interpret them against current `main`:

- one-PDF-per-fresh-Gem-conversation and central lease/heartbeat coordination remain active design principles;
- project-derived path/environment isolation remains active;
- source-derived section title/scope and truthful automated-draft provenance remain active;
- generated material may be published after automated validation; optional manual review does not gate publication;
- Decision 0024 establishes visual-first physics learning: visual specs are declarative, trusted renderers are deterministic, and question/answer/visual consistency is validated; the tool-orchestration contract separates Gemini aesthetic generation, deterministic answer-critical rendering, independent computational verification, and development-only simulation prototyping;
- public deployment remains separate from generation state;
- Section 8.2 is explicitly approved for public draft-review deployment alongside the existing Chapter 8 review routes;
- any historical statement that `config/project.toml` is the current user-facing authority is superseded by the actual current-main configuration path above unless/until a future explicitly merged migration changes it.

Shared conversations and imported files are provenance, not authoritative specifications. Accepted operational behavior must be represented in the repository code/configuration and same-revision canonical documentation.

Accepted Section 8.4 public-review extension: Decision 0022 permits the generated Section 8.4 draft to join the same minimal public GitHub Pages review repository under the same draft labelling, data-exclusion, and human-review constraints.

# 0028 — Authorized Execution and External Blocker Isolation

**Status:** Proposed development-contract amendment implemented in draft PR #223, 3 November 2026; subject to full CI and separate merge authorization. Supplements Decision 0027; never overrides platform safety, authentication, privacy, academic QA or release controls.

## Problem and verified limitations

The Brilliant-style learning app development has repeatedly experienced explicit denials of remote desktop and GitHub operations. The connected apps reported their app-specific permission setting as "Allow all actions", yet safety checks still blocked some operations. The exact rule causing each denial was not exposed. An app-level permission preference does not override platform safety controls, and this repository cannot eliminate or disable those controls.

The goal is to prevent **redundant retries, lost work and unnecessary global stalls**. The new recovery component does not execute tasks. A rejected operation stays rejected unless an independent authorization review permits future action outside the current checkpoint.

## Required project contract

1. **Immutable intent:** Use canonical task IDs rather than arbitrary shell commands. Operation fingerprints bind the exact original-source and candidate-package SHA-256 identifiers to the approved task intent. Do not relabel a denied operation as a new task.
2. **Authority preflight:** Verify the connected tool's approved operation, workspace ownership, current code revision, source/package identity and service/session state before any independently authorized execution. Planner readiness is **not** permission to execute.
3. **No evasion or automatic replay:** An explicit safety denial becomes `BLOCKED_EXTERNAL` in an immutable checkpoint. Do not retry, reword, batch, switch machines or wrap the denied action in another method to evade its control. Record a bounded denial and seek an external authorization determination for the intended operation.
4. **Private metadata-only history:** Each event records a fixed task ID, exact-version operation fingerprint, bounded event ID, denial/tool class or verified receipt digest, previous chain digest and new chain digest. Never save original textbook content, provider responses, secrets, arbitrary commands, private file paths or student records in public checkpoints.
5. **Independent forward progress:** When an operation is blocked, a dependency-aware planner may list unaffected tasks as *eligible for a separate authorization check*. The scheduler must not run them or grant their permissions. Downstream work depending on blocked evidence remains waiting.
6. **Conservative truthfulness:** `RECEIPT_RECORDED` means only that a trusted upstream verifier's digest was recorded, **not** that this module validated the source, science, translations or browser behavior. No academic PASS, publication, merge or permission grant follows automatically.
7. **Evidence integrity:** Append-only private checkpoint files and hash-chained events reject duplicate outcomes, changed versions, tampered records and silent overwrites. The hash chain is not a cryptographic signature. Independently pin a chain-head digest for stronger provenance against wholesale rewriting.
8. **Permanent regression:** Protect the recovery engine and private CLI with adversarial tests in ordinary GitHub Actions, including duplicate rejection, event-order integrity, immutability, malicious field rejection, no false authorization and no replay. Register the incident and its regression anchor under Decision 0027. Distinct future failures require separately linked incidents.
9. **Status separation:** Implemented, source-free-tested, hosted-CI-validated, authoritatively integrated, private-QA-executed, academically accepted and published are different states. Do not claim a blocked operation succeeded, invent external authorization, merge an unapproved draft or publish private materials.

## Operation of reference implementation

`app_generator/validation/execution_access_recovery.py` is a pure offline metadata-planning module; `scripts/plan_external_execution_recovery.py` reads/writes only externally located JSON checkpoints and does not execute commands or contact external services. See `docs/EXTERNAL_EXECUTION_RUNBOOK.md`.

The planner deliberately accepts a **partial evidence inventory** after source verification even when a separate visual/reviewer operation is denied. This does not transform missing evidence into a PASS. Pilot acceptance still requires all independently verified prerequisite categories.

## Re-entry after denial

A denied task is terminal in its existing checkpoint. Only a separately established authorization decision—audited against the same canonical task intent—can permit a future controlled execution. That decision and any new execution are outside this module; it never auto-unblocks a task.

The project retains `git_publish=false` and `git_auto_merge=false` for the current development campaign, and Section 9.4 formal academic acceptance remains 0/18 until independently proven otherwise. This draft decision is not authorization to merge, publish or invoke previously denied operations.

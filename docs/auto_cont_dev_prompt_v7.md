# Autonomous Continuous Development, Recovery, and Forward Progress Contract — v7

## 1. Primary Objective

Proceed autonomously with the next eligible development sequence and continue advancing the codebase toward completion.

**The default behavior must be continuous forward progress, not stopping after completing an individual task, fixing a blocker, passing a test, or closing a milestone.**

Operate as a long-horizon autonomous development workflow that repeatedly identifies, executes, verifies, and closes development tasks, advancing through as many eligible milestones as technically possible within the available execution environment and existing authorization.

Do not require repeated user instructions such as "proceed," "continue," or "start the next stage" when the next action is already authorized and can be determined from the project plan and verified state.

## 2. Mandatory Historical Failure Review and Recovery

Whenever a blocker, error, regression, or unexpected behavior is encountered, follow this exact sequence:

**Historical failure review → targeted repair → real test → fault-injection and regression tests → integration into the executable recovery registry → normal pipeline restart.**

Specifically:

1. Search the project's historical development records, issue logs, recovery registry, previous fixes, and test results for equivalent or closely related failures.
2. If a verified remedy already exists, reuse it instead of independently solving the same problem again.
3. If no suitable remedy exists, investigate the root cause and develop a targeted, reusable repair.
4. Validate the repair against the actual failing operation.
5. Conduct relevant fault-injection and regression tests to confirm that the same failure can be detected and handled automatically.
6. Integrate the verified remedy into the executable production recovery mechanism, not merely into documentation or test scripts.
7. Persist the recovery decision, validation evidence, and operational checkpoint.
8. Automatically restart or resume the interrupted pipeline from the last verified safe checkpoint.
9. Continue immediately to the next eligible development milestone.

A blocker must not be marked resolved until its remedy has passed the required tests and has been integrated into the normal executable recovery path.

## 3. Mandatory Autonomous Forward Progress

**This section takes precedence over any previous practice of stopping after individual development milestones.**

Implement and enforce the following continuous execution cycle:

**Select next eligible milestone → execute → validate → close → persist checkpoint → select next eligible milestone → execute again.**

This cycle must repeat automatically, without requiring a new user message between stages.

The autonomous controller must:

- Maintain a persistent development roadmap and a queue of eligible tasks, including dependencies, priorities, acceptance criteria, and completion status.
- Automatically select the next eligible task based on verified dependencies, project priorities, and the current execution state.
- Execute the task and perform the required functional, scientific, quality-assurance, integration, and regression checks.
- Mark a milestone complete only when its predefined acceptance criteria have been satisfied with verifiable evidence.
- Immediately enqueue or activate newly eligible downstream tasks following successful milestone closure.
- Automatically begin the next task without waiting for manual acknowledgement or another conversational instruction.
- Continue this process across consecutive development milestones for as long as authorized work remains executable.
- Resume safely from persisted checkpoints following recoverable failures, process restarts, or session interruptions.

**Completing one milestone is a transition event, not a stopping condition.**

Likewise, successfully resolving a blocker must automatically trigger pipeline recovery and continuation, rather than terminating the development run.

Do not insert artificial pauses, approval gates, or requests for confirmation between previously authorized operations.

## 4. Long-Horizon Autonomous Execution

Maximize productive development within the available execution window.

Rather than performing only one development step per interaction, plan and execute a sequence of dependent milestones.

Use an autonomous orchestration mechanism that:

1. Continuously evaluates the remaining development backlog.
2. Identifies tasks whose prerequisites are satisfied.
3. Prioritizes work that removes critical blockers or enables downstream progress.
4. Executes consecutive tasks without unnecessary conversational interruptions.
5. Tracks execution, recovery attempts, test outcomes, and remaining work.
6. Avoids repeating completed work or replaying operations whose outcomes are uncertain.
7. Detects stalled operations and applies bounded recovery procedures.
8. Advances automatically when the current stage passes its acceptance tests.

Where supported, implement this behavior through the project's actual job runner, persistent task queue, checkpoint manager, recovery registry, and restart mechanism.

**Autonomy must be implemented in executable code, not merely expressed as an instruction to the AI.**

If an AI session or tool invocation ends, continued execution across that boundary must be handled by an authorized persistent runner or scheduler. Do not assume that a conversational session can continue executing after termination.

## 5. Automatic Recovery and Failure Prevention

The recovery system must progressively improve its ability to handle previously encountered failures.

For every verified repair:

- Register a reusable failure signature, root cause, and recovery procedure.
- Define safe activation conditions and bounded retry limits.
- Include regression and fault-injection tests.
- Integrate the recovery mechanism into normal pipeline execution.
- Verify that the running pipeline actually invokes the mechanism when the corresponding failure occurs.
- Persist the result so that future sessions and executions can reuse the remedy.

Prefer automated detection and recovery over manual intervention whenever safe and technically feasible.

Do not repeatedly investigate or repair the same known issue from scratch.

Ensure retry logic is finite, checkpoint-aware, and safe against duplicate operations or uncertain external API outcomes.

If recovery fails, record the precise remaining blocker and continue with other independent eligible tasks whenever possible.

## 6. Strict Conditions for Manual Intervention

**Manual intervention must be treated as an exception, not a normal development transition.**

Stop or request user intervention only when one of the following is genuinely necessary:

1. A required operation exceeds existing authorization or requires explicit consent.
2. Essential credentials, permissions, or external resources are unavailable and cannot be restored through authorized recovery procedures.
3. A potentially destructive or irreversible operation requires approval not previously granted.
4. A blocker has exhausted its bounded, safe recovery procedures and no independent eligible work can proceed.
5. All planned and discoverable eligible development tasks have been completed and verified.

Do not request intervention simply because a task, test, repair, milestone, or development sequence has finished.

When a mandatory stop occurs, preserve the complete execution state and provide the exact reason, evidence, attempted remedies, remaining work, and minimal action required to resume.

## 7. Continuous Verification and Development Integrity

Autonomous progression must never bypass project acceptance criteria.

Maintain existing requirements for:

- Scientific and technical correctness.
- Independent quality assurance where required.
- Functional, integration, regression, and fault-injection testing.
- Reliable checkpointing and reproducibility.
- Data integrity and prevention of duplicated or unauthorized operations.
- Safe retry limits and existing authorization or expenditure boundaries.

Failed tests must trigger investigation and recovery, not premature milestone closure.

## 8. Progress Tracking and Reporting

Maintain a durable development state containing:

- Completed and verified milestones.
- Current active milestone.
- Remaining eligible and blocked tasks.
- Historical failures and reused remedies.
- New verified recovery mechanisms.
- Test results and acceptance evidence.
- Current pipeline checkpoint.
- Next automatically selected action.

Provide concise progress reports at meaningful checkpoints without interrupting execution merely to obtain acknowledgement.

The report must distinguish between implemented, tested, integrated, and fully accepted work.

## 9. Final Execution Directive

**Begin with the next eligible development milestone and continue autonomously through successive milestones.**

For every encountered blocker, consult historical records before attempting a new repair. Apply the established recovery sequence, integrate verified solutions into the executable workflow, and automatically resume normal processing.

After each milestone is successfully closed, **immediately transition to and execute the next eligible milestone without waiting for another user instruction**.

Continue this execution–verification–recovery–advancement cycle for the longest technically supported and authorized execution horizon.

Persist checkpoints and maintain automatic restart capability wherever the environment supports it.

**Do not stop merely because the current task has succeeded. Stop only when a mandatory intervention condition is reached, no further eligible work exists, or the execution environment genuinely prevents continued operation.**

The ultimate objective is a **self-advancing, self-recovering, checkpointed development workflow** that systematically drives the codebase toward verified completion with minimal manual intervention.
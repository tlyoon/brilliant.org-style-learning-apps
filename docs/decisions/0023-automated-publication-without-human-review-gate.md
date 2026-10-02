# 0023 — Automated publication without a mandatory human-review gate

## Status

Accepted.

## Decision

Validated learning content may be published automatically once all configured machine-enforced gates succeed: deterministic schema/content validation, semantic audit and repair, repository checks, Git integration, and public deployment checks.

Human review is optional and advisory. It may be performed before or after publication, but the codebase must not require human sign-off, reviewer identity, or a review-pending coordinator state as a prerequisite for publication.

The learner-facing app must not display a blanket "review prototype" or "not approved for publication" notice solely because the content was generated automatically.

Package `status` and review-record fields remain metadata for compatibility and traceability; they do not block publication.

## Consequences

- exact-target and continuous-auto runs both finish in the generated/completed state after automated publication succeeds;
- public deployment PRs are normal publication handoffs rather than review-only handoffs;
- optional manual review can still be recorded without affecting deployment eligibility;
- historical decisions that required human review before publication are superseded by this decision for publication gating.

## Supersedes publication-gate portions of

Decisions 0003, 0005, 0007, 0017, 0018, 0020, 0021, and 0022.

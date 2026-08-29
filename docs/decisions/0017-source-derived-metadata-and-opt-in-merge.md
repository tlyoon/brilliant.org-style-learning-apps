# Decision 0017: Source-derived metadata and opt-in draft merging

## Status

Accepted 29 August 2026 by explicit project-owner request.

## Context

Numeric Drive folder names identify a section but do not supply its exact printed title. Requiring operators to
preconfigure title, edition, reviewer, and a precise learning boundary blocks otherwise valid one-PDF jobs. The
prototype also previously stopped every generated draft at a pull request even when the project owner explicitly
wanted validated draft artifacts merged into the configured private repository.

## Decision

- Require source analysis to return the exact concise section title printed in the attached controlled PDF and
  included/excluded scope notes, without quoting source passages.
- Let Python materialize the section label, learning boundary, and activity source-location references from that
  validated analysis.
- When edition metadata is not asserted, record that it was not identified in the controlled PDF. Record automated
  draft generation as the manifest actor while retaining all qualified human-review requirements in the review record.
- Do not prompt an operator for title, edition, reviewer, or learning-boundary values during an ordinary generation
  job.
- Add `git_auto_merge` as an explicit opt-in. It is valid only with `git_publish = true`,
  `git_create_draft_pr = false`, and the existing full repository checks.
- Auto-merge uses a normal GitHub pull-request merge and must verify GitHub reports the PR as merged. It does not
  bypass branch protection, deploy content, change package status from `draft`, or satisfy human-review sign-offs.

This decision narrowly supersedes Decision 0006 and the prototype merge restriction in `SECURITY_AND_PRIVACY.md`
only for an explicitly configured private-repository draft merge. Human review continues to gate `review` and
`publishable` status, deployment, and learner use.

## Consequences

- A similarly structured one-PDF job can derive section-specific metadata without hand-edited per-section values.
- Invalid or generic title analysis is rejected before installation.
- Edition uncertainty and absent human review are represented truthfully rather than with placeholders or invented
  identities.
- Enabling auto-merge is a visible, reviewable project configuration change; the safe default remains disabled.
- GitHub permissions, required checks, conflicts, or branch protection may still stop a merge safely.

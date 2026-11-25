"""Gemini-only BOSLA V3 generated-text assessment execution seam.

The external caller MUST supply already-authorized, verified and independently
owned model conversation sessions. This module cannot log in to a provider,
create a browser connection, change external authorization or release content.
Only generated activity JSON is included in the shared V3 model prompts.\nBoth Gemini browser and native API sessions use this same checkpoint engine;\nno ChatGPT model is accepted as an academic reviewer.
"""
from __future__ import annotations

import os
from pathlib import Path

from app_generator.runtime.run_context import RunContext
from app_generator.validation.autonomous_completion import (
    GEMINI_PROVIDERS, assess_with_models, assessment_progress, package_identity,
)

REPO = Path(__file__).resolve().parents[2]


def advance_v3_generated_text(
    raw: bytes, sessions: tuple | None, *, private_root: Path,
    generated_content_transfer_allowed: bool = False,
    max_activities: int = 6,
) -> dict:
    """Advance at most six activities with externally supplied authorized roles.

    Private checkpoints use a stable full package SHA-256 run directory so a
    new invocation resumes safely without re-sending prior/ambiguous claims.
    A run lock prevents overlapping callers from double-submitting the same
    activity. A leftover lock after process loss requires ownership review;
    this function never silently removes another process's lock.
    """
    if not generated_content_transfer_allowed:
        raise ValueError("V3_GENERATED_CONTENT_MODEL_TRANSFER_NOT_ALLOWED")
    if type(max_activities) is not int or not 1 <= max_activities <= 6:
        raise ValueError("V3_INVALID_BATCH_LIMIT")
    if (not isinstance(sessions, tuple) or len(sessions) != 2
        or any(not getattr(s, "reviewer_id", "")
               or not getattr(s, "session_id", "")
               or not callable(getattr(getattr(s,"conversation",None),"ask",None))
               for s in sessions)):
        raise ValueError("V3_AUTHORIZED_REVIEW_SESSIONS_REQUIRED")
    if (sessions[0].reviewer_id == sessions[1].reviewer_id
        or sessions[0].session_id == sessions[1].session_id
        or sessions[0].conversation is sessions[1].conversation):
        raise ValueError("V3_DISTINCT_REVIEW_CONTEXTS_REQUIRED")
    if any(getattr(s, "provider_id", None) not in GEMINI_PROVIDERS for s in sessions):
        raise ValueError("V3_GEMINI_ONLY_REVIEWERS_REQUIRED")
    if (not isinstance(private_root, Path) or private_root.is_symlink()
        or not private_root.is_absolute()):
        raise ValueError("V3_UNSAFE_PRIVATE_ROOT")
    root=private_root.resolve()
    if root == REPO.resolve() or root.is_relative_to(REPO.resolve()):
        raise ValueError("V3_UNSAFE_PRIVATE_ROOT")
    digest, _ = package_identity(raw)
    run_id="v3-generated-"+digest
    run_dir=root/run_id
    if run_dir.is_symlink() or (run_dir.exists() and not run_dir.is_dir()):
        raise ValueError("V3_UNSAFE_PRIVATE_ROOT")
    # The lock is claimed before loading any checkpoint or contacting models.
    # No stale/ambiguous request can be replayed by launching another process.
    run_dir.mkdir(parents=True,exist_ok=True)
    lock=run_dir/".active-review.lock"
    try:
        descriptor=os.open(lock,os.O_WRONLY | os.O_CREAT | os.O_EXCL,0o600)
    except FileExistsError as exc:
        raise ValueError("V3_REVIEW_RUN_OWNERSHIP_UNCERTAIN") from exc
    try:
        os.close(descriptor)
        context=RunContext.create(root,run_id)
        report=assess_with_models(
            raw,sessions,checkpoint=context,
            generated_content_transfer_allowed=True,
            max_activities=max_activities,
        )
        return assessment_progress(raw,report)
    finally:
        lock.unlink()

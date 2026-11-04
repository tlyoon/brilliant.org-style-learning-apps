"""Resume-safe independent AI academic reviews with no human sign-off stage.

Only owned run-context stages are written. A stale or ambiguous remote
response is not blindly retried; independent other activities can continue.
"""
from __future__ import annotations
from collections.abc import Callable
from typing import Any

from app_generator.runtime.run_context import RunContext
from app_generator.validation.autonomous_ai_review import (
    ReviewerSession, canonical_digest, plan_automated_followup, review_activity,
)


def review_batch_autonomously(
    context: RunContext,
    package: dict[str, Any],
    *,
    package_sha256: str,
    source_sha256: str,
    authorized_source: dict[str, dict[str, Any]],
    reviewer_factory: Callable[[str], tuple[ReviewerSession, ReviewerSession]],
) -> dict[str, Any]:
    """One bounded pass; sessions must be freshly provisioned by caller.

    Skips checked/captured stages on resume, prevents mixed source or output
    identities, and leaves failed/ambiguous reviews queued without invoking a
    human review gate or duplicating an uncertain external submission.
    """
    activities=package.get("activities")
    if not isinstance(activities,list) or not activities or any(
        not isinstance(a,dict) or not isinstance(a.get("id"),str) or not a["id"]
        for a in activities
    ):
        raise ValueError("nonempty uniquely identified activities required")
    ids=[a["id"] for a in activities]
    if len(set(ids))!=len(ids):
        raise ValueError("duplicate activity ID in academic review batch")
    if not isinstance(authorized_source,dict) or set(authorized_source)!=set(ids):
        raise ValueError("each activity requires explicit authorized source context")
    results=[]
    used_sessions=set()
    for index,activity in enumerate(activities):
        source=authorized_source[activity["id"]]
        if not isinstance(source,dict):
            raise ValueError("academic review source context must be an object")
        expected={
            "packageSha256":package_sha256,
            "sourceSha256":source_sha256,
            "sourceContextSha256":canonical_digest(source),
            "activityCanonicalSha256":canonical_digest(activity),
        }
        stage=f"ai-academic-{index:03d}"
        cached=context.load_stage(stage)
        if cached is not None:
            if not isinstance(cached,dict) or any(
                cached.get(k)!=v for k,v in expected.items()
            ) or cached.get("activityId")!=activity["id"]:
                raise ValueError("stale or conflicting academic AI review stage; no unsafe reuse")
            report=cached
        else:
            sessions=reviewer_factory(activity["id"])
            identities={session.session_id for session in sessions}
            if len(identities)!=2 or identities & used_sessions:
                raise ValueError("each activity requires fresh independent AI reviewer sessions")
            used_sessions.update(identities)
            report=review_activity(activity,source,sessions,
                                   package_sha256=package_sha256,
                                   source_sha256=source_sha256,
                                   checkpoint=context,
                                   claim_prefix=f"ai-claim-{index:03d}")
            # Persist before any future continuation so a crash/restart
            # does not re-send an ambiguous or already completed remote job.
            context.save_stage(stage,report)
        results.append(report)
    followups=[plan_automated_followup(report) for report in results]
    counts={kind:sum(1 for x in followups if x["mode"]==kind)
            for kind in ("AUTO_CONTINUE","AUTO_REPAIR","AUTO_RETRY","AUTO_SOURCE_CHECK")}
    return {
        "packageSha256":package_sha256,
        "sourceSha256":source_sha256,
        "activitiesTotal":len(results),
        "aiReviewAttemptedActivities":len(results),
        "aiReviewedActivities":sum(bool(x["aiReviewed"]) for x in results),
        "aiPendingActivities":sum(not bool(x["aiReviewed"]) for x in results),
        "humanReviewRequired":False,
        "humanReviewed":False,
        "academicQA":"REVIEW_REQUIRED",
        "publicationAuthorized":False,
        "followupCounts":counts,
        "followups":followups,
        "receipts":results,
    }

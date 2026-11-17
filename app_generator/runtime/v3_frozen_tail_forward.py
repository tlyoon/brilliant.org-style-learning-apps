"""Finite source-free orchestration around frozen-original untouched V3 tail.

The real Yoga6 normal worker is responsible for the paid authorization,
host, provider health and credential preflight BEFORE invoking this function.
This controller claims each distinct original activity under a new immutable
single-activity package and never replays a prior ambiguous model request.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Any

from app_generator.runtime.v3_frozen_original_tail import (
    plan_frozen_original_tail, reserve_frozen_original_tail_attempt,
    stage_frozen_original_tail_slice,
)
from app_generator.runtime.v3_yoga6_recovery import coordinator_lock

_ALLOWED = {
    "GENUINE_SUPPLEMENTAL_CONSENSUS_PASS",
    "SUPPLEMENTAL_SCIENTIFIC_REPAIR_REQUIRED",
    "SUPPLEMENTAL_UNCERTAIN_NO_REPLAY",
}


def _receipt(status: str, report: dict, *, attempted: int, verified: int) -> dict:
    return {
        "status": status,
        "sourceSection": report["sourceSection"],
        "sourcePackageSha256": report["sourcePackageSha256"],
        "originalAssessedUnchanged": report["originalAssessedUnchanged"],
        "originalModelConsensusPassesUnchanged":
            report["originalModelConsensusPassesUnchanged"],
        "supplemental": report["supplemental"],
        "nextOriginalIndex":
            report["next"]["index"] if report.get("next") else None,
        "attemptedThisInvocation": attempted,
        "verifiedNewSupplementalRowsThisInvocation": verified,
        "originalUncertaintyPreserved": True,
        "versionedScopeAdmitted": False,
        "publicationAuthorized": False,
    }


def advance_frozen_tail_until_boundary(
    course: Path, repo: Path, private: Path,
    review_one: Callable[[bytes, dict], Any], *,
    section: str = "section-9-6",
    max_activities: int = 4,
    max_elapsed_seconds: int = 900,
    monotonic: Callable[[], float] = time.monotonic,
) -> dict:
    """Forward across genuine *new* frozen activities only; no paid call itself.

    review_one is the existing V3 one-activity checkpoint engine, injected by
    the normal worker after authorization. A synthetic fake can test the same
    normal execution path without a provider account.
    """
    if (not callable(review_one)
            or type(max_activities) is not int or not 1 <= max_activities <= 4
            or type(max_elapsed_seconds) is not int
            or not 30 <= max_elapsed_seconds <= 900):
        raise ValueError("V3_TAIL_UNAUTHORIZED_OR_UNBOUNDED_DRIVER")
    began = monotonic()
    attempted = verified = 0
    with coordinator_lock(private):
        for _ in range(max_activities):
            current = plan_frozen_original_tail(
                course,repo,private,section=section)
            if current["status"] != "READY_FOR_AUTHORIZED_FROZEN_ORIGINAL_TAIL_REVIEW":
                return _receipt("STOP_TAIL_NO_ELIGIBLE_ORIGINAL_REVIEW",
                                current,attempted=attempted,verified=verified)
            if monotonic() - began >= max_elapsed_seconds:
                return _receipt("STOP_TAIL_ELAPSED_BUDGET",current,
                                attempted=attempted,verified=verified)
            next_row = current["next"]
            raw, manifest = stage_frozen_original_tail_slice(
                course,repo,private,section=section,index=next_row["index"])
            if (manifest["slicePackageSha256"] != next_row["slicePackageSha256"]
                    or manifest["sourcePackageSha256"] != current["sourcePackageSha256"]
                    or manifest["activityId"] != next_row["activityId"]):
                raise ValueError("V3_TAIL_STAGE_DID_NOT_MATCH_OWNED_PLAN")
            # PRE_CALL is fsynced before the reviewer factory is opened.
            # Even if this call fails before recording a role, its unique
            # old activity is never submitted again by this queue.
            reserve_frozen_original_tail_attempt(
                private,source_sha=current["sourcePackageSha256"],
                index=next_row["index"],
                slice_sha=manifest["slicePackageSha256"])
            attempted += 1
            try:
                review_one(raw,manifest)
            except Exception:
                # Provider or local transport failure may have submitted.
                # The queued immutable PRE_CALL remains a no-replay marker.
                after = plan_frozen_original_tail(
                    course,repo,private,section=section)
                return _receipt("STOP_TAIL_WORKER_EXCEPTION_NO_REPLAY",
                                after,attempted=attempted,verified=verified)
            after = plan_frozen_original_tail(
                course,repo,private,section=section)
            if (after["sourcePackageSha256"] != current["sourcePackageSha256"]
                    or after["originalAssessedUnchanged"] != current["originalAssessedUnchanged"]
                    or after["originalModelConsensusPassesUnchanged"] != current["originalModelConsensusPassesUnchanged"]):
                raise ValueError("V3_TAIL_ORIGINAL_EVIDENCE_CHANGED")
            just = next(
                row for row in after["rows"] if row["index"] == next_row["index"])
            if just["state"] not in _ALLOWED:
                return _receipt("STOP_TAIL_PRE_CALL_WITHOUT_VERIFIED_RESULT_NO_REPLAY",
                                after,attempted=attempted,verified=verified)
            verified += 1
            if just["state"] == "SUPPLEMENTAL_UNCERTAIN_NO_REPLAY":
                # A hash-verified local parse/rubric failure cannot taint a
                # separate original activity, and must not stop safe forward
                # progress. Uncaptured/unknown provider failures DO stop.
                from app_generator.validation.v3_response_recovery import (
                    section_has_only_isolatable_uncertainty,
                )
                package_path = (
                    private / "frozen-original-review-slices"
                    / manifest["slicePackageSha256"] / "package.json")
                if section_has_only_isolatable_uncertainty(
                        private,manifest["slicePackageSha256"],package_path):
                    continue
                return _receipt("STOP_TAIL_UNCERTAIN_NO_REPLAY",
                                after,attempted=attempted,verified=verified)
        after = plan_frozen_original_tail(course,repo,private,section=section)
        status = ("STOP_TAIL_ACTIVITY_BUDGET_REACHED"
                  if after["status"] == "READY_FOR_AUTHORIZED_FROZEN_ORIGINAL_TAIL_REVIEW"
                  else "STOP_TAIL_NO_ELIGIBLE_ORIGINAL_REVIEW")
        return _receipt(status,after,attempted=attempted,verified=verified)

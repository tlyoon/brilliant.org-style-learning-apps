"""BSA224: finite exact-HEAD CI reconciliation inside normal sourcefree worker.

After authentic 108/698 Chrome, GitHub's identical committed SHA may still
be queued or running. Never return a false overall success or ask for another
'proceed'. Poll authenticated hosted CI a bounded number of times, verify
the same Git commit and entire saved science/browser chain, then immediately
dispatch already-authorized private V1-V6 technical work.

No model, PDF, release/merge, background scheduler or unbounded retry.
"""
from __future__ import annotations

import re
import time
from pathlib import Path

from app_generator.runtime import v3_versioned_readiness as readiness

_SHA40=re.compile(r"^[0-9a-f]{40}$")
_GREEN="VERSIONED_SCIENCE_BROWSER_AND_CI_VERIFIED_UNADMITTED"
_WAIT="VERSIONED_SCIENCE_BROWSER_VERIFIED_WAIT_EXACT_HEAD_CI"


def await_exact_ci_and_resume(
    root:Path,private:Path,current:dict, *,
    max_wait_seconds:int=240,
    poll_interval_seconds:int=15,
)->dict:
    """Synchronous bounded wait for an exact GitHub-hosted SHA; never guess.

    Fake-only tests patch the underlying hosted query and monotonic clock.
    All real approval still originates from the original source-bound
    evaluate_current_versioned_evidence, not this polling coordinator.
    """
    if (not isinstance(current,dict)
            or current.get("publicationAuthorized") is not False
            or current.get("sourceVersionOnly") is not True
            or current.get("realChromeChecks")!=698
            or current.get("proposedContentScientificCoverage")!=108):
        raise ValueError("V3_CI_RECOVERY_MISSING_REAL_BROWSER_AND_SCIENCE")
    if current.get("status")==_GREEN:
        if (current.get("exactHeadHostedCiSuccess") is not True
                or current.get("codeWorkingTreeClean") is not True):
            raise ValueError("V3_CI_RECOVERY_FORGED_GREEN_STATUS")
        return current
    head=current.get("gitHead")
    if (current.get("status")!=_WAIT
            or current.get("codeWorkingTreeClean") is not True
            or not isinstance(head,str) or not _SHA40.fullmatch(head)):
        raise ValueError("V3_CI_RECOVERY_UNSAFE_PENDING_STATUS")
    if (not isinstance(max_wait_seconds,int) or max_wait_seconds<1
            or max_wait_seconds>360
            or not isinstance(poll_interval_seconds,int)
            or poll_interval_seconds<1 or poll_interval_seconds>60):
        raise ValueError("V3_CI_RECOVERY_INVALID_FINITE_BOUNDS")
    realhead,branch=readiness._git_info(root)
    if realhead!=head or not readiness._git_clean(root):
        raise ValueError("V3_CI_RECOVERY_GIT_DIRTY_OR_HEAD_MOVED")
    started=time.monotonic()
    attempts=0
    max_attempts=min(25,1+max_wait_seconds//poll_interval_seconds)
    while attempts<max_attempts:
        # This is an already permitted source-free authenticated GH status
        # read; does not touch private source, Gemini or classroom systems.
        latest,branch_now=readiness._git_info(root)
        if latest!=head or branch_now!=branch or not readiness._git_clean(root):
            raise ValueError("V3_CI_RECOVERY_GIT_CHANGED_DURING_WAIT")
        attempts+=1
        rows=readiness._hosted_runs(root,branch)
        matching=[x for x in rows if (
            isinstance(x,dict) and x.get("headSha")==head)]
        if readiness._exact_ci_success(rows,head):
            verified=readiness.evaluate_current_versioned_evidence(
                root,private,hosted_runs=rows)
            if (verified.get("status")!=_GREEN
                    or verified.get("gitHead")!=head
                    or verified.get("publicationAuthorized") is not False
                    or verified.get("exactHeadHostedCiSuccess") is not True):
                raise ValueError("V3_CI_RECOVERY_REVALIDATION_NOT_GREEN")
            return {**verified,"ciRecoveryPolls":attempts,
                    "ciRecoveredInSameInvocation":True}
        if any(x.get("status")=="completed" for x in matching):
            return {"status":"STOP_HOSTED_CI_COMPLETED_NOT_SUCCESS",
                    "gitHead":head,"ciRecoveryPolls":attempts,
                    "paidGeminiCalls":0,"publicationAuthorized":False}
        elapsed=time.monotonic()-started
        if elapsed>=max_wait_seconds or attempts>=max_attempts:
            break
        time.sleep(min(poll_interval_seconds,max(0,max_wait_seconds-elapsed)))
    return {"status":"STOP_HOSTED_CI_BOUNDED_WAIT_EXHAUSTED",
            "gitHead":head,"ciRecoveryPolls":attempts,
            "paidGeminiCalls":0,"publicationAuthorized":False}

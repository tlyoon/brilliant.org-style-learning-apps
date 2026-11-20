"""BOSLA V15 — finite, allowlisted roadmap handoff after signed public PR V14.

This normal-worker controller **executes** multiple independent read-only
next tasks in one invocation, saving an immutable checkpoint per dispatched
task. Missing native public PR checks are recorded honestly, not fabricated
as an approval. No automatic merge, Pages deployment, new AI call, scheduler
or claim of a persistent supervisor beyond the active process.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Callable

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_public_nonmerging_draft_pr import (
    _REPO,_MAIN,_ls_remote,_gh,_preflight as _v13_preflight
)
from app_generator.runtime.v3_public_pr_independent_browser_acceptance import (
    _V14, _STATUS as _V14_STATUS,_verify_v13,_check_pr_snapshot,
    _check_pr_diff,
)

_V15="V15_GLOBAL_READONLY_ROADMAP_DISPATCH.json"
_STATUS="POST_PR_GLOBAL_READONLY_TASKS_EXECUTED_NO_RELEASE"
# The registry selects only explicitly permitted, code-implemented
# tasks. Never use untrusted filenames or arbitrary handler imports.
_TASKS=(
    "ACTUAL_PR_BRANCH_RECONCILIATION",
    "PUBLIC_GITHUB_NATIVE_CHECKS_AND_REVIEWS",
    "HISTORICAL_C3_AND_GLOBAL_RECURRENCE_SCAN",
)
_BASENAME="V15_TASK_"


def _json_readonly(path:str):
    raw=_gh(["gh","api","--method","GET","repos/"+_REPO+"/"+path])
    return json.loads(raw)


def _task_pr_branch(v13:dict,v14:dict,root:Path)->dict:
    n=v13["publicPullRequestNumber"]
    pr=_json_readonly(f"pulls/{n}")
    _check_pr_snapshot(pr,v13)
    files=_json_readonly(f"pulls/{n}/files?per_page=100")
    changed=_check_pr_diff(files,v13)
    if (changed!=v14["actualRemoteGitHubDiffPaths"]
            or _ls_remote("main")!=_MAIN
            or _ls_remote(v13["publicReviewBranch"])!=
                v13["publicReviewBranchSha"]):
        raise ValueError("V15_PUBLIC_PR_BRANCH_OR_SCOPE_CHANGED")
    return {
        "taskStatus":"PUBLIC_PR_OPEN_DRAFT_UNMERGED_VERIFIED",
        "publicPrNumber":n,
        "publicPrUrl":v13["publicPullRequestUrl"],
        "publicMainUnchanged":True,
        "changedPathsChecked":len(changed),
        "publicMergeExecuted":False,
    }


def _task_ci_and_reviews(v13:dict,v14:dict,root:Path)->dict:
    sha=v13["publicReviewBranchSha"]
    status=_json_readonly(f"commits/{sha}/status")
    checks=_json_readonly(f"commits/{sha}/check-runs")
    reviews=_json_readonly(
        f"pulls/{v13['publicPullRequestNumber']}/reviews?per_page=100")
    if (not isinstance(status,dict)
            or not isinstance(checks,dict)
            or not isinstance(reviews,list)
            or not isinstance(status.get("statuses"),list)
            or not isinstance(checks.get("check_runs"),list)
            or type(checks.get("total_count")) is not int
            or checks["total_count"]<0):
        raise ValueError("V15_GITHUB_STATUS_OR_REVIEW_DATA_INVALID")
    native=checks["total_count"]
    traditional=len(status["statuses"])
    approvals=sum(r.get("state")=="APPROVED"
                  for r in reviews if isinstance(r,dict))
    # Missing native GitHub checks is NOT evidence that they passed.
    return {
        "taskStatus":"PUBLIC_PR_NATIVE_EVIDENCE_INVENTORIED_NOT_RELEASE_APPROVED",
        "publicPrNumber":v13["publicPullRequestNumber"],
        "nativeCheckRunCount":native,
        "commitStatusCount":traditional,
        "reviewCount":len(reviews),
        "approvalReviewCount":approvals,
        "nativeChecksPresent":native+traditional>0,
        "independentSourceV14ChromeVerified":True,
        "releaseApproved":False,
        "githubNativeStatusReported":status.get("state","unknown"),
    }


def _task_global_recurrence(v13:dict,v14:dict,root:Path)->dict:
    registry=_trusted_json(root/"docs"/"recurrence_registry.json",
                           maxbytes=8_000_000)
    entries=registry.get("incidents")
    if not isinstance(entries,list):
        raise ValueError("V15_GLOBAL_RECURRENCE_REGISTRY_MISSING")
    active=[x.get("id") for x in entries
            if isinstance(x,dict) and x.get("status")=="active"]
    if any(not isinstance(i,str) or
           not re.fullmatch(r"BSA-[0-9]{8}-[0-9]{3}",i)
           for i in active):
        raise ValueError("V15_GLOBAL_RECURRENCE_BAD_ACTIVE_ID")
    checkpoint=root/"docs"/"CONTINUATION_CHECKPOINT_LATEST.md"
    if (not checkpoint.is_file()
            or "FAILED_LIMITED_CAMPAIGN" not in
                checkpoint.read_text(encoding="utf8")):
        raise ValueError("V15_HISTORICAL_C3_EVIDENCE_UNAVAILABLE")
    return {
        "taskStatus":"GLOBAL_RECURRENCE_AND_HISTORICAL_C3_RECONCILED_READONLY",
        "registeredIncidentCount":len(entries),
        "activeIncidentCount":len(active),
        "activeIncidentIds":active,
        "historicalC3":"FAILED_LIMITED_CAMPAIGN",
        "uncertainProviderRequestsReplayed":False,
        "newPaidModelCalls":0,
    }


_REGISTRY={
    "ACTUAL_PR_BRANCH_RECONCILIATION":_task_pr_branch,
    "PUBLIC_GITHUB_NATIVE_CHECKS_AND_REVIEWS":_task_ci_and_reviews,
    "HISTORICAL_C3_AND_GLOBAL_RECURRENCE_SCAN":_task_global_recurrence,
}
assert tuple(_REGISTRY)==_TASKS


def _dispatch_task(
    folder:Path,ready:dict,v14:dict,
    task:str,fn:Callable,v13:dict,repo:Path,
)->dict:
    if task not in _REGISTRY or fn is not _REGISTRY[task]:
        raise ValueError("V15_UNREGISTERED_TASK_DISPATCH_REFUSED")
    identity={"gitHead":ready["gitHead"],
              "proposalSha256":ready["proposalSha256"],
              "sourceV14ReceiptSha256":v14["integritySha256"],
              "taskId":task}
    # This checkpoint is committed before the task is invoked. The handler
    # itself is read-only; there is no uncertain externally consumed write.
    _v6_checkpoint(folder/(_BASENAME+task+"_PRE_CALL.json"),{
        **identity,"state":"PRE_CALL_READONLY_TASK_DISPATCHED",
        "executionEntryPoint":fn.__name__,
        "externalWritesAuthorized":False,
    })
    receipt_file=folder/(_BASENAME+task+"_RESULT.json")
    # On restart re-evaluate every read-only condition; an existing
    # signed immutable result must still agree, otherwise fail closed.
    try:
        value=fn(v13,v14,repo)
        if not isinstance(value,dict) or "taskStatus" not in value:
            raise ValueError("V15_REGISTERED_TASK_RESULT_INVALID")
        payload={**identity,"state":"READONLY_TASK_EXECUTED",
                 "handler":fn.__name__,"details":value,
                 "publicMergeExecuted":False,
                 "publicDeployExecuted":False}
    except Exception as exc:
        # Continue to independent eligible tasks; do not claim a
        # failed or unknown condition is a successful acceptance.
        payload={**identity,"state":"READONLY_TASK_QUARANTINED",
                 "handler":fn.__name__,
                 "errorClass":type(exc).__name__,
                 "publicMergeExecuted":False,
                 "publicDeployExecuted":False}
    return _v6_checkpoint(receipt_file,payload)


def run_global_readonly_roadmap(
    repo:Path,private:Path,ready:dict,
    v9_result:dict,v11_result:dict,v12_result:dict,
    v13_result:dict,v14_result:dict,
)->dict:
    """Globally scan and dispatch independent eligible read-only tasks."""
    folder,v11,v12,branch,paths=_v13_preflight(
        repo,private,ready,v9_result,v11_result,v12_result)
    v13=_verify_v13(folder,v13_result,ready)
    v14=_trusted_json(folder/_V14)
    if (v14!=v14_result or
            v14.get("status")!=_V14_STATUS or
            v14.get("integritySha256")!=_hash({
                k:v for k,v in v14.items() if k!="integritySha256"})
            or v14.get("gitHead")!=ready["gitHead"]
            or v14.get("proposalSha256")!=ready["proposalSha256"]
            or v14.get("sourceV13ReceiptSha256")!=v13["integritySha256"]
            or v14.get("publicBaseMainPinnedSha")!=_MAIN
            or v14.get("realChromeRoutesPassed")!=9
            or v14.get("changedFileCount")!=21 or len(paths)!=21
            or v14.get("actualRemoteGitHubDiffPaths")!=paths
            or v14.get("publicPrDraft") is not True
            or any(v14.get(k) is not False for k in
                   ("publicMergeExecuted","publicDeployExecuted",
                    "publicationAuthorized","scheduledTaskCreated"))):
        raise ValueError("V15_GENUINE_SIGNED_V14_REQUIRED")
    if (_ls_remote("main")!=_MAIN
            or _ls_remote(branch)!=v13["publicReviewBranchSha"]):
        raise ValueError("V15_PROTECTED_PR_BRANCH_OR_BASE_MOVED")
    # The normal pipeline runs the allowlisted roadmap tasks now, not a
    # future memo or unverified invisible scheduler.
    tasks=[]
    for name in _TASKS:
        tasks.append(_dispatch_task(
            folder,ready,v14,name,_REGISTRY[name],v13,repo))
    quarantined=[r["taskId"] for r in tasks
                 if r["state"]=="READONLY_TASK_QUARANTINED"]
    if len(tasks)!=len(_TASKS):
        raise ValueError("V15_GLOBAL_TASK_SCAN_DID_NOT_DISPATCH")
    payload={
        "contract":"BOSLA_V15_ALLOWLISTED_POST_PR_GLOBAL_READONLY_CONTROLLER_V1",
        "status":_STATUS if not quarantined else
                 "POST_PR_GLOBAL_READONLY_TASKS_QUARANTINED_NO_RELEASE",
        "gitHead":ready["gitHead"],
        "proposalSha256":ready["proposalSha256"],
        "sourceV14ReceiptSha256":v14["integritySha256"],
        "sourceV13ReceiptSha256":v13["integritySha256"],
        "taskDispatchOrder":list(_TASKS),
        "taskDispatchCount":len(tasks),
        "taskReceipts":[{"taskId":r["taskId"],"state":r["state"],
                         "integritySha256":r["integritySha256"]}
                        for r in tasks],
        "quarantinedTaskIds":quarantined,
        "nextTaskDispatchActuallyExecuted":True,
        "publicPrDraft":True,
        "publicMergeExecuted":False,
        "publicDeployExecuted":False,
        "publicationAuthorized":False,
        "schedulerReinstalled":False,
        "crossSessionPersistentSupervisorVerified":False,
        "newModelCalls":0,
        "nextEligibleMilestone":
          "INDEPENDENT_PUBLIC_PR_RELEASE_ADMISSION_OR_AUTHORIZED_OTHER_WORKSTREAM",
    }
    return _v6_checkpoint(folder/_V15,payload)

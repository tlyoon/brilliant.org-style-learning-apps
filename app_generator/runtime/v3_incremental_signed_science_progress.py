"""BSA303: monotonic, signed scientific progress independent of owner outcome.

The owner may fail A22 after signing A21. A successful, independent source-
bound cross-head receipt readback remains valid even if the following task
fails. This module never creates or signs academic evidence and never promotes
a checkpoint merely because a file, model output, or GitHub CI exists.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import re
from typing import Any

from app_generator.runtime.v3_long_horizon_development import read_long_horizon_development

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_HEAD = re.compile(r"[0-9a-f]{40}\Z")
TOTAL = 429
# Descending: never replay/write proof producers here. Verifiers only.
STAGES = (
 (31,"app_generator.runtime.v3_glider_explanation_academic_admission","_FRONTIER","verify_glider_explanation_across_git_heads"),
 (30,"app_generator.runtime.v3_newton_explanation_academic_admission","_FRONTIER","verify_newton_explanation_across_git_heads"),
 (29,"app_generator.runtime.v3_si_explanation_academic_admission","_FRONTIER","verify_si_explanation_across_git_heads"),
 (28,"app_generator.runtime.v3_vector_explanation_academic_admission","_FRONTIER","verify_vector_explanation_across_git_heads"),
 (27,"app_generator.runtime.v3_spring_buffer_academic_batch_admission","_FRONTIER","verify_spring_buffer_batch_across_git_heads"),
 (24,"app_generator.runtime.v3_isolated_pair_academic_batch_admission","_FRONTIER","verify_isolated_pair_batch_across_git_heads"),
 (21,"app_generator.runtime.v3_equal_energy_academic_batch_admission","_FRONTIER","verify_equal_energy_batch_across_git_heads"),
 (18,"app_generator.runtime.v3_equal_speed_academic_batch_admission","_FRONTIER","verify_equal_speed_batch_across_git_heads"),
 (15,"app_generator.runtime.v3_third_law_academic_batch_admission","_FRONTIER","verify_third_law_batch_across_git_heads"),
)

def validate_independent_stage(*, result:dict[str,Any],head:str,
                               expected_count:int)->dict[str,Any]:
    """Strictly validate the *result of an executed independent verifier*."""
    if not isinstance(result,dict) or not isinstance(head,str) or not _HEAD.fullmatch(head):
        raise ValueError("BSA303_INVALID_SCIENCE_FRONTIER_RESULT")
    count=result.get("independentlyAcceptedAcademicTasks")
    remaining=result.get("fullAcademicTasksStillOpen")
    ids=result.get("acceptedAcademicTaskIds")
    if (type(count) is not int or count!=expected_count
        or remaining!=TOTAL-count
        or result.get("currentGitHead")!=head
        or not str(result.get("status","")).endswith("_REVERIFIED")
        or result.get("completeAcademicProofGatesStillOpen")!=90
        or result.get("fullAcademicActivityPASS")!=0
        or result.get("publicationAuthorized") is not False
        or result.get("newProviderCalls")!=0
        or not isinstance(ids,list) or len(ids)!=count
        or len(set(ids))!=count
        or not all(isinstance(i,str) and _SHA.fullmatch(i) for i in ids)):
        raise ValueError("BSA303_SCIENCE_FRONTIER_NOT_INDEPENDENT")
    digest=sha256(json.dumps(result,sort_keys=True,ensure_ascii=True,
        separators=(",",":")).encode("utf8")).hexdigest()
    return {"acceptedCount":count,"pendingCount":remaining,
            "verifiedEvidenceSha256":digest,
            "sourceProofHead":result.get("batchProofOriginGitHead"),
            "lastVerifiedHead":head,"sourceBound":True,
            "fullAcademicProofGatesStillOpen":90}

def apply_independent_progress(*,state:dict[str,Any],verified:dict[str,Any],
                               head:str,now:str,cycle:int)->dict[str,Any]:
    """Publish only upward progress from a successful independent recheck."""
    stamp=datetime.fromisoformat(now)
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("BSA303_PROGRESS_TIME_MUST_BE_AWARE")
    if verified.get("lastVerifiedHead")!=head:
        raise ValueError("BSA303_STALE_SCIENCE_READBACK")
    count=verified["acceptedCount"]
    old=state.get("scienceAcceptance",{})
    prior=old.get("acceptedCount",0) if isinstance(old,dict) else 0
    if type(prior) is not int or count<prior:
        raise ValueError("BSA303_SIGNED_SCIENCE_COUNT_ROLLBACK")
    is_gain=count>prior
    recorded={**verified,"lastVerifiedAt":now,
        "lastIncreaseAt":now if is_gain else old.get("lastIncreaseAt",now),
        "lastVerifiedCycle":cycle,
        "independentReceiptSha256":verified["verifiedEvidenceSha256"],
        "noGainOwnerHeads":0 if is_gain else old.get("noGainOwnerHeads",0),
        "advancedThisObservation":is_gain,
        "evidence":"BSA303_INDEPENDENT_SOURCE_BOUND_SIGNED_FRONTIER_REVERIFIED"}
    state["scienceAcceptance"]=recorded
    state["scientificProgress"]={
        "accepted":count,"remaining":TOTAL-count,"verifiedHead":head,
        "signedEvidenceSha256":verified["verifiedEvidenceSha256"],
        "verifiedAt":now,"fullAcademicGatesStillOpen":90,
        "publicationAuthorized":False,"proofAccepted":True}
    if is_gain:
        state.pop("scienceStall",None)
    return recorded

def reconcile_independent_science(*,private:Path,state:dict[str,Any],
                                 head:str,now:str,cycle:int)->dict[str,Any]:
    """Reopen latest eligible signed source-bound frontier; never sign it."""
    check=read_long_horizon_development(private)
    if check.get("gitHead")!=head:
        raise ValueError("BSA303_SOURCE_HEAD_NOT_CURRENT")
    attempted=[]
    for count,modname,frontier_key,verification_name in STAGES:
        module=import_module(modname)
        frontier=private/"long-horizon-development"/getattr(module,frontier_key)
        if not frontier.is_file() or frontier.is_symlink():
            continue
        try:
            actual=getattr(module,verification_name)(private=private)
            signed=validate_independent_stage(
                result=actual,head=head,expected_count=count)
        except (OSError,ValueError,KeyError,TypeError,IndexError) as exc:
            # Don't certify an invalid/broken highest milestone. Try only
            # previously signed *independent* lower milestones.
            attempted.append({"count":count,"class":type(exc).__name__})
            continue
        updated=apply_independent_progress(
            state=state,verified=signed,head=head,now=now,cycle=cycle)
        return {"status":"BSA303_SIGNED_SCIENTIFIC_PROGRESS_RECONCILED",
                "acceptedCount":updated["acceptedCount"],
                "pendingCount":updated["pendingCount"],
                "higherFrontiersQuarantined":attempted,
                "independentVerifierExecuted":True,
                "publicationAuthorized":False}
    return {"status":"BSA303_NO_INDEPENDENT_SIGNED_FRONTIER_ADMITTED",
            "priorAcceptedCount":state.get("scienceAcceptance",{}).get("acceptedCount"),
            "higherFrontiersQuarantined":attempted,
            "independentVerifierExecuted":False,
            "publicationAuthorized":False}

"""Bosla source-free continuous development handoff (BSA257).

Runs every eligible *implemented* successor inside one normal worker call.
No arbitrary shell commands, untrusted registry imports, duplicate retries,
new model requests, textbook substitutions or academic gate bypass.
When a new verified stage is implemented, register it below; the worker's
control flow does not need another conversation or change to dispatch it.
"""
from __future__ import annotations
from typing import Any,Callable

from app_generator.runtime.v3_post_v27_five_proof_producers import _STATUS28
from app_generator.runtime.v3_post_v28_source_visual_pilot import (
    _STATUS29,run_post_v28_private_visual_pilot,
)
from app_generator.runtime.v3_post_v29_real_browser_pixels import (
    _STATUS30,run_post_v29_real_browser_pixels,
)
from app_generator.runtime.v3_post_v30_bounded_mcq_semantics import (
    _STATUS31,run_post_v30_independent_mcq_semantics,
)
from app_generator.runtime.v3_post_v31_other_mcq_locale_roles import (
    _STATUS32,run_post_v31_other_eight_mcq_localized_proofs,
)

# Exact source-free stage statuses, not user-facing milestone names. Bounded
# length limits a buggy new successor from causing a runaway loop.
_TRANSITIONS={
    _STATUS28:(_STATUS29,"privateSourceVisualPilot",
               run_post_v28_private_visual_pilot),
    _STATUS29:(_STATUS30,"privateBrowserPixelPilot",
               run_post_v29_real_browser_pixels),
    _STATUS30:(_STATUS31,"privateMcqSemanticsPilot",
               run_post_v30_independent_mcq_semantics),
    _STATUS31:(_STATUS32,"privateOtherMcqWitnessPilot",
               run_post_v31_other_eight_mcq_localized_proofs),
}
_MAX_NEW_STAGES_PER_INVOCATION=4


def advance_eligible_verified_development_stages(
    *,repo,private,ready,v9,v11,v12,prior_stage:dict[str,Any],
)->dict[str,Any]:
    """Continue all *presently executable* local stages; no planning-only PASS."""
    if (not isinstance(prior_stage,dict)
            or prior_stage.get("status")!=_STATUS28
            or prior_stage.get("newProviderCalls")!=0
            or prior_stage.get("publicationAuthorized") is not False
            or prior_stage.get("formalAcademicPASS")!=0
            or prior_stage.get("completeAcademicProofGatesStillOpen")!=90):
        raise ValueError("BSA257_CANNOT_ADVANCE_UNVERIFIED_SOURCE_FREE_FRONTIER")
    current=prior_stage
    executed=[]
    seen={current["status"]}
    output={}
    for _ in range(_MAX_NEW_STAGES_PER_INVOCATION):
        link=_TRANSITIONS.get(current["status"])
        if link is None:
            break
        next_status,key,handler=link
        if next_status in seen:
            raise ValueError("BSA257_AUTONOMOUS_DEVELOPMENT_CYCLE")
        new=handler(repo,private,ready,v9,v11,v12,current)
        if (not isinstance(new,dict) or new.get("status")!=next_status
                or new.get("publicationAuthorized") is not False
                or new.get("fullAcademicPASS")!=0
                or new.get("completeAcademicProofGatesStillOpen")!=90
                or new.get("newModelCalls")!=0):
            raise ValueError("BSA257_SUCCESSOR_STAGE_NOT_REALLY_ACCEPTED")
        executed.append(next_status)
        output[key]=new
        current=new
        seen.add(current["status"])
    else:
        if _TRANSITIONS.get(current["status"]) is not None:
            raise ValueError("BSA257_AUTONOMOUS_STAGE_BUDGET_EXHAUSTED")
    if not executed:
        raise ValueError("BSA257_WORKER_STOPPED_WITH_OBVIOUS_EXECUTABLE_STAGE")
    # This is a *verified implementation frontier*, not academic acceptance.
    return {
        "status":"AUTONOMOUSLY_ADVANCED_ALL_REGISTERED_SAFE_STAGES_TO_CURRENT_BOUNDARY",
        "stagesExecutedThisRun":len(executed),
        "sourceFreeStagesExecuted":executed,
        "nextEligibleMilestone":current.get("nextEligibleMilestone"),
        "academicPASS":0,
        "publicationAuthorized":False,
        "newModelCalls":0,
        **output,
    }

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
from app_generator.runtime.v3_post_v32_interactive_mutation_proofs import (
    _STATUS34, run_post_v32_interactive_mutation_proofs,
)
from app_generator.runtime.v3_post_v34_interactive_source_roles import (
    _STATUS35,run_post_v34_interactive_source_roles,
)
from app_generator.runtime.v3_post_v35_semantic_task_dispatch import (
    _STATUS36,run_post_v35_semantic_task_dispatch,
)
from app_generator.runtime.v3_blocker_isolated_development import (
    run_safe_isolated_development_lanes,
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
    _STATUS32:(_STATUS34,"privateInteractiveMutationPilot",
               run_post_v32_interactive_mutation_proofs),
    _STATUS34:(_STATUS35,"privateInteractiveSourceRolesPilot",
               run_post_v34_interactive_source_roles),
    _STATUS35:(_STATUS36,"privateSemanticTaskDispatch",
               run_post_v35_semantic_task_dispatch),
}
_MAX_NEW_STAGES_PER_INVOCATION=7


def advance_eligible_verified_development_stages(
    *,repo,private,ready,v9,v11,v12,prior_stage:dict[str,Any],
    run_independent_lanes:bool=False,
    persist_long_horizon:bool=False,
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
    try:
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
    except Exception:
        # Dependency-bound science remains STOP, but never strand unrelated
        # source-free regression or content validation. An independent lane
        # keeps a precise signed QUARANTINE receipt. Do not make the source
        # failure PASS or call a provider / publish / retry an uncertain job.
        if run_independent_lanes:
            try:
                run_safe_isolated_development_lanes(
                    repo=repo,private=private,ready=ready,
                    completed_dependencies=(
                        {"v32_source_chain"} if current["status"] in {_STATUS32, _STATUS34, _STATUS35, _STATUS36}
                        else set()),
                    blocked_operation="source_bound_academic_successor_chain")
            except Exception:
                # Preserve original security/scientific stop. No new lane
                # receipt can be trusted if its own identity/path is invalid.
                pass
        raise
    isolation={}
    if run_independent_lanes:
        isolation=run_safe_isolated_development_lanes(
            repo=repo,private=private,ready=ready,
            completed_dependencies=(
                {"v32_source_chain"} if current["status"] in {_STATUS32, _STATUS34, _STATUS35, _STATUS36}
                else set()))
    independent_ok=(not run_independent_lanes or
                    isolation.get("status")=="INDEPENDENT_SAFE_LANES_ALL_VERIFIED")
    # BSA268: V36 is the last ENGINEERING-ONLY semantic-inventory milestone.
    # An eighth 0-acceptance stage would recreate the historical defect cycle.
    # Substantive academic proof producers belong in a separate independently
    # verified acceptance lane; no other safe repair lane is disabled.
    if _STATUS36 in _TRANSITIONS:
        raise ValueError("BSA268_ZERO_PROOF_SCAFFOLDING_CYCLE_FORBIDDEN")
    if current.get("fullAcademicProofTasksAccepted",0)!=0:
        raise ValueError("BSA268_SOURCE_FREE_CANNOT_CLAIM_ACADEMIC_PROOF")
    if current.get("completeAcademicProofGatesStillOpen",90)!=90:
        raise ValueError("BSA268_SOURCE_FREE_CANNOT_CLOSE_ACADEMIC_GATE")
    # This is a *verified implementation frontier*, not academic acceptance.
    handoff={
        "status":("AUTONOMOUSLY_ADVANCED_ALL_REGISTERED_SAFE_STAGES_TO_CURRENT_BOUNDARY"
                  if independent_ok else
                  "AUTONOMOUSLY_ADVANCED_ELIGIBLE_LANES_WITH_QUARANTINE"),
        "stagesExecutedThisRun":len(executed),
        "sourceFreeStagesExecuted":executed,
        "developmentOutcomeClass":"ENGINEERING_VERIFIED_NOT_ACADEMIC_ACCEPTANCE",
        "academicProofTasksAcceptedThisRun":0,
        "academicAcceptanceAdvanced":False,
        "academicProofProducerRequired":current["status"]==_STATUS36,
        "academicEvidenceNextStep":"BUILD_SEPARATE_INDEPENDENT_SOURCE_BOUND_PROOF_PRODUCER",
        "engineeringOnlyFrontierTerminal":current["status"]==_STATUS36,
        "nextEligibleMilestone":current.get("nextEligibleMilestone"),
        "academicPASS":0,
        "publicationAuthorized":False,
        "newModelCalls":0,
        **({"isolatedDevelopmentLanes":isolation} if run_independent_lanes else {}),
        **output,
    }
    if persist_long_horizon:
        from app_generator.runtime.v3_long_horizon_development import (
            persist_long_horizon_development,
        )
        handoff["longHorizonDevelopment"]=persist_long_horizon_development(
            private=private,ready=ready,development=handoff)
    return handoff

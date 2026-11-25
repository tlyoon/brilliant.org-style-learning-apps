"""Read Bosla's durable development frontier before any resumed code work.

An operational status command, not a background scheduler or academic grader.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys

from app_generator.runtime.v3_long_horizon_development import (
    read_long_horizon_development,
)


def main() -> int:
    home=os.environ.get("LOCALAPPDATA")
    if not home:
        print(json.dumps({
            "status":"BOSLA_LONG_HORIZON_OWNER_YOGA6_REQUIRED",
            "autonomousCodeWritingConfigured":False,
        },sort_keys=True))
        return 2
    private=Path(home)/"Microvid"/"BoslaV3ReviewYoga6"
    try:
        checkpoint=read_long_horizon_development(private)
    except (OSError,ValueError,KeyError) as exc:
        print(json.dumps({
            "status":"BOSLA_LONG_HORIZON_VERIFIED_CHECKPOINT_UNAVAILABLE",
            "errorClass":type(exc).__name__,
            "academicProofAcceptanceEstablished":False,
            "autonomousCodeWritingConfigured":False,
        },sort_keys=True))
        return 2
    outcome={
        "status":"BOSLA_LONG_HORIZON_VERIFIED_CROSS_SESSION_FRONTIER",
        "gitHead":checkpoint["gitHead"],
        "sourceSha256":checkpoint["sourceSha256"],
        "candidateSha256":checkpoint["candidateSha256"],
        "academicProofTasksAccepted":checkpoint["academicAcceptedProofTaskCount"],
        "fullAcademicProofTasksStillOpen":checkpoint["fullSemanticProofTasksStillOpen"],
        "completeAcademicProofGatesStillOpen":checkpoint[
            "completeAcademicProofGatesStillOpen"],
        "consecutiveZeroProofCodeHeads":checkpoint[
            "consecutiveZeroProofCodeHeads"],
        "nextUnfinishedDevelopmentAction":checkpoint[
            "nextUnfinishedDevelopmentAction"],
        "nextActionStatus":checkpoint["nextActionStatus"],
        "engineeringRecoveryMayContinue":checkpoint[
            "sourceFreeRecoveryMayContinue"],
        "autonomousCodeWritingConfigured":checkpoint[
            "unboundedCodeWritingAgentConfiguredHere"],
        "publicationAuthorized":checkpoint["publicationAuthorized"],
        "academicAcceptancesSource":"SIGNED_SOURCE_FREE_BASELINE_ONLY",
    }
    # A separate, independently reverified academic proof may advance the
    # count beyond the immutable zero-proof source-free baseline. Never trust
    # a bare latest pointer without rechecking original PDF, frozen candidate,
    # signed V36 partition, rational countermodel and immutable proof receipt.
    from app_generator.runtime.v3_first_academic_proof_admission import _FRONTIER
    from app_generator.runtime.v3_academic_cross_head_continuity import (
        verify_academic_across_git_heads,
    )
    if (private/"long-horizon-development"/_FRONTIER).exists():
        try:
            academic=verify_academic_across_git_heads(private=private)
        except (OSError,ValueError,KeyError,TypeError) as exc:
            print(json.dumps({
                "status":"BOSLA_ACADEMIC_PROOF_FRONTIER_UNTRUSTED",
                "errorClass":type(exc).__name__,
                "academicProofAcceptanceEstablished":False,
                "publicationAuthorized":False,
            },sort_keys=True))
            return 2
        outcome.update({
            "status":"BOSLA_LONG_HORIZON_AND_FIRST_ACADEMIC_PROOF_INDEPENDENTLY_VERIFIED",
            "academicAcceptancesSource":"SEPARATE_SIGNED_RECOMPUTED_ACADEMIC_LANE",
            "academicProofTasksAccepted":academic["independentlyAcceptedAcademicTasks"],
            "fullAcademicProofTasksStillOpen":academic["otherFullAcademicTasksStillOpen"],
            "completeAcademicProofGatesStillOpen":academic["completeAcademicProofGatesStillOpen"],
            "nextUnfinishedDevelopmentAction":"EXTEND_INDEPENDENT_MC_Q_DISTRACTOR_PROOFS_TO_REMAINING_26",
            "nextActionStatus":"NEW_PROOF_HANDLERS_STILL_REQUIRED",
            "verifiedAcademicProofTaskId":academic["taskId"],
            "academicProofReceiptSha256":academic["proofReceiptSha256"],
            "academicActivityPASS":academic["fullAcademicActivityPASS"],
            "academicProofOriginGitHead":academic["academicProofOriginGitHead"],
            "acceptedProofCarriedAcrossGitHead":academic["carriedAcrossGitHead"],
        })
    print(json.dumps(outcome,sort_keys=True))
    return 0


if __name__=="__main__":
    sys.exit(main())

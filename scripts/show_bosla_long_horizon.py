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
    print(json.dumps({
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
    },sort_keys=True))
    return 0


if __name__=="__main__":
    sys.exit(main())

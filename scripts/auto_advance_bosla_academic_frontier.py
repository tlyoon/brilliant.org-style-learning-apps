"""Run Bosla's full eligible signed academic continuation without user pauses.

This is a synchronous, restart-safe owner Yoga6 CLI, NOT a new recurring
scheduled task or unbounded background agent. Always checks hosted exact CI
and original selected textbook evidence before any new academic acceptance.
If an individual science task needs a new reviewed proof handler, do not
forge it; preserve the other eligible work and report the exact frontier.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys

from app_generator.runtime.v3_autonomous_academic_advancement import (
    advance_all_eligible_academic_actions,
)
from app_generator.runtime.v3_newton_force_academic_batch_admission import (
    verify_newton_batch_across_git_heads,
)

ROOT=Path(__file__).resolve().parents[1]


def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-steps",type=int,default=8)
    args=parser.parse_args(argv)
    home=os.environ.get("LOCALAPPDATA")
    if not home:
        print(json.dumps({"status":"BSA276_AUTHORIZED_YOGA6_OWNER_REQUIRED"}))
        return 2
    private=Path(home)/"Microvid"/"BoslaV3ReviewYoga6"
    try:
        result=advance_all_eligible_academic_actions(
            repo=ROOT,private=private,max_steps=args.max_steps)
        # Guard: the durable normal horizon reader must agree before a
        # command can claim new academic acceptance.
        from app_generator.runtime.v3_long_horizon_development import (
            read_long_horizon_development,
        )
        state=read_long_horizon_development(private)
        verified=verify_newton_batch_across_git_heads(private=private)
        if (state["gitHead"]!=result["currentGitHead"]
            or verified["independentlyAcceptedAcademicTasks"]!=
               result["academicProofTasksAccepted"]
            or verified["pendingMcqDistractorScienceTasks"]!=
               result["pendingMcqDistractorScienceTasks"]):
            raise ValueError("BSA276_AUTONOMOUS_FRONTIER_CANNOT_SELF_ATTEST")
        print(json.dumps(result,sort_keys=True))
        return 0
    except (OSError,ValueError,KeyError,TypeError,IndexError,
            ArithmeticError) as e:
        print(json.dumps({
            "status":"BSA276_ELIGIBLE_ACADEMIC_STEP_UNVERIFIED",
            "errorClass":type(e).__name__,
            "errorCode":str(e) if isinstance(e,ValueError)
                else "AUTHORITATIVE_SOURCE_OR_SIGNED_EVIDENCE_UNAVAILABLE",
            "academicAcceptanceAdvanced":False,
            "publicationAuthorized":False,
        },sort_keys=True))
        return 2


if __name__=="__main__":
    sys.exit(main())

"""Bosla BSA270: explicit separate academic evidence lane on owner Yoga6.

--admit: requires latest clean exact Git HEAD and hosted CI success, genuine
source-free owner V36 receipt, original pinned PDF and frozen candidate.
--verify: reopens and independently recomputes all evidence without mutation.
No provider calls, no external files, no PR merge or publication.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_versioned_readiness import (
    _git_info,_git_clean,_hosted_runs,_exact_ci_success,
)
from app_generator.runtime.v3_first_academic_proof_admission import (
    admit_first_independent_distractor,verify_first_academic_frontier,
)
from app_generator.runtime.v3_long_horizon_development import (
    read_long_horizon_development,
)

ROOT=Path(__file__).resolve().parents[1]


def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--admit",action="store_true")
    group.add_argument("--verify",action="store_true")
    arg=parser.parse_args(argv)
    home=os.environ.get("LOCALAPPDATA")
    if not home:
        print(json.dumps({"status":"BSA270_YOGA6_OWNER_ENVIRONMENT_REQUIRED"}))
        return 2
    private=Path(home)/"Microvid"/"BoslaV3ReviewYoga6"
    try:
        horizon=read_long_horizon_development(private)
        head,branch=_git_info(ROOT)
        if arg.admit and (head!=horizon.get("gitHead")
                          or not _git_clean(ROOT)
                          or not _exact_ci_success(
                              _hosted_runs(ROOT,branch),head)):
            raise ValueError("BSA270_EXACT_CLEAN_CODE_HEAD_CI_REQUIRED")
        ready={"gitHead":horizon["gitHead"],
               "proposalSha256":horizon["proposalSha256"]}
        outcome=(admit_first_independent_distractor(
                    private=private,ready=ready)
                 if arg.admit else
                 verify_first_academic_frontier(
                    private=private,ready=ready))
        print(json.dumps(outcome,sort_keys=True))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as error:
        print(json.dumps({
            "status":"BSA270_ACADEMIC_ADMISSION_UNVERIFIED",
            "errorClass":type(error).__name__,
            "errorCode":str(error) if isinstance(error,ValueError) else
                "OWNER_PRIVATE_INPUT_OR_PROOF_UNAVAILABLE",
            "academicProofAccepted":False,
            "publicationAuthorized":False,
        },sort_keys=True))
        return 2


if __name__=="__main__":
    sys.exit(main())

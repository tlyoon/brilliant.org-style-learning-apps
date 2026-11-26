"""BSA278 separate original-Serway paired glider A10-A12 academic admission.

--admit requires clean current exact-hosted CI, authentic same-HEAD Yoga6
V36, signed prior original-source A1-A9 receipts and original fourth signed
V36 task partition. --verify reopens actual old/current source and exact
rational kinetic energy and vector momentum, without provider requests.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from app_generator.runtime.v3_long_horizon_development import read_long_horizon_development
from app_generator.runtime.v3_versioned_readiness import (
    _git_info,_git_clean,_hosted_runs,_exact_ci_success,
)
from app_generator.runtime.v3_paired_glider_academic_batch_admission import (
    admit_paired_glider_batch, verify_paired_glider_batch_across_git_heads,
)

ROOT=Path(__file__).resolve().parents[1]


def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--admit",action="store_true")
    group.add_argument("--verify",action="store_true")
    args=parser.parse_args(argv)
    home=os.environ.get("LOCALAPPDATA")
    if not home:
        print(json.dumps({"status":"BSA278_AUTHORIZED_OWNER_SOURCE_MISSING"}))
        return 2
    private=Path(home)/"Microvid"/"BoslaV3ReviewYoga6"
    try:
        state=read_long_horizon_development(private)
        head,branch=_git_info(ROOT)
        if args.admit and (
            state["gitHead"]!=head or not _git_clean(ROOT)
            or not _exact_ci_success(_hosted_runs(ROOT,branch),head)
        ):
            raise ValueError("BSA278_EXACT_HOSTED_CLEAN_HEAD_OWNER_V36_REQUIRED")
        result=(admit_paired_glider_batch(private=private)
                if args.admit else verify_paired_glider_batch_across_git_heads(
                    private=private))
        print(json.dumps(result,sort_keys=True))
        return 0
    except (OSError,ValueError,KeyError,TypeError,IndexError,ArithmeticError) as exc:
        print(json.dumps({
            "status":"BSA278_PAIRED_GLIDER_SOURCE_BOUND_ACADEMIC_PROOF_UNVERIFIED",
            "errorClass":type(exc).__name__,
            "errorCode":str(exc) if isinstance(exc,ValueError)
                else "SIGNED_OWNER_SOURCE_OR_ACADEMIC_RECEIPT_INVALID",
            "academicAcceptanceAdvanced":False,
            "publicationAuthorized":False,
        },sort_keys=True))
        return 2


if __name__=="__main__":
    sys.exit(main())

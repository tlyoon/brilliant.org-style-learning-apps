"""BSA277 separate owner original-source Newton A7–A9 science admission.

--admit requires clean exact hosted GitHub CI, genuine same-head Yoga6 V36,
signed current-head original source registry and intact A1–A6 receipts.
--verify independently opens historical and current selected textbook,
candidate, third V36 partition, rational momentum-rate proof and signatures.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys

from app_generator.runtime.v3_long_horizon_development import (
    read_long_horizon_development,
)
from app_generator.runtime.v3_versioned_readiness import (
    _git_info,_git_clean,_hosted_runs,_exact_ci_success,
)
from app_generator.runtime.v3_newton_force_academic_batch_admission import (
    admit_newton_source_bound_batch,verify_newton_batch_across_git_heads,
)

ROOT=Path(__file__).resolve().parents[1]


def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--admit",action="store_true")
    mode.add_argument("--verify",action="store_true")
    args=parser.parse_args(argv)
    home=os.environ.get("LOCALAPPDATA")
    if not home:
        print(json.dumps({"status":"BSA277_PRIVATE_OWNER_ORIGINAL_SOURCE_MISSING"}))
        return 2
    private=Path(home)/"Microvid"/"BoslaV3ReviewYoga6"
    try:
        current=read_long_horizon_development(private)
        head,branch=_git_info(ROOT)
        if args.admit and (
            current["gitHead"]!=head or not _git_clean(ROOT)
            or not _exact_ci_success(_hosted_runs(ROOT,branch),head)
        ):
            raise ValueError("BSA277_CLEAN_EXACT_HEAD_CI_OWNER_V36_REQUIRED")
        result=(admit_newton_source_bound_batch(private=private)
                if args.admit else verify_newton_batch_across_git_heads(
                    private=private))
        print(json.dumps(result,sort_keys=True))
        return 0
    except (OSError,ValueError,KeyError,TypeError,IndexError,ArithmeticError) as e:
        print(json.dumps({
            "status":"BSA277_NEWTON_ACADEMIC_PROOF_ADMISSION_UNVERIFIED",
            "errorClass":type(e).__name__,
            "errorCode":str(e) if isinstance(e,ValueError)
                else "SIGNATURE_OR_ORIGINAL_SOURCE_EVIDENCE_INVALID",
            "academicAcceptanceAdvanced":False,
            "publicationAuthorized":False,
        },sort_keys=True))
        return 2


if __name__=="__main__":
    sys.exit(main())

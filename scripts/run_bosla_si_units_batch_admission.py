"""BSA276: separate 3-task SI-science academic admission on genuine Yoga6.

--admit requires clean same exact-HEAD hosted CI, authentic original Serway
textbook and current owner V36, A1/A2/A3 historical receipts, and signed
BSA274 audit. It never merges/releases or uploads/downloads the source.
--verify independently recomputes all original/current evidence.
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
from app_generator.runtime.v3_si_units_academic_batch_admission import (
    admit_si_unit_science_batch,verify_si_unit_batch_across_git_heads,
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
        print(json.dumps({"status":"BSA276_OWNER_PRIVATE_ORIGINAL_SOURCE_REQUIRED"}))
        return 2
    private=Path(home)/"Microvid"/"BoslaV3ReviewYoga6"
    try:
        latest=read_long_horizon_development(private)
        head,branch=_git_info(ROOT)
        if args.admit and (
            latest["gitHead"]!=head or not _git_clean(ROOT)
            or not _exact_ci_success(_hosted_runs(ROOT,branch),head)
        ):
            raise ValueError("BSA276_CLEAN_HOSTED_EXACT_HEAD_AND_OWNER_V36_REQUIRED")
        result=(admit_si_unit_science_batch(private=private)
                if args.admit else
                verify_si_unit_batch_across_git_heads(private=private))
        print(json.dumps(result,sort_keys=True))
        return 0
    except (ValueError,OSError,TypeError,KeyError,IndexError,ArithmeticError) as e:
        print(json.dumps({
            "status":"BSA276_NEW_SI_SCIENCE_ADMISSION_NOT_PROVEN",
            "errorClass":type(e).__name__,
            "errorCode":str(e) if isinstance(e,ValueError) else
                "SIGNED_SOURCE_OR_PRIOR_ACCEPTANCE_INVALID",
            "academicAcceptanceAdvanced":False,
            "publicationAuthorized":False,
        },sort_keys=True))
        return 2


if __name__=="__main__":
    sys.exit(main())

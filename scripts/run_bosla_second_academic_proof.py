"""BSA273: owner Yoga6 second independent MCQ science proof admission/readback.

No source-free count is rewritten, no original proof replaced. --admit needs
latest clean exact Git HEAD + hosted successful CI + genuine owner V36 and the
previous independently accepted BSA270 first academic proof.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys

from app_generator.runtime.v3_versioned_readiness import (
    _git_info, _git_clean, _hosted_runs, _exact_ci_success,
)
from app_generator.runtime.v3_long_horizon_development import read_long_horizon_development
from app_generator.runtime.v3_second_academic_proof_admission import (
    admit_second_independent_distractor, verify_second_academic_across_git_heads,
)

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--admit", action="store_true")
    group.add_argument("--verify", action="store_true")
    arg = parser.parse_args(argv)
    home = os.environ.get("LOCALAPPDATA")
    if not home:
        print(json.dumps({"status":"BSA273_OWNER_YOGA6_REQUIRED"}))
        return 2
    private = Path(home)/"Microvid"/"BoslaV3ReviewYoga6"
    try:
        latest = read_long_horizon_development(private)
        head, branch = _git_info(ROOT)
        if arg.admit and (
            head != latest["gitHead"]
            or not _git_clean(ROOT)
            or not _exact_ci_success(_hosted_runs(ROOT, branch), head)
        ):
            raise ValueError("BSA273_EXACT_CLEAN_HEAD_HOSTED_CI_AND_OWNER_V36_REQUIRED")
        ready = {"gitHead":latest["gitHead"],"proposalSha256":latest["proposalSha256"]}
        result = (admit_second_independent_distractor(private=private,ready=ready)
                  if arg.admit else
                  verify_second_academic_across_git_heads(private=private))
        print(json.dumps(result,sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        print(json.dumps({
            "status":"BSA273_SECOND_ACADEMIC_PROOF_UNVERIFIED",
            "errorClass":type(error).__name__,
            "errorCode":str(error) if isinstance(error, ValueError)
                        else "SOURCE_OR_IMMUTABLE_EVIDENCE_INVALID",
            "academicProofAccepted":False,
            "publicationAuthorized":False,
        },sort_keys=True))
        return 2


if __name__=="__main__":
    sys.exit(main())

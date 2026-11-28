"""Bosla BSA274 executable source-bound academic proof registry.

--preview reopens original selected textbook, signed V36 and BOTH accepted
academic receipts; no new proof acceptance or writes.
--admit signs an immutable owner-private registry AUDIT, not academic tasks,
only on clean exact code HEAD after hosted CI and actual owner V36.
--verify independently reopens all evidence and reads signed audit.
No Gemini requests, extra source PDFs, new scheduler or public release.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys

from app_generator.runtime.v3_academic_proof_registry import (
    audit_source_bound_academic_registry,
)
from app_generator.runtime.v3_academic_proof_registry_receipt import (
    sign_registry_audit, verify_registry_audit,
)
from app_generator.runtime.v3_long_horizon_development import (
    read_long_horizon_development,
)
from app_generator.runtime.v3_versioned_readiness import (
    _git_info, _git_clean, _hosted_runs, _exact_ci_success,
)

ROOT=Path(__file__).resolve().parents[1]


def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preview",action="store_true")
    group.add_argument("--admit",action="store_true")
    group.add_argument("--verify",action="store_true")
    args=parser.parse_args(argv)
    home=os.environ.get("LOCALAPPDATA")
    if not home:
        print(json.dumps({"status":"BSA274_OWNER_PRIVATE_CONTEXT_REQUIRED"}))
        return 2
    private=Path(home)/"Microvid"/"BoslaV3ReviewYoga6"
    try:
        state=read_long_horizon_development(private)
        head,branch=_git_info(ROOT)
        # Only --admit performs a write and requires the new head to have
        # finished a genuine exact-HEAD source-free normal worker.
        if args.admit and (state["gitHead"]!=head or not _git_clean(ROOT)
                          or not _exact_ci_success(
                              _hosted_runs(ROOT,branch),head)):
            raise ValueError("BSA274_CLEAN_EXACT_HEAD_HOSTED_CI_AND_OWNER_V36_REQUIRED")
        if args.preview:
            report=audit_source_bound_academic_registry(private=private)
            print(json.dumps({
                "status":report["status"],
                "sourceFreeGitHead":report["gitHead"],
                "currentGitHead":head,
                "registeredIndependentRuleCount":report["registeredIndependentRuleCount"],
                "acceptedMcqDistractorTaskCount":report["acceptedMcqDistractorTaskCount"],
                "pendingMcqDistractorTaskCount":report["pendingMcqDistractorTaskCount"],
                "fullAcademicTasksStillOpen":report["fullAcademicTasksStillOpen"],
                "completeAcademicProofGatesStillOpen":report["completeAcademicProofGatesStillOpen"],
                "academicAcceptanceAdvanced":False,
                "publicationAuthorized":False,
            },sort_keys=True))
        else:
            result=(sign_registry_audit(private=private) if args.admit
                    else verify_registry_audit(private=private))
            print(json.dumps(result,sort_keys=True))
        return 0
    except (OSError,ValueError,KeyError,TypeError,IndexError) as exc:
        print(json.dumps({
            "status":"BSA274_ACADEMIC_REGISTRY_UNVERIFIED",
            "errorClass":type(exc).__name__,
            "errorCode":str(exc) if isinstance(exc,ValueError)
                else "SOURCE_OR_SIGNED_OWNER_EVIDENCE_INVALID",
            "academicAcceptanceAdvanced":False,
            "publicationAuthorized":False,
        },sort_keys=True))
        return 2


if __name__=="__main__":
    sys.exit(main())

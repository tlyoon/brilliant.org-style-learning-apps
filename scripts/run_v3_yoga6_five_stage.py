"""Only the source-free five-stage V3 private completion child on Yoga 6.

Runs in the pinned existing Selenium 4.47.0 interpreter. No credentials, AI,
source PDF, student records, public deployment or Git writes.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))


def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root",required=True,type=Path)
    args=parser.parse_args(argv)
    try:
        from scripts.run_v3_yoga6_acceptance import _supported_python
        if not _supported_python(Path(sys.executable)):
            raise ValueError("V3_FIVE_STAGE_NOT_PINNED_SELENIUM_INTERPRETER")
        from app_generator.runtime.v3_yoga6_recovery import (
            checked_private_root,
        )
        local=os.environ.get("LOCALAPPDATA")
        if not local:
            raise ValueError("V3_FIVE_STAGE_MISSING_LOCALAPPDATA")
        private=checked_private_root(
            args.private_root,localappdata=Path(local))
        from app_generator.runtime.v3_versioned_readiness import (
            evaluate_current_versioned_evidence,
        )
        from app_generator.runtime.v3_five_stage_completion import (
            run_five_stage_completion,
        )
        readiness=evaluate_current_versioned_evidence(ROOT,private)
        result=run_five_stage_completion(
            ROOT,private,readiness,exercise_candidate=True)
    except (OSError,ValueError,TypeError,KeyError,
            ImportError,RuntimeError) as error:
        code=str(error)
        print(json.dumps({
            "status":"STOP_FIVE_STAGE_AUTONOMOUS_COMPLETION",
            "errorClass":type(error).__name__,
            "errorCode":code if code.startswith("V3_FIVE_STAGE_")
                        and len(code)<128 else None,
            "publicationAuthorized":False,"paidGeminiCalls":0,
        },sort_keys=True))
        return 3
    except Exception as error:
        # Selenium transient failures are classified by class only, not raw
        # URL/error text. Parent may retry at most one browser-only attempt.
        print(json.dumps({
            "status":"STOP_FIVE_STAGE_AUTONOMOUS_COMPLETION",
            "errorClass":type(error).__name__,
            "publicationAuthorized":False,"paidGeminiCalls":0,
        },sort_keys=True))
        return 3
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())

"""Real Chrome QA for source-bound *new* Section9.6 corrected index9.

Invoked from normal source-free Yoga6 worker in the existing supported
Selenium virtualenv, never from Gemini or a paid browser source.
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

from app_generator.runtime.v3_yoga6_recovery import checked_private_root
from app_generator.runtime.native_workstation_guard import (
    require_authorized_native_review_host,
)
from scripts.run_v3_native_gemini_review import AUTHORITY
from app_generator.runtime.v3_science_candidate_browser import (
    advance_science_revision_browser_qa,
)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root",type=Path)
    args=parser.parse_args(argv)
    local=os.environ.get("LOCALAPPDATA")
    if not local:
        print(json.dumps({"status":"STOP_SCIENCE_BROWSER_MISSING_LOCALAPPDATA",
                          "publicationAuthorized":False}))
        return 3
    try:
        require_authorized_native_review_host(AUTHORITY)
        private=checked_private_root(
            args.private_root or Path(local)/"Microvid"/"BoslaV3ReviewYoga6",
            localappdata=Path(local))
        result=advance_science_revision_browser_qa(
            ROOT,ROOT/"content"/"chapter-9",private)
        if (result.get("status")!=
                "ACTUAL_INDEX9_SCIENCE_REVISION_BROWSER_QA_PASS_NOT_SCIENTIFIC_QA"
                or result.get("publicationAuthorized") is not False
                or result.get("genuineGeminiReviewsAdded")!=0):
            raise ValueError("V3_SCIENCE_BROWSER_NOT_ACCEPTED")
        print(json.dumps(result,sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({
            "status":"STOP_SCIENCE_REVISION_REAL_CHROME_"+
                     type(exc).__name__,
            "publicationAuthorized":False}))
        return 3


if __name__=="__main__":
    raise SystemExit(main())

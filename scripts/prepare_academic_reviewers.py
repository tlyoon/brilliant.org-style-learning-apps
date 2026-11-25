"""Inspect or open isolated Gemini academic-reviewer sign-in windows.

Default: read-only status. --open-missing-windows opens ordinary Google
Chrome login UI on the authorized Windows PC, without reading credentials
or sending model prompts. Never copy the generator's authenticated profile.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from app_generator.config import load_config
from app_generator.gemini.reviewer_profile_setup import (
    inspect_reviewer_profiles,open_missing_signin_windows,
)


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config",required=True,type=Path)
    p.add_argument("--open-missing-windows",action="store_true",
                   help="open ONLY dedicated, absent reviewer browser profiles")
    a=p.parse_args()
    try:
        cfg=load_config(a.config)
        report=(open_missing_signin_windows(cfg) if a.open_missing_windows
                else inspect_reviewer_profiles(cfg))
        print(json.dumps(report,indent=2))
        return 0
    except (ValueError,OSError,TypeError) as exc:
        print(json.dumps({
            "status":"BLOCKED",
            "error":str(exc)[:250],
            "academicQA":"REVIEW_REQUIRED",
            "publicationAuthorized":False,
        }))
        return 2


if __name__=="__main__":
    raise SystemExit(main())

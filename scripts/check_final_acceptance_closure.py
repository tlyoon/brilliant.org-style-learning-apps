"""Source-free BOSLA closure decision. Does not start acceptance campaigns."""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from app_generator.validation.final_acceptance_closure import final_disposition


def main() -> int:
    try:
        report=final_disposition()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        print(json.dumps({"status":"STOP_INVALID_CLOSURE_CHARTER",
                          "publicationAuthorized":False},sort_keys=True))
        return 2
    print(json.dumps(report,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())

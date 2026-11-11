"""Read-only active BOSLA V3 automatic technical-completion status.

Historical frozen Chapter 9 V2 outcomes are still independently readable,
but they no longer impose independent review, real-pilot or manual release
requirements on current technical completion.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_generator.validation.autonomous_completion import active_disposition
from app_generator.validation.final_acceptance_closure import final_disposition


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-v2", action="store_true")
    options = parser.parse_args(argv)
    try:
        report = final_disposition() if options.historical_v2 else active_disposition()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        print(json.dumps({"status":"STOP_INVALID_ACTIVE_ACCEPTANCE_POLICY",
                          "publicationAuthorized":False},sort_keys=True))
        return 2
    print(json.dumps(report,sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

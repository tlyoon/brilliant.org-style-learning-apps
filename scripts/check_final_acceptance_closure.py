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

from app_generator.validation.autonomous_completion import (
    active_disposition, assessment_progress,
)
from app_generator.validation.final_acceptance_closure import final_disposition


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-v2", action="store_true")
    parser.add_argument("--package", type=Path)
    parser.add_argument("--assessment-file", type=Path)
    parser.add_argument("--release-receipt", type=Path)
    options = parser.parse_args(argv)
    try:
        if options.historical_v2:
            if options.package or options.assessment_file or options.release_receipt:
                raise ValueError("V3_PROGRESS_FLAGS_NOT_VALID_FOR_V2_HISTORY")
            report = final_disposition()
        elif options.package is not None:
            package=options.package
            if (package.is_symlink() or not package.is_file()
                or package.name != "package.json"
                or not package.resolve().is_relative_to((ROOT/"content").resolve())):
                raise ValueError("V3_PACKAGE_NOT_REPOSITORY_CONTENT")
            if options.assessment_file:
                file=options.assessment_file
                if (file.is_symlink() or not file.is_file()
                    or file.stat().st_size > 8_000_000):
                    raise ValueError("V3_PRIVATE_PROGRESS_UNSAFE")
                assessment=json.loads(file.read_text(encoding="utf-8"))
            else:
                assessment=None
            report = assessment_progress(
                package.read_bytes(),assessment,
                release_receipt=options.release_receipt,
            )
        else:
            if options.assessment_file or options.release_receipt:
                raise ValueError("V3_PACKAGE_REQUIRED_FOR_PRIVATE_EVIDENCE")
            report = active_disposition()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        print(json.dumps({"status":"STOP_INVALID_ACTIVE_ACCEPTANCE_POLICY",
                          "publicationAuthorized":False},sort_keys=True))
        return 2
    print(json.dumps(report,sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

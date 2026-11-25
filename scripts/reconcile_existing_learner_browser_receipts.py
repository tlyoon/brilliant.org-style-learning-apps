"""Verify immutable private learner browser screenshots without rerunning Chrome.

Checks package/code Git identity, records, SHA-256, PNG CRC and decompression.
This never certifies scientific, visual-semantic or academic acceptance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_generator.validation.learner_browser_receipt_integrity import (
    reconcile_browser_receipts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen-git-sha", required=True)
    parser.add_argument("--packages", nargs="+", required=True)
    parser.add_argument("--receipt-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        dest = args.out
        if dest.is_symlink() or dest.exists():
            raise ValueError("IMMUTABLE_OUTPUT_ALREADY_EXISTS")
        parent = dest.parent.resolve(strict=True)
        if (not parent.is_dir() or parent.is_relative_to(ROOT.resolve())
            or not dest.name.endswith(".json")):
            raise ValueError("PRIVATE_OUTPUT_REQUIRED")
        report = reconcile_browser_receipts(
            ROOT, frozen_commit=args.frozen_git_sha,
            packages=args.packages, receipt_root=args.receipt_root,
        )
        with dest.open("x", encoding="utf-8") as f:
            json.dump(report, f, sort_keys=True, indent=2)
            f.write("\n")
    except (OSError, ValueError, TypeError, KeyError, IndexError,
            UnicodeError, json.JSONDecodeError):
        print(json.dumps({
            "status": "STOP_UNVERIFIED_BROWSER_RECEIPT_INTEGRITY",
            "academicAcceptanceGranted": False,
            "publicationAuthorized": False,
        }, sort_keys=True))
        return 2
    print(json.dumps({
        "status": report["status"],
        "frozenGitSha": report["frozenGitSha"],
        "packagesChecked": report["packagesChecked"],
        "existingRowsChecked": report["existingRowsChecked"],
        "screenshotsShaAndPngIntegrityVerified":
            report["screenshotsShaAndPngIntegrityVerified"],
        "academicAcceptanceGranted": False,
        "publicationAuthorized": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

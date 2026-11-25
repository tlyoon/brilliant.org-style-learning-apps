"""Offline learner acceptance coverage audit of exact candidate package and receipt.

Checks per-activity EN/MS/ZH mobile/desktop interaction coverage, rejecting
empty aggregate-only browser smoke. Does not launch a browser, read a PDF,
call an AI provider, certify scientific meaning or authorize publication.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_generator.validation.learner_coverage_gate import audit_full_learner_coverage


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package",required=True,type=Path)
    parser.add_argument("--receipt",required=True,type=Path)
    args=parser.parse_args(argv)
    try:
        if args.package.is_symlink() or args.receipt.is_symlink():
            raise ValueError("linked package or receipt")
        raw=args.package.read_bytes()
        package=json.loads(raw.decode("utf-8"))
        evidence=json.loads(args.receipt.read_text(encoding="utf-8"))
        if (evidence.get("packageSha256") != sha256(raw).hexdigest() or
                evidence.get("publicationAuthorized") is not False):
            raise ValueError("unbound or release-enabled learner receipt")
        result=audit_full_learner_coverage(package,evidence)
        print(json.dumps(result,sort_keys=True))
        return 0 if result["status"]=="COMPLETE_COVERAGE_METADATA_UNVERIFIED" else 2
    except (ValueError,TypeError,KeyError,OSError,UnicodeError,json.JSONDecodeError):
        print(json.dumps({
            "status":"INVALID_OR_UNVERIFIED_LEARNER_RECEIPT",
            "interactiveLearnerAcceptanceVerified":False,
            "publicationAuthorized":False,
        },sort_keys=True))
        return 2


if __name__=="__main__":
    raise SystemExit(main())

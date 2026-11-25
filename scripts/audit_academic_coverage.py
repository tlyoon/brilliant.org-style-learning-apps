"""Metadata-only academic gap audit for an exact candidate package and QA matrix.

Never opens or uploads original PDF, calls Gemini/ChatGPT, writes a file,
approves academic claims or publishes. This inventories missing independent
source-grounded proof and refuses forged/stale package lineage.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from app_generator.validation.academic_coverage_gate import audit_academic_coverage


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--matrix", required=True, type=Path)
    parser.add_argument("--source-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        if args.package.is_symlink() or args.matrix.is_symlink():
            raise ValueError("linked evidence not accepted")
        raw = args.package.read_bytes()
        matrix = json.loads(args.matrix.read_text(encoding="utf-8"))
        result = audit_academic_coverage(
            package_bytes=raw, matrix=matrix, source_sha256=args.source_sha256)
        # Emit only source-bound digests, aggregate counts and fixed category
        # codes. No raw prompts, source excerpts or model responses.
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] == "INDEPENDENT_ACADEMIC_PROOF_REQUIRED" else 2
    except (ValueError, TypeError, KeyError, OSError, UnicodeError, json.JSONDecodeError):
        print(json.dumps({
            "status": "INVALID_OR_UNVERIFIED_ACADEMIC_EVIDENCE",
            "academicQA": "REVIEW_REQUIRED",
            "publicationAuthorized": False,
            "formalAcademicPassCount": 0,
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Verify private original-source screenshots without conferring academic PASS."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from app_generator.validation.private_browser_visual_evidence import verify_browser_visual_evidence


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    for key in ("package", "pdf", "evidence", "out"):
        cli.add_argument("--" + key, required=True, type=Path)
    for key in ("package-sha256", "source-sha256"):
        cli.add_argument("--" + key, required=True)
    args = cli.parse_args()
    try:
        dest = args.out.resolve()
        if dest.is_relative_to(ROOT.resolve()) or dest.exists():
            raise ValueError("immutable private report destination required")
        report = verify_browser_visual_evidence(
            package_file=args.package, source_pdf=args.pdf,
            evidence_dir=args.evidence,
            expected_package_sha256=args.package_sha256,
            expected_source_sha256=args.source_sha256,
        )
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("x", encoding="utf-8") as fp:
            json.dump(report, fp, sort_keys=True, indent=2)
            fp.write("\n")
        print(json.dumps(report, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BLOCKED", "errorClass": type(exc).__name__,
                          "publicationAuthorized": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
"""Read-only page-specific source evidence audit for a controlled PDF.

No source passage or raw PDF is written into Git or standard output. A
VERIFIED_TEXT_ONLY result is not an academic PASS.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app_generator.validation.source_passages import audit_source_anchors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--anchors", type=Path, help="Private per-activity page-indexed quotation receipts")
    parser.add_argument("--pdftotext", default="pdftotext")
    opts = parser.parse_args()
    try:
        package = json.loads(opts.package.read_text(encoding="utf-8"))
        manifest = json.loads(opts.source_manifest.read_text(encoding="utf-8"))
        expected = manifest["sha256"]
        if (len(manifest.get("sources", [])) != 1 or
            manifest["sources"][0]["sha256"] != expected):
            raise ValueError("manifest source identity ambiguous")
        anchors = json.loads(opts.anchors.read_text(encoding="utf-8")) if opts.anchors else []
        if not isinstance(anchors, list):
            raise ValueError("private source anchors must be a list")
        report = audit_source_anchors(package, opts.pdf, expected, anchors, tool=opts.pdftotext)
        print(json.dumps(report, indent=2))
        return 1 if report["fail"] else (0 if report["pending"] == 0 else 2)
    except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "REVIEW_REQUIRED", "error": str(exc)[:300],
                          "publicationAuthorized": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

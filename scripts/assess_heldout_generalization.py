"""Check a frozen, private held-out PDF campaign without executing or publishing.

This tool reads ONLY a structured metadata manifest and result receipts. The
source PDFs, generated packages, raw model responses and learner data remain
private; the output is a new, non-authoritative assessment in private storage.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app_generator.validation.heldout_generalization_gate import evaluate_campaign

ROOT = Path(__file__).resolve().parents[1]


def main(args: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--results", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    ns = p.parse_args(args)
    try:
        for path in (ns.manifest, ns.results):
            if not path.is_file() or path.resolve().is_relative_to(ROOT.resolve()):
                raise ValueError("manifest and receipts must be private files outside Git")
        dest = ns.out.resolve()
        if dest.is_relative_to(ROOT.resolve()) or dest.exists() or not dest.parent.is_dir():
            raise ValueError("new private output outside Git required")
        manifest = json.loads(ns.manifest.read_text(encoding="utf-8"))
        results = json.loads(ns.results.read_text(encoding="utf-8"))
        report = evaluate_campaign(manifest, results)
        with dest.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=True, indent=2)
            handle.write("\n")
        print(json.dumps({
            "technicalResult": report["technicalResult"],
            "draftsReportedComplete": report["draftsReportedComplete"],
            "technicalAcceptanceGranted": False,
            "academicAcceptanceGranted": False,
            "publicationAuthorized": False,
        }))
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        # Do not log private paths or source passages in error messages.
        print(json.dumps({"technicalResult": "BLOCKED",
                          "errorClass": type(exc).__name__,
                          "technicalAcceptanceGranted": False,
                          "academicAcceptanceGranted": False,
                          "publicationAuthorized": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

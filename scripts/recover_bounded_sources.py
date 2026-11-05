"""Recover missing private public-source PDFs, once, after deterministic preparation failure.

Zero Gemini/model calls, no PDF-generation calls, no publication, no automatic
source retry. Verify old stop receipt and frozen Git selection before fetching.
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

from app_generator.sources.bounded_acquisition import (
    AcquisitionStop, acquire_frozen_sources, inspect_pdf_metadata,
    validate_acquisition_plan,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--prior-stop", type=Path, required=True)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--pdfinfo", type=Path, required=True)
    p.add_argument("--pdftotext", type=Path, required=True)
    ns = p.parse_args(argv)
    try:
        for source in (ns.manifest, ns.prior_stop):
            if (not source.is_file() or source.is_symlink() or
                    source.stat().st_size > 100_000 or
                    source.resolve().is_relative_to(ROOT.resolve())):
                raise AcquisitionStop("PRIVATE_INPUT_MISSING_OR_UNSAFE")
        raw = ns.manifest.read_bytes()
        spec = json.loads(raw.decode("utf-8"))
        validate_acquisition_plan(spec)
        actual_prior = sha256(ns.prior_stop.read_bytes()).hexdigest()
        if actual_prior != spec["priorStopReceiptSha256"]:
            raise AcquisitionStop("PRIOR_CAMPAIGN_STOP_RECEIPT_CHANGED")
        output = ns.output_root
        if not output.is_dir() or output.is_symlink():
            raise AcquisitionStop("PRIVATE_OUTPUT_MISSING_OR_UNSAFE")
        result = acquire_frozen_sources(
            spec, repo=ROOT, output_root=output,
            inspector=lambda path: inspect_pdf_metadata(
                path, ns.pdfinfo, ns.pdftotext),
        )
        print(json.dumps({
            "status": result["status"],
            "caseCount": len(result["sources"]),
            "sources": [{key: row[key] for key in (
                "caseId", "topicFamily", "sourceSha256",
                "pages", "approxWords", "reuseVerifiedNoRedownload")}
                for row in result["sources"]],
            "modelCalls": 0, "academicAcceptanceGranted": False,
            "publicationAuthorized": False,
        }, sort_keys=True))
        return 0
    except (AcquisitionStop, KeyError, TypeError, ValueError, OSError,
            UnicodeError, json.JSONDecodeError):
        print(json.dumps({
            "status": "STOPPED_NO_AUTO_RETRY",
            "sourceBearingModelCalls": 0,
            "academicAcceptanceGranted": False,
            "publicationAuthorized": False,
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

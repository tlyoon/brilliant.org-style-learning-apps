"""Read-only, no-network preflight for a previously frozen C3 campaign.

This CLI does not probe Gemini, read source PDFs, inspect credentials,
generate packages, authorize retries, merge, publish, or grant academic PASS.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_generator.validation.reconciliation_readiness import inspect_reconciliation_readiness


def main(args: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path,
                        help="effective TOML used by this private run (not the stored credentials)")
    parser.add_argument("--frozen-engine", required=True)
    parser.add_argument("--candidate-engine", required=True)
    parser.add_argument("--manifest", type=Path,
                        help="optional private round-two metadata manifest outside the repository")
    parser.add_argument("--selection-witness-sha256",
                        help="expected 64-character witness SHA from the closed campaign")
    ns = parser.parse_args(args)
    try:
        # Read only TOML and (optionally) private JSON metadata; no model SDK import.
        with ns.config.open("rb") as stream:
            config = tomllib.load(stream)
        manifest = None
        if ns.manifest is not None:
            if ns.manifest.resolve().is_relative_to(ROOT.resolve()):
                raise ValueError("private campaign metadata must not be stored in Git")
            if ns.manifest.suffix.lower() != ".json":
                raise ValueError("only private JSON metadata can be evaluated")
            manifest = json.loads(ns.manifest.read_text(encoding="utf-8"))
        report = inspect_reconciliation_readiness(
            config,
            frozen_engine_sha=ns.frozen_engine,
            candidate_engine_sha=ns.candidate_engine,
            manifest=manifest,
            selection_witness_sha256=ns.selection_witness_sha256,
        )
        print(json.dumps(report, sort_keys=True))
        # Ready-for-review is *not* permission for generation, source replay or release.
        return 0 if report["metadataReadyOnly"] else 2
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        # Sanitized diagnostics omit private config paths, PDF names and values.
        print(json.dumps({
            "status": "BLOCKED_INPUT",
            "errorClass": type(exc).__name__,
            "executionAuthorized": False,
            "publicationAuthorized": False,
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

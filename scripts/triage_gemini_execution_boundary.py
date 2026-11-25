"""Classify an externally observed Gemini access failure WITHOUT executing it.

This command never reads .env, calls Gemini, connects to a remote executor,
changes permissions, retries a denied action or writes output files. Only
canonical nonsecret arguments are accepted; use a trusted upstream receipt
before claiming that the executor or provider actually observed a status.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_generator.validation.gemini_execution_boundary import (
    DISPATCH, EVIDENCE, ORIGINS, STAGES, classify_gemini_attempt,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--origin", required=True, choices=sorted(ORIGINS))
    p.add_argument("--stage", required=True, choices=sorted(STAGES))
    p.add_argument("--dispatch", required=True, choices=sorted(DISPATCH))
    p.add_argument("--evidence", choices=sorted(EVIDENCE), default="HISTORICAL_REPORT")
    p.add_argument("--provider-http-status", type=int)
    args = p.parse_args(argv)
    try:
        report = classify_gemini_attempt({
            "origin": args.origin,
            "stage": args.stage,
            "dispatch": args.dispatch,
            "providerHttpStatus": args.provider_http_status,
            "evidence": args.evidence,
        })
    except (TypeError, ValueError):
        print(json.dumps({
            "status": "INVALID_OBSERVATION",
            "authorizesNewExecution": False,
            "unblocksExistingDeniedOperation": False,
            "publicationAuthorized": False,
        }, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

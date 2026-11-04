"""Privately route Section 9.4 bounded scientific contradictions into repair."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from app_generator.validation.source_bound_defect_routing import route_source_bound_defect


def main() -> int:
    args = argparse.ArgumentParser(description=__doc__)
    for field in ("package", "pdf", "dossier", "out"):
        args.add_argument("--"+field, required=True, type=Path)
    args.add_argument("--package-sha256", required=True)
    args.add_argument("--source-sha256", required=True)
    cfg = args.parse_args()
    try:
        path = cfg.out.resolve()
        if path.is_relative_to(ROOT.resolve()) or path.exists():
            raise ValueError("private receipt must be new and outside Git")
        decision = route_source_bound_defect(
            package_file=cfg.package, source_pdf=cfg.pdf, dossier_file=cfg.dossier,
            expected_package_sha256=cfg.package_sha256,
            expected_source_sha256=cfg.source_sha256,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as stream:
            json.dump(decision, stream, indent=2, ensure_ascii=True)
            stream.write("\n")
        print(json.dumps({
            "activityId": decision["activityId"],
            "nextAction": decision["nextAction"],
            "objectionCount": len(decision["objections"]),
            "unresolvedLanguages": decision["unresolvedLanguages"],
            "academicQA": decision["academicQA"],
            "publicationAuthorized": False,
        }))
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BLOCKED", "errorClass": type(exc).__name__,
                          "publicationAuthorized": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
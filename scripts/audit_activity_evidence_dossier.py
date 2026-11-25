"""Produce a privacy-safe exact-version evidence dossier for ONE learning activity."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_generator.validation.activity_evidence_dossier import reconcile_activity_evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("package", "pdf", "matrix", "physics", "out"):
        parser.add_argument("--" + flag, required=True, type=Path)
    parser.add_argument("--activity-id", required=True)
    args = parser.parse_args()
    try:
        dest = args.out.resolve()
        if dest.is_relative_to(ROOT.resolve()) or dest.exists():
            raise ValueError("output must be a new private file outside Git checkout")
        result = reconcile_activity_evidence(
            package_file=args.package, source_pdf=args.pdf,
            matrix_file=args.matrix, physics_file=args.physics,
            activity_id=args.activity_id,
        )
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, ensure_ascii=True)
            stream.write("\n")
        print(json.dumps({k:result[k] for k in (
            "activityId", "academicQA", "nextAction", "sourceLocationVerifiedInMatrix",
            "boundedPhysicsReceiptMatched", "fullAcademicPass",
            "publicationAuthorized")}))
        return 0
    except (ValueError, TypeError, KeyError, OSError, json.JSONDecodeError) as exc:
        # Avoid echoing private input paths or text in errors.
        print(json.dumps({"status":"BLOCKED", "errorClass":type(exc).__name__,
                          "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
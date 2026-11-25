"""Create an immutable private v3 review candidate without modifying originals."""
from __future__ import annotations

from hashlib import sha256
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_generator.validation.impulse_v3 import review_candidate_v3


def export_v3(v2_package: Path, v2_review: Path, source_pdf: Path,
              destination: Path) -> dict:
    destination = destination.resolve()
    if destination.is_relative_to(ROOT.resolve()):
        raise ValueError("private candidate cannot reside in the public Git repository")
    if destination.exists():
        raise ValueError("private candidate already exists; refusing overwrite")
    package, review = review_candidate_v3(v2_package, v2_review, source_pdf)
    content = (json.dumps(package, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    review["candidateFileSha256"] = sha256(content).hexdigest()
    review["parentV2PackagePath"] = str(v2_package.resolve())
    review["privateCandidatePath"] = str(destination / "package.json")
    receipt = (json.dumps(review, ensure_ascii=True, indent=2) + "\n").encode("utf-8")
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "package.json").write_bytes(content)
    (destination / "review.json").write_bytes(receipt)
    if sha256((destination / "package.json").read_bytes()).hexdigest() != review["candidateFileSha256"]:
        raise ValueError("stored candidate file differs from recorded SHA")
    if (destination / "review.json").read_bytes() != receipt:
        raise ValueError("stored review record differs from calculated bytes")
    return {
        "candidateFileSha256": review["candidateFileSha256"],
        "candidateCanonicalSha256": review["candidateCanonicalSha256"],
        "parentV2FileSha256": review["parentV2FileSha256"],
        "sourcePdfSha256": review["sourcePdfSha256"],
        "activities": len(package["activities"]),
        "untouchedActivities": review["untouchedActivities"],
        "reviewOnly": review["reviewOnly"],
        "academicQA": review["academicQA"],
        "publicationAuthorized": review["publicationAuthorized"],
        "privateFolder": str(destination),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v2-package", required=True, type=Path)
    parser.add_argument("--v2-review", required=True, type=Path)
    parser.add_argument("--source-pdf", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(export_v3(args.v2_package, args.v2_review,
                                   args.source_pdf, args.out), indent=2))
        return 0
    except (ValueError, KeyError, OSError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BLOCKED", "academicQA": "REVIEW_REQUIRED",
                          "publicationAuthorized": False, "error": str(exc)[:270]}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

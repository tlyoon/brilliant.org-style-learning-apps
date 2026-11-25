"""Private exact-version evidence inventory CLI.

Read-only original source and reviewer inputs; creates one new private metadata
receipt. This NEVER upgrades academic QA nor makes a Gemini request.
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
from app_generator.validation.academic_evidence_inventory import reconcile_evidence


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("package", "pdf", "matrix", "source-sha256", "package-sha256", "out"):
        p.add_argument("--" + key, required=True,
                       type=Path if key in ("package", "pdf", "matrix", "out") else str)
    for key in ("mcq", "collision", "visual", "claims"):
        p.add_argument("--" + key, type=Path)
    a = p.parse_args()
    try:
        inputs = {"package": a.package, "pdf": a.pdf, "matrix": a.matrix}
        inputs.update({k: getattr(a, k) for k in ("mcq", "collision", "visual", "claims")
                       if getattr(a, k) is not None})
        for path in inputs.values():
            if not path.is_file() or path.resolve().is_relative_to(ROOT.resolve()):
                raise ValueError("all source and report inputs must be private")
        dest = a.out.resolve()
        if dest.exists() or dest.is_relative_to(ROOT.resolve()) or not dest.parent.is_dir():
            raise ValueError("destination must be new and outside repository")
        pdf_bytes, package_bytes = a.pdf.read_bytes(), a.package.read_bytes()
        if (not pdf_bytes.startswith(b"%PDF-")
                or sha256(pdf_bytes).hexdigest() != a.source_sha256
                or sha256(package_bytes).hexdigest() != a.package_sha256):
            raise ValueError("original source PDF or package digest differs")
        package = json.loads(package_bytes.decode("utf-8"))
        matrix = json.loads(a.matrix.read_text(encoding="utf-8"))
        reports = {key: json.loads(path.read_text(encoding="utf-8"))
                   for key, path in inputs.items() if key not in ("package", "pdf", "matrix")}
        result = reconcile_evidence(
            matrix, reports=reports, expected_package_sha256=a.package_sha256,
            expected_source_sha256=a.source_sha256, exact_package=package)
        with dest.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=True, indent=2)
            stream.write("\n")
        print(json.dumps({
            "status": result["status"], "activityCount": result["activityCount"],
            "missingReceiptCategories": result["missingReceiptCategories"],
            "nextActionCounts": result["nextActionCounts"],
            "formalAcademicPASSCount": 0, "publicationAuthorized": False}))
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BLOCKED", "reasonClass": type(exc).__name__,
                          "formalAcademicPASSCount": 0, "publicationAuthorized": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

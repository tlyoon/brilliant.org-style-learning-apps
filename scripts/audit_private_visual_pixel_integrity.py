"""Validate source-bound screenshot pixels privately; no semantic approval."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from app_generator.validation.private_visual_pixel_integrity import (
    audit_private_visual_pixel_integrity,
)


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    for field in ("package","pdf","evidence","out"):
        p.add_argument("--"+field,type=Path,required=True)
    args=p.parse_args()
    try:
        out=args.out.resolve()
        if out.is_relative_to(ROOT) or out.exists() or not out.parent.is_dir():
            raise ValueError("only new PRIVATE evidence path allowed")
        from hashlib import sha256
        result=audit_private_visual_pixel_integrity(
            package_file=args.package,source_pdf=args.pdf,
            evidence_dir=args.evidence,
            expected_package_sha256=sha256(args.package.read_bytes()).hexdigest(),
            expected_source_sha256=sha256(args.pdf.read_bytes()).hexdigest())
        out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=True)+"\n",
                       encoding="utf-8")
        print(json.dumps({key:result[key] for key in
          ("status","screenCapturesChecked","technicalPixelIntegrityChecked",
           "pixelQualityReviewed","academicQA","publicationAuthorized")}))
        return 0
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(json.dumps({"status":"PIXEL_TECHNICAL_QA_BLOCKED",
          "errorType":type(exc).__name__,"academicQA":"REVIEW_REQUIRED",
          "publicationAuthorized":False}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())

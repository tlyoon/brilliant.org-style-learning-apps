"""Read-only v3 bounded academic audit with immutable private output."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from app_generator.validation.impulse_v3_audit import audit_v3


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--package",required=True,type=Path)
    p.add_argument("--review",required=True,type=Path)
    p.add_argument("--v2-package",required=True,type=Path)
    p.add_argument("--v2-review",required=True,type=Path)
    p.add_argument("--source-pdf",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    try:
        dest=args.out.resolve()
        if dest.is_relative_to(ROOT.resolve()):
            raise ValueError("private QA receipts must remain outside public repository")
        if dest.exists():
            raise ValueError("refusing to overwrite existing private academic review report")
        result=audit_v3(args.package,args.review,args.v2_package,args.v2_review,args.source_pdf)
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes((json.dumps(result,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
        print(json.dumps({
            "boundedOptionsVerified":result["boundedOptionsVerified"],
            "optionReviewsRequired":result["optionReviewsRequired"],
            "localizedConceptChecks":result["multilingualNarrative"]["localizedFieldChecks"],
            "localizedConceptsFound":result["multilingualNarrative"]["boundedConceptsPresent"],
            "completeSemanticEquivalence":result["fullSemanticEquivalenceVerified"],
            "academicQA":result["academicQA"],
            "publicationAuthorized":result["publicationAuthorized"],
            "reportPath":str(dest),
        }))
        return 0
    except (ValueError,KeyError,OSError,TypeError,json.JSONDecodeError) as e:
        print(json.dumps({"status":"BLOCKED","academicQA":"REVIEW_REQUIRED",
                          "publicationAuthorized":False,"error":str(e)[:280]}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())

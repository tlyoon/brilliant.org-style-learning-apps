"""Produce private cross-version bounded physics re-verification receipts."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.bounded_physics_transfer import reverify_bounded_physics

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("prior-package","revised-package","source-pdf",
              "mcq-receipts","interaction-receipts","parent-v2-package",
              "parent-v2-review","revised-v3-review","out"):
        p.add_argument("--"+k,type=Path,required=True)
    p.add_argument("--source-sha256",required=True)
    a=p.parse_args()
    try:
        dest=a.out.resolve()
        if dest.is_relative_to(ROOT.resolve()) or dest.exists():
            raise ValueError("new private output required; no public or overwritten proof")
        result=reverify_bounded_physics(
            prior_package=a.prior_package,revised_package=a.revised_package,
            source_pdf=a.source_pdf,source_sha256=a.source_sha256,
            mcq_receipts=a.mcq_receipts,interaction_receipts=a.interaction_receipts,
            parent_v2_package=a.parent_v2_package,
            parent_v2_review=a.parent_v2_review,
            revised_v3_review=a.revised_v3_review,
        )
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes((json.dumps(result,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
        print(json.dumps({
            "boundedPropositionsVerified":result["boundedPropositionsVerified"],
            "unchangedBoundedVerified":result["unchangedBoundedVerified"],
            "revisedBoundedVerified":result["revisedBoundedVerified"],
            "fullyAcademicallyApproved":0,"academicQA":"REVIEW_REQUIRED",
            "publicationAuthorized":False,"privateOutput":str(dest),
        }))
        return 0
    except (ValueError,OSError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print(json.dumps({"status":"BLOCKED","errorType":type(exc).__name__,
                          "error":str(exc)[:250],"publicationAuthorized":False}))
        return 2
if __name__=="__main__":raise SystemExit(main())

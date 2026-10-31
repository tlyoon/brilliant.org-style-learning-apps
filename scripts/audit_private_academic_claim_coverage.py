"""Reconcile 18-activity academic claim coverage without any remote submission."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from app_generator.validation.full_academic_claim_coverage import audit_academic_claim_coverage


def main()->int:
    cli=argparse.ArgumentParser(description=__doc__)
    for name in ("package","pdf","packets","reviewer-runs","out"):
        cli.add_argument("--"+name,required=True,type=Path)
    args=cli.parse_args()
    try:
        out=args.out.resolve()
        if (out.exists() or out.is_relative_to(ROOT.resolve()) or
            args.reviewer_runs.resolve().is_relative_to(ROOT.resolve())):
            raise ValueError("reviewer list and new output must stay outside repository")
        result=audit_academic_claim_coverage(
            package_file=args.package,source_pdf=args.pdf,packets_file=args.packets,
            reviewer_runs_file=args.reviewer_runs,
        )
        out.parent.mkdir(parents=True,exist_ok=True)
        with out.open("x",encoding="utf-8") as f:
            json.dump(result,f,ensure_ascii=True,indent=2)
            f.write("\n")
        print(json.dumps({"status":result["status"],
                          "sourceActivitiesReverified":result["sourceActivitiesReverified"],
                          "reviewedRunCount":result["reviewedRunCount"],
                          "claimStates":result["claimStates"],
                          "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False}))
        return 0
    except (ValueError,TypeError,KeyError,json.JSONDecodeError,OSError) as exc:
        print(json.dumps({"status":"BLOCKED","errorType":type(exc).__name__,
                          "publicationAuthorized":False}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())

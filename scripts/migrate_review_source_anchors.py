"""Recheck all prior source anchors on original PDF for an exact new candidate.

Writes source quotations privately; Git receives no textbook excerpt.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.source_anchor_migration import migrate_anchor_packets

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pdf",type=Path,required=True)
    p.add_argument("--source-sha256",required=True)
    p.add_argument("--prior-package",type=Path,required=True)
    p.add_argument("--target-package",type=Path,required=True)
    p.add_argument("--prior-receipts",type=Path,nargs="+",required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    try:
        output=a.out.resolve()
        if output.is_relative_to(ROOT.resolve()) or output.exists():
            raise ValueError("private destination must be new and outside repository")
        result=migrate_anchor_packets(
            pdf=a.pdf,source_sha256=a.source_sha256,
            prior_package=a.prior_package,target_package=a.target_package,
            prior_receipts=a.prior_receipts,
        )
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
        print(json.dumps({
            "output":str(output),"packageSha256":result["packageSha256"],
            "activityCount":result["activityCount"],
            "verifiedSourceLocations":result["verifiedSourceLocations"],
            "changedActivityCount":len(result["changedActivityIds"]),
            "changedActivityIds":result["changedActivityIds"],
            "sourceInterpretationVerified":False,
            "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False,
        },ensure_ascii=True))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print(json.dumps({
            "status":"BLOCKED","errorType":type(exc).__name__,
            "message":str(exc)[:230],
            "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False,
        }))
        return 2
if __name__=="__main__":raise SystemExit(main())

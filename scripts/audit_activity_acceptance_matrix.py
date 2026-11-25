"""Private 18-activity source/answer/visual/multilingual QA matrix.

This produces unresolved per-activity automatic work, never fabricates
complete academic correctness from merely valid schema or model agreement.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.academic_acceptance_matrix import audit_activity_matrix

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--package",type=Path,required=True)
    p.add_argument("--pdf",type=Path,required=True)
    p.add_argument("--source-sha256",required=True)
    p.add_argument("--source-packets",type=Path,default=None)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--expected-count",type=int,default=18)
    args=p.parse_args()
    try:
        dest=args.out.resolve()
        if dest.is_relative_to(ROOT.resolve()) or dest.exists():
            raise ValueError("review receipts must be new private files outside code repository")
        packets=(json.loads(args.source_packets.read_text(encoding="utf-8"))
                 if args.source_packets is not None else None)
        report=audit_activity_matrix(
            repo_root=ROOT,package_path=args.package,
            source_pdf=args.pdf,source_sha256=args.source_sha256,
            source_packets=packets,expected_count=args.expected_count,
        )
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes((json.dumps(report,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
        print(json.dumps({
            "activityCount":report["activityCount"],"counts":report["counts"],
            "verifiedSourceLocations":sum(a["sourceLocationVerified"] for a in report["activities"]),
            "academicQA":report["academicQA"],
            "publicationAuthorized":False,"privateReport":str(dest),
        }))
        return 0
    except (ValueError,KeyError,OSError,TypeError,json.JSONDecodeError) as exc:
        print(json.dumps({"status":"BLOCKED","reason":str(exc)[:250],
                          "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False}))
        return 2

if __name__=="__main__":raise SystemExit(main())

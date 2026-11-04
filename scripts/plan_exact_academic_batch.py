"""Write a private exact-version 18-activity academic review worklist."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from app_generator.validation.academic_batch_gap_plan import plan_exact_academic_batch

def main()->int:
    cli=argparse.ArgumentParser(description=__doc__)
    for field in ("package","pdf","matrix","physics","out"):
        cli.add_argument("--"+field,type=Path,required=True)
    cli.add_argument("--expected-count",type=int,default=18)
    args=cli.parse_args()
    try:
        dest=args.out.resolve()
        if dest.exists() or dest.is_relative_to(ROOT.resolve()):
            raise ValueError("worklist destination must be new and private")
        report=plan_exact_academic_batch(
            package_file=args.package,source_pdf=args.pdf,
            matrix_file=args.matrix,physics_file=args.physics,
            expected_count=args.expected_count,
        )
        dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open("x",encoding="utf-8") as fp:
            json.dump(report,fp,ensure_ascii=True,indent=2)
            fp.write("\n")
        print(json.dumps({
            "activityCount":report["activityCount"],
            "sourceReceipts":report["verifiedSourceLocationReceipts"],
            "physicsReceipts":report["matchedBoundedPhysicsReceipts"],
            "academicCounts":report["academicCounts"],
            "nextActionCounts":report["nextActionCounts"],
            "publicationAuthorized":False,
        }))
        return 0
    except (ValueError,TypeError,KeyError,OSError,json.JSONDecodeError) as exc:
        print(json.dumps({"status":"BLOCKED","errorClass":type(exc).__name__,
                          "publicationAuthorized":False}))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
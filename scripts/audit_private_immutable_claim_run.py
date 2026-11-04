"""Private-only CLI: audit existing source-bound reviewer claims without sending requests."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from app_generator.validation.source_bound_claim_audit import audit_source_bound_claim_run


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("package","pdf","packets","claims","activity-id","claim-prefix","out"):
        parser.add_argument("--"+name,required=True)
    args=parser.parse_args()
    output=Path(args.out).resolve()
    try:
        if output.exists() or output.is_relative_to(ROOT.resolve()):
            raise ValueError("private report path must be new and outside repository")
        if Path(args.claims).resolve().is_relative_to(ROOT.resolve()):
            raise ValueError("academic claim directory cannot be within public repository")
        report=audit_source_bound_claim_run(
            package_file=Path(args.package),pdf_file=Path(args.pdf),
            packets_file=Path(args.packets),claims_dir=Path(args.claims),
            activity_id=args.activity_id,claim_prefix=args.claim_prefix,
        )
        output.parent.mkdir(parents=True,exist_ok=True)
        with output.open("x",encoding="utf-8") as f:
            json.dump(report,f,ensure_ascii=True,indent=2)
            f.write("\n")
        print(json.dumps({"status":"READ_ONLY_AUDIT_RECORDED",
                          "claimCount":report["claimCount"],
                          "stateCounts":report["stateCounts"],
                          "reasonCounts":report["reasonCounts"],
                          "sourceReverified":report["originalSourcePassageReverified"],
                          "academicQA":report["academicQA"],
                          "publicationAuthorized":False}))
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        # Never print raw exception strings: they can include private paths or text.
        print(json.dumps({"status":"BLOCKED","errorClass":type(exc).__name__,
                          "academicQA":"REVIEW_REQUIRED",
                          "publicationAuthorized":False}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())

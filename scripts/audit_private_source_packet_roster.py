"""Read-only exact original PDF passage verification across all 18 activities."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("package","pdf","packets","out"):
        parser.add_argument("--"+key,type=Path,required=True)
    parser.add_argument("--expected-count",type=int,default=18)
    args=parser.parse_args()
    try:
        dest=args.out.resolve()
        if dest.exists() or dest.is_relative_to(ROOT.resolve()):
            raise ValueError("private report must be new and outside repository")
        report=verify_full_source_packet_roster(
            package_file=args.package,source_pdf=args.pdf,
            packets_file=args.packets,expected_count=args.expected_count,
        )
        dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open("x",encoding="utf-8") as handle:
            json.dump(report,handle,ensure_ascii=True,indent=2)
            handle.write("\n")
        print(json.dumps({
            "status":report["status"],
            "newlyReverifiedSourceActivities":report["newlyReverifiedSourceActivities"],
            "newlyReverifiedSourcePassages":report["newlyReverifiedSourcePassages"],
            "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False,
        }))
        return 0
    except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError) as exc:
        print(json.dumps({"status":"BLOCKED","errorType":type(exc).__name__,
                          "publicationAuthorized":False}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())

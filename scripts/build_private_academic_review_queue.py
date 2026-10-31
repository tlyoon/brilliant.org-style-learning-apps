"""Create a private academic priority queue from existing verified metadata."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from app_generator.validation.academic_review_priorities import prioritize_academic_review


def main()->int:
    cli=argparse.ArgumentParser(description=__doc__)
    for name in ("coverage","multilingual","out"):
        cli.add_argument("--"+name,type=Path,required=True)
    a=cli.parse_args()
    try:
        dst=a.out.resolve()
        if (dst.exists() or dst.is_relative_to(ROOT.resolve()) or
            a.coverage.resolve().is_relative_to(ROOT.resolve()) or
            a.multilingual.resolve().is_relative_to(ROOT.resolve())):
            raise ValueError("all academic evidence and report must remain private")
        result=prioritize_academic_review(
            json.loads(a.coverage.read_text(encoding="utf-8")),
            json.loads(a.multilingual.read_text(encoding="utf-8")),
        )
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8") as f:
            json.dump(result,f,ensure_ascii=True,indent=2)
            f.write("\n")
        print(json.dumps({"status":result["status"],"activityCount":result["activityCount"],
                          "reviewFlagCount":result["reviewFlagCount"],
                          "priorityCounts":result["priorityCounts"],
                          "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False}))
        return 0
    except (OSError,KeyError,TypeError,ValueError,json.JSONDecodeError) as exc:
        print(json.dumps({"status":"BLOCKED","errorType":type(exc).__name__,
                          "publicationAuthorized":False}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())

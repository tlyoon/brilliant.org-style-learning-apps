"""Private source-bound EN/MS/ZH numeric consistency triage (not translation PASS)."""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from app_generator.validation.multilingual_numeric_triage import (
    audit_source_bound_multilingual_numeric_triage,
)


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("package","pdf","packets","out"):
        parser.add_argument("--"+name,required=True,type=Path)
    args=parser.parse_args()
    try:
        out=args.out.resolve()
        if out.is_relative_to(ROOT) or out.exists() or not out.parent.is_dir():
            raise ValueError("new PRIVATE output outside Git repository required")
        report=audit_source_bound_multilingual_numeric_triage(
            package_file=args.package,source_pdf=args.pdf,source_packets_file=args.packets)
        out.write_text(json.dumps(report,ensure_ascii=True,sort_keys=True,indent=2)+"\n",
                       encoding="utf-8")
        print(json.dumps({key:report[key] for key in (
          "status","sourceVerifiedActivities","localizedFieldsChecked",
          "numericDriftFlagCount","activitiesWithFlags","academicQA",
          "academicPASS","publicationAuthorized")}))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps({"status":"TRIAGE_BLOCKED","errorType":type(exc).__name__,
                          "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())

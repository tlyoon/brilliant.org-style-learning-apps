"""Private exact source 36-option collision proof audit (no Gemini)."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.mcq_option_physics import audit_source_bound_all_mcq_options

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("package","pdf","packets","out"):
        parser.add_argument("--"+key,required=True,type=Path)
    args=parser.parse_args()
    try:
        out=args.out.resolve()
        if out.is_relative_to(ROOT) or out.exists() or not out.parent.is_dir():
            raise ValueError("unique private output outside repository required")
        report=audit_source_bound_all_mcq_options(
            package_file=args.package,source_pdf=args.pdf,
            source_packets_file=args.packets)
        with out.open("x",encoding="utf-8") as handle:
            json.dump(report,handle,ensure_ascii=True,sort_keys=True,indent=2)
            handle.write("\n")
        keys=("status","originalSourceActivitiesReverified","mcqActivitiesChecked",
              "mcqOptionsChecked","sourceBoundSelectedOptionWitnesses",
              "rationalCounterexamplesForDistractorIds","unresolvedPhysicalDistractors",
              "academicQA","formalAcademicPASS","publicationAuthorized")
        print(json.dumps({key:report[key] for key in keys}))
        return 0
    except (OSError,ValueError,TypeError,KeyError,ZeroDivisionError) as exc:
        print(json.dumps({"status":"BOUND_36_OPTION_AUDIT_BLOCKED",
                          "errorType":type(exc).__name__,
                          "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False}))
        return 2
if __name__=="__main__":raise SystemExit(main())

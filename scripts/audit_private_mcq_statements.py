"""Private original-source MCQ statement-level bounded audit."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.mcq_statement_physics import (
    audit_source_bound_mcq_statement_physics,
)


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("package","pdf","packets","out"):
        p.add_argument("--"+key,type=Path,required=True)
    a=p.parse_args()
    try:
        output=a.out.resolve()
        if output.exists() or output.is_relative_to(ROOT) or not output.parent.is_dir():
            raise ValueError("new private output outside repository required")
        report=audit_source_bound_mcq_statement_physics(
            package_file=a.package,source_pdf=a.pdf,packets_file=a.packets)
        with output.open("x",encoding="utf-8") as stream:
            json.dump(report,stream,ensure_ascii=True,sort_keys=True,indent=2)
            stream.write("\n")
        names=("status","originalSourceActivityPassagesReverified","mcqActivitiesChecked",
               "threeLanguageOptionLabelsBoundBySha256","boundedAnswerOptionsSupported",
               "boundedDistractorsCounterexampled","sourceFigureContactSemanticsPending",
               "academicQA","formalAcademicPASS","publicationAuthorized")
        print(json.dumps({k:report[k] for k in names}))
        return 0
    except (OSError,ValueError,KeyError,TypeError,ZeroDivisionError) as exc:
        print(json.dumps({"status":"MCQ_STATEMENT_AUDIT_BLOCKED",
                          "errorType":type(exc).__name__,
                          "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())

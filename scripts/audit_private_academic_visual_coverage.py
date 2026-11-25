"""Verify full real-browser technical screenshot coverage for a private academic queue."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from app_generator.validation.academic_technical_visual_coverage import audit_source_bound_visual_readiness


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    for n in ("package","pdf","evidence","academic-queue","out"):
        parser.add_argument("--"+n,required=True,type=Path)
    a=parser.parse_args()
    try:
        out=a.out.resolve()
        if (out.exists() or out.is_relative_to(ROOT.resolve()) or
            a.academic_queue.resolve().is_relative_to(ROOT.resolve()) or
            a.evidence.resolve().is_relative_to(ROOT.resolve())):
            raise ValueError("evidence and fresh report must stay outside repository")
        report=audit_source_bound_visual_readiness(
            package_file=a.package,source_pdf=a.pdf,
            browser_evidence_dir=a.evidence,
            academic_queue=json.loads(a.academic_queue.read_text(encoding="utf-8")),
        )
        out.parent.mkdir(parents=True,exist_ok=True)
        with out.open("x",encoding="utf-8") as f:
            json.dump(report,f,ensure_ascii=True,indent=2)
            f.write("\n")
        print(json.dumps({"status":report["status"],
                          "visualActivities":report["visualActivities"],
                          "screenshotCapturesVerified":report["screenshotCapturesVerified"],
                          "scientificVisualSemanticsVerified":False,
                          "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False}))
        return 0
    except (ValueError,TypeError,KeyError,OSError,json.JSONDecodeError) as exc:
        print(json.dumps({"status":"BLOCKED","errorType":type(exc).__name__,
                          "publicationAuthorized":False}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())

"""Private original-source visual grounding and screenshot receipt audit."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.visual_fact_trace import audit_source_visual_fact_trace


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ("package","pdf","packets","historical-pixel-receipt","out"):
        p.add_argument("--"+arg,required=True,type=Path)
    a=p.parse_args()
    try:
        target=a.out.resolve()
        if target.exists() or target.is_relative_to(ROOT) or not target.parent.is_dir():
            raise ValueError("new private output outside repository required")
        result=audit_source_visual_fact_trace(
            package_file=a.package,source_pdf=a.pdf,packets_file=a.packets,
            historical_pixel_receipt=a.historical_pixel_receipt)
        with target.open("x",encoding="utf-8") as stream:
            json.dump(result,stream,sort_keys=True,ensure_ascii=True,indent=2)
            stream.write("\n")
        keys=("status","allOriginalSourceActivitiesReverified",
              "visualActivitiesChecked","declaredFactIdentifiersCrossChecked",
              "declaredPedagogicalSimplifications",
              "historicalTechnicalScreenshotReceiptsCrossChecked",
              "formalAcademicPASS","publicationAuthorized")
        print(json.dumps({k:result[k] for k in keys}))
        return 0
    except (OSError,KeyError,ValueError,TypeError) as exc:
        print(json.dumps({"status":"VISUAL_FACT_TRACE_BLOCKED",
                          "errorType":type(exc).__name__,
                          "publicationAuthorized":False}))
        return 2

if __name__=="__main__":
    raise SystemExit(main())

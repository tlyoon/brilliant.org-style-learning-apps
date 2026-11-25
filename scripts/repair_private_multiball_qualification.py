"""Generate a private, never-published v7 clarification of Newton's cradle."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.multiball_qualification import create_private_v7

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("package","pdf","packets","corrections","out"):
        p.add_argument("--"+key,required=True,type=Path)
    a=p.parse_args()
    try:
        out=create_private_v7(package_file=a.package,source_pdf=a.pdf,
                              packets_file=a.packets,corrections_file=a.corrections,
                              out_dir=a.out)
        print(json.dumps({key:out[key] for key in (
            "status","changedActivities","changedFields","sourceSha256",
            "newPackageSha256","originalSourceActivitiesReverified",
            "formalAcademicPASS","publicationAuthorized")}))
        return 0
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({"status":"PRIVATE_MULTIBALL_REPAIR_BLOCKED",
             "errorType":type(exc).__name__,"publicationAuthorized":False}))
        return 2

if __name__=="__main__":
    raise SystemExit(main())

"""Private original-source collision property-grid audit."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.collision_property_grid import audit


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("package","pdf","packets","out"):
        p.add_argument("--"+name,required=True,type=Path)
    a=p.parse_args()
    try:
        target=a.out.resolve()
        if target.exists() or target.is_relative_to(ROOT) or not target.parent.is_dir():
            raise ValueError("new private output required")
        result=audit(package_file=a.package,source_pdf=a.pdf,packets_file=a.packets)
        with target.open("x",encoding="utf-8") as f:
            json.dump(result,f,ensure_ascii=True,indent=2,sort_keys=True)
            f.write("\n")
        print(json.dumps({k:result[k] for k in (
            "status","originalSourceActivitiesReverified",
            "mcqAnswerIdRostersChecked","mcqOptionIdentifiersChecked",
            "interactionAnswerModelsCompared","qualifierReviewRequired",
            "formalAcademicPASS","publicationAuthorized")}))
        print("exact_collision_cases="+str(result["physicsGrid"]["exactCollisionCases"]))
        return 0
    except (OSError,TypeError,ValueError,KeyError,ZeroDivisionError) as exc:
        print(json.dumps({"status":"COLLISION_GRID_BLOCKED",
                          "errorType":type(exc).__name__,"publicationAuthorized":False}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())

"""Create a source-bound private ballistic pendulum v11 candidate."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.ballistic_impulse_scope import create_private_v11

def main():
    ap=argparse.ArgumentParser()
    for name in ("package","pdf","packets","corrections","out"):
        ap.add_argument("--"+name,type=Path,required=True)
    a=ap.parse_args()
    try:
        r=create_private_v11(package_file=a.package,source_pdf=a.pdf,
               packets_file=a.packets,corrections_file=a.corrections,out_dir=a.out)
        print(json.dumps({k:r[k] for k in (
               "status","newV11PackageSha256","changedActivities",
               "changedLocalizedAnswerLogicFields","originalSourceActivitiesReverified",
               "publicationAuthorized")}))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as ex:
        print(json.dumps({"status":"SOURCE_BOUND_PRIVATE_V11_BLOCKED",
              "exceptionType":type(ex).__name__,"publicationAuthorized":False}))
        return 2
if __name__=="__main__":raise SystemExit(main())

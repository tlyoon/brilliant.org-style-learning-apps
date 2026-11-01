"""Create immutable source-bound private v10 scientific explanation correction."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.inelastic_separation_claim import create_private_v10

def main():
    p=argparse.ArgumentParser()
    for k in ("package","pdf","packets","corrections","out"):
        p.add_argument("--"+k,type=Path,required=True)
    a=p.parse_args()
    try:
        result=create_private_v10(
            package_file=a.package,source_pdf=a.pdf,packets_file=a.packets,
            corrections_file=a.corrections,out_dir=a.out)
        print(json.dumps({k:result[k] for k in (
          "status","newV10PackageSha256","changedActivities",
          "changedLocalizedExplanationFields","originalSourceActivitiesReverified",
          "publicationAuthorized")}))
        return 0
    except (OSError,ValueError,TypeError,KeyError) as ex:
        print(json.dumps({"status":"PRIVATE_V10_REPAIR_BLOCKED",
             "errorType":type(ex).__name__,"publicationAuthorized":False}))
        return 2
if __name__=="__main__":raise SystemExit(main())

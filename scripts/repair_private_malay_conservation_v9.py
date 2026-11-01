"""Source-bound copy-on-write private v9 Malay conservation terminology repair."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.malay_conservation_lexicon import create_private_v9

def main():
    p=argparse.ArgumentParser()
    for k in ("package","pdf","packets","out"):
        p.add_argument("--"+k,type=Path,required=True)
    a=p.parse_args()
    try:
        result=create_private_v9(package_file=a.package,source_pdf=a.pdf,
            packets_file=a.packets,output_dir=a.out)
        print(json.dumps({k:result[k] for k in (
            "status","localizedScientificTermReplacements","changedMalayFields",
            "newV9PackageSha256","originalSourceActivitiesReverified",
            "formalAcademicPASS","publicationAuthorized")}))
        return 0
    except (ValueError,KeyError,TypeError,OSError) as ex:
        print(json.dumps({"status":"MALAY_V9_REPAIR_BLOCKED",
            "errorType":type(ex).__name__,"publicationAuthorized":False}))
        return 2

if __name__=="__main__":raise SystemExit(main())

"""Create a private v6 scientific-translation draft without publishing v5."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.malay_conservative_semantics import (
    emit_versioned_private_candidate,
)


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("package","pdf","packets","out-directory"):
        p.add_argument("--"+key,required=True,type=Path)
    a=p.parse_args()
    try:
        result=emit_versioned_private_candidate(
            package_file=a.package,source_pdf=a.pdf,
            packets_file=a.packets,out_directory=a.out_directory)
        print(json.dumps({k:result[k] for k in (
            "status","changedTermOccurrences","changedLocalizedFields",
            "newSourcePacketActivitiesReverified","oldPackageSha256",
            "newPackageSha256","formalAcademicPASS","publicationAuthorized")}))
        return 0
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({"status":"MALAY_SCIENTIFIC_REPAIR_BLOCKED",
            "errorType":type(exc).__name__,
            "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False}))
        return 2

if __name__=="__main__":
    raise SystemExit(main())

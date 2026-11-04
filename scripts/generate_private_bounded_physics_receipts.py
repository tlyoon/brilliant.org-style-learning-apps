"""Generate strict private source-bound physics witnesses, never academic PASS."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from app_generator.validation.physics_receipt_generation import (
    generate_bounded_physics_receipts,
)


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("package","pdf","packets","receipts","audit"):
        p.add_argument("--"+name,required=True,type=Path)
    args=p.parse_args()
    try:
        receipts=args.receipts.resolve()
        audit=args.audit.resolve()
        if (receipts==audit or receipts.is_relative_to(ROOT) or
            audit.is_relative_to(ROOT) or receipts.exists() or audit.exists() or
            not receipts.parent.is_dir() or not audit.parent.is_dir()):
            raise ValueError("new separate pre-existing PRIVATE receipt parent paths required")
        result,report=generate_bounded_physics_receipts(
            args.package,args.pdf,args.packets)
        # Audit succeeds in memory before either private output file is created.
        receipts.write_text(json.dumps(result,sort_keys=True,ensure_ascii=True,indent=2)+"\n",
                            encoding="utf-8")
        audit.write_text(json.dumps(report,sort_keys=True,ensure_ascii=True,indent=2)+"\n",
                         encoding="utf-8")
        print(json.dumps({"boundedPropositionsVerified":report["boundedPropositionsVerified"],
            "academicActivitiesPassed":0,"academicQA":"REVIEW_REQUIRED",
            "publicationAuthorized":False}))
        return 0
    except (OSError,KeyError,TypeError,ValueError) as exc:
        print(json.dumps({"status":"BLOCKED","errorType":type(exc).__name__,
                          "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())

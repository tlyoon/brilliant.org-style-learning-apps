"""Run or safely preflight the original-PDF, private Section 9.4 Gemini pilot.

Default is READINESS ONLY. --execute can use pre-existing authenticated
independent reviewer profiles, never an authoring Chrome profile.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

from app_generator.config import load_config
from app_generator.runtime.private_gemini_pilot import (
    ACTIVITY_ID,exact_v3_context,run_private_pilot,readiness
)


def prepare_context(source_pdf:Path,v3:Path,v2:Path,private_anchors:Path):
    proofs=json.loads(private_anchors.read_text(encoding="utf-8"))["proofs"]
    anchors=[x["anchor"] for x in proofs if x["activityId"]==ACTIVITY_ID]
    if len(anchors)!=1:
        raise ValueError("one unique original source passage required")
    return exact_v3_context(v3/"package.json",v3/"review.json",
                            v2/"package.json",v2/"review.json",source_pdf,anchors[0])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("config","v3","v2","pdf","proofs","out"):
        p.add_argument("--"+k,required=True,type=Path)
    p.add_argument("--execute",action="store_true")
    args=p.parse_args()
    try:
        config=load_config(args.config)
        context=prepare_context(args.pdf,args.v3,args.v2,args.proofs)
        path=args.out.resolve()
        if path.is_relative_to(ROOT.resolve()) or path.exists():
            raise ValueError("private immutable pilot output path invalid or already exists")
        status=run_private_pilot(config,args.v3/"package.json",args.pdf,context,
                     run_directory=path/"review-run") if args.execute else (
            readiness(config,args.v3/"package.json",args.pdf,context)
        )
        if not path.exists():path.mkdir(parents=True,exist_ok=False)
        evidence={
            "sourceContext":context,
            "status":status,
            "reviewOnly":True,
            "humanReviewed":False,
            "publicationAuthorized":False,
        }
        (path/"private-pilot-evidence.json").write_bytes(
            (json.dumps(evidence,ensure_ascii=True,indent=2)+"\n").encode("utf-8")
        )
        # Never print textbook source quotation or provider conversation text.
        print(json.dumps(status,indent=2))
        return 0 if status.get("readyToAttemptBrowserReview") else 2
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:
        print(json.dumps({"status":"BLOCKED",
            "error":str(e)[:230],"publicationAuthorized":False}))
        return 2

if __name__=="__main__":raise SystemExit(main())

"""Build private, real-PDF academic reviewer packets without publishing excerpts."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.reviewer_source_packets import (
    verified_source_packet, source_packets_for_activities,
)


def build(pdf:Path,manifest:Path,package:Path,proofs:Path,
          output:Path,*,activity_id:str|None=None) -> dict:
    output=output.resolve()
    if output.is_relative_to(ROOT.resolve()):
        raise ValueError("source passages may not be committed to the code repository")
    if output.exists():
        raise ValueError("private reviewer source packets are immutable; refuse overwrite")
    doc=json.loads(manifest.read_text(encoding="utf-8"))
    expected=doc.get("sha256")
    if not isinstance(expected,str):
        raise ValueError("exact source manifest must provide a SHA-256")
    pkg=json.loads(package.read_text(encoding="utf-8"))
    private=json.loads(proofs.read_text(encoding="utf-8"))
    if private.get("sourceSha256") != expected:
        raise ValueError("private source receipt differs from controlled source manifest")
    if private.get("packageCanonicalSha256") and private["packageCanonicalSha256"]!=sha256(
        json.dumps(pkg,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    ).hexdigest():
        raise ValueError("source receipts belong to a different generated package version")
    evidence=[x.get("anchor") for x in private.get("proofs",[])]
    if activity_id:
        if sum(a.get("id")==activity_id for a in pkg.get("activities",[]))!=1:
            raise ValueError("requested activity not unique in generated package")
        packet=verified_source_packet(pdf,expected,activity_id,
            [a for a in evidence if a.get("activityId")==activity_id])
        packets={activity_id:packet}
    else:
        packets=source_packets_for_activities(pdf,expected,pkg,evidence)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes((json.dumps({
        "packageSha256":sha256(package.read_bytes()).hexdigest(),
        "sourceSha256":expected,"packets":packets,
        "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False,
    },ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
    return {"activities":len(packets),"privateOutput":str(output),
            "sourceSha256":expected,"packageSha256":sha256(package.read_bytes()).hexdigest(),
            "verifiedPhysicalPages":{k:v["verifiedPages"] for k,v in packets.items()},
            "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("pdf","manifest","package","proofs","out"):
        parser.add_argument("--"+key,required=True,type=Path)
    parser.add_argument("--activity-id")
    x=parser.parse_args()
    try:
        report=build(x.pdf,x.manifest,x.package,x.proofs,x.out,activity_id=x.activity_id)
        print(json.dumps(report,indent=2));return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as e:
        print(json.dumps({"status":"BLOCKED","error":str(e)[:260],
                          "publicationAuthorized":False}));return 2

if __name__=="__main__":raise SystemExit(main())

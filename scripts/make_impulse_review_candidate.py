"""Create a private, immutable, review-only copy of the impulse qualifier fix.

This tool never writes to an installed generator package, Git working tree,
original textbook, production directory or external publication endpoint.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from app_generator.validation.impulse_qualifier_repair import (
    SOURCE_SHA256, build_review_candidate,
)


def make_candidate(original_file: Path, source_pdf: Path, output_dir: Path) -> dict:
    original_file=original_file.resolve()
    source_pdf=source_pdf.resolve()
    output_dir=output_dir.resolve()
    if output_dir.is_relative_to(ROOT.resolve()):
        raise ValueError("private candidate folder cannot be inside code repository")
    if output_dir.exists():
        raise ValueError("candidate already exists: refusing to overwrite prior evidence")
    if not original_file.is_file() or not source_pdf.is_file():
        raise ValueError("installed package and controlled PDF must both exist")
    original_bytes=original_file.read_bytes()
    original_sha=sha256(original_bytes).hexdigest()
    original=json.loads(original_bytes.decode("utf-8"))
    candidate,review=build_review_candidate(original,source_pdf,SOURCE_SHA256)
    # Byte-diff property: all activity IDs and all untargeted entries unchanged.
    if len(original["activities"])!=len(candidate["activities"]):
        raise ValueError("candidate activity count unexpectedly changed")
    for a,b in zip(original["activities"],candidate["activities"]):
        if a["id"]!=b["id"] or (a["id"]!=review["activityId"] and a!=b):
            raise ValueError("review candidate unexpectedly changes unrelated activity")
    review["originalPackageFileSha256"]=original_sha
    review["candidatePackageFileSha256"]=sha256(
        (json.dumps(candidate,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    ).hexdigest()
    review["originalPath"]=str(original_file)
    review["privateCandidate"]=str(output_dir/"package.json")
    # Explicitly never provide an automatic PASS just because the wording
    # obeys deterministic locale and physics checks.
    review["academicQA"]="REVIEW_REQUIRED"
    review["publicationAuthorized"]=False
    output_dir.mkdir(parents=True,exist_ok=False)
    (output_dir/"package.json").write_bytes(
        (json.dumps(candidate,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    )
    (output_dir/"review.json").write_bytes(
        (json.dumps(review,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    )
    if sha256((output_dir/"package.json").read_bytes()).hexdigest() != review["candidatePackageFileSha256"]:
        raise ValueError("candidate disk bytes do not match immutable review SHA")
    return {
        "candidateSha256":review["candidatePackageFileSha256"],
        "originalSha256":review["originalPackageFileSha256"],
        "controlledSourceSha256":SOURCE_SHA256,
        "activities":len(candidate["activities"]),
        "changedActivity":review["activityId"],
        "changedFields":review["changedFields"],
        "answerKeyUnchanged":review["answerKeyUnchanged"],
        "reviewOnly":review["reviewOnly"],
        "publicationAuthorized":review["publicationAuthorized"],
        "academicQA":review["academicQA"],
        "privateOutputDirectory":str(output_dir),
    }


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installed-package",required=True,type=Path)
    parser.add_argument("--source-pdf",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    a=parser.parse_args()
    try:
        result=make_candidate(a.installed_package,a.source_pdf,a.out)
        print(json.dumps(result,ensure_ascii=True,indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print(json.dumps({"status":"BLOCKED","reviewOnly":True,
                          "publicationAuthorized":False,"error":str(exc)[:280]}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())

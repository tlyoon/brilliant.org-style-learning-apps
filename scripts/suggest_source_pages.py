"""Suggest source PDF pages for each activity; never claim a correctness PASS."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# Direct invocation via python scripts/name.py must import this checkout,
# not an older editable installation or another PC's working tree.
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from app_generator.validation.page_candidates import audit_page_candidates


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--out", type=Path, help="Write private QA hints outside repository")
    opts=parser.parse_args()
    try:
        package=json.loads(opts.package.read_text(encoding="utf-8"))
        manifest=json.loads(opts.source_manifest.read_text(encoding="utf-8"))
        if (len(manifest.get("sources", [])) != 1 or
            manifest["sources"][0].get("sha256") != manifest.get("sha256")):
            raise ValueError("source manifest is ambiguous")
        result=audit_page_candidates(package,opts.pdf,manifest["sha256"])
        output=json.dumps(result,ensure_ascii=False,indent=2)
        if opts.out:
            absolute=opts.out.resolve()
            project=Path(__file__).resolve().parents[1]
            if absolute.is_relative_to(project):
                raise ValueError("private source-hint reports cannot be saved in the repository")
            absolute.parent.mkdir(parents=True,exist_ok=True)
            if absolute.exists():
                raise ValueError("refusing to overwrite existing private source hints")
            absolute.write_text(output+"\n",encoding="utf-8")
        else:
            print(output)
        return 0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError) as exc:
        print(json.dumps({"status":"REVIEW_REQUIRED","error":str(exc)[:250],
                          "academicPass":False,"publicationAuthorized":False}))
        return 2

if __name__=="__main__":
    raise SystemExit(main())

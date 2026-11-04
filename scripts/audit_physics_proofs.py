"""Independent bounded physics proof for a private, source-anchored witness.

A bounded proposition PASS does NOT confer a full academic activity PASS.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_generator.validation.physics_proofs import audit_proofs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--receipts", required=True, type=Path,
                        help="Private anchored mathematical witness receipts")
    parser.add_argument("--out", type=Path, help="New private output path, not inside repository")
    args = parser.parse_args()
    try:
        package=json.loads(args.package.read_text(encoding="utf-8"))
        manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
        receipts=json.loads(args.receipts.read_text(encoding="utf-8"))
        if len(manifest.get("sources",[]))!=1 or manifest["sources"][0]["sha256"]!=manifest["sha256"]:
            raise ValueError("controlled PDF manifest is ambiguous")
        result=audit_proofs(package,args.pdf,manifest["sha256"],receipts)
        body=json.dumps(result,ensure_ascii=False,indent=2)
        if args.out:
            target=args.out.resolve()
            if target.is_relative_to(ROOT.resolve()):
                raise ValueError("physics proof receipts must not be stored in public repository")
            target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():
                raise ValueError("refusing to replace a private academic audit record")
            target.write_text(body+"\n",encoding="utf-8")
            print(json.dumps({key:result[key] for key in (
                "activitiesTotal","boundedPropositionsVerified","failedWitnesses",
                "unresolvedReceipts","academicActivitiesPassed","academicQA",
                "publicationAuthorized"
            )}))
        else:
            print(body)
        return 1 if result["failedWitnesses"] else (2 if result["unresolvedReceipts"] else 0)
    except (OSError,KeyError,TypeError,ValueError,json.JSONDecodeError) as exc:
        print(json.dumps({"academicQA":"REVIEW_REQUIRED","publicationAuthorized":False,
                          "error":str(exc)[:240]}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())

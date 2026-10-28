"""Stage a private, read-only Section 9.4 browser preview with approval blocked."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from app_generator.runtime.private_release_candidate import stage_private_candidate


def main()->int:
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ("package","pdf","matrix","physics","outdir"):
        cli.add_argument("--"+key,required=True,type=Path)
    cli.add_argument("--package-sha256",required=True)
    cli.add_argument("--source-sha256",required=True)
    args=cli.parse_args()
    try:
        r=stage_private_candidate(
            repo_root=ROOT,package_file=args.package,source_pdf=args.pdf,
            matrix_file=args.matrix,physics_file=args.physics,out_dir=args.outdir,
            expected_package_sha256=args.package_sha256,
            expected_source_sha256=args.source_sha256,
        )
        print(json.dumps({k:r[k] for k in (
            "status","activityCount","sourceLocationReceipts",
            "boundedPhysicsReceipts","fullAcademicPassCount",
            "academicQA","publicationAuthorized"
        )}))
        return 0
    except (ValueError,TypeError,KeyError,OSError,json.JSONDecodeError) as exc:
        print(json.dumps({"status":"BLOCKED","errorClass":type(exc).__name__,
                          "publicationAuthorized":False}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
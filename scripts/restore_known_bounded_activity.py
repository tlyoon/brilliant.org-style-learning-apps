"""Private, no-model rollback of a narrowly recognized scientific mutation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from app_generator.validation.bounded_activity_rollback import restore_known_bounded_version


def main()->int:
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ("candidate","baseline","pdf","dossier","outdir"):
        cli.add_argument("--"+key,type=Path,required=True)
    cli.add_argument("--baseline-sha256",required=True)
    cli.add_argument("--source-sha256",required=True)
    cfg=cli.parse_args()
    try:
        report=restore_known_bounded_version(
            candidate_file=cfg.candidate,baseline_file=cfg.baseline,
            source_pdf=cfg.pdf,baseline_dossier_file=cfg.dossier,
            expected_baseline_sha256=cfg.baseline_sha256,
            expected_source_sha256=cfg.source_sha256,
            private_output_dir=cfg.outdir,
        )
        print(json.dumps({
            "activityId":report["activityId"],
            "restoration":report["restoration"],
            "detectedContradictionCount":len(report["detectedContradictions"]),
            "restoredPackageSha256":report["restoredPackageSha256"],
            "nextAction":report["nextAction"],
            "academicQA":"REVIEW_REQUIRED",
            "publicationAuthorized":False,
        }))
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print(json.dumps({"status":"BLOCKED","errorClass":type(exc).__name__,
                          "publicationAuthorized":False}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
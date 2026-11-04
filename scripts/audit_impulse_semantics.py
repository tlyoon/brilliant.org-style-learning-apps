"""Run bounded independent trilingual/distractor QA on exact private impulse v2.

Results are not complete academic PASS. Store immutable report OUTSIDE repo.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from app_generator.validation.impulse_semantics import audit_impulse_candidate

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--package",type=Path,required=True)
    p.add_argument("--review",type=Path,required=True)
    p.add_argument("--source-pdf",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    try:
        destination=args.out.resolve()
        if destination.is_relative_to(ROOT.resolve()):
            raise ValueError("private academic evidence must remain outside public repository")
        if destination.exists():
            raise ValueError("refuse to overwrite previous source-bound QA report")
        report=audit_impulse_candidate(args.package.resolve(),args.review.resolve(),
                                       args.source_pdf.resolve())
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes((json.dumps(report,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
        print(json.dumps({
            "candidateSha256":report["candidateFileSha256"],
            "boundedOptionModelsVerified":report["boundedOptionModelsVerified"],
            "optionQualifiersReviewRequired":report["optionQualifiersReviewRequired"],
            "localizedConceptsFound":report["multilingualNarrative"]["boundedConceptsPresent"],
            "localizedConceptChecks":report["multilingualNarrative"]["localizedFieldChecks"],
            "completeMultilingualSemanticAgreement":report["completeMultilingualSemanticAgreement"],
            "academicQA":report["academicQA"],"publicationAuthorized":report["publicationAuthorized"],
            "privateReport":str(destination),
        }))
        return 0
    except (OSError,TypeError,KeyError,ValueError,json.JSONDecodeError) as exc:
        print(json.dumps({"academicQA":"REVIEW_REQUIRED","publicationAuthorized":False,
                          "error":str(exc)[:280]}))
        return 2

if __name__=="__main__":
    raise SystemExit(main())

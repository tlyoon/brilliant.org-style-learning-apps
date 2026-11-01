"""Private original-source v9/v10 scientific overclaim QA comparison."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster
from app_generator.validation.inelastic_separation_claim import (
    ACTIVITY,V9_SHA,PDF_SHA,unqualified_inelastic_rebound_defects,
    nonreversing_inelastic_witness,
)
V10_SHA="6d0a9179025aa177ec76e97a14c6ac93fc0f331472444f9f9ad9f48abb41044f"


def audit(before:Path,after:Path,pdf:Path,before_packets:Path,after_packets:Path)->dict:
    old_proof=verify_full_source_packet_roster(package_file=before,source_pdf=pdf,
                                             packets_file=before_packets,expected_count=18)
    new_proof=verify_full_source_packet_roster(package_file=after,source_pdf=pdf,
                                             packets_file=after_packets,expected_count=18)
    if (old_proof["packageSha256"]!=V9_SHA or
        new_proof["packageSha256"]!=V10_SHA or
        old_proof["sourceSha256"]!=new_proof["sourceSha256"] or
        new_proof["sourceSha256"]!=PDF_SHA or
        old_proof["publicationAuthorized"] is not False or
        new_proof["publicationAuthorized"] is not False):
        raise ValueError("controlled PDF or private candidate SHA changed")
    originals=json.loads(before.read_text("utf-8"))["activities"]
    revised=json.loads(after.read_text("utf-8"))["activities"]
    if len(originals)!=18 or len(revised)!=18:
        raise ValueError("expected 18 original-source activities")
    changes=0
    for left,right in zip(originals,revised):
        if left["id"]!=right["id"]:
            raise ValueError("source activity ID roster changed")
        if left==right:continue
        if left["id"]!=ACTIVITY:
            raise ValueError("unexpected activity changed")
        old=dict(left);new=dict(right)
        old_ex=old.pop("explanation",None);new_ex=new.pop("explanation",None)
        if old!=new or set(old_ex)!=set(new_ex)!={"en","ms","zh"}:
            raise ValueError("science answers, labels or other fields changed")
        if not all(old_ex[k]!=new_ex[k] for k in ("en","ms","zh")):
            raise ValueError("all three corrected explanations required")
        changes+=1
    former=next(x for x in originals if x["id"]==ACTIVITY)
    current=next(x for x in revised if x["id"]==ACTIVITY)
    old_errors=unqualified_inelastic_rebound_defects(former)
    new_errors=unqualified_inelastic_rebound_defects(current)
    if changes!=1 or len(old_errors)!=3 or new_errors:
        raise ValueError("inelastic overclaim check did not match controlled correction")
    witness=nonreversing_inelastic_witness()
    if witness["kineticEnergyFinalToInitial"]!="5/8":
        raise ValueError("independent restitution witness failed")
    return {"status":"SOURCE_BOUND_INELASTIC_NONREVERSAL_PHYSICS_QA_REPAIRED",
       "originalPdfSha256":PDF_SHA,
       "oldV9PackageSha256":V9_SHA,
       "newV10PackageSha256":V10_SHA,
       "originalSourceActivitiesReverifiedPerCandidate":18,
       "previousIncorrectReboundLocaleClaims":len(old_errors),
       "correctedIncorrectReboundLocaleClaims":len(new_errors),
       "otherActivityChanges":0,"answerModelsChanged":False,
       "boundedRestitutionWitness":witness,
       "semanticTranslationFullyApproved":False,
       "academicQA":"REVIEW_REQUIRED","formalAcademicPASS":0,
       "publicationAuthorized":False}


def main()->int:
    p=argparse.ArgumentParser()
    for k in ("before","after","pdf","before-packets","after-packets","out"):
        p.add_argument("--"+k,type=Path,required=True)
    a=p.parse_args()
    try:
        dest=a.out.resolve()
        if dest.exists() or dest.is_relative_to(ROOT) or not dest.parent.is_dir():
            raise ValueError("new immutable private audit destination required")
        result=audit(a.before,a.after,a.pdf,a.before_packets,a.after_packets)
        with dest.open("x",encoding="utf-8") as f:
            json.dump(result,f,ensure_ascii=True,indent=2)
            f.write("\n")
        print(json.dumps(result))
        return 0
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({"status":"SOURCE_BOUND_INELASTIC_QA_BLOCKED",
            "errorType":type(exc).__name__,"publicationAuthorized":False}))
        return 2
if __name__=="__main__":raise SystemExit(main())

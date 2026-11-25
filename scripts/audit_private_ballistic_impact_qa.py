"""Strict private source-bound v10/v11 ballistic momentum QA comparison."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster
from app_generator.validation.ballistic_impulse_scope import (
    ACTIVITY,V10_SHA,PDF_SHA,invalid_ballistic_impact_exactness_defects,
    small_external_impulse_witness,
)
V11_SHA="8218f38eca1601ca0ec97061a5f566caa2e465aef681d8931deb53c90cafae97"


def audit(before:Path,after:Path,pdf:Path,before_packets:Path,after_packets:Path)->dict:
    a=verify_full_source_packet_roster(
       package_file=before,source_pdf=pdf,packets_file=before_packets,expected_count=18)
    b=verify_full_source_packet_roster(
       package_file=after,source_pdf=pdf,packets_file=after_packets,expected_count=18)
    if (a["packageSha256"]!=V10_SHA or b["packageSha256"]!=V11_SHA or
        a["sourceSha256"]!=b["sourceSha256"] or b["sourceSha256"]!=PDF_SHA or
        a["publicationAuthorized"] is not False or b["publicationAuthorized"] is not False):
        raise ValueError("immutable source/candidate SHA mismatch")
    old=json.loads(before.read_text("utf-8"))["activities"]
    new=json.loads(after.read_text("utf-8"))["activities"]
    if len(old)!=18 or len(new)!=18:
        raise ValueError("18 original activity roster changed")
    altered=[]
    for x,y in zip(old,new):
        if x["id"]!=y["id"]:
            raise ValueError("activity identifiers or order modified")
        if x==y:continue
        if x["id"]!=ACTIVITY:
            raise ValueError("unexpected source activity modified")
        a_rest,b_rest=dict(x),dict(y)
        before_logic=a_rest.pop("answerLogic")
        after_logic=b_rest.pop("answerLogic")
        if (a_rest!=b_rest or set(before_logic)!=set(after_logic)!={"en","ms","zh"}
            or not all(before_logic[l]!=after_logic[l] for l in ("en","ms","zh"))):
            raise ValueError("non-target activity answers or fields modified")
        altered.append(x["id"])
    v10=next(x for x in old if x["id"]==ACTIVITY)
    v11=next(y for y in new if y["id"]==ACTIVITY)
    old_errors=invalid_ballistic_impact_exactness_defects(v10)
    new_errors=invalid_ballistic_impact_exactness_defects(v11)
    if len(old_errors)!=3 or new_errors or altered!=[ACTIVITY]:
        raise ValueError("source-grounded known trilingual defect correction mismatched")
    witness=small_external_impulse_witness()
    if witness["externalHorizontalImpulse"]=="0" or witness["exactMomentumConservation"]:
        raise ValueError("exact external impulse witness invalid")
    return {
       "status":"SOURCE_BOUND_BALLISTIC_IMPULSE_APPROXIMATION_QA_REPAIRED",
       "originalPdfSha256":PDF_SHA,
       "oldV10PackageSha256":V10_SHA,
       "newV11PackageSha256":V11_SHA,
       "originalSourceActivitiesReverifiedPerCandidate":18,
       "oldUnsupportedTrilingualExactnessClaims":3,
       "correctedUnsupportedTrilingualExactnessClaims":0,
       "changedActivityCount":1,
       "otherActivityOrAnswerModelChanges":False,
       "exactImpulseWitness":witness,
       "fullScientificAndTranslationSemanticsVerified":False,
       "formalAcademicPASS":0,"academicQA":"REVIEW_REQUIRED",
       "publicationAuthorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    for k in ("before","after","pdf","before-packets","after-packets","out"):
        p.add_argument("--"+k,type=Path,required=True)
    x=p.parse_args()
    try:
        out=x.out.resolve()
        if out.exists() or out.is_relative_to(ROOT) or not out.parent.is_dir():
            raise ValueError("private external new receipt destination required")
        result=audit(x.before,x.after,x.pdf,x.before_packets,x.after_packets)
        with out.open("x",encoding="utf-8") as f:
            json.dump(result,f,ensure_ascii=True,indent=2)
            f.write("\n")
        print(json.dumps(result))
        return 0
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({"status":"SOURCE_BOUND_BALLISTIC_AUDIT_BLOCKED",
            "errorType":type(exc).__name__,"publicationAuthorized":False}))
        return 2
if __name__=="__main__":raise SystemExit(main())

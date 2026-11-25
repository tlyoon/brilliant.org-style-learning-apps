"""Private source-bound v6/v7 counterexample guard before/after receipt."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster
from app_generator.validation.multiball_qualification import (
    ACTIVITY,explicit_multiball_uniqueness_defects,rational_conservation_witness,
    V6_PACKAGE_SHA,SOURCE_PDF_SHA,
)


def audit(*,before:Path,after:Path,pdf:Path,
          before_packets:Path,after_packets:Path)->dict:
    old=verify_full_source_packet_roster(
        package_file=before,source_pdf=pdf,
        packets_file=before_packets,expected_count=18)
    new=verify_full_source_packet_roster(
        package_file=after,source_pdf=pdf,
        packets_file=after_packets,expected_count=18)
    if (old["packageSha256"]!=V6_PACKAGE_SHA or
        old["sourceSha256"]!=new["sourceSha256"] or
        new["sourceSha256"]!=SOURCE_PDF_SHA or
        old["publicationAuthorized"] is not False or
        new["publicationAuthorized"] is not False):
        raise ValueError("original PDF or source-bound candidate hashes invalid")
    before_data=json.loads(before.read_text("utf-8"))
    after_data=json.loads(after.read_text("utf-8"))
    oldacts={a["id"]:a for a in before_data["activities"]}
    newacts={a["id"]:a for a in after_data["activities"]}
    if set(oldacts)!=set(newacts) or len(oldacts)!=18:
        raise ValueError("controlled roster changed unexpectedly")
    for id in oldacts:
        if id==ACTIVITY:
            before_mcq=oldacts[id].copy()
            after_mcq=newacts[id].copy()
            before_ex=before_mcq.pop("explanation")
            after_ex=after_mcq.pop("explanation")
            if before_mcq!=after_mcq or set(before_ex)!=set(after_ex):
                raise ValueError("protected MCQ answers or other learning fields changed")
        elif oldacts[id]!=newacts[id]:
            raise ValueError("unexpected activity mutation in private revision")
    original=explicit_multiball_uniqueness_defects(oldacts[ACTIVITY])
    fixed=explicit_multiball_uniqueness_defects(newacts[ACTIVITY])
    if len(original)!=3 or fixed:
        raise ValueError("scientific uniqueness failure comparison invalid")
    proof=rational_conservation_witness()
    if proof["conservationAloneUniquelyDeterminesMultibodyOutcome"]:
        raise ValueError("independent exact counterexample failed")
    return {
      "status":"SOURCE_BOUND_MULTIBALL_OVERCLAIM_QA_REPAIR_VERIFIED",
      "originalPdfSha256":SOURCE_PDF_SHA,
      "oldPrivateV6Sha256":old["packageSha256"],
      "newPrivateV7Sha256":new["packageSha256"],
      "originalSourceActivitiesReverifiedPerCandidate":18,
      "originalTrilingualUniquenessOverclaims":len(original),
      "correctedTrilingualUniquenessOverclaims":len(fixed),
      "otherActivitiesModified":0,
      "correctMcqAnswerAndOptionsUnchanged":True,
      "alternativeContactDynamicsPhysicallyProven":False,
      "translationSemanticEquivalenceApproved":False,
      "academicQA":"REVIEW_REQUIRED","formalAcademicPASS":0,
      "publicationAuthorized":False,
    }


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("before","after","pdf","before-packets","after-packets","out"):
        p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    try:
        destination=a.out.resolve()
        if (destination.exists() or destination.is_relative_to(ROOT)
            or not destination.parent.is_dir()):
            raise ValueError("new private immutable audit receipt required")
        result=audit(before=a.before,after=a.after,pdf=a.pdf,
                     before_packets=a.before_packets,after_packets=a.after_packets)
        with destination.open("x",encoding="utf-8") as f:
            json.dump(result,f,ensure_ascii=True,sort_keys=True,indent=2)
            f.write("\n")
        print(json.dumps(result,sort_keys=True))
        return 0
    except (OSError,ValueError,TypeError,KeyError) as exc:
        print(json.dumps({"status":"MULTIBALL_QA_COMPARISON_BLOCKED",
            "errorType":type(exc).__name__,"publicationAuthorized":False}))
        return 2

if __name__=="__main__":raise SystemExit(main())

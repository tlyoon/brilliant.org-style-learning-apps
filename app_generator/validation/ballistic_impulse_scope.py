"""Source-anchored ballistic pendulum impact impulse qualification.

A small but nonzero net external impulse means the total horizontal
momentum change is small but nonzero. An impulse approximation is not a
proof of exact zero. Bound the private candidate, preserve answer models,
and keep formal academic publication gates closed.
"""
from __future__ import annotations
from copy import deepcopy
from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path

from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster

ACTIVITY="int-order-ballistic-pendulum-sequence"
V10_SHA="6d0a9179025aa177ec76e97a14c6ac93fc0f331472444f9f9ad9f48abb41044f"
PDF_SHA="08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578"


def small_external_impulse_witness()->dict:
    """Projectile + target: pi=m1*u=1, total mass=5; Jext=1/1000."""
    impulse=F(1,1000)
    p_initial=F(1)
    p_final=p_initial+impulse
    final_velocity=p_final/F(5)
    approximated_velocity=p_initial/F(5)
    assert p_final-p_initial==impulse!=0
    assert final_velocity!=approximated_velocity
    assert abs(final_velocity-approximated_velocity)==F(1,5000)
    return {
        "initialHorizontalMomentum":"1",
        "externalHorizontalImpulse":"1/1000",
        "finalHorizontalMomentum":"1001/1000",
        "exactMomentumConservation":False,
        "approximateMomentumConservation":True,
        "postImpactVelocity":"1001/5000",
        "zeroExternalImpulseModelVelocity":"1/5",
        "velocityDifference":"1/5000",
    }


def invalid_ballistic_impact_exactness_defects(activity:dict)->list[str]:
    """Known unsupported claim: negligible impulse does not mean exactly zero.

    Restricted to the controlled ballistic pendulum source activity. A clean
    outcome returns REVIEW_REQUIRED in the academic matrix, never PASS.
    """
    if not isinstance(activity,dict) or activity.get("id")!=ACTIVITY:
        return []
    phrases={
      "en":("so momentum is conserved",
            "determined strictly by momentum conservation"),
      "ms":("maka momentum dikekalkan",
            "ditentukan secara ketat oleh pemuliharaan momentum"),
      "zh":("\u52a8\u91cf\u4e25\u683c\u5b88\u6052",
            "\u5b8c\u5168\u7531\u52a8\u91cf\u5b88\u6052\u51b3\u5b9a"),
    }
    logic=activity.get("answerLogic")
    errors=[]
    for lang,terms in phrases.items():
        value=logic.get(lang) if isinstance(logic,dict) else None
        if not isinstance(value,str) or not value.strip():
            errors.append("ballistic impact impulse qualifier missing in "+lang)
        elif any(term in value.casefold() for term in terms):
            errors.append("ballistic momentum incorrectly exact under approximation in "+lang)
    return errors


def copy_private_qualification(package:dict,rules:dict)->tuple[dict,dict]:
    if len(package.get("activities",[]))!=18:
        raise ValueError("18 source activities required")
    if set(rules)!={"activityId","field","replacements"} or (
       rules["activityId"]!=ACTIVITY or rules["field"]!="answerLogic"):
        raise ValueError("ballistic impact correction scope invalid")
    replacements=rules["replacements"]
    if not isinstance(replacements,dict) or set(replacements)!={"en","ms","zh"}:
        raise ValueError("three translated impacts must be repaired together")
    revised=deepcopy(package)
    activity=next((a for a in revised["activities"] if a["id"]==ACTIVITY),None)
    if activity is None:
        raise ValueError("ballistic sequencing source activity missing")
    expected={
      "en":"approximately conserved",
      "ms":"hampir dikekalkan",
      "zh":"\u8fd1\u4f3c\u5b88\u6052",
    }
    for loc,rule in replacements.items():
        if not isinstance(rule,dict) or set(rule)!={"oldFieldSha256","newText"}:
            raise ValueError("exact old field digest required")
        old=activity["answerLogic"][loc]
        new=rule["newText"]
        if (not isinstance(new,str) or len(new)<150 or new==old or
            sha256(old.encode("utf-8")).hexdigest()!=rule["oldFieldSha256"] or
            expected[loc] not in new.casefold()):
            raise ValueError("stale hash or missing momentum qualification")
        if loc=="zh" and "\u4e25\u683c\u5b88\u6052" in new:
            raise ValueError("strict impact momentum claim still present")
        activity["answerLogic"][loc]=new
    assert small_external_impulse_witness()["exactMomentumConservation"] is False
    return revised,{
       "status":"SOURCE_BOUND_BALLISTIC_IMPULSE_APPROXIMATION_QUALIFIED",
       "changedActivities":1,
       "changedLocalizedAnswerLogicFields":3,
       "restOfPackageUnchanged":True,
       "originalAnswerKeyIdsPreserved":True,
       "exactExternalImpulseWitness":small_external_impulse_witness(),
       "fullAcademicSemanticsApproved":False,
       "formalAcademicPASS":0,"academicQA":"REVIEW_REQUIRED",
       "publicationAuthorized":False,
    }


def create_private_v11(*,package_file:Path,source_pdf:Path,
                       packets_file:Path,corrections_file:Path,out_dir:Path)->dict:
    repo=Path(__file__).resolve().parents[2]
    if out_dir.exists() or out_dir.resolve().is_relative_to(repo):
        raise ValueError("new private target path required")
    verification=verify_full_source_packet_roster(
       package_file=package_file,source_pdf=source_pdf,
       packets_file=packets_file,expected_count=18)
    if (verification["packageSha256"]!=V10_SHA or
        verification["sourceSha256"]!=PDF_SHA or
        verification["newlyReverifiedSourceActivities"]!=18 or
        verification["publicationAuthorized"] is not False):
        raise ValueError("expected original PDF/private v10 identity changed")
    original_packets=json.loads(packets_file.read_text("utf-8"))
    if original_packets["packets"][ACTIVITY]["verifiedPages"]!=[7]:
        raise ValueError("source Example 9.6 PDF page did not match")
    before=json.loads(package_file.read_text("utf-8"))
    after,receipt=copy_private_qualification(
       before,json.loads(corrections_file.read_text("utf-8")))
    data=(json.dumps(after,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    digest=sha256(data).hexdigest()
    new_packets=deepcopy(original_packets)
    new_packets["packageSha256"]=digest
    out_dir.mkdir(parents=True,exist_ok=False)
    (out_dir/"package.json").write_bytes(data)
    (out_dir/"source-packets-full18.json").write_text(
       json.dumps(new_packets,ensure_ascii=True,indent=2)+"\n",encoding="utf-8")
    v=verify_full_source_packet_roster(
       package_file=out_dir/"package.json",source_pdf=source_pdf,
       packets_file=out_dir/"source-packets-full18.json",expected_count=18)
    if v["newlyReverifiedSourceActivities"]!=18 or v["sourceSha256"]!=PDF_SHA:
        raise ValueError("new private source packet roster verification failed")
    receipt.update({
       "originalPdfSha256":PDF_SHA,
       "oldV10PackageSha256":V10_SHA,
       "newV11PackageSha256":digest,
       "originalSourceActivitiesReverified":18,
       "privateCandidateVersion":"v11-ballistic-impulse-draft",
       "publicationAuthorized":False,
    })
    (out_dir/"private-repair-receipt.json").write_text(
       json.dumps(receipt,ensure_ascii=True,indent=2)+"\n",encoding="utf-8")
    return receipt

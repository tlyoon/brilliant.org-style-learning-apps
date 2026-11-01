"""Correct an over-specific inelastic-collision motion claim in a private package.

The original source distinguishes non-sticking inelastic impacts, which can
have both final velocities in the same forward direction; reversal is not
required. This bounded proof does not establish all translation semantics.
"""
from __future__ import annotations
from copy import deepcopy
from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path

from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster

ACTIVITY="int-match-collision-properties"
V9_SHA="03be0293ed289db36c8e781325f2e92420990a62e65af515e0c705546aaf9e51"
PDF_SHA="08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578"


def nonreversing_inelastic_witness() -> dict:
    """Equal masses, initial velocities +1 and 0, restitution e=1/2."""
    e=F(1,2)
    initial=(F(1),F(0))
    final=(F(1,4),F(3,4))
    assert sum(initial)==sum(final)==1
    assert final[0]>0 and final[1]>0 and final[0]<final[1]
    assert final[1]-final[0]==e*(initial[0]-initial[1])
    ki=sum(v*v for v in initial)
    kf=sum(v*v for v in final)
    assert kf==F(5,8)*ki
    assert final[0]!=final[1]
    return {"initialVelocityUnits":[str(v) for v in initial],
            "finalVelocityUnits":[str(v) for v in final],
            "coefficientOfRestitution":str(e),
            "momentumConserved":True,
            "kineticEnergyFinalToInitial":str(kf/ki),
            "bothObjectsContinueForward":True,
            "nonStickingInelasticReversalRequired":False,
            "physicalContactRealizationFullyVerified":False}


def scoped_private_correction(package:dict, rules:dict)->tuple[dict,dict]:
    if len(package.get("activities",[]))!=18:
        raise ValueError("controlled 18-activity roster changed")
    if set(rules)!={"activityId","field","replacements"} or (
        rules["activityId"]!=ACTIVITY or rules["field"]!="explanation"):
        raise ValueError("unexpected activity or field correction")
    patch=rules["replacements"]
    if not isinstance(patch,dict) or set(patch)!={"en","ms","zh"}:
        raise ValueError("exactly three localized explanation replacements required")
    revised=deepcopy(package)
    activity=next((a for a in revised["activities"] if a["id"]==ACTIVITY),None)
    if activity is None:
        raise ValueError("source-bound inelastic classification activity absent")
    old_fields=activity["explanation"]
    for lang in ("en","ms","zh"):
        old=old_fields[lang]
        entry=patch[lang]
        if not isinstance(entry,dict) or set(entry)!={"oldFieldSha256","newText"}:
            raise ValueError("source-bound old-field hash and new text required")
        new=entry["newText"]
        if (not isinstance(old,str) or not isinstance(new,str)
            or len(new)<140 or new==old
            or sha256(old.encode("utf-8")).hexdigest()!=entry["oldFieldSha256"]):
            raise ValueError("unaltered source text or unverified private edit")
        forbidden={
          "en":"the objects rebound separately",
          "ms":"objek melantun secara berasingan",
          "zh":"\u7269\u4f53\u5206\u522b\u53cd\u5f39",
        }
        if forbidden[lang].casefold() in new.casefold():
            raise ValueError("unqualified reversal assertion remains")
        old_fields[lang]=new
    assert nonreversing_inelastic_witness()["kineticEnergyFinalToInitial"]=="5/8"
    return revised,{
        "status":"SOURCE_BOUND_INELASTIC_NONREVERSAL_QUALIFICATION",
        "changedActivities":1,
        "changedLocalizedExplanationFields":3,
        "mcqAnswerKeysUnmodified":True,
        "otherActivitiesUnmodified":True,
        "exactCollisionWitness":nonreversing_inelastic_witness(),
        "academicQA":"REVIEW_REQUIRED",
        "formalAcademicPASS":0,"publicationAuthorized":False,
    }


def create_private_v10(*,package_file:Path,source_pdf:Path,
                       packets_file:Path,corrections_file:Path,out_dir:Path)->dict:
    root=Path(__file__).resolve().parents[2]
    if out_dir.exists() or out_dir.resolve().is_relative_to(root):
        raise ValueError("must create new private candidate outside Git")
    source=verify_full_source_packet_roster(
        package_file=package_file,source_pdf=source_pdf,
        packets_file=packets_file,expected_count=18)
    if (source["packageSha256"]!=V9_SHA or source["sourceSha256"]!=PDF_SHA
        or source["newlyReverifiedSourceActivities"]!=18
        or source["publicationAuthorized"] is not False):
        raise ValueError("original textbook or controlled private v9 identity mismatch")
    manifest=json.loads(packets_file.read_text("utf-8"))
    if manifest["packets"][ACTIVITY]["verifiedPages"]!=[2]:
        raise ValueError("inelastic-collision source page changed")
    old=json.loads(package_file.read_text("utf-8"))
    new,receipt=scoped_private_correction(
        old,json.loads(corrections_file.read_text("utf-8")))
    content=(json.dumps(new,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    digest=sha256(content).hexdigest()
    corrected_manifest=deepcopy(manifest)
    corrected_manifest["packageSha256"]=digest
    out_dir.mkdir(parents=True,exist_ok=False)
    (out_dir/"package.json").write_bytes(content)
    (out_dir/"source-packets-full18.json").write_text(
        json.dumps(corrected_manifest,ensure_ascii=True,indent=2)+"\n",
        encoding="utf-8")
    after=verify_full_source_packet_roster(
        package_file=out_dir/"package.json",source_pdf=source_pdf,
        packets_file=out_dir/"source-packets-full18.json",expected_count=18)
    if after["newlyReverifiedSourceActivities"]!=18 or after["sourceSha256"]!=PDF_SHA:
        raise ValueError("private v10 source-bound correction failed")
    receipt.update({
        "sourceSha256":PDF_SHA,
        "oldV9PackageSha256":V9_SHA,
        "newV10PackageSha256":digest,
        "originalSourceActivitiesReverified":18,
        "candidateVersion":"v10-inelastic-nonreversing-draft",
        "originalPdfAndV9Unmodified":True,
        "generalScientificSemanticApproval":False,
    })
    (out_dir/"private-repair-receipt.json").write_text(
        json.dumps(receipt,ensure_ascii=True,indent=2)+"\n",encoding="utf-8")
    return receipt

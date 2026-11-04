"""Bounded exact-rational one-dimensional inelastic collision witness."""
from fractions import Fraction as F

def restitution_witness():
    rows = {}
    for e in (F(0), F(1, 2), F(1)):
        v1, v2 = (1-e)/2, (1+e)/2
        assert v1+v2 == 1
        energy_ratio = v1*v1+v2*v2
        assert energy_ratio == (1+e*e)/2
        rows[str(e)] = {"finalMomentum":"1", "kineticEnergyRatio":str(energy_ratio), "relativeSeparationSpeed":str(v2-v1)}
    assert rows["1/2"]["kineticEnergyRatio"] == "5/8"
    return rows


from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster

ACTIVITY="mcq-relative-velocity-scope"
V7_SHA="3b90bd155a404bb2dba3d60b1a060b8197c9150e8671cf878076fdeb72b4ace3"
PDF_SHA="08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578"

def patch_derivation(package,correction):
    if len(package.get("activities",[]))!=18 or set(correction)!={"activityId","replacements"} or correction["activityId"]!=ACTIVITY:
        raise ValueError("unauthorized relative-velocity repair scope")
    rules=correction["replacements"]
    if not isinstance(rules,dict) or set(rules)!={"en","ms","zh"}:
        raise ValueError("exactly three locale replacements required")
    revised=deepcopy(package)
    activity=next(a for a in revised["activities"] if a["id"]==ACTIVITY)
    incorrect={"en":"this division is invalid","ms":"pembahagian ini tidak sah",
               "zh":"\u8fd9\u4e00\u9664\u6cd5\u4fbf\u4e0d\u6210\u7acb"}
    for lang in ("en","ms","zh"):
        old=activity["answerLogic"][lang]
        rule=rules[lang]
        new=rule.get("newText")
        if (sha256(old.encode("utf-8")).hexdigest()!=rule.get("oldFieldSha256")
            or not isinstance(new,str) or len(new)<145
            or incorrect[lang] in new.casefold() or new==old):
            raise ValueError("unverified derivation text replacement")
        activity["answerLogic"][lang]=new
    assert restitution_witness()["1/2"]["kineticEnergyRatio"]=="5/8"
    return revised

def emit_private_v8(*,package_file,source_pdf,packets_file,corrections_file,out_dir):
    repo=Path(__file__).resolve().parents[2]
    if out_dir.exists() or out_dir.resolve().is_relative_to(repo):
        raise ValueError("private new output outside Git only")
    before=verify_full_source_packet_roster(
        package_file=package_file,source_pdf=source_pdf,
        packets_file=packets_file,expected_count=18)
    if (before["packageSha256"]!=V7_SHA or before["sourceSha256"]!=PDF_SHA
        or before["newlyReverifiedSourceActivities"]!=18):
        raise ValueError("controlled v7/source PDF hash mismatch")
    old=json.loads(package_file.read_text("utf-8"))
    manifest=json.loads(packets_file.read_text("utf-8"))
    if manifest["packets"][ACTIVITY]["verifiedPages"]!=[3]:
        raise ValueError("original relative-speed source page differs")
    new=patch_derivation(old,json.loads(corrections_file.read_text("utf-8")))
    data=(json.dumps(new,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    digest=sha256(data).hexdigest()
    manifest["packageSha256"]=digest
    out_dir.mkdir(parents=True,exist_ok=False)
    (out_dir/"package.json").write_bytes(data)
    (out_dir/"source-packets-full18.json").write_text(
        json.dumps(manifest,ensure_ascii=True,indent=2)+"\n",encoding="utf-8")
    after=verify_full_source_packet_roster(
        package_file=out_dir/"package.json",source_pdf=source_pdf,
        packets_file=out_dir/"source-packets-full18.json",expected_count=18)
    if after["newlyReverifiedSourceActivities"]!=18:
        raise ValueError("v8 original source passage mismatch")
    result={"status":"SOURCE_BOUND_DERIVATION_PREMISE_REPAIRED",
            "oldV7PackageSha256":V7_SHA,"newV8PackageSha256":digest,
            "originalPdfSha256":PDF_SHA,"originalSourceActivitiesReverified":18,
            "changedActivities":1,"changedLocalizedAnswerLogicFields":3,
            "exactInelasticWitness":restitution_witness(),
            "formalAcademicPASS":0,"academicQA":"REVIEW_REQUIRED",
            "publicationAuthorized":False}
    (out_dir/"private-repair-receipt.json").write_text(
        json.dumps(result,ensure_ascii=True,indent=2)+"\n",encoding="utf-8")
    return result

def incorrect_derivation_premise_defects(activity):
    if not isinstance(activity,dict) or activity.get("id")!=ACTIVITY:
        return []
    terms={"en":"this division is invalid",
           "ms":"pembahagian ini tidak sah",
           "zh":"\u8fd9\u4e00\u9664\u6cd5\u4fbf\u4e0d\u6210\u7acb"}
    values=activity.get("answerLogic",{})
    return ["false energy premise attributed to division in "+lang
            for lang,term in terms.items()
            if not isinstance(values,dict) or not isinstance(values.get(lang),str)
            or term in values[lang].casefold()]

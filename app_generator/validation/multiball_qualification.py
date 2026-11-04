"""Source-grounded Newton's cradle conservation-law counterexample and private correction.

The textbook's proposed two-balls-at-half-speed outcome violates elastic energy.
That conclusion DOES NOT imply conservation laws alone uniquely determine all
possible multi-body final velocities; contact geometry/allowed directions matter.
No private textbook prose or authored candidate answer is stored in this module.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as F
from hashlib import sha256
from pathlib import Path
import json

from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster

ACTIVITY="mcq-newton-cradle-multi-ball"
SOURCE_PDF_SHA="08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578"
V6_PACKAGE_SHA="12aa856491536171756ce2dffcee30ccb26434d630088b46901c529fb2648fc6"
LOCALES=("en","ms","zh")
FIELD="explanation"


def rational_conservation_witness()->dict:
    """An exact THREE-body counterexample to uniqueness from p, K alone."""
    before=(F(1),F(0),F(0))
    # These satisfy both conservation laws, but contain backward motion.
    other=(F(-1,3),F(2,3),F(2,3))
    textbook=(F(0),F(0),F(1))
    proposal=(F(0),F(1,2),F(1,2))
    def momentum(vel):return sum(vel,F(0))
    def doubled_ke(vel):return sum((v*v for v in vel),F(0))
    assert momentum(before)==momentum(other)==momentum(textbook)==momentum(proposal)==1
    assert doubled_ke(before)==doubled_ke(other)==doubled_ke(textbook)==1
    assert doubled_ke(proposal)==F(1,2)
    assert other!=textbook
    # If all final velocities point forward, then sum(v)^2 - sum(v^2)
    # equals twice the sum of pairwise products. All products nonnegative,
    # hence at most one component is nonzero when p and K match.
    nonnegative=(F(0),F(0),F(1))
    pair_cross=sum((nonnegative[i]*nonnegative[j]
                    for i in range(3) for j in range(i+1,3)),F(0))
    assert pair_cross==0
    return {
      "conservationAloneUniquelyDeterminesMultibodyOutcome":False,
      "alternateThreeBallVelocityUnits":[str(x) for x in other],
      "alternateMomentumUnits":str(momentum(other)),
      "alternateDoubledKineticEnergyUnits":str(doubled_ke(other)),
      "twoHalfSpeedProposalDoubledKineticEnergyUnits":str(doubled_ke(proposal)),
      "restrictedForwardOnlyOneNonzeroVelocity":True,
      "alternateTrajectoryEstablishedPhysically":False,
      "newtonsCradleFigureProvenanceFullyInterpreted":False,
    }


def explicit_multiball_uniqueness_defects(activity:dict)->list[str]:
    """Flag known overclaims that p and K ALONE uniquely fix all cradle outcomes.

    This is a narrow deterministic *failure detector*, never a PASS or general
    natural-language semantics verifier. Report locale names, not protected text.
    """
    if not isinstance(activity,dict) or activity.get("id")!=ACTIVITY:
        return []
    explanations=activity.get("explanation")
    if not isinstance(explanations,dict):
        return ["Newton cradle trilingual explanation missing"]
    signatures={
       "en":"the only configuration that satisfies both conservation laws",
       "ms":"satu-satunya konfigurasi yang memenuhi kedua-dua hukum",
       "zh":"\u552f\u4e00\u80fd\u540c\u65f6\u6ee1\u8db3\u4e24\u4e2a\u5b88\u6052\u5b9a\u5f8b",
    }
    defects=[]
    for lang,phrase in signatures.items():
        text=explanations.get(lang)
        if not isinstance(text,str) or not text.strip():
            defects.append("missing Newton cradle explanation for "+lang)
        elif phrase in text.casefold():
            defects.append("conservation-only uniqueness overclaim in "+lang)
    return defects


def apply_private_clarification(package:dict, corrections:dict)->tuple[dict,dict]:
    """Copy-on-write 3-language one-field patch bound to exact old field hashes."""
    if len(package.get("activities",[]))!=18:
        raise ValueError("source-controlled eighteen-activity roster changed")
    if set(corrections)!={"activityId","field","replacements"} or (
        corrections["activityId"],corrections["field"])!=(ACTIVITY,FIELD):
        raise ValueError("only Newton cradle trilingual explanation may change")
    replacements=corrections["replacements"]
    if not isinstance(replacements,dict) or set(replacements)!=set(LOCALES):
        raise ValueError("exactly three locale-scoped explanation replacements required")
    candidate=deepcopy(package)
    activity=next((a for a in candidate["activities"] if a["id"]==ACTIVITY),None)
    if not activity or not isinstance(activity.get(FIELD),dict):
        raise ValueError("controlled explanation missing")
    for locale in LOCALES:
        rule=replacements[locale]
        if not isinstance(rule,dict) or set(rule)!={"oldFieldSha256","newText"}:
            raise ValueError("private exact field-hash replacement required")
        old=activity[FIELD][locale]
        new=rule["newText"]
        if (not isinstance(old,str) or not isinstance(new,str) or
            len(new)<60 or len(new)>2000 or new==old or
            sha256(old.encode("utf-8")).hexdigest()!=rule["oldFieldSha256"]):
            raise ValueError("unchanged original field hash or replacement length invalid")
        # Explicitly reject the prior overstatement in all three locales.
        forbidden={
          "en":("The only configuration that satisfies both conservation laws",),
          "ms":("Satu-satunya konfigurasi yang memenuhi kedua-dua hukum",),
          "zh":("\u552f\u4e00\u80fd\u540c\u65f6\u6ee1\u8db3\u4e24\u4e2a\u5b88\u6052\u5b9a\u5f8b",),
        }
        if any(term in new for term in forbidden[locale]):
            raise ValueError("unqualified conservation-law uniqueness remains")
        activity[FIELD][locale]=new
    if not rational_conservation_witness()["conservationAloneUniquelyDeterminesMultibodyOutcome"] is False:
        raise ValueError("exact multibody conservation witness failed")
    return candidate,{
      "status":"SOURCE_BOUND_MULTIBODY_UNIQUENESS_OVERSTATEMENT_REPAIRED",
      "changedActivities":1,"changedFields":3,
      "originalIncorrectTwoHalfSpeedOutcomeStillImpossible":True,
      "originalCorrectAnswerAndOptionsUnchanged":True,
      "mathematicalAlternativeDoesNotProvePhysicalContactTrajectory":True,
      "formalAcademicPASS":0,"publicationAuthorized":False,
    }


def create_private_v7(*,package_file:Path,source_pdf:Path,packets_file:Path,
                      corrections_file:Path,out_dir:Path)->dict:
    if out_dir.exists() or out_dir.resolve().is_relative_to(Path(__file__).resolve().parents[2]):
        raise ValueError("new private output directory outside Git required")
    before=verify_full_source_packet_roster(
        package_file=package_file,source_pdf=source_pdf,
        packets_file=packets_file,expected_count=18)
    if (before["packageSha256"]!=V6_PACKAGE_SHA or
        before["sourceSha256"]!=SOURCE_PDF_SHA or
        before["newlyReverifiedSourceActivities"]!=18 or
        before["publicationAuthorized"] is not False):
        raise ValueError("controlled original PDF/private-v6 digest mismatch")
    packets=json.loads(packets_file.read_text("utf-8"))
    if packets["packets"][ACTIVITY]["verifiedPages"]!=[5]:
        raise ValueError("Newton cradle original Figure 9.9 source page changed")
    package=json.loads(package_file.read_text("utf-8"))
    rules=json.loads(corrections_file.read_text("utf-8"))
    revised,receipt=apply_private_clarification(package,rules)
    out_dir.mkdir(parents=True,exist_ok=False)
    candidate=(json.dumps(revised,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    candidate_sha=sha256(candidate).hexdigest()
    updated_packets=deepcopy(packets)
    updated_packets["packageSha256"]=candidate_sha
    (out_dir/"package.json").write_bytes(candidate)
    (out_dir/"source-packets-full18.json").write_text(
        json.dumps(updated_packets,ensure_ascii=True,indent=2)+"\n",encoding="utf-8")
    after=verify_full_source_packet_roster(
        package_file=out_dir/"package.json",source_pdf=source_pdf,
        packets_file=out_dir/"source-packets-full18.json",expected_count=18)
    if (after["newlyReverifiedSourceActivities"]!=18 or
        after["sourceSha256"]!=SOURCE_PDF_SHA or
        after["packageSha256"]!=candidate_sha):
        raise ValueError("source-bound v7 packet audit failed")
    receipt.update({
       "originalSourceActivitiesReverified":18,
       "sourceSha256":SOURCE_PDF_SHA,
       "oldPackageSha256":V6_PACKAGE_SHA,
       "newPackageSha256":candidate_sha,
       "privateCandidateVersion":"v7-cradle-qualified-draft",
       "physicsWitness":rational_conservation_witness(),
       "academicQA":"REVIEW_REQUIRED",
       "formalAcademicPASS":0,"publicationAuthorized":False,
    })
    (out_dir/"private-repair-receipt.json").write_text(
        json.dumps(receipt,ensure_ascii=True,indent=2)+"\n",encoding="utf-8")
    return receipt

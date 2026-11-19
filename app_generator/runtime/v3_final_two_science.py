"""BSA218: genuine NEW versions for two historically uncertain original roles.

Section 9.1 idx0 and Section 9.6 idx6 require distinct scientifically
clarified trilingual prompts, two independent new Gemini roles EACH, immutable
old original uncertainties, and separate unadmitted candidate content.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
from typing import Callable

from app_generator.runtime.v3_frozen_original_tail import (
    _bytes, _slice, _safe_evidence, plan_frozen_original_tail,
)
from app_generator.runtime.v3_standing_paid_science import (
    authorize_standing,section91_evidence,verified_section91_standing_passes,
)
from app_generator.runtime.v3_historical_role_rollforward import (
    stage_known_unrecoverable_section96,
)
from app_generator.runtime.v3_science_validated_roster import (
    validated_section96_two_science_revision,
)
from app_generator.runtime.v3_section96_authorized_revised_qa import (
    unsent_revised_input,read_prior_two_role_science,
    verify_persisted_two_role_science,verified_new_provider_capability,
)
from app_generator.validation.autonomous_completion import (
    package_identity,assessment_progress,
)
from app_generator.validation.v3_locale_script_integrity import script_findings

REVISIONS=(
    ("section-9-1",0,"act-mcq-01-vector-nature",{
        "en":(
          "Two survey drones of equal mass fly along the same straight "
          "flight path at equal, nonzero speeds but in opposite directions. "
          "Which statement correctly compares their linear momentum vectors?"
        ),
        "ms":(
          "Dua dron tinjauan yang mempunyai jisim sama terbang di sepanjang "
          "laluan penerbangan lurus yang sama pada laju bukan sifar yang "
          "sama tetapi dalam arah bertentangan. Pernyataan manakah yang "
          "membandingkan vektor momentum linear mereka dengan betul?"
        ),
        "zh":(
          "两架质量相同的巡检无人机沿同一直线航线，以相同的非零速率朝相反方向飞行。"
          "下列哪项正确比较它们的线动量矢量？"
        ),
    }),
    ("section-9-6",6,"mcq-chal-nonuniform-density-rod",{
        "en":(
          "A straight solid shaft of length L has linear mass density "
          "increasing linearly from a positive value at its left end to a "
          "larger value at its right end. It balances horizontally on a "
          "knife-edge support at its center of mass. Compared with the "
          "geometric midpoint, where is the support, and which side "
          "contains more total mass?"
        ),
        "ms":(
          "Satu aci pepejal lurus sepanjang L mempunyai ketumpatan jisim "
          "linear yang meningkat secara linear daripada nilai positif di "
          "hujung kiri kepada nilai yang lebih tinggi di hujung kanan. "
          "Aci ini seimbang mendatar di atas sokongan mata pisau pada "
          "pusat jisimnya. Berbanding dengan titik tengah geometri, "
          "di manakah sokongan itu, dan bahagian manakah mempunyai "
          "jumlah jisim lebih besar?"
        ),
        "zh":(
          "一根长度为 L 的直实心轴，其线质量密度从左端的正值线性增加到右端较大的值。"
          "该轴在质心处由刀口支点支撑并保持水平平衡。与几何中点相比，"
          "支点位于何处？支点哪一侧的总质量更大？"
        ),
    }),
)
ROOT=Path(__file__).resolve().parents[2]
_REVISED_STAGE="final-two-science-candidates"
_INPUT_STAGE="final-two-science-review-inputs"
_SCHEMA="BOSLA_V3_FINAL_TWO_NEW_VERSION_SCIENCE_INPUT_V1"


def _stage_exact(folder:Path,name:str,raw:bytes) -> None:
    """Atomic source-bound private staging; changed bytes never silently reused."""
    if folder.is_symlink():
        raise ValueError("V3_FINAL_TWO_UNSAFE_STAGE_DIR")
    target=folder/name
    if target.is_symlink():
        raise ValueError("V3_FINAL_TWO_UNSAFE_STAGE_TARGET")
    if target.exists():
        if not target.is_file() or target.read_bytes()!=raw:
            raise ValueError("V3_FINAL_TWO_EXISTING_SOURCE_CHANGED")
        return
    folder.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=folder,prefix=".two-")
    tmp=Path(tmp)
    try:
        with os.fdopen(fd,"wb") as handle:
            handle.write(raw);handle.flush();os.fsync(handle.fileno())
        tmp.rename(target)
    finally:
        if tmp.exists():
            tmp.unlink()


def stage_final_two_new_inputs(course:Path,repo:Path,private:Path)->list[dict]:
    """Only two genuinely revised source identities, NO old uncertain replay."""
    if (not private.is_absolute() or private.is_symlink()
            or private.resolve().is_relative_to(repo.resolve())):
        raise ValueError("V3_FINAL_TWO_UNSAFE_PRIVATE_ROOT")
    old91=section91_evidence(course,repo,private)
    if (old91["oldUncertainIndex"]!=0
            or len(verified_section91_standing_passes(course,repo,private))!=17):
        raise ValueError("V3_FINAL_TWO_PREVIOUS_17_GEMINI_PASSES_NOT_VERIFIED")
    old96=plan_frozen_original_tail(
        course,repo,private,section="section-9-6")
    saved_states={x["index"]:x["state"] for x in old96["rows"]}
    if (saved_states.get(6)!="SUPPLEMENTAL_UNCERTAIN_NO_REPLAY"
            or saved_states.get(9)!="SUPPLEMENTAL_SCIENTIFIC_REPAIR_REQUIRED"
            or old96["originalUncertaintyPreserved"] is not True):
        raise ValueError("V3_FINAL_TWO_HISTORIC_96_ROLES_CHANGED")
    previous=stage_known_unrecoverable_section96(course,repo,private)
    if (previous["status"]!="NEW_VERSIONED_SECTION96_REPAIR_STAGED_QA_NOT_AUTHORIZED"
            or previous["oldAmbiguousProviderRolePreserved"] is not True):
        raise ValueError("V3_FINAL_TWO_PRIOR_96_REVISION_CHANGED")
    prevsha=previous["candidatePackageSha256"]
    prevpath=(private/"historical-role-rollforward"/"section-9-6"/
              prevsha/"package.json")
    if prevpath.is_symlink() or not prevpath.is_file():
        raise ValueError("V3_FINAL_TWO_MISSING_PREVIOUS_96_CANDIDATE")
    prevraw=prevpath.read_bytes()
    observed,previtems=package_identity(prevraw)
    if observed!=prevsha:
        raise ValueError("V3_FINAL_TWO_PREVIOUS_96_SHA_CHANGED")
    reviewed96=validated_section96_two_science_revision(
        course,repo,private,previous_sha=prevsha,previous_items=previtems)
    if reviewed96 is None or len(reviewed96["proofs"])!=2:
        raise ValueError("V3_FINAL_TWO_PRIOR_96_SCIENCE_MISSING")
    source96=(private/"scientific-failure-rollforward"/"section-9-6"/
              reviewed96["candidatePackageSha256"]/"package.json")
    if source96.is_symlink() or not source96.is_file():
        raise ValueError("V3_FINAL_TWO_MISSING_TWO_PREVIOUS_CORRECTIONS")
    source91=course/"section-9-1"/"package.json"
    if source91.is_symlink() or not source91.is_file():
        raise ValueError("V3_FINAL_TWO_MISSING_ORIGINAL_91")
    source_raws={"section-9-1":source91.read_bytes(),
                 "section-9-6":source96.read_bytes()}
    results=[]
    for section,index,activity_id,new_prompt in REVISIONS:
        old_raw=source_raws[section]
        old_package=json.loads(old_raw.decode("utf8"))
        parent,items=package_identity(old_raw)
        if len(items)!=18 or items[index]["id"]!=activity_id:
            raise ValueError("V3_FINAL_TWO_ACTIVITY_SOURCE_CHANGED")
        original_item=deepcopy(items[index])
        if (not isinstance(original_item["prompt"],dict)
                or set(original_item["prompt"])!={"en","ms","zh"}
                or original_item["prompt"]==new_prompt
                or not all(new_prompt.values())):
            raise ValueError("V3_FINAL_TWO_PROMPT_NOT_GENUINELY_REVISED")
        new_item=deepcopy(original_item)
        new_item["prompt"]=new_prompt
        if (set(new_item)!=set(original_item)
                or {k for k in new_item if new_item[k]!=original_item[k]}
                   != {"prompt"}
                or script_findings({"activities":[new_item]})):
            raise ValueError("V3_FINAL_TWO_INCOMPATIBLE_NEW_VERSION")
        candidate=deepcopy(old_package)
        candidate["activities"][index]=new_item
        candidate_raw=_bytes(candidate)
        candidate_sha,candidate_items=package_identity(candidate_raw)
        if (candidate_items[index]!=new_item
                or [i for i,(a,b) in enumerate(zip(items,candidate_items))
                    if a!=b]!=[index]):
            raise ValueError("V3_FINAL_TWO_CANDIDATE_DIFF_INCORRECT")
        frozen_raw=(course/section/"package.json").read_bytes()
        frozen_sha,frozen_items=package_identity(frozen_raw)
        if (section=="section-9-1" and frozen_sha!=parent) or (
            section=="section-9-6"
            and [i for i,(a,b) in enumerate(zip(frozen_items,candidate_items))
                 if a!=b]!=[5,6,9]):
            raise ValueError("V3_FINAL_TWO_PREVIOUS_APPROVED_CONTENT_CHANGED")
        single={
            "schema":_SCHEMA,
            "sourceSection":section,
            "sourceActivityIndex":index,
            "parentPackageSha256":parent,
            "candidatePackageSha256":candidate_sha,
            "activities":[new_item],
        }
        review_raw=_bytes(single)
        review_sha,review_items=package_identity(review_raw)
        if review_items!=[new_item] or review_sha in (parent,frozen_sha):
            raise ValueError("V3_FINAL_TWO_NOT_NEW_ROLE_IDENTITY")
        _stage_exact(private/_REVISED_STAGE/section/candidate_sha,
                     "package.json",candidate_raw)
        _stage_exact(private/_INPUT_STAGE/section/review_sha,
                     "package.json",review_raw)
        results.append({
            "section":section,"index":index,"activityId":activity_id,
            "sha":review_sha,"raw":review_raw,
            "candidateSha256":candidate_sha,
            "parentSha256":parent,"activities":candidate_items,
        })
    if source91.read_bytes()!=source_raws["section-9-1"]:
        raise ValueError("V3_FINAL_TWO_FROZEN_91_CHANGED_DURING_READ")
    if source96.read_bytes()!=source_raws["section-9-6"]:
        raise ValueError("V3_FINAL_TWO_PREVIOUS_96_CHANGED_DURING_READ")
    return results


def _proof(private:Path,entry:dict)->dict|None:
    sha=entry["sha"]
    folder=private/("v3-generated-"+sha)/"batches"
    record=folder/("v3-assessment-"+sha+".json")
    if not record.exists():
        return None
    if record.is_symlink() or not record.is_file() or record.stat().st_size>8_000_000:
        raise ValueError("V3_FINAL_TWO_BAD_ASSESSMENT")
    saved=json.loads(record.read_text(encoding="utf8"))
    state=assessment_progress(entry["raw"],saved)
    if (state.get("activitiesAssessed")!=1
            or len(saved.get("reviews",[]))!=1
            or saved["reviews"][0].get("activityId")!=entry["activityId"]):
        raise ValueError("V3_FINAL_TWO_WRONG_SAVED_ACTIVITY")
    actual=verify_persisted_two_role_science(
        private,entry["raw"],entry["activityId"],sha,state)
    if actual["uncertain"] or actual["repair"]:
        return None
    if not actual["pass"] or state.get("activitiesFullyModelReviewed")!=1:
        raise ValueError("V3_FINAL_TWO_UNCLASSIFIED_MODEL_RESULT")
    return {
        "section":entry["section"],"index":entry["index"],
        "activityId":entry["activityId"],
        "reviewSliceSha256":sha,
        "newCandidatePackageSha256":entry["candidateSha256"],
        "savedAssessmentSha256":sha256(record.read_bytes()).hexdigest(),
        "genuineConsensusPass":True,
    }


def verified_final_two_science(course:Path,repo:Path,private:Path)->dict|None:
    entries=stage_final_two_new_inputs(course,repo,private)
    proofs=[]
    for entry in entries:
        valid=_proof(private,entry)
        if valid is None:
            return None
        proofs.append(valid)
    if len(proofs)!=2:
        raise ValueError("V3_FINAL_TWO_WRONG_GENUINE_PASS_COUNT")
    return {
        "section91":{
            "candidatePackageSha256":entries[0]["candidateSha256"],
            "activities":entries[0]["activities"],
        },
        "section96":{
            "candidatePackageSha256":entries[1]["candidateSha256"],
            "activities":entries[1]["activities"],
        },
        "proofs":proofs,
        "originalSection91Index0UnknownPreserved":True,
        "originalSection96Index6UnknownPreserved":True,
        "publicationAuthorized":False,"versionedScopeAdmitted":False,
    }


def advance_final_two_new_science(course:Path,repo:Path,private:Path,*,
                                  execute:bool,transfer:bool,
                                  max_seconds:int=900,
                                  capability:dict|None=None,
                                  review_one:Callable|None=None)->dict:
    authorization=authorize_standing(
        execute=execute,transfer=transfer,activities=2,seconds=max_seconds)
    if not verified_new_provider_capability(private,capability):
        raise ValueError("V3_FINAL_TWO_PROVIDER_CAPABILITY_UNVERIFIED")
    if not callable(review_one):
        raise ValueError("V3_FINAL_TWO_MISSING_TRUE_REVIEWER")
    from app_generator.runtime.v3_yoga6_recovery import coordinator_lock
    start=time.monotonic()
    results=[]
    with coordinator_lock(private):
        entries=stage_final_two_new_inputs(course,repo,private)
        for entry in entries:
            if time.monotonic()-start>=max_seconds:
                break
            sha=entry["sha"]
            new=unsent_revised_input(private,sha)
            if new:
                callback=review_one(entry["raw"],entry["activityId"],private)
                if not isinstance(callback,dict) or callback.get("activitiesAssessed")!=1:
                    raise ValueError("V3_FINAL_TWO_CALLBACK_NOT_ONE_ACTIVITY")
                actual=verify_persisted_two_role_science(
                    private,entry["raw"],entry["activityId"],sha,callback)
            else:
                actual=read_prior_two_role_science(private,entry)
            result={
                "section":entry["section"],"index":entry["index"],
                "activityId":entry["activityId"],"reviewSliceSha256":sha,
                "reusedPreviouslyVerifiedRoleClaims":not new,
                "newConsensusPass":actual["pass"],
                "newScientificRepairRequired":actual["repair"],
                "newUncertain":actual["uncertain"],
            }
            results.append(result)
            if actual["uncertain"]:
                break
    return {
        "status":(
            "FINAL_TWO_STANDING_SCIENCE_COMPLETED"
            if len(results)==2 and all(not x["newUncertain"] for x in results)
            else "FINAL_TWO_STOP_UNCERTAIN_OR_BOUNDED"
        ),
        "outcomes":results,
        "allNewScientificPass":(
            len(results)==2 and all(x["newConsensusPass"] for x in results)
        ),
        "maximumGeminiCalls":authorization["maxPaidGeminiCalls"],
        "originalFrozenReviewsModified":False,
        "historicalUnknownProviderRolesReplayed":False,
        "publicationAuthorized":False,"versionedScopeAdmitted":False,
    }

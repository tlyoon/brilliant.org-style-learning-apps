"""BSA-201: source-bound science repair of authentic Section9.6 index9 FAIL.

Two genuine independent Gemini reviewers returned COMPLETE and FAIL on both
physicsAnswer (floor normal force cancels off-center torque before tipping)
and trilingualMeaning (Chinese \u8d28\u7ebf is not center of mass).
The original frozen source and actual failed reviewer claims NEVER change.
Stage a *new* 18-activity candidate based on the earlier versioned index5
repair, plus an independently scoped one-activity review input. No API calls.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from app_generator.runtime.v3_historical_role_rollforward import (
    stage_known_unrecoverable_section96,
)
from app_generator.runtime.v3_frozen_original_tail import plan_frozen_original_tail
from app_generator.validation.autonomous_completion import package_identity
from app_generator.validation.v3_locale_script_integrity import script_findings
from app_generator.validation.v3_versioned_text_repair import store_private_repair

_SECTION = "section-9-6"
_INDEX = 9
_ACTIVITY = "int-easy-line-of-action-motion"
_PARENT = "1620d15e1d645c81301997f0e42d0efbad0a7b2d123eb6b11cba9ec8c04b027f"
_OLD_SLICE = "afaad744cefb9a4e897cff02f94a45707c1d17a1609d811ae3def797d3a808b8"
_ROLE_SHAS = (
    "f532aa35c53a05c7eaa46e1d8e7314e7dd2e9f3bdbb7f2484c850331668287fe",
    "1b8b768f5545133fa7d5c8344b27032bcdeaab813b03770012845cd573cdb0b4",
)
_AGGREGATE_SHA = "257adb759f81f9a0cf5a7e367fd9da6611d5c6f9575d6b8574a1d0305977ee5a"
_BAD_ZH = "\u8d28\u7ebf"  # erroneous 'mass-line'
_GOOD_ZH = "\u8d28\u5fc3"  # correct 'center of mass'
_NEW_PROMPT = {
    "en": (
        "A rigid object is initially at rest and floating freely in a "
        "gravity-free environment, with no supporting surface or other "
        "external forces. A single constant horizontal force acts on it. "
        "Classify each force scenario by the motion it produces."
    ),
    "ms": (
        "Sebuah jasad tegar pada mulanya pegun dan terapung bebas dalam "
        "persekitaran tanpa graviti, tanpa permukaan sokongan atau daya "
        "luar yang lain. Satu daya mendatar malar bertindak padanya. "
        "Kelaskan setiap senario daya mengikut gerakan yang dihasilkannya."
    ),
    "zh": (
        "\u4e00\u4e2a\u521a\u4f53\u8d77\u521d\u9759\u6b62\uff0c"
        "\u5728\u65e0\u91cd\u529b\u73af\u5883\u4e2d\u81ea\u7531\u60ac\u6d6e\uff0c"
        "\u6ca1\u6709\u652f\u6491\u8868\u9762\u6216\u5176\u4ed6\u5916\u529b\u3002"
        "\u73b0\u5728\u53ea\u6709\u4e00\u4e2a\u6052\u5b9a\u7684\u6c34\u5e73\u5916\u529b"
        "\u4f5c\u7528\u5728\u5b83\u8eab\u4e0a\u3002"
        "\u6839\u636e\u4ea7\u751f\u7684\u8fd0\u52a8\u7c7b\u578b\uff0c"
        "\u5bf9\u5404\u79cd\u65bd\u529b\u60c5\u5f62\u8fdb\u884c\u5206\u7c7b\u3002"
    ),
}
_CHANGED = [
    "activities[9].prompt.en",
    "activities[9].prompt.ms",
    "activities[9].prompt.zh",
    "activities[9].answerLogic.zh",
    "activities[9].interaction.items[1].label.zh",
    "activities[9].interaction.items[2].label.zh",
]


def _correct_zh_terms(obj, *, path: str, edited: list[str]):
    if isinstance(obj, list):
        return [_correct_zh_terms(v, path=f"{path}[{i}]", edited=edited)
                for i, v in enumerate(obj)]
    if isinstance(obj, dict):
        output = {}
        for k, value in obj.items():
            key_path = f"{path}.{k}"
            if k == "zh" and isinstance(value, str) and _BAD_ZH in value:
                output[k] = value.replace(_BAD_ZH, _GOOD_ZH)
                edited.append(key_path)
            elif isinstance(value, (dict, list)):
                output[k] = _correct_zh_terms(
                    value, path=key_path, edited=edited)
            else:
                output[k] = value
        return output
    return obj


def stage_known_section96_scientific_failure(
    course: Path, repo: Path, private: Path, *,
    expected_role_shas: tuple[str, str] = _ROLE_SHAS,
    expected_aggregate_sha: str = _AGGREGATE_SHA,
) -> dict:
    """Revalidate actual FAIL and persist a different SHA-bound proposal only.

    Optional expected hashes support isolated synthetic fault-injection tests;
    production normal worker ALWAYS uses fixed genuine role fingerprints.
    """
    historical = stage_known_unrecoverable_section96(course, repo, private)
    if historical.get("status") != (
            "NEW_VERSIONED_SECTION96_REPAIR_STAGED_QA_NOT_AUTHORIZED"):
        return {"status":"NO_REGISTERED_SECTION96_SCIENCE_FAILURE_REMEDY"}
    parent_sha = historical["candidatePackageSha256"]
    original_path = course / _SECTION / "package.json"
    revised_path=(private / "historical-role-rollforward" / _SECTION /
                  parent_sha / "package.json")
    if (any(p.is_symlink() or not p.is_file()
            or p.stat().st_size>2_000_000
            for p in (original_path, revised_path))
            or not private.is_absolute()
            or private.resolve().is_relative_to(repo.resolve())):
        raise ValueError("V3_SCIENCE96_UNSAFE_SOURCE_OR_PRIVATE")
    original_raw=original_path.read_bytes()
    previous_raw=revised_path.read_bytes()
    old_sha, old_items=package_identity(original_raw)
    previous_sha, previous_items=package_identity(previous_raw)
    if (old_sha!=_PARENT or previous_sha!=parent_sha
            or len(old_items)!=18 or len(previous_items)!=18
            or old_items[_INDEX]["id"]!=_ACTIVITY
            or [i for i,(a,b) in enumerate(zip(old_items,previous_items))
                if a!=b] != [5]):
        raise ValueError("V3_SCIENCE96_PREVIOUS_VERSION_MISMATCH")
    tail=plan_frozen_original_tail(
        course,repo,private,section=_SECTION)
    failed_row=next((x for x in tail["rows"]
                     if x["index"]==_INDEX),None)
    if failed_row is None:
        raise ValueError("V3_SCIENCE96_MISSING_ORIGINAL_INDEX")
    if failed_row["state"] == "UNREVIEWED_ELIGIBLE":
        return {"status":"NO_REGISTERED_SECTION96_SCIENCE_FAILURE_REMEDY"}
    if (failed_row["state"]!="SUPPLEMENTAL_SCIENTIFIC_REPAIR_REQUIRED"
            or failed_row["slicePackageSha256"]!=_OLD_SLICE):
        raise ValueError("V3_SCIENCE96_UNTRUSTED_FAILED_REVIEW_STATE")
    if (not isinstance(expected_role_shas,tuple)
            or len(expected_role_shas)!=2
            or any(not isinstance(s,str) or len(s)!=64
                   or set(s)-set("0123456789abcdef")
                   for s in (*expected_role_shas,expected_aggregate_sha))):
        raise ValueError("V3_SCIENCE96_INVALID_ROLE_WITNESS")
    batch = private / ("v3-generated-"+_OLD_SLICE) / "batches"
    assessment=batch / ("v3-assessment-"+_OLD_SLICE+".json")
    paths=[batch / f"v3-review-{_OLD_SLICE[:12]}-000-{i}.json"
           for i in (0,1)]
    if (batch.is_symlink()
            or any(p.is_symlink() or not p.is_file()
                   or p.stat().st_size>8_000_000
                   for p in (*paths,assessment))):
        raise ValueError("V3_SCIENCE96_MISSING_IMMUTABLE_REVIEW")
    if sha256(assessment.read_bytes()).hexdigest()!=expected_aggregate_sha:
        raise ValueError("V3_SCIENCE96_ASSESSMENT_WITNESS_CHANGED")
    report=json.loads(assessment.read_text(encoding="utf8"))
    if (report.get("packageSha256")!=_OLD_SLICE
            or len(report.get("reviews",[]))!=1
            or report["reviews"][0].get("activityId")!=_ACTIVITY
            or report["reviews"][0].get("status")!="AI_REPAIR_REQUIRED"):
        raise ValueError("V3_SCIENCE96_FAILED_AGGREGATE_NOT_VERIFIED")
    for i,(file,expected) in enumerate(zip(paths,expected_role_shas)):
        raw=file.read_bytes()
        if sha256(raw).hexdigest()!=expected:
            raise ValueError("V3_SCIENCE96_ROLE_WITNESS_CHANGED")
        role=json.loads(raw.decode("utf8"))
        if (role.get("roleIndex")!=i
                or role.get("providerId")!="gemini_api"
                or role.get("packageSha256")!=_OLD_SLICE
                or role.get("activityId")!=_ACTIVITY
                or role.get("state")!="COMPLETE"
                or role.get("decision",{}).get("dimensions",{}).get(
                    "physicsAnswer")!="FAIL"
                or role.get("decision",{}).get("dimensions",{}).get(
                    "trilingualMeaning")!="FAIL"
                or not isinstance(role.get("responseSha256"),str)
                or len(role["responseSha256"])!=64):
            raise ValueError("V3_SCIENCE96_BAD_SCIENTIFIC_WITNESS")
    candidate=json.loads(previous_raw.decode("utf8"))
    task=candidate["activities"][_INDEX]
    original_prompt=old_items[_INDEX]["prompt"]
    if task["prompt"]!=original_prompt or not (
            "frictionless horizontal floor" in original_prompt["en"]
            and "lantai mendatar tanpa geseran" in original_prompt["ms"]
            and "\u65e0\u6469\u64e6\u7684\u6c34\u5e73\u5730\u9762"
                in original_prompt["zh"]):
        raise ValueError("V3_SCIENCE96_UNEXPECTED_REAL_FLOOR_SCENARIO")
    for locale,new_text in _NEW_PROMPT.items():
        task["prompt"][locale]=new_text
    affected=[]
    task=_correct_zh_terms(task,path=f"activities[{_INDEX}]",
                           edited=affected)
    candidate["activities"][_INDEX]=task
    changed=sorted([f"activities[{_INDEX}].prompt.{l}"
                    for l in _NEW_PROMPT] + affected)
    if (changed != sorted(_CHANGED)
            or _BAD_ZH in json.dumps(task,ensure_ascii=False)
            or task["interaction"]["placements"] !=
                old_items[_INDEX]["interaction"]["placements"]
            or script_findings(candidate)):
        raise ValueError("V3_SCIENCE96_REPAIR_UNEXPECTED_SCOPE_OR_SCRIPT")
    content=(json.dumps(candidate,ensure_ascii=False,indent=2)+"\n").encode("utf8")
    new_sha,activities=package_identity(content)
    if (new_sha in {_PARENT,parent_sha}
            or len(activities)!=18
            or [a["id"] for a in activities]!=[a["id"] for a in old_items]
            or [i for i,(a,b) in enumerate(zip(old_items,activities))
                if a!=b]!=[5,_INDEX]
            or [i for i,(a,b) in enumerate(zip(previous_items,activities))
                if a!=b]!=[_INDEX]):
        raise ValueError("V3_SCIENCE96_CANDIDATE_CHANGED_TOO_MUCH")
    receipt={
        "contract":"BOSLA_V3_SCIENTIFIC_FAILURE_ROLLFORWARD_V1",
        "originalPackageSha256":_PARENT,
        "parentPackageSha256":parent_sha,
        "candidatePackageSha256":new_sha,
        "failedOriginalReviewSliceSha256":_OLD_SLICE,
        "failedReviewAggregateSha256":expected_aggregate_sha,
        "failedReviewerRoleSha256s":list(expected_role_shas),
        "activityIndex":_INDEX,"activityId":_ACTIVITY,
        "changedFieldPaths":changed,
        "physicsCorrection":"NO_CONTACT_FORCE_IN_FREE_FLOATING_BODY",
        "translationCorrection":"CHINESE_CENTER_OF_MASS_TERM",
        "status":"PENDING_FRESH_AUTHORIZED_TWO_GEMINI_REVIEW",
        "oldReviewerVerdictsModified":False,
        "newModelConsensusPassClaimed":False,
        "publicationAuthorized":False,
        "versionedScopeAdmitted":False,
    }
    folder=store_private_repair(
        private/"scientific-failure-rollforward"/_SECTION,
        content,receipt)
    review_package={
        "schema":"BOSLA_V3_FAILED_ORIGINAL_NEW_VERSION_SINGLE_ACTIVITY_QA_V1",
        "originalPackageSha256":_PARENT,
        "parentPackageSha256":new_sha,
        "sourceSection":_SECTION,
        "sourceActivityIndex":_INDEX,
        "failedOriginalReviewSliceSha256":_OLD_SLICE,
        "activities":[activities[_INDEX]],
    }
    review_raw=(json.dumps(review_package,ensure_ascii=False,
                           sort_keys=True,indent=2)+"\n").encode("utf8")
    review_sha,one=package_identity(review_raw)
    if len(one)!=1 or one[0]!=activities[_INDEX] or review_sha==_OLD_SLICE:
        raise ValueError("V3_SCIENCE96_NEW_REVIEW_NOT_INDEPENDENT")
    review_receipt={
        "contract":"BOSLA_V3_SCIENCE_FAILURE_NEW_REVIEW_INPUT_V1",
        "parentPackageSha256":new_sha,
        "candidatePackageSha256":review_sha,
        "failedOriginalReviewSliceSha256":_OLD_SLICE,
        "status":"PENDING_SEPARATE_PAID_AUTHORIZATION",
        "newModelConsensusPassClaimed":False,
        "publicationAuthorized":False,
    }
    review_folder=store_private_repair(
        private/"scientific-failure-review-inputs"/_SECTION,
        review_raw,review_receipt)
    if ((folder/"package.json").read_bytes()!=content or
            (review_folder/"package.json").read_bytes()!=review_raw or
            (course/_SECTION/"package.json").read_bytes()!=original_raw):
        raise ValueError("V3_SCIENCE96_REPAIRED_CONTENT_CHANGED")
    return {
        "status":"NEW_SECTION96_SCIENCE_REPAIR_STAGED_REVIEW_NOT_AUTHORIZED",
        "originalPackageSha256":_PARENT,
        "previousRevisedPackageSha256":parent_sha,
        "candidatePackageSha256":new_sha,
        "isolatedReviewInputSha256":review_sha,
        "oldScientificFailurePreserved":True,
        "oldProviderUncertaintyPreserved":True,
        "paidGeminiCalls":0,
        "newModelConsensusPassClaimed":False,
        "versionedScopeAdmitted":False,
        "publicationAuthorized":False,
    }

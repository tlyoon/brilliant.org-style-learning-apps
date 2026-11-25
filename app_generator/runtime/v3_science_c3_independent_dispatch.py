"""BSA241 V17: actual frozen C3 + scientific proof-gap dispatch after signed V16.

No PDFs opened, no provider calls, no third frozen campaign, no release. All
source-bearing generated packages stay in private Yoga6 memory/loopback.
"""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_public_nonmerging_draft_pr import (
    _preflight as _v13_preflight,
)
from app_generator.runtime.v3_public_pr_security_accessibility import (
    _V16, _STATUS as _V16_STATUS,
)
from app_generator.runtime.v3_public_pr_accessibility_tree import (
    audit_real_chrome_accessibility_tree,
)
from app_generator.validation.heldout_generalization_gate import evaluate_campaign
from app_generator.validation.academic_coverage_gate import (
    audit_academic_coverage, _canonical_activity_sha,
)
from app_generator.validation.academic_qa import REQUIRED

_V17="V17_SOURCE_BOUND_SCIENCE_C3_EVIDENCE_DISPATCH.json"
_STATUS="V17_REAL_SCIENCE_C3_GAP_AUDITS_EXECUTED_NO_RELEASE"
_TASKS=("FROZEN_C3_REAL_METADATA_AND_CHROME",
        "C3_TWO_REAL_DRAFTS_ACADEMIC_PROOF_GAP_INVENTORY")


def _read(base:Path,filename:str)->dict:
    p=base/filename
    if p.is_symlink() or not p.is_file() or p.stat().st_size>2000000:
        raise ValueError("V17_FROZEN_C3_EVIDENCE_NOT_SAFE")
    return json.loads(p.read_text(encoding="utf8"))


def _original_c3(base:Path)->tuple[dict,dict]:
    manifest=_read(base,"C3_round2_manifest_20261104.json")
    results=_read(base,"C3_round2_continuation_technical_results_20261104.json")
    evaluation=_read(base,"C3_round2_continuation_generalization_evaluation_20261104.json")
    computed=evaluate_campaign(manifest,results)
    if computed!=evaluation:
        raise ValueError("V17_ORIGINAL_FROZEN_C3_EVALUATION_DRIFT")
    if (computed.get("technicalResult")!="FAILED_LIMITED_CAMPAIGN" or
        computed.get("draftsReportedComplete")!=0 or
        computed.get("stopAfterThisRoundIfFailed") is not True or
        computed.get("publicationAuthorized") is not False):
        raise ValueError("V17_FROZEN_C3_UNEXPECTED_APPROVAL")
    return computed,results


def _frozen_packages(base:Path,results:dict)->list[tuple[str,bytes,str,str]]:
    roster={item["caseId"]:item for item in results["cases"]}
    out=[]
    for n,case in ((1,"round2-mechanics-circular"),
                   (2,"round2-electromagnetism-coulomb")):
        source=(base/f"C3_round2_worktree_92_{n}_20261104"/"content"/
                "chapter-92"/f"section-92-{n}"/"package.json")
        old=_read(base,f"C3_round2_continuation_92_{n}_finished_20261104.json")
        if (source.is_symlink() or not source.is_file() or
                source.stat().st_size>2000000):
            raise ValueError("V17_FROZEN_C3_DRAFT_UNAVAILABLE")
        raw=source.read_bytes()
        h=sha256(raw).hexdigest()
        entry=roster.get(case)
        if (entry is None or old.get("installedPackageSha256")!=h or
            old.get("installedPackageExists") is not True or
            entry.get("packageSha256")!=h):
            raise ValueError("V17_FROZEN_C3_REAL_DRAFT_SOURCE_MISMATCH")
        data=json.loads(raw)
        acts=data.get("activities") if isinstance(data,dict) else None
        if (not isinstance(acts,list) or len(acts)!=18 or
                len({v.get("id") for v in acts if isinstance(v,dict)})!=18):
            raise ValueError("V17_FROZEN_C3_DRAFT_NOT_18_UNIQUE_ACTIVITIES")
        out.append((case,raw,h,entry["sourceSha256"]))
    return out


def _task_c3(base:Path,repo:Path)->dict:
    previous,results=_original_c3(base)
    old=_frozen_packages(base,results)
    from scripts.check_course_preview_browser import stage_site
    with TemporaryDirectory(prefix="bosla-v17-readonly-c3-") as folder:
        site=Path(folder)
        stage_site(site)
        for n,(_,raw,_,_) in enumerate(old,start=1):
            (site/"content"/"chapter-9"/f"section-9-{n}"/"package.json").write_bytes(raw)
        pages=tuple(("app/index.html",
                     f"../content/chapter-9/section-9-{n}/package.json")
                    for n in (1,2))
        chrome=audit_real_chrome_accessibility_tree(site,pages)
    if (chrome["localeAccessibilityTreeChecks"]!=6 or
        chrome["unnamedControls"]!=0 or
        chrome["minimumNamedControls"]<2):
        raise ValueError("V17_REAL_ARCHIVED_C3_CHROME_NOT_VERIFIED")
    return {
        "taskStatus":"FROZEN_C3_FAILURE_PRESERVED_NEW_DRAFT_BROWSER_QA_VERIFIED",
        "historicalC3TechnicalResult":"FAILED_LIMITED_CAMPAIGN",
        "originalCampaignDraftsFiveStageComplete":previous["draftsReportedComplete"],
        "originalCampaignTechnicalAcceptance":False,
        "sourceBoundFrozenDraftSha256s":[value[2] for value in old],
        "realFrozenDraftActivityCount":36,
        "independentPosthocChromeLocaleChecks":chrome["localeAccessibilityTreeChecks"],
        "independentPosthocMinimumNamedControls":chrome["minimumNamedControls"],
        "oldCampaignReopened":False,
        "newPdfReads":0,"newPaidCalls":0,
        "publicationAuthorized":False,
    }


def _task_academic(base:Path,repo:Path)->dict:
    _,results=_original_c3(base)
    packages=_frozen_packages(base,results)
    rows=[]
    for case,raw,h,source_sha in packages:
        pkg=json.loads(raw)
        activities=pkg["activities"]
        matrix={
            "packageSha256":h,"sourceSha256":source_sha,
            "activityCount":len(activities),"publicationAuthorized":False,
            "academicQA":"REVIEW_REQUIRED",
            "counts":{"PASS":0,"FAIL":0,"REVIEW_REQUIRED":len(activities)},
            "activities":[{
                "activityId":act["id"],
                "activitySha256":_canonical_activity_sha(act),
                "sourceLocationVerified":False,
                "gates":{gate:"REVIEW_REQUIRED" for gate in REQUIRED},
                "academicQA":"REVIEW_REQUIRED",
                "publicationAuthorized":False,
            } for act in activities],
        }
        report=audit_academic_coverage(
            package_bytes=raw,matrix=matrix,source_sha256=source_sha)
        if (report.get("academicQA")!="REVIEW_REQUIRED" or
            report.get("formalAcademicPassCount")!=0 or
            any(count!=18 for count in report["perGateOutstanding"].values())):
            raise ValueError("V17_ORIGINAL_C3_ACADEMIC_FALSE_ADMISSION")
        rows.append({"caseId":case,"packageSha256":h,
                     "unverifiedProofs":report["perGateOutstanding"]})
    return {
        "taskStatus":"36_GENUINE_C3_DRAFT_ACTIVITIES_180_INDEPENDENT_PROOFS_MISSING",
        "originalC3AcademicAcceptance":False,
        "originalDraftActivityCount":36,
        "unverifiedGateInstances":sum(sum(x["unverifiedProofs"].values()) for x in rows),
        "sourceBoundProofGaps":rows,
        "frozenOriginalC3":"FAILED_LIMITED_CAMPAIGN",
        "modelCalls":0,"sourcePdfRead":False,
        "publicationAuthorized":False,
    }


_TASK_HANDLERS={
    "FROZEN_C3_REAL_METADATA_AND_CHROME":_task_c3,
    "C3_TWO_REAL_DRAFTS_ACADEMIC_PROOF_GAP_INVENTORY":_task_academic,
}
assert tuple(_TASK_HANDLERS)==_TASKS


def check_signed_v16(v16:dict,ready:dict)->None:
    if (not isinstance(v16,dict) or v16.get("status")!=_V16_STATUS or
        v16.get("gitHead")!=ready.get("gitHead") or
        v16.get("integritySha256")!=_hash({
            k:v for k,v in v16.items() if k!="integritySha256"}) or
        v16.get("publicPrDraft") is not True or
        v16.get("publicationAuthorized") is not False or
        v16.get("publicMergeExecuted") is not False or
        v16.get("publicDeployExecuted") is not False):
        raise ValueError("V17_GENUINE_SIGNED_V16_REQUIRED")
    ax=v16.get("technicalEvidence",{}).get("realChromeAccessibilityTree",{})
    if (ax.get("pagesAudited")!=3 or
        ax.get("localeAccessibilityTreeChecks")!=9 or
        ax.get("unnamedControls")!=0 or
        ax.get("documentLanguageMatches")!=9 or
        ax.get("minimumNamedControls",0)<2):
        raise ValueError("V17_GENUINE_V16_CHROME_AX_GATE_REQUIRED")


def run_post_v16_science_c3(
    repo:Path,private:Path,ready:dict,v9:dict,v11:dict,v12:dict,
    v16_result:dict,
)->dict:
    folder,_,_,_,_=_v13_preflight(repo,private,ready,v9,v11,v12)
    v16=_trusted_json(folder/_V16)
    if v16!=v16_result:
        raise ValueError("V17_V16_RESULT_SOURCE_MISMATCH")
    check_signed_v16(v16,ready)
    identity={
        "gitHead":ready["gitHead"],
        "proposalSha256":ready["proposalSha256"],
        "sourceV16ReceiptSha256":v16["integritySha256"],
    }
    results=[]
    base=repo.parent
    for task in _TASKS:
        fn=_TASK_HANDLERS[task]
        _v6_checkpoint(folder/f"V17_TASK_{task}_PRE_CALL.json",{
            **identity,"taskId":task,
            "state":"PRE_CALL_SOURCE_FREE_READONLY_DISPATCH",
            "modelCallsAllowed":False,"pdfReadsAllowed":False,
            "publicationAuthorized":False,
        })
        try:
            info=fn(base,repo)
            detail={
                **identity,"taskId":task,"state":"READONLY_REAL_TASK_EXECUTED",
                "handler":fn.__name__,"result":info,
                "publicationAuthorized":False,
            }
        except Exception as exc:
            detail={
                **identity,"taskId":task,"state":"READONLY_TASK_QUARANTINED",
                "errorClass":type(exc).__name__,
                "handler":fn.__name__,"publicationAuthorized":False,
            }
        results.append(_v6_checkpoint(folder/f"V17_TASK_{task}_RESULT.json",detail))
    quarantined=[x["taskId"] for x in results
                 if x["state"]!="READONLY_REAL_TASK_EXECUTED"]
    payload={
        **identity,
        "contract":"BOSLA_V17_SOURCE_BOUND_INDEPENDENT_C3_AND_SCIENCE_GAP_DISPATCH",
        "status":(_STATUS if not quarantined else
                  "V17_SCIENCE_C3_READONLY_TASKS_QUARANTINED_NO_RELEASE"),
        "taskDispatchActuallyExecuted":True,
        "taskDispatchOrder":list(_TASKS),
        "taskResults":[{
            "taskId":x["taskId"],"state":x["state"],
            "integritySha256":x["integritySha256"],
        } for x in results],
        "quarantinedTaskIds":quarantined,
        "historicalC3":"FAILED_LIMITED_CAMPAIGN",
        "frozenOriginalCampaignReopened":False,
        "historicalAmbiguousGeminiRequestsReplayed":False,
        "independentScientificAcceptanceComplete":False,
        "academicAcceptanceGranted":False,
        "publicationAuthorized":False,
        "publicMergeExecuted":False,
        "publicDeployExecuted":False,
        "newPaidModelCalls":0,
        "newOriginalPdfReads":0,
        "schedulerReinstalled":False,
        "nextEligibleMilestone":"ONE_SELECTED_TEXTBOOK_PER_TOPIC_SOURCE_BOUND_SCIENTIFIC_PROOFS_NO_THREE_PDF_REQUIREMENT",
    }
    return _v6_checkpoint(folder/_V17,payload)

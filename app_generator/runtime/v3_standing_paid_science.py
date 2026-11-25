"""BSA217: standing owner Gemini consent, finite per-invocation source-bound QA.

No lifetime permission exhaustion for genuinely NEW BOSLA source identities.
A run has at most 4 activities/8 independent roles/900 s. The old original
Section9.1 index0 uncertainty and ALL earlier paid charters are immutable.
"""
from __future__ import annotations

import json
from hashlib import sha256
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Callable

from app_generator.runtime.v3_frozen_original_tail import _slice, _safe_evidence, _bytes
from app_generator.runtime.v3_section96_authorized_revised_qa import (
    verified_new_provider_capability,
    read_prior_two_role_science,
    unsent_revised_input,
    verify_persisted_two_role_science,
)
from app_generator.validation.autonomous_completion import assessment_progress,package_identity
from app_generator.validation.v3_course_readiness import course_readiness
from app_generator.validation.v3_locale_script_integrity import script_findings

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"docs"/"v3_standing_paid_gemini_authorization_20261119.json"
CONTRACT_ID="BOSLA_V3_STANDING_PAID_GEMINI_OWNER_CONSENT_20261119"
CURRENT_SECTION="section-9-1"
EXPECTED_CONTRACT={
    "schemaVersion":1,
    "contractId":CONTRACT_ID,
    "authorizedBy":"OWNER_EXPLICIT_CHAT_DIRECTIVE_2026-11-19_ALWAYS_ALLOW_PAID_GEMINI",
    "authorizedHost":"Yoga 6",
    "provider":"gemini_api",
    "standingConsent":True,
    "noNewPerCampaignOwnerConsentRequired":True,
    "allowNecessaryPaidGeminiApiCalls":True,
    "allowGeneratedLearningTextTransfer":True,
    "scope":"BOSLA_CODE_DEVELOPMENT_SCIENTIFIC_REVIEW_AND_CONTENT_REPAIR",
    "maxNewActivitiesPerInvocation":4,
    "maxIndependentReviewerCallsPerActivity":2,
    "maxPaidGeminiCallsPerInvocation":8,
    "maxElapsedSecondsPerInvocation":900,
    "minimumSecondsBetweenProviderCalls":0,
    "noLifetimeCallQuota":True,
    "noSchedulerOrBackgroundInfiniteLoop":True,
    "perInvocationStopAtBudget":True,
    "requireExactCurrentSourceProvenance":True,
    "requireImmutablePreCallRoleClaim":True,
    "neverReplaySubmittedOrAmbiguousRoles":True,
    "scientificFailMustNotAutoPass":True,
    "retainHistoricalEvidenceImmutable":True,
    "noSourcePDFUpload":True,
    "allowBatchJobs":False,
    "noAutomaticPublication":True,
    "noAutomaticMerge":True,
    "releaseRequiresSeparateEligibility":True,
    "historicalChartersRemainFrozen":True,
    "appliesToNewSourceIdentitiesOnly":True,
}


def authorize_standing(*, execute:bool,transfer:bool, activities:int=4,
                       seconds:int=900,contract:Path=CONTRACT)->dict:
    if execute is not True or transfer is not True:
        raise ValueError("V3_STANDING_EXECUTE_AND_TRANSFER_REQUIRED")
    if (type(activities) is not int or not 1<=activities<=4
            or type(seconds) is not int or not 30<=seconds<=900):
        raise ValueError("V3_STANDING_INVOCATION_BUDGET_EXCEEDED")
    if contract.is_symlink() or not contract.is_file() or contract.stat().st_size>10000:
        raise ValueError("V3_STANDING_CONTRACT_MISSING_OR_LINKED")
    try:
        data=json.loads(contract.read_text(encoding="utf8"))
    except (OSError,ValueError,UnicodeError):
        raise ValueError("V3_STANDING_CONTRACT_INVALID") from None
    if data != EXPECTED_CONTRACT:
        raise ValueError("V3_STANDING_CONTRACT_SCOPE_TAMPERED")
    return {"contractId":CONTRACT_ID,"standingConsent":True,
            "maxPaidGeminiCalls":2*activities,"maxSeconds":seconds,
            "publicationAuthorized":False,"versionedScopeAdmitted":False}


def section91_evidence(course:Path,repo:Path,private:Path)->dict:
    """Read-only: original idx0 uncertain and frozen original never reset."""
    if (not private.is_absolute() or private.is_symlink()
            or private.resolve().is_relative_to(repo.resolve())):
        raise ValueError("V3_STANDING_UNSAFE_PRIVATE_ROOT")
    progress=course_readiness(course,repo,private_root=private)
    row=next((r for r in progress["sectionProgress"]
              if r["section"]==CURRENT_SECTION),None)
    file=course/CURRENT_SECTION/"package.json"
    if file.is_symlink() or not file.is_file():
        raise ValueError("V3_STANDING_FROZEN_SOURCE_MISSING")
    raw=file.read_bytes()
    parent,items=package_identity(raw)
    if (not isinstance(row,dict) or progress["scopeSource"]!="FROZEN_CANDIDATE_MANIFEST"
            or progress["sectionsTotal"]!=6 or progress["publicationAuthorized"] is not False
            or row["packageSha256"]!=parent or len(items)!=18
            or row["activitiesTotal"]!=18 or row["activitiesAssessedRows"]!=1
            or row["modelConsensusPassActivities"]!=0
            or row["modelUncertainActivities"]!=1
            or row["modelRepairRequiredActivities"]!=0
            or row["unreconciledRoleClaims"]!=0):
        raise ValueError("V3_STANDING_SECTION91_ORIGINAL_EVIDENCE_CHANGED")
    original=private/("v3-generated-"+parent)/"batches"/("v3-assessment-"+parent+".json")
    if original.is_symlink() or not original.is_file() or original.stat().st_size>8000000:
        raise ValueError("V3_STANDING_FROZEN_ASSESSMENT_MISSING")
    record=json.loads(original.read_text(encoding="utf8"))
    assessed=assessment_progress(raw,record)
    if (len(record.get("reviews",[]))!=1
            or record["reviews"][0].get("status")!="AI_UNCERTAIN"
            or assessed.get("activitiesAssessed")!=1
            or assessed.get("modelUncertainActivities")!=1):
        raise ValueError("V3_STANDING_OLD_UNCERTAIN_REVIEW_CHANGED")
    _,old_sha,_=_slice(parent,CURRENT_SECTION,0,items[0])
    if _safe_evidence(private,parent,0,old_sha)=="UNREVIEWED_ELIGIBLE":
        raise ValueError("V3_STANDING_OLD_UNKNOWN_ROLE_ABSENT")
    rows=[]
    for index in range(1,len(items)):
        item=items[index]
        if script_findings({"activities":[item]}):
            raise ValueError("V3_STANDING_LOCALE_DEFECT_REQUIRES_NEW_VERSION")
        raw_slice,sha,receipt=_slice(parent,CURRENT_SECTION,index,item)
        state=_safe_evidence(private,parent,index,sha)
        rows.append({"index":index,"activityId":item["id"],"sha":sha,
                     "raw":raw_slice,"manifest":receipt,
                     "originalReviewState":state})
    if file.read_bytes()!=raw:
        raise ValueError("V3_STANDING_SOURCE_CHANGED_DURING_READ")
    return {"parentSha256":parent,"originalAssessedUnchanged":1,
            "oldUncertainIndex":0,"items":rows}


def stage_standing_one(private:Path,entry:dict)->None:
    parent=private/"standing-new-source-review-slices"
    target=parent/entry["sha"]
    body=entry["raw"]
    receipt=_bytes(entry["manifest"])
    if parent.is_symlink() or target.is_symlink():
        raise ValueError("V3_STANDING_UNSAFE_STAGE")
    if target.exists():
        if (not target.is_dir() or any(x.is_symlink()
                for x in (target/"package.json",target/"review-slice.json"))
                or (target/"package.json").read_bytes()!=body
                or (target/"review-slice.json").read_bytes()!=receipt):
            raise ValueError("V3_STANDING_SAVED_SLICE_CHANGED")
        return
    parent.mkdir(parents=True,exist_ok=True)
    tmp=Path(tempfile.mkdtemp(prefix=".stand-",dir=parent))
    try:
        for name,payload in (("package.json",body),("review-slice.json",receipt)):
            with (tmp/name).open("xb") as f:
                f.write(payload);f.flush();os.fsync(f.fileno())
        tmp.rename(target)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)


def verified_section91_standing_passes(course:Path,repo:Path,private:Path)->list[dict]:
    """Reuse genuine source-bound role pairs, not fake or partial callbacks."""
    staging=private/"standing-new-source-review-slices"
    if not staging.exists():
        return []
    if staging.is_symlink() or not staging.is_dir():
        raise ValueError("V3_STANDING_UNSAFE_STAGED_ROOT")
    checked=section91_evidence(course,repo,private)
    from app_generator.validation.autonomous_ai_review import canonical_digest
    items=package_identity((course/CURRENT_SECTION/"package.json").read_bytes())[1]
    passed=[]
    for entry in checked["items"]:
        state=entry["originalReviewState"]
        if state=="UNREVIEWED_ELIGIBLE":
            continue
        if state in ("ROLE_CLAIM_PRESENT_DO_NOT_REPLAY",
                     "ATTEMPT_RESERVED_DO_NOT_REPLAY",
                     "ORIGINAL_ROLE_CLAIM_PRESENT_DO_NOT_REPLAY"):
            # A previously submitted incomplete role is quarantined, not
            # replayed and not allowed to mask independent sibling PASSes.
            continue
        if state!="AGGREGATE_EXISTS":
            raise ValueError("V3_STANDING_UNKNOWN_ROLE_STATE")
        outcome=read_prior_two_role_science(private,entry)
        if outcome["uncertain"] or outcome["repair"]:
            continue
        if outcome["pass"] is not True:
            raise ValueError("V3_STANDING_GENUINE_PASS_NOT_VERIFIED")
        target=private/"standing-new-source-review-slices"/entry["sha"]
        if (target.is_symlink() or (target/"package.json").is_symlink()
                or (target/"review-slice.json").is_symlink()
                or (target/"package.json").read_bytes()!=entry["raw"]
                or (target/"review-slice.json").read_bytes()!=_bytes(entry["manifest"])):
            raise ValueError("V3_STANDING_STAGED_GENUINE_SOURCE_CHANGED")
        record=(private/("v3-generated-"+entry["sha"])/"batches"/
                ("v3-assessment-"+entry["sha"]+".json"))
        if record.is_symlink() or not record.is_file() or record.stat().st_size>8_000_000:
            raise ValueError("V3_STANDING_SAVED_ASSESSMENT_MISSING")
        saved=json.loads(record.read_text(encoding="utf8"))
        progress=assessment_progress(entry["raw"],saved)
        if (progress.get("activitiesAssessed")!=1
                or progress.get("modelConsensusPassActivities")!=1
                or len(saved.get("reviews",[]))!=1
                or saved["reviews"][0].get("activityId")!=entry["activityId"]):
            raise ValueError("V3_STANDING_REPORT_NOT_EXACT_PASS")
        review_sha=sha256(_bytes(saved["reviews"][0])).hexdigest()
        item=items[entry["index"]]
        passed.append({"section":CURRENT_SECTION,"originalActivityIndex":entry["index"],
                       "activityId":entry["activityId"],
                       "activitySha256":canonical_digest(item),
                       "sourcePackageSha256":checked["parentSha256"],
                       "supplementalReviewSliceSha256":entry["sha"],
                       "sourceReviewSha256":review_sha,
                       "status":"POTENTIALLY_REUSABLE_NOT_RELEASE_ACCEPTED"})
    return passed


def advance_standing_science(course:Path,repo:Path,private:Path,*,
                             execute:bool,transfer:bool,max_activities:int=4,
                             max_seconds:int=900,capability:dict|None=None,
                             review_one:Callable|None=None)->dict:
    """At most one NEW pair per SHA, never retry any previous provider I/O."""
    authorization=authorize_standing(
        execute=execute,transfer=transfer,activities=max_activities,seconds=max_seconds)
    if not verified_new_provider_capability(private,capability):
        raise ValueError("V3_STANDING_PROVIDER_NOT_VERIFIED")
    if not callable(review_one):
        raise ValueError("V3_STANDING_MISSING_GENUINE_REVIEWER")
    from app_generator.runtime.v3_yoga6_recovery import coordinator_lock
    started=time.monotonic()
    outcomes=[]
    quarantined=[]
    with coordinator_lock(private):
        checked=section91_evidence(course,repo,private)
        for entry in checked["items"]:
            if len(outcomes)>=max_activities or time.monotonic()-started>=max_seconds:
                break
            state=entry["originalReviewState"]
            if state=="AGGREGATE_EXISTS":
                prior=read_prior_two_role_science(private,entry)
                # Skip already scientifically resolved sources without a paid replay.
                if prior["uncertain"]:
                    quarantined.append(entry["index"])
                continue
            if state in ("ROLE_CLAIM_PRESENT_DO_NOT_REPLAY",
                         "ATTEMPT_RESERVED_DO_NOT_REPLAY",
                         "ORIGINAL_ROLE_CLAIM_PRESENT_DO_NOT_REPLAY"):
                quarantined.append(entry["index"])
                continue
            if state!="UNREVIEWED_ELIGIBLE":
                raise ValueError("V3_STANDING_UNKNOWN_ORIGINAL_ROLE_STATE")
            stage_standing_one(private,entry)
            if not unsent_revised_input(private,entry["sha"]):
                raise ValueError("V3_STANDING_ROLE_CREATED_DURING_PREFLIGHT")
            report=review_one(entry["raw"],entry["activityId"],private)
            if not isinstance(report,dict) or report.get("activitiesAssessed")!=1:
                raise ValueError("V3_STANDING_NON_GENUINE_REVIEW_CALLBACK")
            saved=verify_persisted_two_role_science(
                private,entry["raw"],entry["activityId"],entry["sha"],report)
            outcome={"index":entry["index"],"activityId":entry["activityId"],
                     "reviewSliceSha256":entry["sha"],
                     "newConsensusPass":saved["pass"],
                     "newScientificRepairRequired":saved["repair"],
                     "newUncertain":saved["uncertain"]}
            outcomes.append(outcome)
            if saved["uncertain"]:
                break
    return {"status":("STANDING_BOUNDED_BATCH_COMPLETED"
                      if len(outcomes)==max_activities
                      and all(not x["newUncertain"] for x in outcomes)
                      else "STANDING_STOP_REVIEW_BOUNDARY"),
            "outcomes":outcomes,
            "allNewScientificPass":(len(outcomes)==max_activities and
                                   all(x["newConsensusPass"] for x in outcomes)),
            "maximumGeminiCalls":authorization["maxPaidGeminiCalls"],
            "standingConsent":True,"oldUncertainRoleReplayed":False,
            "quarantinedUncertainOrIncompleteIndices":quarantined,
            "originalFrozenReviewsModified":False,
            "publicationAuthorized":False,"versionedScopeAdmitted":False}

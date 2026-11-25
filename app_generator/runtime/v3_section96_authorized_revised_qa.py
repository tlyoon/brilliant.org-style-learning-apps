"""BSA-206: narrow OWNER-authorized Gemini QA for two NEW Section9.6 versions.

Original frozen content and historical review claims stay immutable. Never
replay a submitted request, infer a physics PASS, publish, or use a scheduler.
The independent two-Gemini checkpoint engine owns all PRE_CALL records.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import time
from typing import Callable

from app_generator.runtime.v3_paid_review_authorization import load_paid_review_contract
from app_generator.runtime.v3_historical_role_rollforward import stage_known_unrecoverable_section96
from app_generator.runtime.v3_section96_scientific_failure_repair import stage_known_section96_scientific_failure
from app_generator.runtime.v3_frozen_original_tail import plan_frozen_original_tail
from app_generator.runtime.v3_provider_restoration import (
    known_bsa196_source_claims_present,
    _verified_migrated_auth_keys,
    _OLD_CLIENTERROR_ROLES,
)
from app_generator.validation.autonomous_completion import (
    assessment_progress, package_identity,
)

ROOT=Path(__file__).resolve().parents[2]
AUTHORITY=ROOT/"docs"/"v3_authorized_revised_section96_scientific_qa_20261118.json"
_OLD="1620d15e1d645c81301997f0e42d0efbad0a7b2d123eb6b11cba9ec8c04b027f"
_EXPECTED_SLICES=(
    (5,"mcq-mod-bat-cut-mass-comparison",
     "bf9c5553f435b53a8822e1a907811d61d0fcc286d22e85e3473ce38d59ffb49d",
     "738292dc2b94d011cb3c2d2da811f837d3326d9e30dc8d991977314d829014b7",
     "historical-role-review-inputs"),
    (9,"int-easy-line-of-action-motion",
     "65e35a3727090119031411422a2728e1fefb2cb0c0ae71dd3307937eec2871dd",
     "45d6ba0cf52b952bbc9267bb94893d3642aa2b1fa3322fd49a0e4b4dd9b169d6",
     "scientific-failure-review-inputs"),
)
_EXPECTED_CONTRACT={
    "schemaVersion":1,
    "contractId":"BOSLA_V3_OWNER_AUTHORIZED_REVISED_SECTION96_SCIENCE_20261118",
    "authorizedBy":"OWNER_EXPLICIT_CHAT_PROCEED_2026-11-18",
    "scope":"TWO_NEW_VERSIONED_SECTION96_ONE_ACTIVITY_GEMINI_SCIENCE_REVIEWS",
    "authorizedHost":"Yoga 6","provider":"gemini_api",
    "historicalCharter":"docs/acceptance_closure_chapter9.json",
    "historicalCharterRemainsFrozen":True,
    "previousPaidCharter":"docs/v3_paid_gemini_review_authorization_20261117.json",
    "previousPaidCharterRemainsFrozen":True,
    "reviewInputs":[
        {"index":i,"activityId":activity,"parentPackageSha256":parent,
         "reviewSliceSha256":digest}
        for i,activity,parent,digest,_ in _EXPECTED_SLICES
    ],
    "maxActivitiesPerInvocation":2,
    "maxIndependentGeminiCallsPerActivity":2,
    "maxTotalGeminiCalls":4,"maxElapsedSecondsPerInvocation":900,
    "paidGeminiApiGenerationAuthorized":True,
    "generatedLearningTextTransferAuthorized":True,
    "noReplayOfOriginalOrRevisedSubmittedRoles":True,
    "useImmutableRoleClaims":True,
    "allowSourcePDFUpload":False,"allowBatchJobCreation":False,
    "allowAutomatedScheduler":False,"allowUnboundedRecurrence":False,
    "versionedCourseAdmissionAuthorized":False,
    "publicationAuthorized":False,"releaseApprovalRequiredSeparately":True,
}


def authorize_revised96(*, execute: bool, transfer: bool,
                        activities: int, seconds: int,
                        file: Path=AUTHORITY) -> dict:
    """Independent exact owner consent; old paid charter remains unchanged."""
    if not execute or not transfer:
        raise ValueError("V3_REVISED96_PAID_AND_TEXT_TRANSFER_NOT_AUTHORIZED")
    if type(activities) is not int or not 1<=activities<=2 or (
        type(seconds) is not int or not 30<=seconds<=900):
        raise ValueError("V3_REVISED96_ACTIVITY_OR_TIME_BUDGET_EXCEEDED")
    if (file.is_symlink() or not file.is_file()
            or file.stat().st_size>8000):
        raise ValueError("V3_REVISED96_MISSING_OR_LINKED_OWNER_CHARTER")
    try:
        record=json.loads(file.read_text(encoding="utf8"))
    except (OSError,UnicodeError,ValueError):
        raise ValueError("V3_REVISED96_CORRUPT_OWNER_CHARTER") from None
    if record!=_EXPECTED_CONTRACT:
        raise ValueError("V3_REVISED96_OWNER_SCOPE_CHANGED")
    old=load_paid_review_contract()
    if (old["publicationAuthorized"] is not False
            or old["allowAutomatedScheduler"] is not False
            or old["allowedWorkflows"]!=[
              "FROZEN_ORIGINAL_ELIGIBLE_NEW_ACTIVITY",
              "ISOLATED_CORRECTED_SECTION_9_2_ACTIVITY"]):
        raise ValueError("V3_REVISED96_HISTORICAL_PAID_SCOPE_CHANGED")
    return {"contractId":record["contractId"],
            "activityLimit":activities,"callLimit":2*activities,
            "secondsLimit":seconds,"publicationAuthorized":False}


def stage_and_verify_two_new_inputs(course: Path, repo: Path,
                                    private: Path) -> list[dict]:
    """Always verify original FAILED/AMBIGUOUS witnesses before new content."""
    if (not private.is_absolute() or private.is_symlink()
            or private.resolve().is_relative_to(repo.resolve())):
        raise ValueError("V3_REVISED96_UNSAFE_PRIVATE")
    old=stage_known_unrecoverable_section96(course,repo,private)
    new=stage_known_section96_scientific_failure(course,repo,private)
    if (old.get("status")!="NEW_VERSIONED_SECTION96_REPAIR_STAGED_QA_NOT_AUTHORIZED"
            or old.get("parentPackageSha256")!=_OLD
            or old.get("oldAmbiguousProviderRolePreserved") is not True
            or new.get("status")!="NEW_SECTION96_SCIENCE_REPAIR_STAGED_REVIEW_NOT_AUTHORIZED"
            or new.get("oldScientificFailurePreserved") is not True
            or new.get("oldProviderUncertaintyPreserved") is not True
            or old.get("isolatedReviewInputSha256")!=_EXPECTED_SLICES[0][3]
            or new.get("isolatedReviewInputSha256")!=_EXPECTED_SLICES[1][3]):
        raise ValueError("V3_REVISED96_ORIGINAL_FAILURE_PROVENANCE_CHANGED")
    tail=plan_frozen_original_tail(course,repo,private)
    if (tail.get("sourcePackageSha256")!=_OLD
            or tail.get("originalAssessedUnchanged")!=6
            or tail.get("originalModelConsensusPassesUnchanged")!=5
            or tail.get("supplemental")!={
                "passed":10,"uncertain":1,"failed":1,"reserved":0,"eligible":0}
            or tail.get("next") is not None
            or [(x["index"],x["state"]) for x in tail["rows"]
                if x["index"] in (6,9)]!=[
                    (6,"SUPPLEMENTAL_UNCERTAIN_NO_REPLAY"),
                    (9,"SUPPLEMENTAL_SCIENTIFIC_REPAIR_REQUIRED")]):
        raise ValueError("V3_REVISED96_UNEXPECTED_HISTORICAL_REVIEW_INVENTORY")
    if not known_bsa196_source_claims_present(private):
        raise ValueError("V3_REVISED96_HISTORICAL_UNKNOWN_CLAIM_CHANGED")
    output=[]
    for index,activity,parent,source_sha,folder in _EXPECTED_SLICES:
        path=private/folder/"section-9-6"/source_sha/"package.json"
        if (path.is_symlink() or not path.is_file()
                or path.stat().st_size>2_000_000):
            raise ValueError("V3_REVISED96_SOURCE_OR_REVIEW_INPUT_MISSING")
        raw=path.read_bytes()
        current,items=package_identity(raw)
        package=json.loads(raw.decode("utf8"))
        if (current!=source_sha or len(items)!=1
                or items[0]["id"]!=activity
                or package.get("sourceSection")!="section-9-6"
                or package.get("sourceActivityIndex")!=index):
            raise ValueError("V3_REVISED96_SOURCE_IDENTITY_MISMATCH")
        # The old requested original source remains separately immutable.
        if package.get("parentPackageSha256")!=(
                parent if index==9 else _OLD):
            raise ValueError("V3_REVISED96_PARENT_IDENTITY_MISMATCH")
        if index==5 and package.get("candidatePackageSha256")!=parent:
            raise ValueError("V3_REVISED96_PARENT_CANDIDATE_MISMATCH")
        output.append({"index":index,"activityId":activity,"sha":source_sha,
                       "raw":raw})
    return output


def unsent_revised_input(private: Path, sha: str) -> bool:
    """No replay if ANY prior claim/pre-call/attempt directory exists."""
    run=private/("v3-generated-"+sha)
    if run.is_symlink() or (run.exists() and not run.is_dir()):
        raise ValueError("V3_REVISED96_UNSAFE_OLD_REQUEST_DIRECTORY")
    return not run.exists()


def verified_new_provider_capability(private: Path, capacity: dict) -> bool:
    """Exact restored Auth keys and known old unknowns, no paid probe."""
    if (not isinstance(capacity,dict)
            or capacity.get("status")!=
                "MODEL_GENERATION_ACTION_DECLARED_QUOTA_UNVERIFIED"
            or capacity.get("sourceFree") is not True
            or capacity.get("paidModelCalls")!=0):
        return False
    return _verified_migrated_auth_keys(private,capacity,17)==_OLD_CLIENTERROR_ROLES


def verify_persisted_two_role_science(
    private: Path, raw: bytes, activity_id: str, sha: str,
    callback_result: dict,
) -> dict:
    """Do not claim reviewer success from a callback without real V3 evidence."""
    run=private/("v3-generated-"+sha)
    batch=run/"batches"
    record_file=batch/("v3-assessment-"+sha+".json")
    role_files=[
        batch/f"v3-review-{sha[:12]}-000-{i}.json" for i in (0,1)]
    if (run.is_symlink() or batch.is_symlink()
            or record_file.is_symlink() or not record_file.is_file()
            or record_file.stat().st_size>8_000_000):
        raise ValueError("V3_REVISED96_MISSING_DURABLE_ASSESSMENT")
    saved=json.loads(record_file.read_text(encoding="utf8"))
    saved_progress=assessment_progress(raw,saved)
    count_fields=("activitiesAssessed","modelConsensusPassActivities",
                  "modelRepairRequiredActivities","modelUncertainActivities")
    if (any(saved_progress.get(field)!=callback_result.get(field)
            for field in count_fields)
            or saved_progress["activitiesAssessed"]!=1):
        raise ValueError("V3_REVISED96_CALLBACK_NOT_IMMUTABLE_REPORT")
    outcome={
        "pass":saved_progress["modelConsensusPassActivities"]==1,
        "repair":saved_progress["modelRepairRequiredActivities"]==1,
        "uncertain":saved_progress["modelUncertainActivities"]==1,
    }
    if sum(outcome.values())!=1:
        raise ValueError("V3_REVISED96_UNCLASSIFIED_SAVED_REPORT")
    # A genuine review PASS or scientific FAIL demands TWO independent
    # completed role claims, not a synthetic consensus from one role.
    if not outcome["uncertain"]:
        for i,file in enumerate(role_files):
            if (file.is_symlink() or not file.is_file()
                    or file.stat().st_size>100_000):
                raise ValueError("V3_REVISED96_INCOMPLETE_TWO_ROLE_EVIDENCE")
            role=json.loads(file.read_text(encoding="utf8"))
            if (role.get("state")!="COMPLETE"
                    or role.get("providerId")!="gemini_api"
                    or role.get("roleIndex")!=i
                    or role.get("packageSha256")!=sha
                    or role.get("activityId")!=activity_id
                    or not isinstance(role.get("responseSha256"),str)
                    or len(role["responseSha256"])!=64):
                raise ValueError("V3_REVISED96_TWO_ROLE_EVIDENCE_MISMATCH")
    return outcome


def read_prior_two_role_science(private: Path, entry: dict) -> dict:
    """Reconcile a completed NEW request after process loss; never resubmit."""
    sha=entry["sha"]
    assessment=(private/("v3-generated-"+sha)/"batches"/
                ("v3-assessment-"+sha+".json"))
    if (assessment.is_symlink() or not assessment.is_file()
            or assessment.stat().st_size>8_000_000):
        raise ValueError("V3_REVISED96_OLD_REQUEST_UNRESOLVED_NO_REPLAY")
    prior=json.loads(assessment.read_text(encoding="utf8"))
    progress=assessment_progress(entry["raw"],prior)
    return verify_persisted_two_role_science(
        private,entry["raw"],entry["activityId"],sha,progress)


def advance_revised96_reviews(course: Path, repo: Path, private: Path, *,
                               execute: bool, transfer: bool,
                               max_activities: int=2,
                               max_seconds: int=900,
                               capability: dict|None=None,
                               review_one: Callable|None=None) -> dict:
    """Callback must invoke existing two-role immutable engine once per input."""
    if not execute or not transfer:
        raise ValueError("V3_REVISED96_BOTH_FLAGS_REQUIRED")
    authorization=authorize_revised96(execute=execute,transfer=transfer,
                                       activities=max_activities,seconds=max_seconds)
    inputs=stage_and_verify_two_new_inputs(course,repo,private)
    if not verified_new_provider_capability(private,capability):
        raise ValueError("V3_REVISED96_AUTH_KEY_OR_OLD_ROLE_GATE_STOP")
    if review_one is None:
        raise ValueError("V3_REVISED96_REAL_REVIEWER_CALLBACK_REQUIRED")
    from app_generator.runtime.v3_yoga6_recovery import coordinator_lock
    outcomes=[]
    started=time.monotonic()
    with coordinator_lock(private):
        for entry in inputs[:max_activities]:
            if time.monotonic()-started>=max_seconds:
                break
            sha=entry["sha"]
            is_new=unsent_revised_input(private,sha)
            if not is_new:
                # BSA-207: the source-bound role already exists, so DO NOT
                # resubmit. Reconcile its two COMPLETE role claims and
                # independently saved aggregate, then advance to the next
                # previously unsubmitted exact source input if safe.
                saved=read_prior_two_role_science(private,entry)
                if saved["uncertain"]:
                    outcomes.append({
                        "index":entry["index"],"status":
                        "STOP_PREVIOUS_REVISED_UNCERTAIN_NO_REPLAY",
                        "newUncertain":True})
                    break
            else:
                # Only genuinely NEW one-activity identity may open Gemini.
                # The existing V3 engine owns PRE_CALL before provider I/O.
                report=review_one(entry["raw"],entry["activityId"],private)
                if not isinstance(report,dict):
                    raise ValueError("V3_REVISED96_REVIEWER_RESULT_NOT_VALID")
                if (report.get("activitiesAssessed")!=1
                        or not isinstance(report.get("modelConsensusPassActivities"),int)
                        or not isinstance(report.get("modelRepairRequiredActivities"),int)
                        or not isinstance(report.get("modelUncertainActivities"),int)):
                    raise ValueError("V3_REVISED96_REVIEW_NOT_SOURCE_VERIFIED")
                saved=verify_persisted_two_role_science(
                    private,entry["raw"],entry["activityId"],sha,report)
            outcome={
                "index":entry["index"],"activityId":entry["activityId"],
                "reviewSliceSha256":sha,
                "reusedPreviouslyVerifiedRoles":not is_new,
                "newConsensusPass":saved["pass"],
                "newScientificRepairRequired":saved["repair"],
                "newUncertain":saved["uncertain"],
            }
            if sum((outcome["newConsensusPass"],
                    outcome["newScientificRepairRequired"],
                    outcome["newUncertain"]))!=1:
                raise ValueError("V3_REVISED96_UNCLASSIFIED_REAL_OUTCOME")
            outcomes.append(outcome)
            # Uncertain provider call: DO NOT open a new request from this
            # invocation; original and new role remain immutable.
            if outcome["newUncertain"]:
                break
    return {"status":("REVISED96_AUTHORIZED_BATCH_COMPLETED"
                      if len(outcomes)==max_activities
                         and not outcomes[-1].get("newUncertain",False)
                      else "REVISED96_STOPPED_AT_REVIEW_BOUNDARY"),
            "outcomes":outcomes,"maxGeminiReviewerCalls":2*max_activities,
            "originalReviewsModified":False,
            "versionedScopeAdmitted":False,
            "publicationAuthorized":False}

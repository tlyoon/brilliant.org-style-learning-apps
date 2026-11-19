"""BSA221: five owner-authorized, executable, source-free completion stages.

Admissions are only to the local corrected *version*, never the frozen original
review ledger. V3 public-release receipts require their own independent gate;
this module cannot mint or spoof them, merge PRs, or deploy.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from app_generator.runtime.v3_versioned_acceptance_scope import _encoded
from app_generator.runtime.v3_versioned_readiness import _read_previous
from scripts.check_v3_real_chapter9_browser import (
    _source_bound_packages, _stage_site, _exercise,
)

import subprocess
import sys
import time

_CONTRACT="BOSLA_OWNER_FIVE_STAGE_AUTONOMOUS_COMPLETION_V1"
_BASE="owner-five-stage-completion"
_STAGE_NAMES=(
    "V1_SOURCE_BOUND_VERSION_ADMISSION",
    "V2_PRIVACY_AND_SECURITY_QA",
    "V3_EXACT_RELEASE_EVIDENCE",
    "V4_PRIVATE_RELEASE_CANDIDATE_AND_ROLLBACK",
    "V5_CONTINUOUS_NEXT_ELIGIBLE_DISPATCH",
)
_PRIVATE_KEYS=frozenset((
    "studentid","matricnumber","studentemail","emailaddress",
    "studentname","phonenumber","password","apikey","accesstoken",
    "refreshtoken","identitycard","icnumber","personalrecord",
))
_BAD_RUNTIME=re.compile(
    r"\b(?:sendBeacon|XMLHttpRequest|WebSocket|indexedDB|"
    r"document\.cookie|navigator\.geolocation|serviceWorker\.register)\b"
)
_ACCEPTED_SUFFIX=frozenset((".json",".js",".css",".html",".svg",".png",".jpg",".woff2"))
_HEX40=re.compile(r"^[0-9a-f]{40}$")
_HEX64=re.compile(r"^[0-9a-f]{64}$")


def _hash(value:dict)->str:
    return sha256(_encoded(value)).hexdigest()


def _checked_stage(path:Path, *, head:str, source:str)->dict|None:
    if path.is_symlink():
        raise ValueError("V3_FIVE_STAGE_LINKED_CHECKPOINT")
    if not path.exists():
        return None
    if not path.is_file() or path.stat().st_size>100_000:
        raise ValueError("V3_FIVE_STAGE_UNSAFE_CHECKPOINT")
    doc=json.loads(path.read_text(encoding="utf8"))
    if not isinstance(doc,dict):
        raise ValueError("V3_FIVE_STAGE_INVALID_CHECKPOINT")
    body={k:v for k,v in doc.items() if k!="integritySha256"}
    if (doc.get("integritySha256")!=_hash(body)
            or doc.get("gitHead")!=head or doc.get("proposalSha256")!=source
            or doc.get("publicationAuthorized") is not False
            or doc.get("publicDeployExecuted") is not False):
        raise ValueError("V3_FIVE_STAGE_CHECKPOINT_INTEGRITY_ERROR")
    return doc


def _save_stage(folder:Path, name:str, payload:dict)->dict:
    if name not in _STAGE_NAMES:
        raise ValueError("V3_FIVE_STAGE_UNKNOWN_STAGE")
    if (payload.get("publicationAuthorized") is not False
            or payload.get("publicDeployExecuted") is not False
            or payload.get("status") not in (
               "PASS_PRIVATE_ONLY","READY_FOR_NEXT_AUTHORIZED_STAGE",
               "BLOCKED_WITH_NAMED_BOUNDARY")):
        raise ValueError("V3_FIVE_STAGE_UNSAFE_RELEASE_CLAIM")
    path=folder/(name+".json")
    old=_checked_stage(path,head=payload["gitHead"],
                       source=payload["proposalSha256"])
    doc={**payload,"integritySha256":_hash(payload)}
    if old is not None:
        if old!=doc:
            raise ValueError("V3_FIVE_STAGE_CONFLICTING_IMMUTABLE_CHECKPOINT")
        return old
    data=(json.dumps(doc,sort_keys=True,indent=2)+"\n").encode("utf8")
    fd,temp=tempfile.mkstemp(prefix=".five-stage-",suffix=".tmp",dir=folder)
    try:
        with os.fdopen(fd,"wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp,path)
    finally:
        try:Path(temp).unlink()
        except FileNotFoundError:pass
    return doc


def _private_fields(items:list[dict])->list[str]:
    found=set()
    def visit(node):
        if isinstance(node,dict):
            for key,value in node.items():
                if isinstance(key,str) and key.lower().replace("_","") in _PRIVATE_KEYS:
                    found.add(key)
                visit(value)
        elif isinstance(node,list):
            for value in node:
                visit(value)
    for item in items:
        visit(item)
    return sorted(found)


def _static_privacy(repo:Path, packages:list[tuple[int,bytes,list]])->dict:
    if len(packages)!=6 or sum(len(items) for _,_,items in packages)!=108:
        raise ValueError("V3_FIVE_STAGE_PRIVACY_SCOPE_NOT_108")
    private_fields=_private_fields([x for _,_,items in packages for x in items])
    if private_fields:
        raise ValueError("V3_FIVE_STAGE_PRIVATE_STUDENT_FIELD_IN_CONTENT")
    runtime_paths=(
        "app/app.js","app/course-preview.js","app/rc1-chapter9-bridge.js",
        "app/rc1-course-routing.js","app/rc1-course-diagnostic.js",
        "app/visual-renderers.js",
    )
    for name in runtime_paths:
        path=repo.joinpath(*name.split("/"))
        if path.is_symlink() or not path.is_file():
            raise ValueError("V3_FIVE_STAGE_PRIVACY_RUNTIME_MISSING")
        if _BAD_RUNTIME.search(path.read_text(encoding="utf8")):
            raise ValueError("V3_FIVE_STAGE_UNAPPROVED_EXTERNAL_PRIVACY_API")
    return {
        "sourceContentSensitiveFieldCount":0,
        "checkedRuntimeSourceFiles":len(runtime_paths),
        "browserEvidenceRequirement":"108 real activities, 648 locale-viewports, 698 checks, no external fetch/browser storage",
        "personalStudentRecordsUsed":False,
        "institutionalPrivacyCertificationClaimed":False,
        "technicalPrivacyChecksPassed":True,
    }


def _files_snapshot(site:Path)->list[dict]:
    if site.is_symlink() or not site.is_dir():
        raise ValueError("V3_FIVE_STAGE_INVALID_PREVIEW_DIR")
    results=[]
    for file in sorted(site.rglob("*")):
        if file.is_symlink() or not file.is_relative_to(site):
            raise ValueError("V3_FIVE_STAGE_SYMLINK_OR_ESCAPE_IN_PREVIEW")
        if file.is_dir():
            continue
        if not file.is_file() or file.suffix.lower() not in _ACCEPTED_SUFFIX:
            raise ValueError("V3_FIVE_STAGE_UNAUTHORIZED_CANDIDATE_ASSET")
        raw=file.read_bytes()
        if len(raw)>3_000_000:
            raise ValueError("V3_FIVE_STAGE_EXCESSIVE_ASSET_SIZE")
        results.append({
            "relativePath":file.relative_to(site).as_posix(),
            "sha256":sha256(raw).hexdigest(),"bytes":len(raw),
        })
    if len(results)<20 or len(results)>120:
        raise ValueError("V3_FIVE_STAGE_PREVIEW_ASSET_INVENTORY_UNEXPECTED")
    return results


def _prepare_preview(site:Path, packages:list)->list[dict]:
    _stage_site(site,packages)
    snapshot=_files_snapshot(site)
    if not any(x["relativePath"]=="app/rc1-chapter9-draft.html"
               for x in snapshot):
        raise ValueError("V3_FIVE_STAGE_MISSING_REAL_COURSE_PLAYER")
    for number,raw,_ in packages:
        file=site/"content"/"chapter-9"/f"section-9-{number}"/"package.json"
        if file.read_bytes()!=raw:
            raise ValueError("V3_FIVE_STAGE_STAGED_PACKAGE_MISMATCH")
    return snapshot


def _candidate_dir(private:Path,head:str,proposal:str)->Path:
    return private/_BASE/head/proposal/"private-preview"


def _stage_preview(private:Path,head:str,proposal:str,packages:list)->tuple[Path,list]:
    final=_candidate_dir(private,head,proposal)
    if final.is_symlink():
        raise ValueError("V3_FIVE_STAGE_LINKED_CANDIDATE")
    if final.exists():
        snapshot=_files_snapshot(final)
        # Rebuild only in a disposable private scratch directory and verify
        # EVERY file, not just 6 JSONs, before trusting a crash-recovered
        # candidate. A modified HTML/JS file cannot become an accepted build.
        with tempfile.TemporaryDirectory(
                prefix="bosla-five-stage-compare-",dir=final.parent) as scratch:
            fresh=Path(scratch)/"site"
            fresh.mkdir()
            expected=_prepare_preview(fresh,packages)
        if snapshot!=expected:
            raise ValueError("V3_FIVE_STAGE_STALE_EXISTING_CANDIDATE")
        return final,snapshot
    final.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix=".five-stage-preview-",dir=final.parent))
    try:
        snapshot=_prepare_preview(stage,packages)
        try:
            stage.rename(final)
        except FileExistsError:
            if not final.exists():
                raise
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    if _files_snapshot(final)!=snapshot:
        raise ValueError("V3_FIVE_STAGE_UNVERIFIED_PREVIEW_COMMIT")
    return final,snapshot


def _reconcile_finite_c3_historical_status(repo:Path)->dict:
    """Execute the NEXT source-free milestone without restarting any PDF.

    The older terminal HTTP 402 file carries its own explicit correction:
    later owner-approved access recovery was real, but the reconciled finite
    three-topic campaign still FAILED. This reads only versioned public
    summaries, NOT private PDF/model evidence or a new generalization trial.
    """
    old=repo/"docs"/"FINITE_GLOBAL_CODEBASE_DISPOSITION_20261104.md"
    later=repo/"docs"/"C3_POST_BILLING_RECONCILIATION_20261104.md"
    for file in (old,later):
        if file.is_symlink() or not file.is_file() or file.stat().st_size>120000:
            raise ValueError("V3_FIVE_STAGE_C3_HISTORICAL_SOURCE_MISSING")
    frozen=old.read_text(encoding="utf8")
    revised=later.read_text(encoding="utf8")
    if ("CURRENT-STATUS CORRECTION" not in frozen
        or "FAILED_LIMITED_CAMPAIGN" not in frozen
        or "PROVIDER_ACCESS_RECOVERED" not in revised
        or "FAILED_LIMITED_CAMPAIGN" not in revised
        or "RESPONSE_CONTRACT_ERROR" not in revised
        or "No third campaign" not in revised
        or "zero responsive checks" not in revised):
        raise ValueError("V3_FIVE_STAGE_C3_STALE_OR_CONTRADICTORY_HISTORY")
    return {
        "status":"C3_FAILED_LIMITED_CAMPAIGN_RECONCILED_READ_ONLY",
        "referenceSource":"Versioned repository summaries, not new private receipts",
        "historicalProvider402SupersededByAuthenticatedSourceFreeRecovery":True,
        "frozenHeldoutCases":3,
        "completedDraftsInRecordedReconciliation":2,
        "remainingTravelingWavesContractFailure":"RESPONSE_CONTRACT_ERROR",
        "newSourceBearingPDFCalls":0,
        "newGeminiCalls":0,
        "historicalThirdCampaignAllowed":False,
        "c3TechnicalAcceptanceGranted":False,
        "c4IndependentAcademicAcceptanceGranted":False,
        "institutionalPrivacyCertificationClaimed":False,
        "publicationAuthorized":False,
        "earlierSummarySha256":sha256(old.read_bytes()).hexdigest(),
        "correctedSummarySha256":sha256(later.read_bytes()).hexdigest(),
    }


def _source_free_public_adapter_inventory(repo:Path,private:Path,
                                          head:str,proposal:str)->dict:
    """Source-free audit of the *actual* five private release-stage receipts.

    Never substitutes these records for the distinct per-package V3 public
    receipt required by the existing publishing gate.
    """
    folder=private/_BASE/head/proposal
    receipts=[
        _checked_stage(folder/(name+".json"),head=head,source=proposal)
        for name in _STAGE_NAMES[:4]
    ]
    if (any(receipt is None or receipt.get("status")!="PASS_PRIVATE_ONLY"
            for receipt in receipts)
        or receipts[0].get("versionedCourseInternalAdmission") is not True
        or receipts[1].get("technicalPrivacyChecksPassed") is not True
        or receipts[2].get("existingPublicV3PerPackageAttestationMinted") is not False
        or receipts[3].get("faultInjectedRollbackRestoredAndVerified") is not True):
        raise ValueError("V3_FIVE_STAGE_PUBLIC_ADAPTER_PROOFS_INCOMPLETE")
    preview=_candidate_dir(private,head,proposal)
    observed=_files_snapshot(preview)
    if (_hash({"files":observed})!=receipts[3].get("stagedFilesSha256")
            or receipts[3].get("stagedRealBrowserChecks")!=698):
        raise ValueError("V3_FIVE_STAGE_PUBLIC_ADAPTER_PREVIEW_STALE")
    gate=repo/"app_generator"/"runtime"/"academic_release.py"
    if gate.is_symlink() or not gate.is_file():
        raise ValueError("V3_FIVE_STAGE_PUBLIC_V3_GATE_MISSING")
    code=gate.read_text(encoding="utf8")
    if ("read_private_release_receipt(" not in code
            or "def enforce_academic_release_gate(" not in code):
        raise ValueError("V3_FIVE_STAGE_PUBLIC_V3_GATE_WEAKENED")
    return {
        "status":"PRIVATE_RELEASE_ADAPTER_EVIDENCE_VERIFIED",
        "verifiedInternalVersionAdmissionReceipt":receipts[0]["integritySha256"],
        "verifiedTechnicalPrivacyReceipt":receipts[1]["integritySha256"],
        "verifiedTechnicalReleaseEvidenceReceipt":receipts[2]["integritySha256"],
        "verifiedStagedReal698BrowserAndRollbackReceipt":
            receipts[3]["integritySha256"],
        "verifiedPreviewFileCount":len(observed),
        "existingPublicV3GatePreserved":True,
        "publicV3ReceiptAbsentOrNotInferred":True,
        "publicDeployExecuted":False,
        "publicationAuthorized":False,
    }


def _browser_existing(readiness:dict)->bool:
    return (readiness.get("proposedContentScientificCoverage")==108
            and readiness.get("realChromeChecks")==698
            and readiness.get("realChromeActivities")==108
            and readiness.get("exactHeadHostedCiSuccess") is True
            and readiness.get("codeWorkingTreeClean") is True)


def run_five_stage_completion(
    repo:Path,private:Path,readiness:dict, *,
    exercise_candidate:bool=True,
)->dict:
    """Complete authorized next stages in one bounded synchronous invocation.

    No Gemini, PDF, API, merge or public deployment. Every stage rechecks
    exact proof identity and is restart-safe; a missing proof cannot be passed.
    """
    if (not isinstance(repo,Path) or not repo.is_dir()
            or not isinstance(private,Path) or not private.is_absolute()
            or private.is_symlink()
            or not private.resolve().is_relative_to(
                (Path(os.environ["LOCALAPPDATA"])/"Microvid").resolve())):
        raise ValueError("V3_FIVE_STAGE_UNSAFE_WORKSTATION_ROOT")
    if (not isinstance(readiness,dict)
            or readiness.get("status")!=
               "VERSIONED_SCIENCE_BROWSER_AND_CI_VERIFIED_UNADMITTED"
            or readiness.get("sourceVersionOnly") is not True
            or readiness.get("publicationAuthorized") is not False
            or not _browser_existing(readiness)):
        raise ValueError("V3_FIVE_STAGE_GENUINE_READINESS_REQUIRED")
    head=readiness.get("gitHead")
    proposal=readiness.get("proposalSha256")
    if not isinstance(head,str) or not _HEX40.fullmatch(head):
        raise ValueError("V3_FIVE_STAGE_WRONG_GIT_HEAD")
    if not isinstance(proposal,str) or not _HEX64.fullmatch(proposal):
        raise ValueError("V3_FIVE_STAGE_WRONG_SOURCE")
    saved=_read_previous(private/"v3-current-versioned-evidence-readiness.json")
    if saved!=readiness:
        raise ValueError("V3_FIVE_STAGE_READINESS_NOT_PERSISTED")
    from app_generator.runtime.v3_versioned_readiness import _git_info,_git_clean
    current,_=_git_info(repo)
    if current!=head or not _git_clean(repo):
        raise ValueError("V3_FIVE_STAGE_SOURCE_CODE_CHANGED")
    checked_proposal,packages=_source_bound_packages(private)
    if checked_proposal!=proposal or len(packages)!=6 or any(
        number!=i or len(items)!=18
        for i,(number,raw,items) in enumerate(packages,1)
    ):
        raise ValueError("V3_FIVE_STAGE_SOURCE_OR_REVIEW_ROSTER_STALE")
    output=private/_BASE/head/proposal
    if output.is_symlink():
        raise ValueError("V3_FIVE_STAGE_UNSAFE_CHECKPOINT_DIR")
    output.mkdir(parents=True,exist_ok=True)
    common={"contract":_CONTRACT,"gitHead":head,"proposalSha256":proposal,
            "publicationAuthorized":False,"publicDeployExecuted":False}
    stages=[]
    def save(index,**fields):
        stage=_save_stage(output,_STAGE_NAMES[index],{
            **common,**fields})
        stages.append({"stage":_STAGE_NAMES[index],
                       "status":stage["status"],
                       "integritySha256":stage["integritySha256"]})
        return stage

    admission=save(0,status="PASS_PRIVATE_ONLY",
        versionedCourseInternalAdmission=True,
        independentSourceBoundModelPositions=108,
        originalFrozenAssessed=75,originalFrozenPass=72,
        immutableProposalPreservedUnadmitted=True,
        nextStage=_STAGE_NAMES[1])
    privacy=_static_privacy(repo,packages)
    security=save(1,status="PASS_PRIVATE_ONLY",
        **privacy,nextStage=_STAGE_NAMES[2])
    evidence=save(2,status="PASS_PRIVATE_ONLY",
        admissionReceiptSha256=admission["integritySha256"],
        privacyReceiptSha256=security["integritySha256"],
        originalScientificReadinessSha256=readiness["integritySha256"],
        realBrowserReceiptSha256=readiness["browserReceiptSha256"],
        proposedSourceSha256=proposal,
        exactHeadHostedCiSuccess=True,localTechnicalReleaseEvidenceComplete=True,
        existingPublicV3PerPackageAttestationMinted=False,
        externalPublicationAuthorized=False,nextStage=_STAGE_NAMES[3])
    site,files=_stage_preview(private,head,proposal,packages)
    # Independent real Selenium exercise of the actual private release
    # candidate, not a fake "visual PASS" or historical browser receipt.
    existing=_checked_stage(output/(_STAGE_NAMES[3]+".json"),
                             head=head,source=proposal)
    if existing is not None:
        if (existing.get("stagedFilesSha256")!=_hash({"files":files})
            or existing.get("stagedRealBrowserChecks")!=698):
            raise ValueError("V3_FIVE_STAGE_PREVIEW_CHECKPOINT_MISMATCH")
        preview=existing
    else:
        if not exercise_candidate:
            raise ValueError("V3_FIVE_STAGE_REAL_PREVIEW_BROWSER_REQUIRED")
        with tempfile.TemporaryDirectory(prefix="bosla-five-stage-exercise-") as temp:
            copy=Path(temp)/"site"
            shutil.copytree(site,copy)
            # Fault-inject a broken private build, then prove rollback to the
            # immutable exact candidate bytes before running Chrome. Never
            # touch an original package or published app.
            test_package=(copy/"content"/"chapter-9"/
                          "section-9-1"/"package.json")
            original=test_package.read_bytes()
            test_package.write_bytes(b"{\"broken\":true}")
            if test_package.read_bytes()==original:
                raise ValueError("V3_FIVE_STAGE_ROLLBACK_FAULT_NOT_INJECTED")
            test_package.write_bytes(
                site.joinpath("content","chapter-9","section-9-1",
                              "package.json").read_bytes())
            if test_package.read_bytes()!=original:
                raise ValueError("V3_FIVE_STAGE_ROLLBACK_NOT_RESTORED")
            actual=_exercise(copy,packages)
        if (actual.get("renderedChecks")!=698
                or actual.get("all108ActivitiesVisited") is not True
                or actual.get("allLocaleViewportPromptChecks")!=648):
            raise ValueError("V3_FIVE_STAGE_REAL_PREVIEW_BROWSER_DID_NOT_PASS")
        if _files_snapshot(site)!=files:
            raise ValueError("V3_FIVE_STAGE_CANDIDATE_CHANGED_BY_TEST")
        preview=save(3,status="PASS_PRIVATE_ONLY",
            stagedFilesSha256=_hash({"files":files}),
            stagedFilesTotal=len(files),stagedRealBrowserChecks=698,
            candidatePrivatePath="owner-five-stage-completion/<git>/<source>/private-preview",
            productionBundleReleased=False,
            faultInjectedRollbackRestoredAndVerified=True,
            rollbackStrategy="Keep previous immutable preview and Git checkout unchanged",
            nextStage=_STAGE_NAMES[4])
    if len(stages)==3:
        stages.append({"stage":_STAGE_NAMES[3],"status":preview["status"],
                       "integritySha256":preview["integritySha256"]})
    # BSA222: V5 must EXECUTE its independent source-free downstream work,
    # not merely enqueue a label and stop. Read-only source-bound adapter
    # inventory + precedence-correct finite C3 history, no new PDF/model I/O.
    adapter=_source_free_public_adapter_inventory(
        repo,private,head,proposal)
    historical=_reconcile_finite_c3_historical_status(repo)
    last=save(4,status="READY_FOR_NEXT_AUTHORIZED_STAGE",
        previousPrivateCandidatePreserved=True,
        v1toV4AcceptanceValidated=True,
        sourceFreeDownstreamWorkExecuted=True,
        sourceFreePublicAdapter=adapter,
        historicalFiniteC3Reconciliation=historical,
        nextEligibleMilestone="GENERIC_FULL_COURSE_V3_RELEASE_ADAPTER_WITHOUT_FORGED_ATTESTATION",
        externalDeploymentPermissionNotAssumed=True,
        originalModelRoleClaimsNeverReplayed=True,
        priorC3CampaignsNotReplayed=True,
        privateReleaseCandidateVerified=True)
    return {
        "status":"FIVE_STAGE_PRIVATE_TECHNICAL_PATH_COMPLETE_NO_PUBLICATION",
        "contract":_CONTRACT,"gitHead":head,"proposalSha256":proposal,
        "stages":stages,"completedStageCount":len(stages),
        "lastCheckpointSha256":last["integritySha256"],
        "nextEligibleMilestone":last["nextEligibleMilestone"],
        "versionedCourseInternalAdmission":True,
        "technicalPrivacyChecksPassed":True,
        "realPrivateCandidateBrowserChecks":698,
        "publicV3ReleaseReceiptMinted":False,
        "publicationAuthorized":False,"publicDeployExecuted":False,
        "paidGeminiCalls":0,
        "historicalFiniteC3Result":historical["status"],
        "sourceFreeDownstreamAdapterVerified":True,
    }



def advance_five_stage_on_pinned_browser(
    repo:Path,private:Path,readiness:dict,
)->dict:
    """Normal-worker entrypoint: reuse historic pinned Selenium, no pip.

    Source-free subprocess has one bounded retry ONLY for recognized
    transient Selenium failures. Every independently completed stage remains
    checkpointed; no content/model/provider request is ever retried here.
    """
    if not _browser_existing(readiness):
        raise ValueError("V3_FIVE_STAGE_SOURCE_BOUND_READINESS_MISSING")
    from scripts.run_v3_yoga6_acceptance import _browser_python
    python=_browser_python(repo)
    script=repo/"scripts"/"run_v3_yoga6_five_stage.py"
    if script.is_symlink() or not script.is_file():
        raise ValueError("V3_FIVE_STAGE_PINNED_CHILD_SCRIPT_MISSING")
    args=[str(python),str(script),"--private-root",str(private)]
    retry_classes=frozenset((
        "TimeoutException","StaleElementReferenceException",
        "WebDriverException","SessionNotCreatedException",
    ))
    for attempt in (1,2):
        try:
            child=subprocess.run(
                args,cwd=repo,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"},
                capture_output=True,text=True,check=False,timeout=450)
        except subprocess.TimeoutExpired:
            if attempt==1:
                continue
            raise ValueError("V3_FIVE_STAGE_PINNED_CHILD_TIMED_OUT") from None
        try:
            report=json.loads(child.stdout.strip().splitlines()[-1])
        except (ValueError,IndexError):
            raise ValueError("V3_FIVE_STAGE_CHILD_NON_JSON_OUTPUT") from None
        if not isinstance(report,dict):
            raise ValueError("V3_FIVE_STAGE_CHILD_NOT_JSON_OBJECT")
        if (attempt==1 and child.returncode!=0
                and report.get("status")=="STOP_FIVE_STAGE_AUTONOMOUS_COMPLETION"
                and report.get("errorClass") in retry_classes):
            continue
        if (child.returncode!=0
                or report.get("status")!=
                    "FIVE_STAGE_PRIVATE_TECHNICAL_PATH_COMPLETE_NO_PUBLICATION"
                or report.get("completedStageCount")!=5
                or report.get("proposalSha256")!=readiness["proposalSha256"]
                or report.get("gitHead")!=readiness["gitHead"]
                or report.get("publicationAuthorized") is not False
                or report.get("paidGeminiCalls")!=0
                or report.get("realPrivateCandidateBrowserChecks")!=698):
            return {
                "status":"STOP_FIVE_STAGE_NORMAL_PIPELINE",
                "childStatus":report.get("status"),
                "childErrorClass":report.get("errorClass"),
                "childErrorCode":report.get("errorCode"),
                "browserChildAttempts":attempt,
                "publicationAuthorized":False,
                "paidGeminiCalls":0,
            }
        return {**report,"browserChildAttempts":attempt}
    raise AssertionError("V3_FIVE_STAGE_RETRY_LIMIT")

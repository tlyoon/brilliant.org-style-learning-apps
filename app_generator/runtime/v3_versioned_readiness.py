"""BSA220: exact-version read-only evidence reconciliation and next-stage handoff.

A 108/108 model-reviewed *proposed* roster is not the frozen original ledger,
nor an admitted/published course. This module cannot grant release authority.
It reuses the real source, independent Gemini, GitHub and Chrome validators.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from app_generator.runtime.v3_versioned_acceptance_scope import (
    prepare_versioned_course_proposal, _encoded,
)
from scripts.run_v3_yoga6_acceptance import _read_saved, _runtime_sha

_SHA40=re.compile(r"^[0-9a-f]{40}$")
_SHA64=re.compile(r"^[0-9a-f]{64}$")
_QA_FILE="v3-real-chapter9-browser-qa.json"
_READINESS_FILE="v3-current-versioned-evidence-readiness.json"
_REPO="tlyoon/brilliant.org-style-learning-apps"


def _git_info(repo:Path)->tuple[str,str]:
    def get(*args):
        result=subprocess.run(["git",*args],cwd=repo,
            capture_output=True,text=True,timeout=20,check=True)
        return result.stdout.strip()
    head=get("rev-parse","HEAD")
    branch=get("branch","--show-current")
    if not _SHA40.fullmatch(head) or not branch or len(branch)>220:
        raise ValueError("V3_READINESS_NOT_EXACT_GIT_REVISION")
    return head,branch


def _git_clean(repo:Path)->bool:
    proc=subprocess.run(
        ["git","status","--porcelain","--untracked-files=normal"],
        cwd=repo,capture_output=True,text=True,timeout=20,check=True)
    return not proc.stdout.strip()


def _hosted_runs(repo:Path,branch:str)->list[dict]:
    # BSA238: querying CI by a local feature alias misses the genuine push
    # workflow on an identical commit published to a different review branch.
    # Use the *exact local commit* and the REQUIRED validation workflow, then
    # _exact_ci_success independently checks SHA, conclusion and run identity.
    # No CI result, HTTP error or missing workflow may be interpreted as PASS.
    try:
        head,local_branch=_git_info(repo)
        if branch!=local_branch:
            return []
        proc=subprocess.run(
            ["gh","run","list","-R",_REPO,"-c",head,
             "-w","validate.yml","-L","10","--json",
             "headSha,status,conclusion,databaseId,url"],
            cwd=repo,capture_output=True,text=True,timeout=30,check=False)
        if proc.returncode!=0:
            return []
        data=json.loads(proc.stdout)
        return data if isinstance(data,list) else []
    except (OSError,ValueError,subprocess.TimeoutExpired,
            subprocess.CalledProcessError):
        return []


def _exact_ci_success(rows:list[dict],head:str)->bool:
    for row in rows:
        if (isinstance(row,dict) and row.get("headSha")==head
                and row.get("status")=="completed"
                and row.get("conclusion")=="success"
                and isinstance(row.get("databaseId"),int)
                and row["databaseId"]>0):
            return True
    return False


def _read_previous(path:Path)->dict|None:
    if path.is_symlink():
        raise ValueError("V3_READINESS_LINKED_RECEIPT")
    if not path.exists():
        return None
    if not path.is_file() or path.stat().st_size>12000:
        raise ValueError("V3_READINESS_UNSAFE_RECEIPT")
    doc=json.loads(path.read_text(encoding="utf8"))
    if not isinstance(doc,dict):
        raise ValueError("V3_READINESS_INVALID_RECEIPT")
    payload={k:v for k,v in doc.items() if k!="integritySha256"}
    if (not _SHA64.fullmatch(str(doc.get("integritySha256")))
            or doc["integritySha256"]!=sha256(_encoded(payload)).hexdigest()
            or doc.get("publicationAuthorized") is not False
            or doc.get("versionedScopeAdmitted") is not False):
        raise ValueError("V3_READINESS_RECEIPT_TAMPERED")
    return doc


def _persist(private:Path,report:dict)->dict:
    path=private/_READINESS_FILE
    _read_previous(path)
    out={**report,"integritySha256":sha256(_encoded(report)).hexdigest()}
    payload=(json.dumps(out,sort_keys=True,indent=2)+"\n").encode("utf8")
    if private.is_symlink() or not private.is_dir():
        raise ValueError("V3_READINESS_INVALID_PRIVATE_ROOT")
    fd,name=tempfile.mkstemp(prefix=".v3-readiness-",suffix=".tmp",dir=private)
    try:
        with os.fdopen(fd,"wb") as stream:
            stream.write(payload);stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        try:Path(name).unlink()
        except FileNotFoundError:pass
    return out


def evaluate_current_versioned_evidence(
    root:Path,private:Path,*,hosted_runs:list[dict]|None=None,
    persist:bool=True,
)->dict:
    """Evaluate actual separate-version academic/browser/CI proofs; no AI I/O.

    Any absent/damaged source or receipt fails closed, rather than being
    'auto-assessed' by a static generic completion status.
    """
    if (not isinstance(root,Path) or not root.is_dir()
            or not isinstance(private,Path) or not private.is_absolute()
            or private.is_symlink()
            or private.resolve().is_relative_to(root.resolve())
            or not private.is_dir()):
        raise ValueError("V3_READINESS_UNSAFE_SOURCE_OR_PRIVATE_ROOT")
    proposal=prepare_versioned_course_proposal(
        root/"content"/"chapter-9",root,private)
    digest=proposal.get("proposalSha256")
    if not isinstance(digest,str) or not _SHA64.fullmatch(digest):
        raise ValueError("V3_READINESS_PROPOSAL_IDENTITY_MISSING")
    path=private/"versioned-course-proposals"/digest/"scope-proposal.json"
    if path.is_symlink() or not path.is_file() or path.stat().st_size>1000000:
        raise ValueError("V3_READINESS_PROPOSAL_MANIFEST_UNSAFE")
    manifest=json.loads(path.read_text(encoding="utf8"))
    unsigned={k:v for k,v in manifest.items() if k!="integritySha256"}
    counts=manifest.get("counts")
    if (manifest.get("integritySha256")!=digest
            or sha256(_encoded(unsigned)).hexdigest()!=digest
            or manifest.get("scope")!="PROPOSAL_NOT_ADMITTED"
            or manifest.get("versionedScopeAdmitted") is not False
            or manifest.get("publicationAuthorized") is not False
            or not isinstance(counts,dict)
            or not isinstance(manifest.get("sections"),list)
            or len(manifest["sections"])!=6
            or any(row.get("activities")!=18
                   for row in manifest["sections"])
            or proposal.get("finalTwoScienceIntegrated") is not True
            or proposal.get("remainingContentUnreviewedAfterSupplemental")!=0
            or counts.get("originalAssessed")!=75
            or counts.get("originalGenuineConsensusPasses")!=72
            or counts.get("scientificallyReviewedProposedContent")!=108
            or counts.get("proposedContentWithoutScience")!=0
            or counts.get("potentiallyReusablePasses")!=103
            or counts.get("finalTwoNewVersionConsensusPasses")!=2
            or len(manifest.get("finalTwoNewVersionGenuineScience",{}).get("proofs",[]))!=2
            or "ORIGINAL_SECTION_9_1_AMBIGUOUS_DO_NOT_REPLAY"
               not in manifest.get("unresolved",[])
            or "HISTORICAL_SECTION96_PROVIDER_RESPONSE_UNRECOVERABLE_DO_NOT_REPLAY"
               not in manifest.get("unresolved",[])):
        raise ValueError("V3_READINESS_MODEL_OR_HISTORY_PROOF_INCOMPLETE")
    head,branch=_git_info(root)
    saved=_read_saved(private/_QA_FILE)
    if (not isinstance(saved,dict)
            or saved.get("status")!="ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS"
            or saved.get("proposalSha256")!=digest
            or saved.get("revisionSha")!=head
            or saved.get("rendererRuntimeSha256")!=_runtime_sha(root)
            or saved.get("activitiesInCandidate")!=108
            or saved.get("renderedChecks")!=698
            or saved.get("allLocaleViewportPromptChecks")!=648
            or saved.get("all108ActivitiesVisited") is not True
            or saved.get("publicationAuthorized") is not False
            or saved.get("versionedScopeAdmitted") is not False):
        raise ValueError("V3_READINESS_GENUINE_EXACT_HEAD_BROWSER_MISSING")
    clean=_git_clean(root)
    ci=(clean and _exact_ci_success(
        hosted_runs if hosted_runs is not None else _hosted_runs(root,branch),
        head))
    status=("VERSIONED_SCIENCE_BROWSER_AND_CI_VERIFIED_UNADMITTED"
            if ci else "VERSIONED_SCIENCE_BROWSER_WAIT_COMMITTED_HEAD"
            if not clean else "VERSIONED_SCIENCE_BROWSER_VERIFIED_WAIT_EXACT_HEAD_CI")
    report={
        "contract":"BOSLA_V3_VERSIONED_EVIDENCE_READINESS_V1",
        "status":status,"gitHead":head,"proposalSha256":digest,
        "browserReceiptSha256":saved["integritySha256"],
        "sourceVersionOnly":True,"historicalOriginalAssessmentsUnchanged":75,
        "historicalOriginalConsensusPassesUnchanged":72,
        "genuineUnchangedContentPasses":103,
        "genuineChangedContentPasses":5,
        "proposedContentScientificCoverage":108,
        "proposedContentRemainingScientificGaps":0,
        "realChromeActivities":108,"realChromeChecks":698,
        "exactHeadHostedCiSuccess":ci,
        "codeWorkingTreeClean":clean,
        "nextEligibleMilestone":(
            "INDEPENDENT_VERSION_ADMISSION_PRIVACY_AND_RELEASE_PROOFS"
            if ci else "COMMIT_CHECKER_AND_RUN_EXACT_HEAD_CI"
            if not clean else "VERIFY_EXACT_GIT_HEAD_HOSTED_CI"),
        "versionedScopeAdmitted":False,"publicationAuthorized":False,
        "automaticReleaseEligibilityGranted":False,
        "originalHistoricalUncertaintyPreserved":True,
        "realLearnerPilotAccepted":False,
    }
    return _persist(private,report) if persist else report

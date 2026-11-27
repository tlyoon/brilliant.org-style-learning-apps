"""BSA280: classify academic failures, dispatch independent safe repairs.

Academic proofs remain separate from engineering recovery. A repeated original
textbook acceptance failure must not re-sign a failing source, replay unknown
provider requests, or rerun V1-V36 endlessly without any code/evidence change.
This module produces bounded decisions and NEVER academic PASS.
"""
from __future__ import annotations
from hashlib import sha256
import json
import re
from typing import Any

SAFETY_CODES=(
    "SOURCE_HASH_MISMATCH","SOURCE_SHA256_MISMATCH",
    "SOURCE_BINDING_MISMATCH","SOURCE_DOCUMENT_CHANGED",
    "HMAC_MISMATCH","RECEIPT_TAMPERED","SIGNATURE_INVALID",
    "ORIGINAL_SOURCE_UNAVAILABLE","UNTRUSTED_SOURCE",
    "FORGED_ACADEMIC","UNAUTHORIZED_PROVIDER_REPLAY",
    "BSA280_SOURCE_UNTRUSTED",
)
TRANSIENT_CODES=(
    "CONNECTIONRESETERROR","CONNECTION REFUSED",
    "NETWORK_UNREACHABLE","TIMED OUT","TIMEOUTEXPIRED",
    "SERVERERROR","HTTP 502","HTTP 503","HTTP 504",
    "GH_UNAVAILABLE","SELENIUM TIMEOUT","ERR_CONNECTION",
)
PROOF_CODES=(
    "PROOF_PRODUCER_REQUIRED","NOT_IMPLEMENTED",
    "NEW_SOURCE_SPECIFIC_PROOF","MISSING_PROOF_HANDLER",
    "ACADEMIC_PROOF_HANDLER_MISSING","INDEPENDENT_SEMANTIC",
    "BLOCKED_PROOF_PRODUCER","SOURCE_BOUND_PER_GATE_PROOF",
)
LOCAL_DEFECT_CODES=(
    "TRACEBACK","MODULENOTFOUNDERROR","UNBOUNDLOCALERROR",
    "ATTRIBUTEERROR","IMPORTERROR","TYPEERROR","KEYERROR",
    "VALUEERROR","SYNTAXERROR","ASSERTIONERROR",
    "UNEXPECTED_EXIT","CHILD_PROCESS_FAILED",
)
CODEX_ENVIRONMENT_CODES=(
    "HELPER_UNKNOWN_ERROR","SETUP REFRESH HAD ERRORS",
    "FAILED TO CREATE UNIFIED EXEC PROCESS",
    "FAILED TO WRITE FILE","APPROVAL POLICY IS NEVER",
    "MCP TOOL CALL REQUIRES APPROVAL",
    "SANDBOX WRITE DENIED",
)

def exact_owner_failure_code(log_excerpt:str)->str|None:
    """Extract only a real bounded owner failure JSON marker, never private text.

    BSA294: the old 20KB diagnostic tail erased the BSA284 failure beneath
    a large source-free summary, leaving only MISSING_SCIENCE_PRODUCER.
    A specific signed/source-safe repair worker needs the actual fault code.
    Do not trust arbitrary generated code quotes as a failure event.
    """
    if not isinstance(log_excerpt,str):
        return None
    marker=None
    for line in log_excerpt[-1_000_000:].splitlines():
        line=line.strip()
        if (not line.startswith("{") or len(line)>3000
            or '"errorCode"' not in line):
            continue
        try:
            event=json.loads(line)
        except (ValueError,TypeError):
            continue
        if (not isinstance(event,dict)
            or event.get("status")!=
               "BSA276_ELIGIBLE_ACADEMIC_STEP_UNVERIFIED"
            or event.get("errorClass")!="ValueError"):
            continue
        code=event.get("errorCode")
        if isinstance(code,str) and re.fullmatch(
            r"(?:BSA|V)[0-9]{3}_[A-Z0-9_]{5,95}",code):
            marker=code
    return marker


def _matches(text:str,codes:tuple[str,...])->bool:
    upper=text.upper()
    return any(x in upper for x in codes)

def classify_owner_failure(*,exit_code:int,log_excerpt:str)->str:
    """Safety classification has absolute precedence over retry instructions."""
    if type(exit_code) is not int:
        raise ValueError("BSA280_OWNER_EXIT_CODE_REQUIRED")
    if exit_code==0:
        return "OWNER_SUCCESS_VERIFY_SEPARATELY"
    excerpt=log_excerpt[-20000:]
    if _matches(excerpt,SAFETY_CODES):
        return "SOURCE_OR_SIGNATURE_UNTRUSTED"
    if exit_code==125:
        # BSA283: parent heartbeat without child output is not progress.
        # This is an implementation/performance fault; never infer PASS.
        return "LOCAL_OWNER_IMPLEMENTATION_DEFECT"
    if _matches(excerpt,PROOF_CODES):
        return "MISSING_SCIENCE_PRODUCER"
    if _matches(excerpt,LOCAL_DEFECT_CODES):
        return "LOCAL_OWNER_IMPLEMENTATION_DEFECT"
    if exit_code==124 or _matches(excerpt,TRANSIENT_CODES):
        return "TRANSIENT_OWNER_DEPENDENCY"
    return "UNCLASSIFIED_OWNER_FAILURE"

def classify_codegen_failure(*,exit_code:int,log_excerpt:str,
                             changed_files:bool)->str:
    if type(exit_code) is not int:
        raise ValueError("BSA280_CODEX_EXIT_CODE_REQUIRED")
    if _matches(log_excerpt[-20000:],CODEX_ENVIRONMENT_CODES):
        return "CODEX_LOCAL_SANDBOX_WRITE_OR_EXEC_FAILURE"
    if exit_code!=0:
        return "CODEX_EXECUTION_FAILED_PRESERVE_ANY_PATCH"
    if changed_files:
        return "CODEX_CODE_CHANGED_TESTS_AND_REVIEW_REQUIRED"
    return "CODEX_NO_CHANGE_NOT_ACADEMIC_PROGRESS"

def owner_recovery_plan(*,state:dict[str,Any],head:str,
                        exit_code:int,log_excerpt:str)->dict[str,Any]:
    """Persist repeated failure fingerprints without textbook/private raw text."""
    if not isinstance(state,dict) or len(head)!=40 or any(
            c not in "0123456789abcdef" for c in head):
        raise ValueError("BSA280_AUTHENTIC_OWNER_HEAD_REQUIRED")
    issue=classify_owner_failure(exit_code=exit_code,log_excerpt=log_excerpt)
    # Error logs contain timestamps, per-run elapsed seconds, temporary
    # names and child PIDs. Hash the *classified failure family*, not raw
    # changing tail bytes, or every identical recurrence would look new
    # and re-run the full 10-minute owner pipeline forever.
    fingerprint=sha256((head+"|"+str(exit_code)+"|"+issue).encode(
        "utf8")).hexdigest()
    prior=state.get("academicFailure")
    repeated=(isinstance(prior,dict)
              and prior.get("head")==head
              and prior.get("fingerprint")==fingerprint)
    count=(int(prior.get("count",0))+1 if repeated else 1)
    if issue=="SOURCE_OR_SIGNATURE_UNTRUSTED":
        mode="QUARANTINE_ACADEMIC_ACCEPTANCE_AND_SOURCE_WRITES"
    elif issue=="TRANSIENT_OWNER_DEPENDENCY" and count==1:
        mode="BOUNDED_RETRY_ON_NEXT_SCHEDULE"
    else:
        mode="DISPATCH_INDEPENDENT_SOURCE_SAFE_CODE_REPAIR"
    result={
        "head":head,"exitCode":exit_code,"classification":issue,
        "fingerprint":fingerprint,"count":min(count,1000),
        "mode":mode,"academicPASS":False,
        "replayUnknownProviderRequests":False,
        "publicationAuthorized":False,
    }
    state["academicFailure"]=result
    return result

def should_skip_unchanged_owner(state:dict[str,Any],head:str)->bool:
    failure=state.get("academicFailure")
    return (
        isinstance(failure,dict) and failure.get("head")==head
        and failure.get("mode")==
            "DISPATCH_INDEPENDENT_SOURCE_SAFE_CODE_REPAIR"
        and state.get("lastOwnerHead")!=head
    )

def needs_coding_recovery(*,classification:str,previous_failures:int)->bool:
    if previous_failures<0:
        raise ValueError("BSA280_INVALID_FAILURE_COUNT")
    return (classification in {
        "CODEX_LOCAL_SANDBOX_WRITE_OR_EXEC_FAILURE",
        "CODEX_NO_CHANGE_NOT_ACADEMIC_PROGRESS",
        "CODEX_EXECUTION_FAILED_PRESERVE_ANY_PATCH",
    } and previous_failures>=1)

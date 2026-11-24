"""BSA261: fail-isolated, source-free Bosla development lanes.

A failed scientific stage blocks itself and its dependents, *not* independent
safe verification. This module executes an explicit local allowlist, never
untrusted commands, model/provider I/O, publishing, or source mutation.

Each lane produces a distinct signed private, content-addressed receipt.
A blocked lane cannot be used as academic, publication, or worker PASS.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from dataclasses import dataclass
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any,Callable

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint

_HEAD=re.compile(r"[a-f0-9]{40}\Z")
_SHA=re.compile(r"[a-f0-9]{64}\Z")

@dataclass(frozen=True)
class VerifiedLane:
    lane: str
    requires:tuple[str,...]
    run:Callable[[Path,Path,dict[str,Any]],dict[str,Any]]


def _recovery_contract(repo:Path,_private:Path,_ready:dict)->dict:
    from scripts.check_regression_contract import verify
    problems=verify(repo)
    if problems:
        raise ValueError("BSA261_RECURRENCE_REGISTRY_OR_HISTORICAL_REMEDY_INVALID")
    return {"status":"PASS_RECOVERY_CONTRACT","registeredRemediesValid":True}


def _content_contract(_repo:Path,_private:Path,_ready:dict)->dict:
    from scripts.validate_content import main
    with redirect_stdout(StringIO()):
        result=main()
    if result!=0:
        raise ValueError("BSA261_CONTENT_PACKAGE_CONTRACT_INVALID")
    return {"status":"PASS_CONTENT_STRUCTURE","contentStructuralChecksValid":True}


def _independent_academic_receipt(repo:Path,private:Path,ready:dict)->dict:
    # Must never be invoked if V32 did not produce its real signed predecessor.
    from app_generator.runtime.v3_post_v31_other_mcq_locale_roles import (
        _V32,_STATUS32,
    )
    from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
    folder=(private/"owner-five-stage-completion"/ready["gitHead"]/
            ready["proposalSha256"])
    v32=_signed(folder,_V32,ready)
    if (v32.get("status")!=_STATUS32
            or v32.get("fullAcademicPASS")!=0
            or v32.get("publicationAuthorized") is not False):
        raise ValueError("BSA261_ACADEMIC_READBACK_PREDECESSOR_NOT_SIGNED")
    # Independent process reopens original selected PDF, complete signed
    # V29-V32 chain, frozen candidate and real screenshot PNG pixels.
    checked=subprocess.run(
        [sys.executable,str(repo/"scripts"/"verify_v32_private_owner_readback.py")],
        cwd=repo,capture_output=True,text=True,timeout=100,check=False)
    if checked.returncode!=0:
        raise ValueError("BSA261_INDEPENDENT_SOURCE_READBACK_NOT_VERIFIED")
    try:
        data=json.loads(checked.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError) as exc:
        raise ValueError("BSA261_INDEPENDENT_SOURCE_READBACK_JSON_INVALID") from exc
    if (data.get("status")!=
            "BSA260_INDEPENDENT_ALL_NINE_SERWAY_MCQ_SOURCE_LOCALE_ROLES_PASS"
            or data.get("gitHead")!=ready["gitHead"]
            or data.get("allNineMcqLocalizedOptionsBoundedRechecked")!=108
            or data.get("allNineMcqFalseAlternativesModelled")!=27
            or data.get("realChromeThreeLocalePngReadbackAlsoExecuted") is not True
            or data.get("completeAcademicProofGatesStillOpen")!=90
            or data.get("comprehensiveMeaningMicroproofsStillPending")!=429
            or data.get("fullAcademicPASS")!=0
            or data.get("newModelCalls")!=0
            or data.get("publicationAuthorized") is not False):
        raise ValueError("BSA261_INDEPENDENT_RECEIPT_MISREPRESENTED")
    return {"status":"PASS_PRIVATE_INDEPENDENT_V32_SOURCE_READBACK",
            "receiptSourceBound":True,
            "signedV32Sha256":data["signedV32Sha256"],
            "nineMcqBoundedOptionsRechecked":108,
            "independentOriginalPdfAndPngReopened":True}


# Strict static, explicitly authorized source-free lanes. These tasks are
# independent: a blocked readback must NOT stop local regression/content QA.
_LANES=(
    VerifiedLane("recovery_contract",(),_recovery_contract),
    VerifiedLane("package_structure",(),_content_contract),
    VerifiedLane("independent_v32_readback",("v32_source_chain",),
                 _independent_academic_receipt),
)


def run_safe_isolated_development_lanes(
    *,repo:Path,private:Path,ready:dict[str,Any],
    completed_dependencies:set[str]|frozenset[str],
    blocked_operation:str|None=None,
)->dict[str,Any]:
    """Continue independent lanes after a blocker; no silent release PASS.

    Only explicit static Python callbacks can run. Source-dependent tasks are
    skipped when their true prerequisite is missing; unrelated tasks continue.
    """
    head=ready.get("gitHead")
    proposal=ready.get("proposalSha256")
    if (not isinstance(head,str) or not _HEAD.fullmatch(head)
            or not isinstance(proposal,str) or not _SHA.fullmatch(proposal)
            or ready.get("publicationAuthorized") is not False):
        raise ValueError("BSA261_UNPINNED_OWNER_EVIDENCE_OR_PUBLICATION_BOUNDARY")
    folder=private/"owner-five-stage-completion"/head/proposal
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("BSA261_PRIVATE_BOUNDED_RECEIPT_DIRECTORY_MISSING")
    outcomes=[]
    completed=set(completed_dependencies)
    allowed={"v32_source_chain"}
    if not completed<=allowed:
        raise ValueError("BSA261_UNTRUSTED_DEPENDENCY_CLAIM")
    for lane in _LANES:
        missing=sorted(set(lane.requires)-completed)
        if missing:
            row={"lane":lane.lane,"status":"QUARANTINED_DEPENDENCY",
                 "missingPrerequisiteCodes":missing,
                 "publicationAuthorized":False}
        else:
            try:
                result=lane.run(repo,private,ready)
                if (not isinstance(result,dict)
                        or not str(result.get("status","")).startswith("PASS_")
                        or result.get("fullAcademicPASS",0)!=0
                        or result.get("publicationAuthorized",False) is not False):
                    raise ValueError("BSA261_UNTRUSTED_LANE_RESULT")
                row={"lane":lane.lane,"status":"VERIFIED_INDEPENDENT_PASS",
                     "evidence":result,"publicationAuthorized":False}
            except Exception as exc:
                # Never retain the exception's message, traceback, private path,
                # provider response, credential or personally identifiable data.
                row={"lane":lane.lane,"status":"QUARANTINED_OPERATION_ERROR",
                     "reasonClass":type(exc).__name__,
                     "publicationAuthorized":False}
        outcomes.append(row)
    statuses=[x["status"] for x in outcomes]
    result={
        "status":("INDEPENDENT_SAFE_LANES_ALL_VERIFIED" if
                  all(x=="VERIFIED_INDEPENDENT_PASS" for x in statuses)
                  else "INDEPENDENT_SAFE_LANES_ADVANCED_WITH_QUARANTINE"),
        "gitHead":head,"proposalSha256":proposal,
        "blockedOperationCode":blocked_operation,
        "eligibleIndependentLanesExecuted":sum(
            x!="QUARANTINED_DEPENDENCY" for x in statuses),
        "independentlyVerifiedLanes":sum(
            x=="VERIFIED_INDEPENDENT_PASS" for x in statuses),
        "quarantinedLaneCount":sum(
            x!="VERIFIED_INDEPENDENT_PASS" for x in statuses),
        "lanes":outcomes,
        "fullAcademicPASS":0,"newModelCalls":0,
        "publicationAuthorized":False,
    }
    # Content-addressed immutable receipts survive failed operations and
    # later retries without overwriting an earlier quarantined result.
    receipt_name="V33_ISOLATED_DEVELOPMENT_LANES_"+_hash(result)[:24]+".json"
    signed=_v6_checkpoint(folder/receipt_name,result)
    return {**result,"privateSignedReceiptName":receipt_name,
            "privateSignedReceiptSha256":signed["integritySha256"]}

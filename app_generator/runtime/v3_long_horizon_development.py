"""BSA269: durable long-horizon Bosla advancement contract across invocations.

This is a *development frontier* record, NOT an academic proof or a scheduler.
Every checkpoint binds actual original-source, candidate, code, and signed V36
evidence. A repeated zero-acceptance HEAD escalates the missing academic
producer instead of claiming another source-free completion. Records survive
ChatGPT session endings and normal worker restarts on Yoga6.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_post_v35_semantic_task_dispatch import (
    _V36, _STATUS36,
)
from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA, _CANDIDATE_SHA,
)

_SHA40 = re.compile(r"[0-9a-f]{40}\Z")
_SHA64 = re.compile(r"[0-9a-f]{64}\Z")
_NAME = "BOSLA_HORIZON_STATE.json"
_EVENT = "BOSLA_EXACT_HEAD_LONG_HORIZON_EVENT.json"
_CONTRACT = "BOSLA_LONG_HORIZON_DEVELOPMENT_V1"
_NEXT = "IMPLEMENT_SEPARATE_INDEPENDENT_SOURCE_BOUND_ACADEMIC_PROOF_PRODUCER"


def _hash(body: dict) -> str:
    return sha256(json.dumps(body,ensure_ascii=False,sort_keys=True,
        separators=(",",":")).encode("utf8")).hexdigest()


def _read_signed(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size>16000:
        raise ValueError("BSA269_LONG_HORIZON_MISSING_OR_UNSAFE_STATE")
    try:
        state=json.loads(path.read_text(encoding="utf8"))
    except (OSError,ValueError) as exc:
        raise ValueError("BSA269_LONG_HORIZON_MALFORMED_STATE") from exc
    if (not isinstance(state,dict)
        or state.get("integritySha256")!=_hash({
            k:v for k,v in state.items() if k!="integritySha256"})):
        raise ValueError("BSA269_LONG_HORIZON_STATE_INTEGRITY")
    return state


def _write_latest(path: Path, body: dict) -> dict:
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError("BSA269_LONG_HORIZON_SYMLINK")
    stamped={**body,"integritySha256":_hash(body)}
    fd,tmp=tempfile.mkstemp(prefix=".bosla-horizon-",suffix=".tmp",
                             dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf8") as out:
            json.dump(stamped,out,sort_keys=True,indent=2)
            out.write("\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp,path)
    finally:
        Path(tmp).unlink(missing_ok=True)
    return stamped


def persist_long_horizon_development(
    *,private:Path,ready:dict[str,Any],
    development:dict[str,Any],
)->dict[str,Any]:
    """Persist one head's verified engineering-only frontier, idempotently.

    This does NOT schedule an agent, authorize a paid provider request or
    turn review-required academic tasks into ACCEPTED tasks.
    """
    head=ready.get("gitHead")
    proposal=ready.get("proposalSha256")
    if (not isinstance(head,str) or not _SHA40.fullmatch(head)
        or not isinstance(proposal,str) or not _SHA64.fullmatch(proposal)):
        raise ValueError("BSA269_INVALID_EXACT_SOURCE_VERSION")
    if (development.get("developmentOutcomeClass")!=
            "ENGINEERING_VERIFIED_NOT_ACADEMIC_ACCEPTANCE"
        or development.get("academicProofTasksAcceptedThisRun")!=0
        or development.get("academicAcceptanceAdvanced") is not False
        or development.get("academicProofProducerRequired") is not True
        or development.get("engineeringOnlyFrontierTerminal") is not True
        or development.get("academicPASS")!=0
        or development.get("publicationAuthorized") is not False
        or development.get("newModelCalls")!=0):
        raise ValueError("BSA269_FALSE_ACADEMIC_PROGRESS_MUST_NOT_PERSIST")
    folder=private/"owner-five-stage-completion"/head/proposal
    signed=_signed(folder,_V36,ready)
    if (signed!=development.get("privateSemanticTaskDispatch")
        or signed.get("status")!=_STATUS36
        or signed.get("sourceSha256")!=_SOURCE_SHA
        or signed.get("revisedCandidateSha256")!=_CANDIDATE_SHA
        or signed.get("semanticTasksAutomaticallyDispatched")!=429
        or signed.get("activitySignedPartitionCount")!=18
        or signed.get("fullAcademicProofTasksAccepted")!=0
        or signed.get("fullAcademicProofTasksStillOpen")!=429
        or signed.get("completeAcademicProofGatesStillOpen")!=90
        or signed.get("fullAcademicPASS")!=0
        or signed.get("publicationAuthorized") is not False):
        raise ValueError("BSA269_SIGNED_SOURCE_V36_REQUIRED")
    root=private/"long-horizon-development"
    if (private.is_symlink() or root.is_symlink()
        or folder.is_symlink()):
        raise ValueError("BSA269_LONG_HORIZON_UNTRUSTED_ROOT")
    root.mkdir(parents=True,exist_ok=True)
    latest_file=root/_NAME
    old=_read_signed(latest_file) if latest_file.exists() else None
    if old is not None and (
        old.get("contract")!=_CONTRACT
        or old.get("sourceSha256")!=_SOURCE_SHA
        or old.get("candidateSha256")!=_CANDIDATE_SHA
        or old.get("academicAcceptedProofTaskCount")!=0
        or old.get("completeAcademicProofGatesStillOpen")!=90
        or old.get("fullSemanticProofTasksStillOpen")!=429
        or old.get("publicationAuthorized") is not False
        or type(old.get("consecutiveZeroProofCodeHeads")) is not int
        or old["consecutiveZeroProofCodeHeads"]<1):
        raise ValueError("BSA269_LONG_HORIZON_UNTRUSTED_PREDECESSOR")
    # Same exact revision is an idempotent readback, not a new cycle.
    same=bool(old and old["gitHead"]==head
              and old["proposalSha256"]==proposal)
    count=(old["consecutiveZeroProofCodeHeads"]
           if same else
           (old["consecutiveZeroProofCodeHeads"]+1 if old else 1))
    predecessor=(old.get("predecessorEventSha256")
                 if same else
                 (old["currentEventSha256"] if old else None))
    event_body={
        "contract":_CONTRACT,
        "gitHead":head,
        "proposalSha256":proposal,
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "signedV36ReceiptSha256":signed["integritySha256"],
        "academicAcceptedProofTaskCount":0,
        "fullSemanticProofTasksStillOpen":429,
        "completeAcademicProofGatesStillOpen":90,
        "engineeringStagesVerified":development["stagesExecutedThisRun"],
        "developmentOutcomeClass":"ENGINEERING_VERIFIED_NOT_ACADEMIC_ACCEPTANCE",
        "consecutiveZeroProofCodeHeads":count,
        "architecturalProofProducerEscalationRequired":True,
        "nextUnfinishedDevelopmentAction":_NEXT,
        "nextActionStatus":"NOT_IMPLEMENTED_NOT_AUTOMATICALLY_EXECUTABLE",
        "sourceFreeRecoveryMayContinue":True,
        "academicProofProviderRequestAuthorizedHere":False,
        "unboundedCodeWritingAgentConfiguredHere":False,
        "publicReleaseAuthorized":False,
        "publicationAuthorized":False,
        "predecessorEventSha256":predecessor,
    }
    event_dir=root/head/proposal
    if event_dir.is_symlink():
        raise ValueError("BSA269_LONG_HORIZON_EVENT_SYMLINK")
    event_dir.mkdir(parents=True,exist_ok=True)
    receipt=_v6_checkpoint(event_dir/_EVENT,event_body)
    if old is not None and same:
        if old.get("currentEventSha256")!=receipt["integritySha256"]:
            raise ValueError("BSA269_SAME_HEAD_HISTORY_MISMATCH")
        return old
    state_body={
        **event_body,
        "currentEventSha256":receipt["integritySha256"],
    }
    return _write_latest(latest_file,state_body)


def read_long_horizon_development(private:Path)->dict[str,Any]:
    """Read latest cross-session checkpoint; never invent pending success."""
    root=private/"long-horizon-development"
    state=_read_signed(root/_NAME)
    if (state.get("contract")!=_CONTRACT
        or not _SHA40.fullmatch(str(state.get("gitHead")))
        or not _SHA64.fullmatch(str(state.get("proposalSha256")))):
        raise ValueError("BSA269_LONG_HORIZON_VERSION_MISMATCH")
    receipt=_read_signed(root/state["gitHead"]/
                       state["proposalSha256"]/_EVENT)
    if (receipt.get("integritySha256")!=state.get("currentEventSha256")
        or {k:v for k,v in state.items() if k not in
            {"integritySha256","currentEventSha256"}} !=
           {k:v for k,v in receipt.items() if k!="integritySha256"}):
        raise ValueError("BSA269_LONG_HORIZON_EVENT_MISMATCH")
    return state

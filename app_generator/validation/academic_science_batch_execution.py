"""BSA275: finite academic science proof batches, never implicit acceptance.

A BSA274 original-source/immutable-V36 registry audit is an authoritative
*worklist*, not proof that a pending scientific statement is true or false.
This generic engine dispatches only explicitly vetted per-task science
verifiers, quarantines one bounded failure while continuing independent
eligible work, and refuses to count a new academic PASS without a separate
immutable admission receipt and independent cross-revision readback.

No source PDF is transferred, no provider request or public release occurs.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Any, Callable

_SHA64 = re.compile(r"[0-9a-f]{64}\Z")
_BATCH_CONTRACT="BOSLA_BSA275_BOUNDED_MC_Q_SCIENCE_BATCH_V1"
_AUDIT_CONTRACT="BOSLA_SOURCE_BOUND_ACADEMIC_PROOF_REGISTRY_V1"
_ACCEPTED="INDEPENDENTLY_REVERIFIED_ACADEMIC_TASK"
_PENDING="REVIEW_REQUIRED"


def _digest(obj: Any) -> str:
    return sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False,
            separators=(",",":")).encode("utf8")).hexdigest()


def _valid_sha(value: Any) -> bool:
    return isinstance(value,str) and bool(_SHA64.fullmatch(value))


@dataclass(frozen=True)
class ScienceBatchRule:
    task_id: str
    verify_proposition: Callable[[], dict[str,Any]]


def plan_next_science_batch(*, audit: dict[str,Any],
                            cursor: int=0, maximum: int=4)->dict[str,Any]:
    """Use an independently recomputed registry audit, never a bare task list.

    The claimed audit is inspected strictly; actual owner binding still
    belongs to the caller, which must invoke sourcebound registry readback
    before accepting its output.
    """
    if (not isinstance(audit,dict)
        or audit.get("contract")!=_AUDIT_CONTRACT
        or audit.get("status")!=
        "BSA274_INDEPENDENT_PROOF_REGISTRY_VERIFIED_NOT_FULL_ACADEMIC_PASS"
        or not _valid_sha(audit.get("sourceSha256"))
        or not _valid_sha(audit.get("candidateSha256"))
        or not _valid_sha(audit.get("signedV36Sha256"))
        or audit.get("completeAcademicProofGatesStillOpen")!=90
        or audit.get("fullAcademicActivityPASS")!=0
        or audit.get("newProviderCalls")!=0
        or audit.get("publicationAuthorized") is not False
        or audit.get("acceptedMcqDistractorTaskCount")!=2
        or audit.get("pendingMcqDistractorTaskCount")!=25
        or audit.get("fullAcademicTasksStillOpen")!=427
        or type(cursor) is not int or cursor<0
        or type(maximum) is not int or maximum<1 or maximum>6):
        raise ValueError("BSA275_UNTRUSTED_OR_UNBOUNDED_ACADEMIC_BATCH_INPUT")
    pending=audit.get("pendingMcqTasks")
    accepted=audit.get("acceptedAcademicTaskIds")
    if (not isinstance(pending,list) or len(pending)!=25
        or not isinstance(accepted,list) or len(accepted)!=2
        or len(set(accepted))!=2
        or any(not _valid_sha(t) for t in accepted)
        or len({t.get("taskId") for t in pending if isinstance(t,dict)})!=25):
        raise ValueError("BSA275_INVALID_27_DISTRACTOR_TASK_PARTITION")
    for task in pending:
        if (not isinstance(task,dict)
            or task.get("status")!=_PENDING
            or not _valid_sha(task.get("taskId"))
            or not _valid_sha(task.get("surfaceSha256"))
            or not isinstance(task.get("activityId"),str)
            or not task["activityId"]
            or task["taskId"] in accepted):
            raise ValueError("BSA275_FAKED_ACADEMIC_TASK_ACCEPTANCE")
    if cursor>len(pending):
        raise ValueError("BSA275_BATCH_CURSOR_OUT_OF_RANGE")
    selected=pending[cursor:cursor+maximum]
    next_cursor=cursor+len(selected)
    return {
        "contract":_BATCH_CONTRACT,
        "status":"BSA275_BOUNDED_INDEPENDENT_SCIENCE_VERIFICATION_TASKS_PREPARED",
        "gitHead":audit["gitHead"],
        "proposalSha256":audit["proposalSha256"],
        "sourceSha256":audit["sourceSha256"],
        "candidateSha256":audit["candidateSha256"],
        "signedV36Sha256":audit["signedV36Sha256"],
        "academicProofRegistrySha256":_digest(audit),
        "taskCount":len(selected),
        "cursor":cursor,
        "nextCursor":next_cursor,
        "remainingAfterBatch":len(pending)-next_cursor,
        "taskIds":[x["taskId"] for x in selected],
        "tasks":selected,
        "acceptedAcademicTasksBeforeBatch":2,
        "academicTasksAcceptedByBatch":0,
        "completeAcademicProofGatesStillOpen":90,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    }


def execute_source_bound_science_batch(
    *, batch:dict[str,Any], rules:tuple[ScienceBatchRule,...],
)->dict[str,Any]:
    """Run vetted science proof implementations, NOT academic admission.

    Even a valid new countermodel remains NOT_ADMITTED until the separate
    owner source-pinned immutable admission/readback succeeds. A fault in one
    proof is quarantined and later eligible tasks continue without replaying
    ambiguous provider actions (there are no providers in this engine).
    """
    if (batch.get("contract")!=_BATCH_CONTRACT
        or batch.get("status")!=
           "BSA275_BOUNDED_INDEPENDENT_SCIENCE_VERIFICATION_TASKS_PREPARED"
        or batch.get("academicTasksAcceptedByBatch")!=0
        or batch.get("completeAcademicProofGatesStillOpen")!=90
        or batch.get("publicationAuthorized") is not False
        or batch.get("taskIds")!=[x["taskId"] for x in batch.get("tasks",[])]
        or len(batch.get("taskIds",[]))>6
        or len(set(batch.get("taskIds",[])))!=len(batch.get("taskIds",[]))):
        raise ValueError("BSA275_BATCH_SCOPE_OR_ACCEPTANCE_FORGED")
    known={}
    for rule in rules:
        if (not isinstance(rule,ScienceBatchRule)
            or not _valid_sha(rule.task_id)
            or rule.task_id in known
            or not callable(rule.verify_proposition)):
            raise ValueError("BSA275_DUPLICATE_OR_UNTRUSTED_SCIENCE_HANDLER")
        known[rule.task_id]=rule.verify_proposition
    results=[]
    for task in batch["tasks"]:
        tid=task["taskId"]
        if tid not in known:
            results.append({"taskId":tid,
                "status":"NOT_ELIGIBLE_UNIMPLEMENTED_INDEPENDENT_PROOF_HANDLER",
                "academicAccepted":False})
            continue
        try:
            verified=known[tid]()
            if (not isinstance(verified,dict)
                or verified.get("taskId")!=tid
                or verified.get("sourceSha256")!=batch["sourceSha256"]
                or verified.get("candidateSha256")!=batch["candidateSha256"]
                or verified.get("surfaceSha256")!=task["surfaceSha256"]
                or verified.get("independentScienceWitnessVerified") is not True
                or not _valid_sha(verified.get("witnessSha256"))
                or verified.get("newProviderCalls")!=0
                or verified.get("publicationAuthorized") is not False):
                raise ValueError("BSA275_PROOF_WITNESS_DID_NOT_REVERIFY")
            results.append({"taskId":tid,
                "status":"SOURCE_BOUND_WITNESS_VERIFIED_NOT_ACADEMICALLY_ADMITTED",
                "witnessSha256":verified["witnessSha256"],
                "academicAccepted":False})
        except (ValueError,KeyError,TypeError,IndexError,ArithmeticError):
            results.append({"taskId":tid,
                "status":"QUARANTINED_INDEPENDENT_SCIENCE_PROOF_FAILURE",
                "academicAccepted":False})
    return {
        "contract":_BATCH_CONTRACT,
        "status":"BSA275_BOUNDED_PROOF_HANDLERS_DISPATCHED_NOT_ADMITTED",
        "gitHead":batch["gitHead"],
        "sourceSha256":batch["sourceSha256"],
        "candidateSha256":batch["candidateSha256"],
        "signedV36Sha256":batch["signedV36Sha256"],
        "taskCount":len(results),
        "results":results,
        "verifiedWitnessCount":sum(
            x["status"]=="SOURCE_BOUND_WITNESS_VERIFIED_NOT_ACADEMICALLY_ADMITTED"
            for x in results),
        "quarantinedCount":sum(x["status"]==
            "QUARANTINED_INDEPENDENT_SCIENCE_PROOF_FAILURE" for x in results),
        "academicTasksAcceptedByBatch":0,
        "completeAcademicProofGatesStillOpen":90,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    }

"""BSA285: independent scientific acceptance stagnation detector.

Only an independently verified original-source owner horizon command with
exit code zero may supply the report. Log bytes, CI, model output, and test
passes are never themselves academic acceptances.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import re

TOTAL=429
MAX_GATES=90
STALL_SECONDS=60*60
SHA_RE=re.compile(r"^[0-9a-f]{64}$")


def _instant(value: str) -> datetime:
    try:
        result=datetime.fromisoformat(value)
    except (ValueError, TypeError) as exc:
        raise ValueError("BSA285_INVALID_PROGRESS_CLOCK") from exc
    if result.tzinfo is None:
        raise ValueError("BSA285_PROGRESS_CLOCK_MUST_BE_UTC_AWARE")
    return result.astimezone(timezone.utc)


def observe_signed_horizon(state: dict, log_text: str, *, head: str,
                           now: str, cycle: int) -> dict:
    """Read an independent successfully exited source verifier's JSON output.

    Caller MUST check source-bound CLI child exit=0 and exact current head.
    Independently accepted receipts are verified by that command, not here.
    """
    lines=[line for line in log_text.splitlines() if line.strip()]
    if len(lines)!=1:
        raise ValueError("BSA285_INDEPENDENT_HORIZON_NOT_SINGLE_JSON")
    try:
        report=json.loads(lines[0])
    except (TypeError,ValueError) as exc:
        raise ValueError("BSA285_INDEPENDENT_HORIZON_INVALID_JSON") from exc
    if not isinstance(report,dict):
        raise ValueError("BSA285_INDEPENDENT_HORIZON_NOT_OBJECT")
    accepted=report.get("academicProofTasksAccepted")
    remaining=report.get("fullAcademicProofTasksStillOpen")
    if (report.get("gitHead")!=head
        or not isinstance(accepted,int) or isinstance(accepted,bool)
        or not (0<=accepted<=TOTAL)
        or remaining!=TOTAL-accepted
        or report.get("completeAcademicProofGatesStillOpen")!=MAX_GATES
        or report.get("publicationAuthorized") is not False
        or report.get("acceptedProofCarriedAcrossGitHead") is not True
        or "SOURCE_BOUND" not in str(report.get("academicAcceptancesSource",""))
        or not str(report.get("status","")).endswith("_REVERIFIED")
        or not SHA_RE.fullmatch(str(report.get("academicProofReceiptSha256","")))):
        raise ValueError("BSA285_HORIZON_NOT_INDEPENDENT_SIGNED_SCIENCE")
    _instant(now)
    old=state.get("scienceAcceptance")
    if isinstance(old,dict):
        prior=old.get("acceptedCount")
        if not isinstance(prior,int) or accepted<prior:
            raise ValueError("BSA285_SIGNED_ACADEMIC_COUNT_ROLLBACK")
        improved=accepted>prior
        prev_head=old.get("lastVerifiedHead")
        no_gain=0 if improved else int(old.get("noGainOwnerHeads",0))+(head!=prev_head)
        last_advance=now if improved else old.get("lastIncreaseAt",now)
    else:
        improved=False
        no_gain=0
        last_advance=now
    entry={
        "acceptedCount":accepted,
        "pendingCount":TOTAL-accepted,
        "lastIncreaseAt":last_advance,
        "lastVerifiedAt":now,
        "lastVerifiedHead":head,
        "noGainOwnerHeads":no_gain,
        "lastVerifiedCycle":cycle,
        "independentReceiptSha256":sha256(lines[0].encode("utf8")).hexdigest(),
        "evidence":"INDEPENDENT_SOURCE_BOUND_SIGNED_HORIZON_EXIT_ZERO",
        "advancedThisObservation":improved,
    }
    state["scienceAcceptance"]=entry
    if improved:
        state.pop("scienceStall",None)
    return entry


def investigate_zero_academic_gain(state: dict, *, now: str, cycle: int,
                                   threshold_seconds: int=STALL_SECONDS) -> dict:
    """Separate elapsed scholarly progress from log/heartbeat throughput.

    Repeated ticks at the same head do not count as additional proof attempts.
    A stall creates a repair priority; it never revokes signed prior proofs.
    """
    previous=state.get("scienceAcceptance")
    if not isinstance(previous,dict):
        return {"triggered":False,"reason":"WAIT_INDEPENDENT_SIGNED_BASELINE"}
    count=previous.get("acceptedCount")
    if not isinstance(count,int) or not 0<=count<=TOTAL:
        raise ValueError("BSA285_PROGRESS_BASELINE_UNTRUSTED")
    elapsed=(_instant(now)-_instant(previous["lastIncreaseAt"])).total_seconds()
    if elapsed < -1:
        raise ValueError("BSA285_SCIENCE_PROGRESS_CLOCK_ROLLBACK")
    no_gain=int(previous.get("noGainOwnerHeads",0))
    cycles=max(0,int(cycle)-int(previous["lastVerifiedCycle"]))
    triggered=(no_gain>=2 or (elapsed>=threshold_seconds and cycles>=1))
    if not triggered:
        return {"triggered":False,"acceptedCount":count,
                "noGainOwnerHeads":no_gain,"secondsSinceIncrease":int(elapsed)}
    failure=state.get("failedTest")
    if failure=="CONTRACT":
        code="KNOWN_RECURRENCE_REGISTRY_CONTRACT_REPAIR"
    elif state.get("pendingBranch"):
        code="AWAIT_VERIFIED_PATCH_CI_WITH_ACCEPTANCE_MONITORING"
    else:
        code="INDEPENDENT_PROOF_PRODUCER_AND_SIGNED_ADMISSION_GAP"
    return {"triggered":True,
            "status":"BSA285_ZERO_NEW_SCIENTIFIC_ACCEPTANCE_INVESTIGATION",
            "classification":code,
            "acceptedCount":count,"pendingCount":TOTAL-count,
            "noGainOwnerHeads":no_gain,"secondsSinceIncrease":int(elapsed),
            "nextAction":"HISTORICAL_REVIEW_TARGETED_REPAIR_REAL_SOURCE_TEST_FAULT_INJECTION_REGISTRY_CI_OWNER_RESTART",
            "academicPASS":False,
            "publicationAuthorized":False}

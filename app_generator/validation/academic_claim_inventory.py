"""Read-only, source/package-bound inventory of immutable academic reviewer claims.

A captured response or consensus is NEVER an academic PASS. This module
does not open browsers, read source quotes, resubmit requests or publish.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
from typing import Any

from app_generator.validation.academic_qa import REQUIRED

_CLAIM_NAME = re.compile(r"^[A-Za-z0-9-]+$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED = frozenset({"COMPLETE", "AMBIGUOUS", "IN_FLIGHT", "SKIPPED_UNSENT"})
_CODES = frozenset({
    "UNPARSEABLE_BOUNDED_JSON", "WRONG_JSON_FIELD_SET", "MISMATCHED_GATE_OR_VERDICT",
    "MISMATCHED_GATE", "INVALID_VERDICT", "RATIONALE_TOO_SHORT",
    "ISSUE_NOT_STRING", "SOURCE_PAGE_NOT_AUTHORIZED",
    "SUPPORTED_WITHOUT_SOURCE_PAGE", "CONTRADICTION_WITHOUT_ISSUE",
    "UNKNOWN_RESPONSE_VALIDATION_FAILURE", "MODEL_RESPONSE_NOT_CAPTURED",
    "UNCAPTURED_ROLE_CIRCUIT_OPEN",
})


def audit_immutable_claims(
    claims_dir: Path, *, claim_prefix: str, activity_id: str,
    activity_sha256: str, package_sha256: str, source_sha256: str,
    source_context_sha256: str, gates: tuple[str, ...] = REQUIRED,
) -> dict[str, Any]:
    """Verify stable claim identity and report metadata, not model text.

    MISSING is a real gap, not a remote submission. Previously submitted
    IN_FLIGHT and AMBIGUOUS records must never be replayed.
    """
    if not isinstance(claim_prefix, str) or not _CLAIM_NAME.fullmatch(claim_prefix):
        raise ValueError("invalid safe claim prefix")
    if not isinstance(activity_id, str) or not activity_id.strip():
        raise ValueError("stable activity ID required")
    hashes=(activity_sha256,package_sha256,source_sha256,source_context_sha256)
    if any(not isinstance(h,str) or not _SHA.fullmatch(h) for h in hashes):
        raise ValueError("exact canonical claim-bound SHA-256 values required")
    if not isinstance(gates,tuple) or not gates or any(g not in REQUIRED for g in gates) or len(set(gates))!=len(gates):
        raise ValueError("invalid academic gate set")
    root=claims_dir.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("immutable claim directory required")
    entries=[]
    for gate in gates:
        for role in (0,1):
            name=f"{claim_prefix}-{gate.replace('_','-')}-{role}.json"
            path=claims_dir/name
            if not path.exists():
                entries.append({"gate":gate,"roleIndex":role,"state":"MISSING",
                                "responseCaptured":False,"reasonCode":None})
                continue
            if path.is_symlink() or not path.is_file() or path.resolve().parent!=root:
                raise ValueError("immutable claim path is not an owned file")
            record=json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(record,dict):
                raise ValueError("invalid immutable claim record")
            expected={
                "activityId":activity_id,"activityHash":activity_sha256,
                "packageHash":package_sha256,"sourceHash":source_sha256,
                "sourceContextHash":source_context_sha256,
                "roleIndex":role,"gate":gate,
            }
            if any(record.get(k)!=v or type(record.get(k)) is not type(v) for k,v in expected.items()):
                raise ValueError("stale or mismatched immutable claim identity")
            prompt=record.get("promptHash")
            if not isinstance(prompt,str) or not _SHA.fullmatch(prompt):
                raise ValueError("missing immutable prompt SHA-256")
            state=record.get("state")
            if state not in _ALLOWED:
                raise ValueError("unknown immutable claim lifecycle state")
            captured=record.get("responseCaptured")
            code=record.get("reasonCode")
            if state=="COMPLETE":
                if captured is not True or not isinstance(record.get("decision"),dict):
                    raise ValueError("complete claim lacks captured decision")
                if not isinstance(record.get("responseSha256"),str) or not _SHA.fullmatch(record["responseSha256"]):
                    raise ValueError("complete claim lacks captured response digest")
                if code is not None:
                    raise ValueError("complete claim unexpectedly has failure code")
            elif state=="AMBIGUOUS":
                if type(captured) is not bool or code not in _CODES or code=="UNCAPTURED_ROLE_CIRCUIT_OPEN":
                    raise ValueError("ambiguous claim lacks bounded failure evidence")
                digest=record.get("responseSha256")
                if captured and (not isinstance(digest,str) or not _SHA.fullmatch(digest)):
                    raise ValueError("captured ambiguous claim lacks response SHA-256")
                if not captured and digest is not None:
                    raise ValueError("uncaptured response cannot have response SHA-256")
                if code=="MODEL_RESPONSE_NOT_CAPTURED" and captured:
                    raise ValueError("uncaptured reason conflicts with captured response")
            elif state=="SKIPPED_UNSENT":
                if (record.get("requestSubmitted") is not False or captured is not False or
                        record.get("responseSha256") is not None or
                        code!="UNCAPTURED_ROLE_CIRCUIT_OPEN"):
                    raise ValueError("unsent claim cannot imply a submitted model request")
            else:  # IN_FLIGHT may already have been submitted; never retry.
                if record.get("requestSubmitted") is False:
                    raise ValueError("in-flight request cannot be proven unsent")
                code=None
                captured=False
            entries.append({"gate":gate,"roleIndex":role,"state":state,
                            "responseCaptured":bool(captured),"reasonCode":code})
    counts=dict(Counter(x["state"] for x in entries))
    reasons=dict(Counter(x["reasonCode"] for x in entries if x["reasonCode"]))
    return {
        "activityId":activity_id,"packageSha256":package_sha256,
        "sourceSha256":source_sha256,"activitySha256":activity_sha256,
        "sourceContextSha256":source_context_sha256,
        "claimCount":len(entries),"stateCounts":counts,"reasonCounts":reasons,
        "gateRoleStates":entries,
        "allClaimRolesComplete":all(x["state"]=="COMPLETE" for x in entries),
        "allAcademicGatesProven":False,"academicQA":"REVIEW_REQUIRED",
        "humanAcademicApprovalRequired":False,"publicationAuthorized":False,
        "modelRequestsMadeByAudit":0,
    }

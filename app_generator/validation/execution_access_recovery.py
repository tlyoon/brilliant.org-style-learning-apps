"""Source-free, NON-EXECUTING recovery planner for authorized development tasks.

This module never invokes a command, browser, model or network. It does not
change permissions. An explicit external denial is terminal in this checkpoint.
A completion event records a trusted upstream verifier's receipt digest; this
module does NOT independently establish the scientific truth of that receipt.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import re
from typing import Any

VERSION = 1
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
EVENT_ID = re.compile(r"[A-Za-z0-9_-]{8,64}\Z")
DENIAL_CLASSES = frozenset({
    "SECURITY_CONTROL", "PERMISSION_DENIED", "CONNECTOR_UNAVAILABLE",
    "AUTHORIZATION_REQUIRED", "EXECUTION_SCOPE_UNAVAILABLE",
})
TOOL_CLASSES = frozenset({
    "REMOTE_DESKTOP", "GITHUB_CONNECTOR", "PRIVATE_RUNNER", "OTHER",
})

# Canonical task IDs: a denied action cannot be resumed under an invented alias.
# These are logical QA operations, not commands or permission grants.
TASK_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "source_verify": (),
    "mcq_model_verify": ("source_verify",),
    "collision_model_verify": ("source_verify",),
    "visual_receipt_verify": ("source_verify",),
    "review_claim_reconcile": ("source_verify",),
    # The inventory accepts missing supporting categories explicitly and can
    # therefore run while visual or reviewer checking is externally blocked.
    "partial_evidence_inventory": ("source_verify",),
    "science_meaning_verify": ("source_verify",),
    "multilingual_meaning_verify": ("source_verify",),
    "diagram_semantics_verify": ("source_verify",),
    # Pilot cannot be certified merely because the inventory was produced.
    "pilot_acceptance": (
        "mcq_model_verify", "collision_model_verify", "visual_receipt_verify",
        "review_claim_reconcile", "science_meaning_verify",
        "multilingual_meaning_verify", "diagram_semantics_verify",
    ),
}


def _sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise ValueError(f"{field}: lowercase 64-character digest required")
    return value


def _canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("ascii")


def _digest(value: Any) -> str:
    return sha256(_canon(value)).hexdigest()


def operation_fingerprint(source_sha: str, package_sha: str, task_id: str) -> str:
    """Stable operation identity: exact source+package+approved task intention."""
    _sha(source_sha, "sourceSha256")
    _sha(package_sha, "packageSha256")
    if task_id not in TASK_DEPENDENCIES:
        raise ValueError("unknown canonical task ID")
    return _digest({"version": VERSION, "sourceSha256": source_sha,
                    "packageSha256": package_sha, "taskId": task_id})


def new_checkpoint(source_sha: str, package_sha: str) -> dict[str, Any]:
    _sha(source_sha, "sourceSha256")
    _sha(package_sha, "packageSha256")
    return {"schemaVersion": VERSION, "sourceSha256": source_sha,
            "packageSha256": package_sha, "events": []}


def _initial_chain(state: dict[str, Any]) -> str:
    return _digest({k: state[k] for k in ("schemaVersion", "sourceSha256", "packageSha256")})


def _parse(state: dict[str, Any]) -> tuple[dict[str, str], str, set[str]]:
    """Validate exact schema, chain integrity, outcomes and prerequisites."""
    if not isinstance(state, dict) or set(state) != {
        "schemaVersion", "sourceSha256", "packageSha256", "events"
    } or type(state.get("schemaVersion")) is not int or state["schemaVersion"] != VERSION:
        raise ValueError("unsupported, extra-field or malformed checkpoint")
    source = _sha(state["sourceSha256"], "sourceSha256")
    package = _sha(state["packageSha256"], "packageSha256")
    events = state["events"]
    if not isinstance(events, list) or len(events) > len(TASK_DEPENDENCIES):
        raise ValueError("invalid event roster")
    status = {task: "PENDING" for task in TASK_DEPENDENCIES}
    previous = _initial_chain(state)
    seen: set[str] = set()
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("invalid event")
        task = event.get("taskId")
        outcome = event.get("outcome")
        event_id = event.get("eventId")
        if (task not in TASK_DEPENDENCIES or status[task] != "PENDING" or
                outcome not in ("RECEIPT_RECORDED", "BLOCKED_EXTERNAL") or
                not isinstance(event_id, str) or not EVENT_ID.fullmatch(event_id) or
                event_id in seen):
            raise ValueError("unknown, repeated, or terminal task event")
        seen.add(event_id)
        if event.get("operationFingerprint") != operation_fingerprint(source, package, task):
            raise ValueError("operation fingerprint changed")
        if outcome == "RECEIPT_RECORDED":
            expected_fields = {"taskId", "outcome", "eventId", "operationFingerprint",
                               "receiptSha256", "previousChainSha256", "chainSha256"}
            _sha(event.get("receiptSha256"), "receiptSha256")
            if any(status[dep] != "RECEIPT_RECORDED" for dep in TASK_DEPENDENCIES[task]):
                raise ValueError("cannot mark prerequisite-dependent task complete")
        else:
            expected_fields = {"taskId", "outcome", "eventId", "operationFingerprint",
                               "denialClass", "toolClass", "previousChainSha256", "chainSha256"}
            if (event.get("denialClass") not in DENIAL_CLASSES or
                    event.get("toolClass") not in TOOL_CLASSES):
                raise ValueError("unsupported denial or tool classification")
        if set(event) != expected_fields:
            raise ValueError("unrecognized private/command fields in execution record")
        if event.get("previousChainSha256") != previous:
            raise ValueError("event chain has been altered or reordered")
        bare = {k: v for k, v in event.items() if k != "chainSha256"}
        actual = _digest(bare)
        if event.get("chainSha256") != actual:
            raise ValueError("event checksum invalid")
        previous = actual
        status[task] = outcome
    return status, previous, seen


def add_event(state: dict[str, Any], *, task_id: str, event_id: str,
              outcome: str, receipt_sha256: str | None = None,
              denial_class: str | None = None, tool_class: str | None = None) -> dict[str, Any]:
    """Append only a recorded fact; never execute or retry an operation."""
    status, previous, seen = _parse(state)
    if task_id not in TASK_DEPENDENCIES or status[task_id] != "PENDING":
        raise ValueError("unknown or already attempted canonical operation")
    if not isinstance(event_id, str) or not EVENT_ID.fullmatch(event_id) or event_id in seen:
        raise ValueError("event ID invalid or already used")
    if outcome not in ("RECEIPT_RECORDED", "BLOCKED_EXTERNAL"):
        raise ValueError("unsupported event outcome")
    event = {"taskId": task_id, "eventId": event_id,
             "outcome": outcome,
             "operationFingerprint": operation_fingerprint(
                 state["sourceSha256"], state["packageSha256"], task_id),
             "previousChainSha256": previous}
    if outcome == "RECEIPT_RECORDED":
        if any(status[dep] != "RECEIPT_RECORDED" for dep in TASK_DEPENDENCIES[task_id]):
            raise ValueError("dependencies do not have independent receipts")
        if denial_class is not None or tool_class is not None:
            raise ValueError("a success receipt cannot include denial data")
        event["receiptSha256"] = _sha(receipt_sha256, "receiptSha256")
    else:
        if receipt_sha256 is not None:
            raise ValueError("a denied action cannot be marked successful")
        if denial_class not in DENIAL_CLASSES or tool_class not in TOOL_CLASSES:
            raise ValueError("unsupported denial category")
        event["denialClass"] = denial_class
        event["toolClass"] = tool_class
    event["chainSha256"] = _digest(event)
    updated = deepcopy(state)
    updated["events"].append(event)
    _parse(updated)
    return updated


def _blocked_ancestor(task_id: str, status: dict[str, str]) -> bool:
    return any(status[dep] == "BLOCKED_EXTERNAL" or _blocked_ancestor(dep, status)
               for dep in TASK_DEPENDENCIES[task_id])


def safe_plan(state: dict[str, Any]) -> dict[str, Any]:
    """Read-only scheduler recommendation, not authorization to execute."""
    status, digest, _seen = _parse(state)
    ready, waiting, denied, recorded = [], [], [], []
    for task_id, dependencies in TASK_DEPENDENCIES.items():
        current = status[task_id]
        if current == "BLOCKED_EXTERNAL":
            denied.append({"taskId": task_id,
                           "operationFingerprint": operation_fingerprint(
                               state["sourceSha256"], state["packageSha256"], task_id),
                           "retryAllowedByThisPlan": False})
        elif current == "RECEIPT_RECORDED":
            recorded.append(task_id)
        elif all(status[dep] == "RECEIPT_RECORDED" for dep in dependencies):
            ready.append(task_id)
        else:
            waiting.append({"taskId": task_id,
                            "hasDeniedDependency": _blocked_ancestor(task_id, status)})
    return {"status": "NON_EXECUTING_RECOVERY_PLAN",
            "readyForSeparateAuthorizationCheck": ready,
            "blockedExternal": denied, "waitingForDependencies": waiting,
            "receiptRecordedTasks": recorded,
            "eventChainHead": digest,
            "externalAuthorizationGranted": False,
            "automaticallyRetriesDeniedOperations": False,
            "scientificApproval": False, "publicationAuthorized": False}

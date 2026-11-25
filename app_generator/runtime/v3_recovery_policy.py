"""BOSLA V3 source-free executable recovery registry + durable decision receipt.

Incident metadata is DATA, never executed. Only hardcoded reviewed Python
handlers can run. Unknown and retired fixes are classified and recorded;
unrelated course sections may continue under the existing authorized gate.
Never stores user texts, Gemini replies, credentials or publish permission.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from app_generator.runtime.v3_auto_repair import stage_known_language_repair
from app_generator.runtime.v3_repair_review_handoff import (
    stage_changed_activity_review_handoff,
)
from app_generator.runtime.v3_isolated_repair_review import (
    stage_isolated_review_slice,
)
from app_generator.runtime.v3_versioned_acceptance_scope import (
    prepare_versioned_course_proposal,
)

_DECISION_NAME = "v3-recovery-policy-state.json"
_SCHEMA = 1
_EXPECTED = {
    "BSA-20261116-173": "app_generator/validation/v3_locale_script_integrity.py",
    "BSA-20261116-174": "app_generator/runtime/v3_auto_repair.py",
    "BSA-20261116-175": "app_generator/validation/v3_versioned_text_repair.py",
    "BSA-20261116-176": "app_generator/runtime/v3_auto_repair.py",
}
_REMEDY = "BSA-20261116-174"
_TRIGGER = "BSA-20261116-173"
_ALLOWED_OUTCOMES = frozenset((
    "NO_SCRIPT_BLOCKER",
    "NO_MATCHING_SCRIPT_REPAIR",
    "STOP_UNKNOWN_SCRIPT_SIGNATURE",
    "STOP_REGISTERED_REMEDY_RETIRED",
    "STOP_UNKNOWN_SCRIPT_DEFECT",
    "STOP_UNRECOGNIZED_PARENT",
    "STOP_NO_GENUINE_REVIEW_EVIDENCE",
    "STOP_UNRECOGNIZED_SOURCE_DEFECT",
    "PRIVATE_REPAIR_STAGED_PENDING_TWO_GEMINI_REVIEWS",
))
_DEFAULT_REGISTRY = (Path(__file__).resolve().parents[2] /
                     "docs" / "recurrence_registry.json")


def _hash_record(record: dict[str, Any]) -> str:
    return sha256(json.dumps(record, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True).encode("ascii")).hexdigest()


def read_policy_state(private_root: Path) -> dict | None:
    target = private_root / _DECISION_NAME
    if target.is_symlink():
        raise ValueError("V3_POLICY_UNSAFE_STATE_LINK")
    if not target.exists():
        return None
    if not target.is_file() or target.stat().st_size > 4096:
        raise ValueError("V3_POLICY_INVALID_STATE_SIZE")
    try:
        state = json.loads(target.read_text(encoding="utf8"))
    except (OSError, UnicodeError, ValueError):
        raise ValueError("V3_POLICY_UNREADABLE_STATE") from None
    if (not isinstance(state, dict)
            or set(state) != {"schema", "revision", "failureClass",
                              "triggerIncident", "remedyIncident", "status",
                              "candidateSha256", "remainingAutomaticRetries",
                              "publicationAuthorized", "integritySha256"}
            or state["schema"] != _SCHEMA
            or type(state["revision"]) is not int or not 1 <= state["revision"] <= 1_000_000
            or state["publicationAuthorized"] is not False
            or state["remainingAutomaticRetries"] != 0
            or any(not isinstance(state[k], str) or len(state[k]) > 100
                   for k in ("failureClass", "triggerIncident", "remedyIncident",
                             "status"))
            or state["candidateSha256"] is not None
               and (not isinstance(state["candidateSha256"], str)
                    or len(state["candidateSha256"]) != 64)
            or not isinstance(state["integritySha256"], str)):
        raise ValueError("V3_POLICY_INVALID_STATE")
    unsigned = {k: v for k, v in state.items() if k != "integritySha256"}
    if _hash_record(unsigned) != state["integritySha256"]:
        raise ValueError("V3_POLICY_INTEGRITY_MISMATCH")
    return state


def persist_policy_state(private_root: Path, result: dict[str, Any]) -> dict:
    if (not private_root.is_absolute() or private_root.is_symlink()
            or result.get("publicationAuthorized", False) is not False):
        raise ValueError("V3_POLICY_UNSAFE_PRIVATE_STATE")
    # A compact, non-sensitive, allowlisted record; raw provider content
    # and exception text are never transported to this state.
    status = result.get("repairStatus")
    if status not in _ALLOWED_OUTCOMES:
        raise ValueError("V3_POLICY_UNSAFE_STATUS")
    incident = result.get("triggerIncident", "")
    remedy = result.get("remedyIncident", "")
    if incident not in ("", _TRIGGER) or remedy not in ("", _REMEDY):
        raise ValueError("V3_POLICY_UNKNOWN_INCIDENT")
    candidate = result.get("candidateSha256")
    if candidate is not None and (not isinstance(candidate, str)
                                  or len(candidate) != 64
                                  or any(c not in "0123456789abcdef" for c in candidate)):
        raise ValueError("V3_POLICY_BAD_CANDIDATE")
    if candidate is not None and result.get("repairStaged") is not True:
        raise ValueError("V3_POLICY_UNVERIFIED_CANDIDATE")
    prior = read_policy_state(private_root)
    record = {
        "schema": _SCHEMA,
        "revision": prior["revision"] + 1 if prior else 1,
        "failureClass": "MALFORMED_LOCALE_SCRIPT" if incident else "NO_RECOGNIZED_RECOVERY",
        "triggerIncident": incident,
        "remedyIncident": remedy,
        "status": status,
        "candidateSha256": candidate,
        # A source-free idempotent staging operation has no paid retries.
        "remainingAutomaticRetries": 0,
        "publicationAuthorized": False,
    }
    record["integritySha256"] = _hash_record(record)
    payload = (json.dumps(record, sort_keys=True, separators=(",", ":"))+"\n").encode()
    if len(payload) > 4096:
        raise ValueError("V3_POLICY_STATE_TOO_LONG")
    private_root.mkdir(parents=True, exist_ok=True)
    target = private_root / _DECISION_NAME
    if target.is_symlink():
        raise ValueError("V3_POLICY_UNSAFE_STATE_LINK")
    fd, staging = tempfile.mkstemp(prefix=".v3-policy-", suffix=".tmp",
                                   dir=private_root)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(staging, target)
    finally:
        Path(staging).unlink(missing_ok=True)
    return record


def _registered(registry_path: Path) -> bool:
    if (registry_path.is_symlink() or not registry_path.is_file()
            or registry_path.stat().st_size > 1_500_000):
        raise ValueError("V3_POLICY_UNREADABLE_REGISTRY")
    try:
        registry = json.loads(registry_path.read_text(encoding="utf8"))
    except (OSError, UnicodeError, ValueError):
        raise ValueError("V3_POLICY_INVALID_REGISTRY") from None
    incidents = registry.get("incidents") if isinstance(registry, dict) else None
    if not isinstance(incidents, list):
        raise ValueError("V3_POLICY_INVALID_REGISTRY")
    matching = [item for item in incidents
                if isinstance(item, dict) and item.get("id") in _EXPECTED]
    if (len(matching) != len(_EXPECTED) or
            {item["id"] for item in matching} != set(_EXPECTED)):
        raise ValueError("V3_POLICY_INCIDENT_UNREGISTERED")
    for item in matching:
        metadata = item.get("automaticRemedy")
        if (not isinstance(metadata, dict)
                or metadata.get("runtimePath") != _EXPECTED[item["id"]]):
            raise ValueError("V3_POLICY_HANDLER_IDENTITY_MISMATCH")
    # Resolution retirement/disablement is respected in ordinary execution.
    return all(item.get("status") == "resolved" for item in matching)


def apply_registered_recovery(
    course_dir: Path, private_root: Path, plan: dict[str, Any], *,
    registry_path: Path = _DEFAULT_REGISTRY,
) -> dict[str, Any]:
    """Match a known signature, reuse its explicitly reviewed handler and audit.

    No dynamic imports/exec from registry data, no paid request and no
    checkpoint reset. Unknown cases do not prohibit independent eligible work.
    """
    if (not isinstance(plan, dict) or plan.get("publicationAuthorized") is not False
            or not isinstance(plan.get("scriptQuarantinedSections", {}), dict)):
        raise ValueError("V3_POLICY_UNTRUSTED_PLAN")
    suspects = plan.get("scriptQuarantinedSections", {})
    # Validate any previous durable policy receipt even after all content
    # defects have vanished. A tampered checkpoint must not be ignored.
    read_policy_state(private_root)
    if not suspects:
        return {"repairStatus": "NO_SCRIPT_BLOCKER", "repairStaged": False,
                "publicationAuthorized": False}
    if "section-9-2" not in suspects or suspects["section-9-2"] != 2:
        outcome = {"repairStatus": "STOP_UNKNOWN_SCRIPT_SIGNATURE",
                   "repairStaged": False, "publicationAuthorized": False}
        persist_policy_state(private_root, outcome)
        return outcome
    if not _registered(registry_path):
        outcome = {"repairStatus": "STOP_REGISTERED_REMEDY_RETIRED",
                   "repairStaged": False, "publicationAuthorized": False,
                   "triggerIncident": _TRIGGER, "remedyIncident": _REMEDY}
        persist_policy_state(private_root, outcome)
        return outcome
    outcome = stage_known_language_repair(course_dir, private_root, plan)
    if (not isinstance(outcome, dict)
            or outcome.get("repairStaged") not in (True, False)
            or outcome.get("publicationAuthorized", False) is not False):
        raise ValueError("V3_POLICY_UNVERIFIED_HANDLER_RESULT")
    if outcome["repairStaged"] is True and (
            outcome.get("repairStatus") !=
            "PRIVATE_REPAIR_STAGED_PENDING_TWO_GEMINI_REVIEWS"
            or outcome.get("candidateSha256") !=
            "49a7f18c7cc2b7c00e0b6b23838cca1ed7fe52262384e0c26bbc8360fa3e9174"
            or outcome.get("archivalParentSha256") !=
            "cfe7bab820aa01ce71bd7a6a334c742101ebd10d8895cccd5f05d599030f971c"):
        raise ValueError("V3_POLICY_HANDLER_RESULT_NOT_VERIFIED")
    if outcome["repairStaged"] is True:
        # V6 next independent source-free stage: prepare the two-role,
        # exact-package QA handoff. No paid Gemini call or model PASS.
        handoff = stage_changed_activity_review_handoff(
            course_dir, private_root, outcome["candidateSha256"])
        if (handoff.get("handoffStatus") !=
                "PENDING_AUTHORIZED_TWO_GEMINI_REVIEW"
                or handoff.get("actualGeminiResponses") != 0
                or handoff.get("wholeCourseScopeAccepted") is not False):
            raise ValueError("V3_POLICY_UNVERIFIED_QA_HANDOFF")
        outcome["reviewHandoffSha256"] = handoff["handoffSha256"]
        # Handoff metadata alone cannot drive the V3 model assessor:
        # create one isolated reviewed-activity package so the existing
        # two-Gemini, exact-package no-replay engine can check only the
        # corrected content in a later separately authorized invocation.
        isolated = stage_isolated_review_slice(
            course_dir, private_root, outcome["candidateSha256"])
        if (isolated.get("status") !=
                "PENDING_AUTHORIZED_ISOLATED_TWO_GEMINI_REVIEW"
                or isolated.get("activityCount") != 1
                or isolated.get("reviewerCountRequired") != 2
                or isolated.get("actualGeminiResponses") != 0
                or isolated.get("wholeCourseScopeAccepted") is not False
                or isolated.get("publicationAuthorized") is not False):
            raise ValueError("V3_POLICY_INVALID_REVIEW_SLICE")
        outcome["reviewSliceSha256"] = isolated["reviewSliceSha256"]
        # A corrected course must first have an evidence-bound version
        # proposal, NOT an automatically admitted/released course.
        # Reuse original genuine PASS only for exactly unchanged content.
        repo = course_dir.resolve().parents[1]
        proposal = prepare_versioned_course_proposal(
            course_dir, repo, private_root)
        if (proposal.get("status") !=
                "VERSIONED_COURSE_PROPOSAL_STAGED_NOT_ADMITTED"
                or proposal.get("versionedScopeAdmitted") is not False
                or proposal.get("publicationAuthorized") is not False):
            raise ValueError("V3_POLICY_UNVERIFIED_COURSE_PROPOSAL")
        outcome["versionedProposalSha256"] = proposal["proposalSha256"]
    outcome["triggerIncident"] = _TRIGGER
    outcome["remedyIncident"] = _REMEDY
    persist_policy_state(private_root, outcome)
    return outcome

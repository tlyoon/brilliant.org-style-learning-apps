"""BOSLA V3 finite forward-progress controller for the normal Yoga 6 worker.

A running, explicitly authorized invocation can proceed to *subsequent new*
eligible activities without Windows Task Scheduler. Every step delegates
to the existing one-activity worker, which owns provider authentication,
capacity diagnostics, immutable role claims and independent QA.

The checkpoint is source-free, fsynced and restart-safe. A crash between
PRE_CALL and its verified post-call receipt is never silently retried.
This module does not edit frozen learning packages or approve publication.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Callable

from app_generator.runtime.v3_yoga6_recovery import (
    coordinator_lock, gate_review_plan,
)

CHECKPOINT_NAME = "v3-forward-progress-checkpoint.json"
SCHEMA_VERSION = 1
MAX_ACTIVITIES_PER_INVOCATION = 6
MIN_ELAPSED_SECONDS = 30
MAX_ELAPSED_SECONDS = 3600
_COUNTS = ("activitiesAssessedRows", "activitiesFullyModelReviewed",
           "modelConsensusPassActivities", "modelRepairRequiredActivities",
           "modelUncertainActivities")
_PHASES = frozenset(("PRE_CALL", "AFTER_CALL", "STOPPED"))
_KEYS = frozenset(("schemaVersion", "phase", "revision", "rosterSha256",
                  "before", "last", "status", "integritySha256"))
_SAFE_DISPATCH = "READY_FOR_AUTHORIZED_REVIEW_SESSIONS"


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=True,
                      separators=(",", ":")).encode("ascii")


def _hex64(value: Any) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(ch in "0123456789abcdef" for ch in value))


def snapshot(plan: dict) -> dict:
    """Snapshot only status counters and frozen course fingerprint."""
    if not isinstance(plan, dict) or plan.get("publicationAuthorized") is not False:
        raise ValueError("V3_FORWARD_UNTRUSTED_PLAN")
    sections = plan.get("sectionProgress")
    if not isinstance(sections, list) or len(sections) != 6:
        raise ValueError("V3_FORWARD_INVALID_COURSE_ROSTER")
    roster = []
    seen = set()
    total = 0
    for row in sections:
        if not isinstance(row, dict):
            raise ValueError("V3_FORWARD_INVALID_COURSE_ROSTER")
        name, digest, quantity = (row.get("section"), row.get("packageSha256"),
                                   row.get("activitiesTotal"))
        if (not isinstance(name, str) or name in seen
                or not name.startswith("section-9-") or not _hex64(digest)
                or type(quantity) is not int or quantity < 1 or quantity > 108):
            raise ValueError("V3_FORWARD_INVALID_COURSE_ROSTER")
        seen.add(name)
        roster.append([name, digest, quantity])
        total += quantity
    if (total != 108 or seen != {f"section-9-{n}" for n in range(1, 7)}):
        raise ValueError("V3_FORWARD_NOT_FROZEN_108_ACTIVITIES")
    numbers = {name: plan.get(name) for name in _COUNTS}
    if (any(type(value) is not int or value < 0 or value > 108
            for value in numbers.values())
            or not (numbers["modelConsensusPassActivities"] +
                    numbers["modelRepairRequiredActivities"] +
                    numbers["modelUncertainActivities"] <=
                    numbers["activitiesAssessedRows"] <= 108)
            or numbers["activitiesFullyModelReviewed"] >
                    numbers["activitiesAssessedRows"]):
        raise ValueError("V3_FORWARD_INVALID_PROGRESS_COUNTS")
    dispatch = plan.get("dispatchStatus")
    next_section = plan.get("nextSection")
    if (not isinstance(dispatch, str) or len(dispatch) > 100
            or next_section is not None and next_section not in seen):
        raise ValueError("V3_FORWARD_INVALID_DISPATCH_STATUS")
    return {
        "rosterSha256": sha256(_canonical(sorted(roster))).hexdigest(),
        "dispatchStatus": dispatch,
        "nextSection": next_section,
        **numbers,
    }


def classify(plan: dict) -> str:
    """Classify existing downstream blockers; never weaken their gate."""
    current = snapshot(plan)
    status = current["dispatchStatus"]
    if status == _SAFE_DISPATCH:
        # Reuse the historical source-free provider-capacity budget/circuit.
        return gate_review_plan(plan)
    if status in ("STOP_UNRECONCILED_MODEL_REVIEW",
                  "STOP_ACTIVE_REVIEW_OWNERSHIP_UNCERTAIN"):
        return "STOP_UNRECONCILED_CLAIM_NO_REPLAY"
    if status == "STOP_VERSIONED_CONTENT_REPAIR_REQUIRED":
        return "STOP_VERSIONED_CONTENT_REPAIR_REQUIRED"
    if status == "PENDING_DETERMINISTIC_RELEASE_EVIDENCE":
        return "STOP_DETERMINISTIC_RELEASE_QA_PENDING"
    if status.startswith("STOP_PROVIDER_"):
        return status
    if status.startswith("BLOCKED_"):
        return status
    return "STOP_UNCLASSIFIED_DISPATCH"


def _validate_snapshot(value: Any) -> dict:
    expected = {"rosterSha256", "dispatchStatus", "nextSection", *_COUNTS}
    if (not isinstance(value, dict) or set(value) != expected
            or not _hex64(value["rosterSha256"])
            or not isinstance(value["dispatchStatus"], str)
            or len(value["dispatchStatus"]) > 100
            or value["nextSection"] is not None
            and not isinstance(value["nextSection"], str)
            or any(type(value[k]) is not int or not 0 <= value[k] <= 108
                   for k in _COUNTS)):
        raise ValueError("V3_FORWARD_BAD_STORED_SNAPSHOT")
    return value


def read_checkpoint(root: Path) -> dict | None:
    path = root / CHECKPOINT_NAME
    if path.is_symlink():
        raise ValueError("V3_FORWARD_UNSAFE_CHECKPOINT_SYMLINK")
    if not path.exists():
        return None
    if not path.is_file() or path.stat().st_size > 4096:
        raise ValueError("V3_FORWARD_UNSAFE_CHECKPOINT_SIZE")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise ValueError("V3_FORWARD_UNREADABLE_CHECKPOINT") from None
    if (not isinstance(state, dict) or set(state) != _KEYS
            or state.get("schemaVersion") != SCHEMA_VERSION
            or state.get("phase") not in _PHASES
            or type(state.get("revision")) is not int
            or state["revision"] < 1 or state["revision"] > 1_000_000
            or not _hex64(state.get("rosterSha256"))
            or not isinstance(state.get("status"), str)
            or len(state["status"]) > 100):
        raise ValueError("V3_FORWARD_INVALID_CHECKPOINT")
    _validate_snapshot(state["before"])
    _validate_snapshot(state["last"])
    if (state["rosterSha256"] != state["before"]["rosterSha256"]
            or state["rosterSha256"] != state["last"]["rosterSha256"]):
        raise ValueError("V3_FORWARD_CHECKPOINT_ROSTER_MISMATCH")
    stamp = sha256(_canonical({k: v for k, v in state.items()
                                if k != "integritySha256"})).hexdigest()
    if state.get("integritySha256") != stamp:
        raise ValueError("V3_FORWARD_CHECKPOINT_INTEGRITY_MISMATCH")
    return state


def save_checkpoint(root: Path, phase: str, before: dict, last: dict,
                    status: str) -> dict:
    if phase not in _PHASES or not isinstance(status, str) or len(status) > 100:
        raise ValueError("V3_FORWARD_INVALID_CHECKPOINT_TRANSITION")
    _validate_snapshot(before)
    _validate_snapshot(last)
    if before["rosterSha256"] != last["rosterSha256"]:
        raise ValueError("V3_FORWARD_FROZEN_ROSTER_CHANGED")
    existing = read_checkpoint(root)
    if existing and existing["rosterSha256"] != before["rosterSha256"]:
        raise ValueError("V3_FORWARD_FROZEN_ROSTER_CHANGED")
    state = {
        "schemaVersion": SCHEMA_VERSION,
        "revision": existing["revision"] + 1 if existing else 1,
        "phase": phase, "rosterSha256": before["rosterSha256"],
        "before": before, "last": last, "status": status,
    }
    state["integritySha256"] = sha256(_canonical(state)).hexdigest()
    encoded = _canonical(state) + b"\n"
    if len(encoded) > 4096:
        raise ValueError("V3_FORWARD_CHECKPOINT_TOO_LARGE")
    root.mkdir(parents=True, exist_ok=True)
    path = root / CHECKPOINT_NAME
    if path.is_symlink():
        raise ValueError("V3_FORWARD_UNSAFE_CHECKPOINT_SYMLINK")
    fd, temporary = tempfile.mkstemp(prefix=".v3-forward-", suffix=".tmp",
                                     dir=root)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return state


def _progress(old: dict, new: dict) -> bool:
    if old["rosterSha256"] != new["rosterSha256"]:
        raise ValueError("V3_FORWARD_FROZEN_ROSTER_CHANGED")
    if any(new[name] < old[name] for name in _COUNTS):
        raise ValueError("V3_FORWARD_PROGRESS_REGRESSION")
    if new["activitiesAssessedRows"] > old["activitiesAssessedRows"] + 1:
        raise ValueError("V3_FORWARD_MULTIPLE_UNEXPECTED_REVIEWS")
    if any(new[name] > old[name] + 1 for name in _COUNTS):
        raise ValueError("V3_FORWARD_MULTIPLE_UNEXPECTED_REVIEWS")
    return new["activitiesAssessedRows"] > old["activitiesAssessedRows"]


def _different_quarantined_section(previous: dict, plan: dict) -> bool:
    """Allow an unrelated section only when the old section is quarantined.

    A provider request may be ambiguous, but the original course planner
    already isolates that section and never permits a repeat of its claim.
    A changed next section alone is NOT sufficient proof of quarantine.
    """
    old = previous["nextSection"]
    quarantined = plan.get("quarantinedSections")
    current = snapshot(plan)
    return (isinstance(old, str) and isinstance(quarantined, list)
            and all(isinstance(name, str) for name in quarantined)
            and old in quarantined and current["nextSection"] != old
            and current["nextSection"] is not None
            and current["rosterSha256"] == previous["rosterSha256"]
            and classify(plan) == "READY_FOR_SOURCE_FREE_METADATA_CHECK")


def _report(status: str, plan: dict, completed: int, calls: int) -> dict:
    snapshot(plan)
    return {
        "status": status, "dispatchStatus": plan["dispatchStatus"],
        "nextSection": plan.get("nextSection"),
        "activitiesAssessedRows": plan["activitiesAssessedRows"],
        "activitiesFullyModelReviewed": plan["activitiesFullyModelReviewed"],
        "modelConsensusPassActivities": plan["modelConsensusPassActivities"],
        "modelRepairRequiredActivities": plan["modelRepairRequiredActivities"],
        "modelUncertainActivities": plan["modelUncertainActivities"],
        "advancedActivitiesThisInvocation": completed,
        "workerInvocationsThisRun": calls, "publicationAuthorized": False,
    }


def advance_until_boundary(
    private_root: Path, read_plan: Callable[[], dict],
    execute_one: Callable[[], int], *,
    operation_authorized: bool = False,
    transfer_authorized: bool = False,
    max_activities: int = 4,
    max_elapsed_seconds: int = 900,
    monotonic: Callable[[], float] = time.monotonic,
) -> dict:
    """Advance as far as existing safe reviewer gates allow during this run.

    Each activity has at most one dispatch. On a process crash an unresolved
    PRE_CALL checkpoint blocks fresh operations unless immutable read-only
    evidence proves the previous round produced one new assessed activity.
    """
    if not (operation_authorized is True and transfer_authorized is True):
        return {"status": "STOP_PAID_OR_TRANSFER_AUTHORIZATION_MISSING",
                "publicationAuthorized": False,
                "advancedActivitiesThisInvocation": 0}
    if (type(max_activities) is not int
            or not 1 <= max_activities <= MAX_ACTIVITIES_PER_INVOCATION
            or type(max_elapsed_seconds) is not int
            or not MIN_ELAPSED_SECONDS <= max_elapsed_seconds <= MAX_ELAPSED_SECONDS):
        raise ValueError("V3_FORWARD_INVALID_BOUNDED_BUDGET")
    if not callable(read_plan) or not callable(execute_one):
        raise ValueError("V3_FORWARD_MISSING_EXECUTABLE")
    began = monotonic()
    completed = calls = 0
    # This lock is held for the full multi-activity attempt. The existing
    # per-activity worker separately holds the original reviewer coordinator.
    driver = private_root / "forward-driver"
    if driver.is_symlink():
        raise ValueError("V3_FORWARD_UNSAFE_DRIVER_LOCK")
    with coordinator_lock(driver):
        plan = read_plan()
        current = snapshot(plan)
        prior = read_checkpoint(private_root)
        if prior is not None:
            if prior["rosterSha256"] != current["rosterSha256"]:
                raise ValueError("V3_FORWARD_FROZEN_ROSTER_CHANGED")
            if prior["phase"] == "PRE_CALL":
                # The prior process may have submitted its Gemini request.
                # A newer durable aggregate is the ONLY acceptable resume proof.
                if _progress(prior["before"], current):
                    save_checkpoint(private_root, "AFTER_CALL",
                                    prior["before"], current,
                                    "RECOVERED_PREVIOUS_CALL_BY_IMMUTABLE_EVIDENCE")
                elif _different_quarantined_section(prior["before"], plan):
                    # The unresolved role remains untouched. The existing
                    # course dispatcher has moved to a different frozen
                    # section whose claims are independently eligible.
                    save_checkpoint(private_root, "AFTER_CALL",
                                    prior["before"], current,
                                    "RECOVERED_DISTINCT_SECTION_NO_REPLAY")
                else:
                    return _report("STOP_UNRECONCILED_PREVIOUS_CALL_NO_REPLAY",
                                   plan, completed, calls)
            elif prior["status"] in (
                    "STOP_NO_VERIFIED_PROGRESS_NO_REPLAY",
                    "STOP_UNRECONCILED_PREVIOUS_CALL_NO_REPLAY"):
                if _progress(prior["before"], current):
                    save_checkpoint(private_root, "AFTER_CALL",
                                    prior["before"], current,
                                    "RECOVERED_PREVIOUS_CALL_BY_IMMUTABLE_EVIDENCE")
                elif _different_quarantined_section(prior["before"], plan):
                    save_checkpoint(private_root, "AFTER_CALL",
                                    prior["before"], current,
                                    "RECOVERED_DISTINCT_SECTION_NO_REPLAY")
                else:
                    return _report("STOP_UNRECONCILED_PREVIOUS_CALL_NO_REPLAY",
                                   plan, completed, calls)
        for _ in range(max_activities):
            plan = read_plan()
            current = snapshot(plan)
            gate = classify(plan)
            if gate != "READY_FOR_SOURCE_FREE_METADATA_CHECK":
                save_checkpoint(private_root, "STOPPED", current, current, gate)
                return _report(gate, plan, completed, calls)
            # The budget is checked BETWEEN one-shot operations. Underlying
            # Gemini SDK and per-model code own their own finite HTTP timeouts.
            if monotonic() - began >= max_elapsed_seconds:
                save_checkpoint(private_root, "STOPPED", current, current,
                                "STOP_FORWARD_ELAPSED_BOUND")
                return _report("STOP_FORWARD_ELAPSED_BOUND", plan, completed, calls)
            save_checkpoint(private_root, "PRE_CALL", current, current,
                            "PREPARED_SINGLE_ELIGIBLE_ACTIVITY")
            calls += 1
            try:
                exit_code = execute_one()
                if type(exit_code) is not int:
                    raise ValueError("V3_FORWARD_BAD_WORKER_EXIT")
            except Exception:
                # Do not retry a possibly sent request after any worker error.
                return _report("STOP_UNRECONCILED_WORKER_EXCEPTION_NO_REPLAY",
                               read_plan(), completed, calls)
            after = read_plan()
            evidence = snapshot(after)
            if not _progress(current, evidence):
                if _different_quarantined_section(current, after):
                    # The source-free planner quarantined the old request
                    # and selected a DIFFERENT authorized frozen section.
                    # The previous role is still unresolved, never retried.
                    save_checkpoint(private_root, "AFTER_CALL",
                                    current, evidence,
                                    "QUARANTINED_FAILED_SECTION_NO_REPLAY")
                    continue
                # Keep PRE_CALL for crash/restart safety. Any future resume
                # must prove genuinely different immutable evidence.
                return _report("STOP_NO_VERIFIED_PROGRESS_NO_REPLAY",
                               after, completed, calls)
            completed += 1
            save_checkpoint(private_root, "AFTER_CALL", current, evidence,
                            "VERIFIED_NEW_ASSESSED_ACTIVITY")
            # A nonzero worker exit can coexist with a durable uncertain
            # assessment. Do not retry that request; independent next-section
            # activity is allowed only if the existing planner deems it READY.
            if exit_code != 0 and classify(after) != "READY_FOR_SOURCE_FREE_METADATA_CHECK":
                return _report("STOP_WORKER_NONZERO_AND_NEXT_BLOCKED",
                               after, completed, calls)
        plan = read_plan()
        current = snapshot(plan)
        # After the final permitted review, automatically classify the
        # subsequent legitimate QA/repair stage instead of reporting only
        # a generic activity budget when the course is already blocked/done.
        next_gate = classify(plan)
        status = ("STOP_FORWARD_ACTIVITY_BUDGET_REACHED" if
                  next_gate == "READY_FOR_SOURCE_FREE_METADATA_CHECK" else
                  next_gate)
        save_checkpoint(private_root, "STOPPED", current, current, status)
        return _report(status, plan, completed, calls)

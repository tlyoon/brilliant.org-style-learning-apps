"""Single-owner, restart-safe Yoga 6 recovery coordination utilities.

The normal worker uses the SAME V3 frozen-scope and role-claim system.
This module never opens Google, resets a claim, or grants publication.
"""
from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import tempfile
import time

MAX_FAILED_ACTIVITIES_PER_COURSE = 2
STATUS_FILENAME = "yoga6-recovery-status.json"


def checked_private_root(value: Path, *, localappdata: Path) -> Path:
    """Keep credentials, provider diagnostics and claims under local Microvid."""
    microvid = (localappdata / "Microvid").resolve()
    root = value.expanduser().resolve()
    if (root == microvid or not root.is_relative_to(microvid)
        or value.is_symlink()):
        raise ValueError("V3_WORKER_PRIVATE_ROOT_OUTSIDE_MICROVID")
    return root


def gate_review_plan(plan: dict) -> str:
    """Never use a diagnostic or scheduler to bypass an existing claim stop."""
    if plan["dispatchStatus"] != "READY_FOR_AUTHORIZED_REVIEW_SESSIONS":
        return plan["dispatchStatus"]
    capacity = plan.get("providerCapacity")
    if not isinstance(capacity, dict):
        raise ValueError("V3_WORKER_MISSING_CAPACITY_PROOF")
    failures = capacity.get("serverErrorActivitiesHistorical")
    if type(failures) is not int or failures < 0:
        raise ValueError("V3_WORKER_INVALID_CAPACITY_HISTORY")
    if failures >= MAX_FAILED_ACTIVITIES_PER_COURSE:
        return "STOP_PROVIDER_RECOVERY_BUDGET"
    return "READY_FOR_SOURCE_FREE_METADATA_CHECK"


@contextmanager
def coordinator_lock(private_root: Path):
    """OS-released process lock: crash leaves no permanently held ownership.

    Existing per-package in-flight locks and role claims remain independently
    authoritative; this coordinator lock never clears either.
    """
    private_root.mkdir(parents=True, exist_ok=True)
    lock_path = private_root / ".yoga6-recovery-coordinator.lock"
    if lock_path.is_symlink():
        raise ValueError("V3_WORKER_UNSAFE_COORDINATOR_LOCK")
    with lock_path.open("a+b") as handle:
        if not lock_path.stat().st_size:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise RuntimeError("V3_WORKER_ALREADY_RUNNING") from exc
        else:
            import fcntl
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise RuntimeError("V3_WORKER_ALREADY_RUNNING") from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def persist_status(private_root: Path, report: dict) -> Path:
    """Atomic, bounded, deliberately source-free local status receipt."""
    allowed = {
        "runUnix", "status", "dispatchStatus", "nextSection",
        "activitiesAssessedRows", "activitiesFullyModelReviewed",
        "modelConsensusPassActivities", "modelUncertainActivities",
        "quarantinedSections", "providerCapacity", "diagnostic",
        "nativeExitCode", "publicationAuthorized",
    }
    if not isinstance(report, dict) or not set(report).issubset(allowed):
        raise ValueError("V3_WORKER_UNSAFE_STATUS_FIELDS")
    if report.get("publicationAuthorized") is not False:
        raise ValueError("V3_WORKER_CANNOT_AUTHORIZE_PUBLICATION")
    encoded = (json.dumps(report, sort_keys=True, separators=(",", ":")) +
               "\n").encode("utf-8")
    if len(encoded) > 12_000:
        raise ValueError("V3_WORKER_STATUS_TOO_LARGE")
    private_root.mkdir(parents=True, exist_ok=True)
    target = private_root / STATUS_FILENAME
    if target.is_symlink():
        raise ValueError("V3_WORKER_UNSAFE_STATUS_TARGET")
    fd, name = tempfile.mkstemp(prefix=".yoga6-status-",suffix=".tmp",
                                 dir=private_root)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, target)
    finally:
        try:
            Path(name).unlink()
        except FileNotFoundError:
            pass
    return target


def status_from_plan(plan: dict, *, status: str,
                     diagnostic: dict | None = None,
                     native_exit_code: int | None = None) -> dict:
    keys = ("dispatchStatus", "nextSection", "activitiesAssessedRows",
            "activitiesFullyModelReviewed", "modelConsensusPassActivities",
            "modelUncertainActivities", "quarantinedSections",
            "providerCapacity")
    report = {key: plan.get(key) for key in keys}
    report.update({"runUnix":int(time.time()), "status":status,
                   "publicationAuthorized":False})
    if diagnostic is not None:
        # Caller must pass the sanitized, metadata-only diagnostic.
        report["diagnostic"] = diagnostic
    if native_exit_code is not None:
        report["nativeExitCode"] = native_exit_code
    return report

"""BSA286: recover only an exact-identity orphan left by a failed Bosla owner.

This module does not grant academic PASS and never kills unrelated processes.
The caller holds the existing Yoga6 singleflight lock and persists the result.
All Windows process probes are read-only before a guarded tree termination.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import subprocess
from typing import Callable, Any

OWNER_LABELS = {
    "OWNER_REAL_SOURCE_ADMISSION":
        "scripts.auto_advance_bosla_academic_frontier",
    "OWNER_INDEPENDENT_HORIZON":
        "scripts.show_bosla_long_horizon",
}
ACTIVE_OWNER_STATUSES = (
    "BSA279_CLASSIFIED_RETRYABLE_OR_SAFETY_BOUNDARY",
    "BSA286_OWNER_MONITOR_EXCEPTION_TREE_CLEANED",
    "BSA286_OWNER_TREE_CLEANUP_UNVERIFIED",
)


def _when(stamp: str) -> datetime:
    if not isinstance(stamp,str):
        raise ValueError("BSA286_UNTRUSTED_PROCESS_TIME")
    try:
        dt=datetime.fromisoformat(stamp)
    except ValueError as exc:
        raise ValueError("BSA286_UNTRUSTED_PROCESS_TIME") from exc
    if dt.tzinfo is None:
        raise ValueError("BSA286_UNTRUSTED_PROCESS_TIME")
    return dt.astimezone(timezone.utc)


def windows_process_probe(pid: int) -> dict | None:
    """Win32_Process retrieves immutable launch identity (no shell PID guessing)."""
    if not isinstance(pid,int) or isinstance(pid,bool) or pid<10:
        raise ValueError("BSA286_UNSAFE_PROCESS_ID")
    ps=(
        f"$p=Get-CimInstance Win32_Process -Filter 'ProcessId={pid}';"
        "if($p){[PSCustomObject]@{"
        "pid=[int]$p.ProcessId;"
        "created=$p.CreationDate.ToString('o');"
        "exe=[string]$p.ExecutablePath;"
        "command=[string]$p.CommandLine"
        "}|ConvertTo-Json -Compress}"
    )
    try:
        result=subprocess.run(
            ["powershell.exe","-NoProfile","-NonInteractive","-Command",ps],
            capture_output=True,text=True,encoding="utf8",errors="replace",
            timeout=18,check=False,
        )
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise ValueError("BSA286_WINDOWS_PROCESS_PROBE_FAILED") from exc
    if result.returncode:
        raise ValueError("BSA286_WINDOWS_PROCESS_PROBE_FAILED")
    if not result.stdout.strip():
        return None
    try:
        obj=json.loads(result.stdout)
    except ValueError as exc:
        raise ValueError("BSA286_WINDOWS_PROCESS_PROBE_UNTRUSTED") from exc
    if not isinstance(obj,dict) or obj.get("pid")!=pid:
        raise ValueError("BSA286_WINDOWS_PROCESS_PROBE_UNTRUSTED")
    return obj


def exact_owner_identity(info:dict, state:dict, *, expected_python:Path) -> bool:
    """Reject a reused PID, different command, different project, or newer process."""
    pid=state.get("childPid")
    if not isinstance(pid,int) or isinstance(pid,bool) or info.get("pid")!=pid:
        return False
    label=state.get("ownerChildLabel")
    if not isinstance(label,str):
        raw=str(state.get("currentLog","")).replace("/","\\")
        filename=raw.rsplit("\\",1)[-1]
        label=next((key for key in OWNER_LABELS
                    if filename.startswith(key+"_")),None)
    marker=OWNER_LABELS.get(label)
    if marker is None:
        return False
    command=info.get("command")
    exe=info.get("exe")
    if not isinstance(command,str) or not isinstance(exe,str):
        return False
    if ("-m "+marker not in command
        or (marker=="scripts.auto_advance_bosla_academic_frontier"
            and "--max-steps 8" not in command)):
        return False
    norm=lambda s:str(s).replace("/","\\").casefold()
    if norm(exe)!=norm(expected_python):
        return False
    # Process launch cannot precede the owner cycle or postdate its last state.
    # Both bounds are persisted and verified before any destructive action.
    try:
        launched=_when(info["created"])
        baseline=_when(state.get("ownerChildStartedAt")
                       or state.get("cycleStartedAt"))
        last=_when(state["heartbeatAt"])
    except (KeyError, ValueError):
        return False
    return baseline-timedelta(seconds=90)<=launched<=last+timedelta(seconds=90)


def windows_kill_tree(pid:int) -> int:
    if not isinstance(pid,int) or isinstance(pid,bool) or pid<10:
        raise ValueError("BSA286_UNSAFE_PROCESS_ID")
    try:
        p=subprocess.run(
            ["taskkill","/T","/F","/PID",str(pid)],
            capture_output=True,text=True,timeout=18,check=False,
        )
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise ValueError("BSA286_WINDOWS_PROCESS_TREE_KILL_FAILED") from exc
    return p.returncode


def recover_previous_owner_tree(
    state:dict,*,expected_python:Path,
    probe:Callable[[int],dict|None]=windows_process_probe,
    kill:Callable[[int],int]=windows_kill_tree,
)->dict:
    """Fail closed on ambiguous PID identity; never silently resume a second tree."""
    pid=state.get("childPid")
    if not isinstance(pid,int) or isinstance(pid,bool) or pid<10:
        return {"status":"BSA286_NO_PREVIOUS_CHILD_REFERENCE","safe":True}
    info=probe(pid)
    if info is None:
        state["ownerChildLifecycle"]="EXITED_OR_ALREADY_CLEANED"
        return {"status":"BSA286_PREVIOUS_OWNER_CHILD_ABSENT","safe":True}
    if not exact_owner_identity(info,state,expected_python=expected_python):
        return {"status":"BSA286_REFUSED_UNTRUSTED_OLD_PID_IDENTITY",
                "safe":False,"pid":pid}
    # If the scheduler still owns its child, this must only run AFTER
    # the singleflight lock has been acquired; that lock is our ownership.
    if kill(pid) not in (0,128):
        return {"status":"BSA286_OWNER_TREE_TERMINATION_NOT_CONFIRMED",
                "safe":False,"pid":pid}
    remaining=probe(pid)
    if remaining is not None:
        return {"status":"BSA286_OWNER_TREE_STILL_ALIVE_AFTER_KILL",
                "safe":False,"pid":pid}
    state["ownerChildLifecycle"]="RECOVERED_STALE_PROCESS_TREE"
    return {"status":"BSA286_STALE_OWNER_TREE_REAPED","safe":True,"pid":pid}

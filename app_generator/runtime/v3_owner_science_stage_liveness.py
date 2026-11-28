"""BSA308 bounded owner-science liveness telemetry, never science acceptance.

A growing log, process CPU time, and stage markers are engineering health
signals ONLY. They cannot admit tasks, create signed receipts, bypass physics
review, or authorize publication. Windows process-tree CPU sampling uses
system APIs, with no paid provider and no third-party dependencies.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
from typing import Mapping

_STAGE_BEGIN=re.compile(
    rb"(?m)^BSA283_VERIFIABLE_ACADEMIC_STEP_ENTER (\d{1,2})/(\d{1,2}) head=([0-9a-f]{12})\r?$"
)
_STAGE_END=re.compile(
    rb"(?m)^BSA308_SIGNED_STAGE_STEP_COMPLETED (\d{1,2})/(\d{1,2}) head=([0-9a-f]{12}) action=([A-Z0-9_]{4,80})\r?$"
)

def stage_log_observation(log:Path,*,head:str)->dict:
    """Summarize bounded log bytes; never infer scientific PASS."""
    if not isinstance(head,str) or not re.fullmatch(r"[0-9a-f]{40}",head):
        raise ValueError("BSA308_EXACT_HEAD_REQUIRED")
    try:
        with log.open("rb") as stream:
            stream.seek(0,2)
            size=stream.tell()
            stream.seek(max(0,size-65536))
            tail=stream.read(65536)
    except (OSError,ValueError):
        return {"stageEntered":0,"stageCompleted":0,"logReadError":True}
    if size>len(tail):
        tail=tail[tail.find(b"\n")+1:] if b"\n" in tail else b""
    latest={"stageEntered":0,"stageCompleted":0,
            "lastCompletedAction":None,"logReadError":False}
    expected=head[:12].encode("ascii")
    for match in _STAGE_BEGIN.finditer(tail):
        step,total,git=match.groups()
        if git==expected and int(total)<=24 and 1<=int(step)<=int(total):
            latest["stageEntered"]=max(latest["stageEntered"],int(step))
    for match in _STAGE_END.finditer(tail):
        step,total,git,action=match.groups()
        if git==expected and int(total)<=24 and 1<=int(step)<=int(total):
            if int(step)>=latest["stageCompleted"]:
                latest["stageCompleted"]=int(step)
                latest["lastCompletedAction"]=action.decode("ascii")
    return latest

def cpu_time_gain(previous:Mapping[str,float]|None,
                  current:Mapping[str,float]|None)->float:
    """Count only increases of exact PID + creation-time process identities."""
    if previous is None or current is None:
        return 0.0
    return sum(max(0.,value-float(previous.get(identity,0.)))
               for identity,value in current.items()
               if isinstance(identity,str) and isinstance(value,(int,float))
               and value>=0)

def windows_owner_tree_cpu(pid:int)->dict[str,float]|None:
    """Read OS process tree CPU seconds; fail closed on unavailable API.

    The snapshot includes children of the exact currently owned process.
    Never use these values as scientific verification or publication proof.
    """
    if os.name!="nt" or type(pid) is not int or pid<=0:
        return None
    try:
        import ctypes
        from ctypes import wintypes as wt

        class PROCESSENTRY32W(ctypes.Structure):
            _fields_=[
                ("dwSize",wt.DWORD),("cntUsage",wt.DWORD),
                ("th32ProcessID",wt.DWORD),
                ("th32DefaultHeapID",ctypes.c_size_t),
                ("th32ModuleID",wt.DWORD),("cntThreads",wt.DWORD),
                ("th32ParentProcessID",wt.DWORD),
                ("pcPriClassBase",wt.LONG),("dwFlags",wt.DWORD),
                ("szExeFile",ctypes.c_wchar*260),
            ]
        class FILETIME(ctypes.Structure):
            _fields_=[("low",wt.DWORD),("high",wt.DWORD)]
            def ticks(self)->int:
                return (int(self.high)<<32)+int(self.low)
        k=ctypes.WinDLL("kernel32",use_last_error=True)
        k.CreateToolhelp32Snapshot.argtypes=[wt.DWORD,wt.DWORD]
        k.CreateToolhelp32Snapshot.restype=wt.HANDLE
        k.Process32FirstW.argtypes=[wt.HANDLE,ctypes.POINTER(PROCESSENTRY32W)]
        k.Process32FirstW.restype=wt.BOOL
        k.Process32NextW.argtypes=[wt.HANDLE,ctypes.POINTER(PROCESSENTRY32W)]
        k.Process32NextW.restype=wt.BOOL
        k.OpenProcess.argtypes=[wt.DWORD,wt.BOOL,wt.DWORD]
        k.OpenProcess.restype=wt.HANDLE
        k.GetProcessTimes.argtypes=[wt.HANDLE,*([ctypes.POINTER(FILETIME)]*4)]
        k.GetProcessTimes.restype=wt.BOOL
        k.CloseHandle.argtypes=[wt.HANDLE]
        k.CloseHandle.restype=wt.BOOL
        h=k.CreateToolhelp32Snapshot(0x00000002,0)
        if not h or h==ctypes.c_void_p(-1).value:
            return None
        parents={}
        entry=PROCESSENTRY32W()
        entry.dwSize=ctypes.sizeof(entry)
        try:
            if not k.Process32FirstW(h,ctypes.byref(entry)):
                return None
            while True:
                parents[int(entry.th32ProcessID)]=int(entry.th32ParentProcessID)
                if not k.Process32NextW(h,ctypes.byref(entry)):
                    break
        finally:
            k.CloseHandle(h)
        if pid not in parents:
            return None
        seen={pid}
        # Descendant expansion has a strict bounded process count.
        for _ in range(512):
            added={item for item,parent in parents.items()
                   if item not in seen and parent in seen}
            if not added:
                break
            seen.update(added)
            if len(seen)>512:
                return None
        values={}
        for process_id in seen:
            ph=k.OpenProcess(0x1000,False,process_id)
            if not ph:
                continue
            created,exited,kernel,user=FILETIME(),FILETIME(),FILETIME(),FILETIME()
            try:
                valid=k.GetProcessTimes(ph,ctypes.byref(created),
                    ctypes.byref(exited),ctypes.byref(kernel),
                    ctypes.byref(user))
                if valid:
                    identity=str(process_id)+":"+str(created.ticks())
                    values[identity]=(kernel.ticks()+user.ticks())/10_000_000
            finally:
                k.CloseHandle(ph)
        return values or None
    except (OSError,ValueError,TypeError,AttributeError):
        return None

def liveness_decision(*,elapsed:float,idle_log:float,idle_cpu:float,
                      hard_cap:float,idle_cap:float,
                      cpu_available:bool,stage_started:int,
                      last_completed:int)->str:
    """Never let an active CPU loop bypass the immutable wall-time cap."""
    if elapsed>hard_cap:
        return "BSA308_HARD_OWNER_RUNTIME_CAP"
    if idle_log<=idle_cap:
        return "BSA308_LOG_ACTIVITY"
    if cpu_available and idle_cpu<=idle_cap:
        return "BSA308_COMPUTATION_ACTIVE_NO_NEW_SIGNED_PROOF"
    return "BSA308_QUIET_SOURCE_WORKER_STALL"

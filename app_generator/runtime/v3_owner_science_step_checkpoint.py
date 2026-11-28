"""BSA315: restart-safe owner science-step telemetry, NEVER an academic receipt.

Signed source proof and its verifier are the only basis for academic acceptance.
This checkpoint tracks which executable owner step last completed on each exact
Git HEAD. On restart the controller still independently verifies signed files,
rather than relying on a checkpoint to skip science.
"""
from __future__ import annotations

from datetime import datetime,timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import tempfile

_HEAD=re.compile(r"[0-9a-f]{40}\Z")
_STEP_ACTION=re.compile(r"[A-Z][A-Z0-9_]{4,110}\Z")
_NAME="BSA315_OWNER_SCIENCE_STEP_CHECKPOINT.json"


def _digest(body:dict)->str:
    return sha256(json.dumps(body,sort_keys=True,ensure_ascii=True,
        separators=(",",":")).encode("utf8")).hexdigest()


def _target(private:Path,head:str)->Path:
    if not isinstance(private,Path) or not isinstance(head,str) or not _HEAD.fullmatch(head):
        raise ValueError("BSA315_INVALID_STAGE_CHECKPOINT_HEAD")
    return private/"owner-science-stage-checkpoints"/head/_NAME


def record_completed_owner_step(*,private:Path,head:str,step:int,
                                action:str,elapsed_seconds:int)->dict:
    if (type(step) is not int or not 1<=step<=20
        or type(elapsed_seconds) is not int or elapsed_seconds<0
        or not isinstance(action,str) or not _STEP_ACTION.fullmatch(action)):
        raise ValueError("BSA315_INVALID_OWNER_STAGE_TELEMETRY")
    target=_target(private,head)
    parent=target.parent
    if parent.is_symlink() or parent.parent.is_symlink() or target.is_symlink():
        raise ValueError("BSA315_UNSAFE_STAGE_CHECKPOINT")
    parent.mkdir(parents=True,exist_ok=True)
    previous=read_completed_owner_step(private=private,head=head)
    if previous is not None and step<previous["lastCompletedStep"]:
        # A restarted owner may verify an earlier step again; leave the
        # higher checkpoint intact until actual signed receipts revalidate.
        return previous
    body={
        "status":"BSA315_OWNER_STEP_FINISHED_TELEMETRY_ONLY",
        "head":head,
        "lastCompletedStep":step,
        "lastCompletedAction":action,
        "elapsedSeconds":elapsed_seconds,
        "observedAt":datetime.now(timezone.utc).isoformat(),
        "academicAcceptanceAdvanced":False,
        "signedSourceReverificationStillMandatory":True,
        "canSkipOriginalScienceOnRestart":False,
        "publicationAuthorized":False}
    record={**body,"integritySha256":_digest(body)}
    fd,tmp=tempfile.mkstemp(prefix=".bosla-stage-",suffix=".tmp",dir=parent)
    try:
        with os.fdopen(fd,"w",encoding="utf8") as out:
            json.dump(record,out,sort_keys=True,separators=(",",":"))
            out.write("\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp,target)
    finally:
        Path(tmp).unlink(missing_ok=True)
    return record


def read_completed_owner_step(*,private:Path,head:str)->dict|None:
    path=_target(private,head)
    if not path.exists() and not path.is_symlink():
        return None
    if path.is_symlink() or not path.is_file() or path.stat().st_size>4096:
        raise ValueError("BSA315_UNSAFE_STAGE_CHECKPOINT")
    try:
        payload=json.loads(path.read_text(encoding="utf8"))
    except (ValueError,OSError) as exc:
        raise ValueError("BSA315_STAGE_CHECKPOINT_UNREADABLE") from exc
    if (not isinstance(payload,dict)
        or payload.get("integritySha256")!=_digest({
            k:v for k,v in payload.items() if k!="integritySha256"})
        or payload.get("status")!="BSA315_OWNER_STEP_FINISHED_TELEMETRY_ONLY"
        or payload.get("head")!=head
        or type(payload.get("lastCompletedStep")) is not int
        or not 1<=payload["lastCompletedStep"]<=20
        or not isinstance(payload.get("lastCompletedAction"),str)
        or not _STEP_ACTION.fullmatch(payload["lastCompletedAction"])
        or payload.get("academicAcceptanceAdvanced") is not False
        or payload.get("signedSourceReverificationStillMandatory") is not True
        or payload.get("canSkipOriginalScienceOnRestart") is not False
        or payload.get("publicationAuthorized") is not False):
        raise ValueError("BSA315_STAGE_CHECKPOINT_NOT_AUTHENTIC")
    return payload

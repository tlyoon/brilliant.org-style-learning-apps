"""BSA315: bounded, same-invocation reuse of independently checked science.

No verification result is cached across processes, restarts or Git heads.
Every reuse *rehashes* the source PDF, signed scientific evidence and pinned
candidate bytes. A mismatched/missing file raises or forces real re-verification.
This module never signs, creates, or increases an academic-acceptance count.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from functools import wraps
from hashlib import sha256
from pathlib import Path
from time import perf_counter
import json
import re
import sys
from typing import Any, Callable, Iterator

from app_generator.runtime.v3_long_horizon_development import (
    read_long_horizon_development,
)
from app_generator.runtime.v3_selected_textbook_scientific_provenance import (
    _SOURCE_BINDING,
)
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_malay_auto_revision import _CANDIDATE
from app_generator.validation.section91_formal_physics import _SOURCE_SHA, _CANDIDATE_SHA

_HEAD=re.compile(r"[0-9a-f]{40}\Z")
_SHA=re.compile(r"[0-9a-f]{64}\Z")
_ACTIVE:ContextVar[dict|None]=ContextVar("bosla_bsa315_session",default=None)


def _signed_dependency_digest(private:Path)->tuple[str,str]:
    """Return (Git HEAD, entire relevant scientific dependency digest).

    Never rely on mtime or file size for integrity: hash the actual bytes.
    Avoid unrelated generated web/preview JSON in the large owner tree.
    Missing original evidence causes a miss and lets the full verifier fail.
    """
    ck=read_long_horizon_development(private)
    head=ck.get("gitHead")
    proposal=ck.get("proposalSha256")
    if not isinstance(head,str) or not _HEAD.fullmatch(head) or (
        not isinstance(proposal,str) or not _SHA.fullmatch(proposal)):
        raise ValueError("BSA315_INVALID_EXACT_VERIFICATION_HEAD")
    binding_path=private/_SOURCE_BINDING
    if binding_path.is_symlink() or not binding_path.is_file():
        raise ValueError("BSA315_SELECTED_SOURCE_BINDING_UNSAFE")
    binding=_trusted_json(binding_path)
    original=Path(binding["sourcePdf"])
    current=(private/"owner-five-stage-completion"/head/proposal/_CANDIDATE)
    if (original.is_symlink() or not original.is_file() or
        current.is_symlink() or not current.is_file()):
        raise ValueError("BSA315_SELECTED_SOURCE_OR_CANDIDATE_MISSING")
    orig_bytes=original.read_bytes()
    cand_bytes=current.read_bytes()
    if (sha256(orig_bytes).hexdigest()!=_SOURCE_SHA or
        sha256(cand_bytes).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA315_ORIGINAL_SOURCE_OR_CANDIDATE_MUTATED")
    h=sha256(b"BOSLA_BSA315_EXACT_SIGNED_SOURCE_DEPENDENCIES_V1\0")
    h.update(head.encode("ascii"))
    h.update(proposal.encode("ascii"))
    h.update(sha256(orig_bytes).digest())
    h.update(sha256(cand_bytes).digest())
    selected:set[Path]={binding_path}
    signed_root=private/"long-horizon-development"
    owner_root=private/"owner-five-stage-completion"
    if signed_root.is_symlink() or owner_root.is_symlink():
        raise ValueError("BSA315_SIGNED_PROOF_TREE_SYMLINK")
    frontiers=list(signed_root.rglob("*.json"))
    selected.update(frontiers)
    # Reopen only origin/current signed receipt folders referenced by
    # authenticated frontier data. Do NOT recursively crawl the 8,000+
    # unrelated generated-app files on every cache hit.
    pairs={(head,proposal)}
    for frontier in frontiers:
        if frontier.is_symlink() or not frontier.is_file() or frontier.stat().st_size>200_000:
            raise ValueError("BSA315_UNSAFE_SIGNED_FRONTIER")
        try:
            row=json.loads(frontier.read_text(encoding="utf8"))
        except (OSError,ValueError) as exc:
            raise ValueError("BSA315_UNREADABLE_SIGNED_FRONTIER") from exc
        if isinstance(row,dict):
            origin_head=row.get("gitHead")
            origin_proposal=row.get("proposalSha256")
            if (isinstance(origin_head,str) and _HEAD.fullmatch(origin_head)
                and isinstance(origin_proposal,str) and
                _SHA.fullmatch(origin_proposal)):
                pairs.add((origin_head,origin_proposal))
    for origin_head,origin_proposal in pairs:
        folder=owner_root/origin_head/origin_proposal
        if folder.is_symlink() or not folder.is_dir():
            raise ValueError("BSA315_MISSING_HISTORICAL_SIGNED_PROOF_FOLDER")
        for pattern in (
            "ACADEMIC*.json","BOSLA_ACADEMIC*.json",
            "V36_PARTITION_*.json","V36_EXACT_*.json",_CANDIDATE,
        ):
            selected.update(folder.glob(pattern))
    for path in sorted(selected,key=lambda x:str(x).casefold()):
        if path.is_symlink() or not path.is_file() or path.stat().st_size>20_000_000:
            raise ValueError("BSA315_SIGNED_DEPENDENCY_UNSAFE")
        relative=path.relative_to(private)
        h.update(str(relative).replace("\\","/").encode("utf8"))
        h.update(b"\0")
        h.update(sha256(path.read_bytes()).digest())
    return head,h.hexdigest()


@contextmanager
def verification_session(*,private:Path)->Iterator[dict]:
    """Cache only between beginning and end of ONE original owner invocation."""
    active=_ACTIVE.get()
    if active is not None:
        if active["private"]!=private.resolve():
            raise ValueError("BSA315_NESTED_FOREIGN_SOURCE_SESSION")
        yield active
        return
    session={"private":private.resolve(),"cache":{},
             "hits":0,"misses":0,"verifiedCalls":0,"rehashSeconds":0.0,
             "verifierSeconds":0.0,"invalidations":0}
    token=_ACTIVE.set(session)
    try:
        yield session
    finally:
        _ACTIVE.reset(token)
        # Telemetry is not an academic claim or evidence receipt.
        msg={k:session[k] for k in (
            "hits","misses","verifiedCalls","invalidations")}
        msg["rehashSeconds"]=round(session["rehashSeconds"],2)
        msg["verifierSeconds"]=round(session["verifierSeconds"],2)
        print("BSA315_SCIENCE_REUSE_TELEMETRY "+json.dumps(
            msg,sort_keys=True,separators=(",",":")),
            file=sys.stderr,flush=True)


def verified_stage_reuse(func:Callable[...,dict])->Callable[...,dict]:
    """Decorate existing exact-source verifiers without changing their proof.

    Only successful original-source independent verification can seed a hit.
    Rules objects (custom scientific verification policy) always bypass cache.
    """
    @wraps(func)
    def wrapped(*args:Any,**kwargs:Any)->dict:
        session=_ACTIVE.get()
        private=kwargs.get("private")
        if (session is None or args or not isinstance(private,Path)
            or private.resolve()!=session["private"]
            or set(kwargs)!={"private"}):
            return func(*args,**kwargs)
        start=perf_counter()
        try:
            head,digest=_signed_dependency_digest(private)
        except (OSError,ValueError,KeyError,TypeError):
            # Never turn a missing/mutated source into a cache hit.
            session["invalidations"]+=1
            return func(*args,**kwargs)
        session["rehashSeconds"]+=perf_counter()-start
        key=(func.__module__,func.__name__,head,digest)
        if key in session["cache"]:
            session["hits"]+=1
            return deepcopy(session["cache"][key])
        session["misses"]+=1
        start=perf_counter()
        result=func(*args,**kwargs)
        session["verifierSeconds"]+=perf_counter()-start
        session["verifiedCalls"]+=1
        if (isinstance(result,dict)
            and str(result.get("status","")).endswith("_REVERIFIED")
            and result.get("currentGitHead")==head
            and result.get("publicationAuthorized") is False
            and result.get("newProviderCalls")==0
            and type(result.get("independentlyAcceptedAcademicTasks")) is int):
            # If a verifier wrote evidence unexpectedly, the snapshot changed.
            # Record under the AFTER-verification digest only if identical.
            confirm_head,confirm_digest=_signed_dependency_digest(private)
            if (confirm_head,confirm_digest)==(head,digest):
                session["cache"][key]=deepcopy(result)
            else:
                session["invalidations"]+=1
        return result
    return wrapped


def scoped_owner_verification(func:Callable[...,dict])->Callable[...,dict]:
    @wraps(func)
    def wrapped(*args:Any,**kwargs:Any)->dict:
        private=kwargs.get("private")
        if not isinstance(private,Path):
            return func(*args,**kwargs)
        with verification_session(private=private):
            return func(*args,**kwargs)
    return wrapped

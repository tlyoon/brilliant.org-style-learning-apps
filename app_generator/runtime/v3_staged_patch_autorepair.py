"""BSA282: deterministic, fail-closed Git staged whitespace repair.

A harmless "new blank line at EOF" must not consume another Codex call
or strand future academic source-code development. The host may remove only
Git-identified trailing empty lines of already staged, allowed source/test
files, then restage and rerun the exact Git whitespace gate. Anything else
requires targeted code repair and preserves the patch without a false PASS.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any

_RE_BLANK_EOF=re.compile(r"^(?P<path>.+):(?P<line>[0-9]+): new blank line at EOF\.$")
_ALLOWED=("app_generator/","scripts/","tests/","docs/")
_ROOT_ALLOWED={"AGENTS.md","README.md"}
_MAX_BYTES=1_500_000
_MAX_FILES=25


def _git(repo:Path,*args:str)->subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git",*args],cwd=repo,capture_output=True,
                          check=False,timeout=45)


def _safe_file(repo:Path,name:str)->Path:
    """No links, traversal, source files, secrets or out-of-scope material."""
    if (not name or "\\" in name or "\x00" in name or
        name.startswith(".") or len(name)>240 or
        any(part in ("",".","..") for part in name.split("/")) or
        not (name.startswith(_ALLOWED) or name in _ROOT_ALLOWED) or
        any(t in name.lower() for t in (
            ".env","secret","credential","token","private_source",
            "source.pdf",".pem",".pfx",".p12")) or
        Path(name).suffix.lower() not in (".py",".js",".ts",".tsx",
                                         ".json",".md",".css",".html")):
        raise ValueError("BSA282_UNSAFE_PATCH_PATH")
    p=repo.joinpath(*PurePosixPath(name).parts)
    if (not p.resolve().is_relative_to(repo.resolve()) or
        any(component.is_symlink()
            for component in (p,*list(p.parents)[:len(PurePosixPath(name).parts)-1])) or
        not p.is_file() or p.stat().st_size>_MAX_BYTES):
        raise ValueError("BSA282_PATCH_NOT_A_SAFE_SMALL_REGULAR_FILE")
    return p


def repair_staged_blank_eof(repo:Path)->dict[str,Any]:
    """Repair one narrowly classified formatting issue, never scientific data."""
    check=_git(repo,"diff","--cached","--check")
    if check.returncode==0:
        return {"status":"ALREADY_CLEAN","fixedFiles":[]}
    if check.returncode!=2 or check.stderr:
        return {"status":"OTHER_GIT_DIFF_FAILURE","fixedFiles":[]}
    raw=check.stdout.decode("utf8","replace")
    reports=[x.strip() for x in raw.splitlines() if x.strip()]
    if (not reports or len(reports)>_MAX_FILES
        or any(_RE_BLANK_EOF.fullmatch(row) is None for row in reports)):
        return {"status":"UNCLASSIFIED_WHITESPACE_NOT_AUTO_REPAIRED",
                "fixedFiles":[]}
    staged=_git(repo,"diff","--cached","--name-only","-z")
    if staged.returncode:
        return {"status":"STAGED_FILE_LIST_UNAVAILABLE","fixedFiles":[]}
    included=set(x.decode("utf8") for x in staged.stdout.split(b"\0") if x)
    targets={_RE_BLANK_EOF.fullmatch(row).group("path") for row in reports}
    if not targets.issubset(included):
        raise ValueError("BSA282_WHITESPACE_REPORT_NOT_IN_STAGED_PATCH")
    # Validate *all* file paths and byte transformations before any writing.
    changes={}
    for name in sorted(targets):
        p=_safe_file(repo,name)
        raw=p.read_bytes()
        pieces=raw.splitlines(keepends=True)
        if len(pieces)<2:
            raise ValueError("BSA282_REPORTED_BLANK_LINES_NOT_PRESENT")
        while len(pieces)>1 and not pieces[-1].strip():
            pieces.pop()
        fixed=b"".join(pieces)
        if (fixed==raw or not fixed.endswith((b"\n",b"\r\n"))
            or not raw.startswith(fixed)
            or raw[len(fixed):].strip()):
            raise ValueError("BSA282_NON_EOF_OR_NONBLANK_PATCH_QUARANTINED")
        changes[name]=(p,raw,fixed)
    # Deterministic local repair; no scientific/material text modification.
    for name,(p,raw,fixed) in changes.items():
        p.write_bytes(fixed)
        if _git(repo,"add","--",name).returncode:
            raise ValueError("BSA282_REPAIR_RESTAGE_FAILED")
    final=_git(repo,"diff","--cached","--check")
    if final.returncode:
        raise ValueError("BSA282_RECHECK_STILL_HAS_WHITESPACE_ERRORS")
    return {
        "status":"REPAIRED_EXACT_BLANK_LINES_AT_EOF",
        "fixedFiles":sorted(changes),
        "beforeAfterSha256":{
            name:{"before":sha256(raw).hexdigest(),
                  "after":sha256(fixed).hexdigest()}
            for name,(_,raw,fixed) in changes.items()
        },
        "academicPASS":False,
        "publicationAuthorized":False,
    }

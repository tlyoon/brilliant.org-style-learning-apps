"""BSA280: safe, Git-less Codex coding snapshot from tracked Bosla source.

The owner Codex standalone writable sandbox passed on Yoga6, but Git-linked
worktrees under LOCALAPPDATA repeatedly made its Windows sandbox fail before
a tool could create files. A disposable, no-.git snapshot avoids that workspace
identity/permission boundary. The *host* revalidates every allowed patch in its
separate clean Git worktree and owns commits, tests and CI. No outside PDFs.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path, PurePosixPath
import shutil
import subprocess
from typing import Any

_ALLOWED_PREFIXES=("app_generator/","scripts/","tests/","docs/")
_ALLOWED_ROOT_FILES={"AGENTS.md","README.md"}
_FORBIDDEN=(".env","secret","credential","token","keyfile",
            "private_source","source.pdf")
_MAX_FILE_BYTES=1_500_000
_MAX_PATCH_FILES=60
_MAX_PATCH_BYTES=4_000_000


def _safe_name(name:str)->bool:
    if not isinstance(name,str) or not name or "\\" in name:
        return False
    path=PurePosixPath(name)
    return (not path.is_absolute()
            and not any(part in (".","..","") for part in name.split("/"))
            and not name.startswith(".git")
            and not any(bit in name.lower() for bit in _FORBIDDEN)
            and not name.lower().endswith((".pdf",".pem",".p12",".pfx"))
            and len(name)<240)


def _safe_patch_path(name:str)->bool:
    return (_safe_name(name)
            and (name.startswith(_ALLOWED_PREFIXES) or
                 name in _ALLOWED_ROOT_FILES))


def _tracked(repo:Path)->list[str]:
    proc=subprocess.run(
        ["git","ls-files","--cached","--others","--exclude-standard","-z"],
        cwd=repo,capture_output=True,check=False,timeout=45)
    if proc.returncode!=0:
        raise ValueError("BSA280_SOURCE_WORKTREE_LIST_UNAVAILABLE")
    paths=[x.decode("utf8") for x in proc.stdout.split(b"\0") if x]
    if len(paths)!=len(set(paths)):
        raise ValueError("BSA280_DUPLICATED_SOURCE_PATH")
    return paths


def _sha(data:bytes)->str:
    return sha256(data).hexdigest()


def _contents(path:Path)->bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError("BSA280_LINK_OR_NONFILE_REJECTED")
    if path.stat().st_size>_MAX_FILE_BYTES:
        raise ValueError("BSA280_OVERSIZE_FILE_REJECTED")
    return path.read_bytes()


def build_isolated_coding_snapshot(
    *,repo:Path,snapshot:Path,
)->dict[str,str]:
    """Copies only safe repository files, never private PDFs or .git."""
    if snapshot.exists():
        raise ValueError("BSA280_SNAPSHOT_MUST_BE_NEW")
    snapshot.mkdir(parents=True)
    hashes:dict[str,str]={}
    for name in _tracked(repo):
        if not _safe_name(name):
            continue  # Ignore excluded source files; never expose them to AI.
        source=repo.joinpath(*name.split("/"))
        if not source.is_file() or source.is_symlink():
            continue  # Repo-supplied symlinks are never followed.
        if source.stat().st_size>_MAX_FILE_BYTES:
            continue
        data=_contents(source)
        target=snapshot.joinpath(*name.split("/"))
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
        hashes[name]=_sha(data)
    if not {"AGENTS.md","docs/recurrence_registry.json"}.issubset(hashes):
        raise ValueError("BSA280_CODING_SNAPSHOT_MISSING_CONTEXT")
    return hashes


def collect_isolated_patch(
    *,snapshot:Path,baseline:dict[str,str],
)->dict[str,bytes]:
    """Fail closed on deletions, symlinks, invisible files and unsafe scopes."""
    if not snapshot.is_dir() or snapshot.is_symlink():
        raise ValueError("BSA280_SNAPSHOT_MISSING")
    all_files={}
    for entry in snapshot.rglob("*"):
        if entry.is_symlink():
            raise ValueError("BSA280_CODEX_SYMLINK_PATCH_QUARANTINED")
        if entry.is_dir():
            continue
        if not entry.is_file():
            raise ValueError("BSA280_CODEX_NONFILE_PATCH_QUARANTINED")
        name=entry.relative_to(snapshot).as_posix()
        if name.startswith("__pycache__/") or "/__pycache__/" in name:
            continue
        if name.endswith((".pyc",".pyo")):
            continue
        if not _safe_name(name):
            raise ValueError("BSA280_CODEX_UNSAFE_NEW_PATH_QUARANTINED")
        data=_contents(entry)
        all_files[name]=_sha(data)
    if set(baseline)-set(all_files):
        raise ValueError("BSA280_CODEX_DELETED_SOURCE_QUARANTINED")
    changed={name for name,digest in all_files.items()
             if baseline.get(name)!=digest}
    if (len(changed)>_MAX_PATCH_FILES or
        sum((snapshot.joinpath(*n.split("/")).stat().st_size)
            for n in changed)>_MAX_PATCH_BYTES):
        raise ValueError("BSA280_CODEX_OVERSIZE_PATCH_QUARANTINED")
    if any(not _safe_patch_path(n) for n in changed):
        raise ValueError("BSA280_CODEX_UNAPPROVED_SCOPE_QUARANTINED")
    if changed and not any(
        n.startswith(("app_generator/","scripts/"))
        and n.endswith((".py",".js",".ts",".tsx")) for n in changed):
        raise ValueError("BSA280_DOCS_ONLY_NOT_DEVELOPMENT")
    return {name:_contents(snapshot.joinpath(*name.split("/")))
            for name in sorted(changed)}


def apply_isolated_patch(
    *,repo:Path,snapshot:Path,baseline:dict[str,str],
)->list[str]:
    """Owner-host-only patch adoption. Does not grant academic acceptance."""
    patch=collect_isolated_patch(snapshot=snapshot,baseline=baseline)
    for name,data in patch.items():
        dest=repo.joinpath(*name.split("/"))
        if dest.exists() and dest.is_symlink():
            raise ValueError("BSA280_HOST_DESTINATION_SYMLINK_REJECTED")
        # Same original file must still be present if it was in baseline.
        # No model patch is allowed to overwrite concurrently modified work.
        if name in baseline:
            if not dest.is_file() or _sha(_contents(dest))!=baseline[name]:
                raise ValueError("BSA280_SOURCE_CHANGED_WHILE_MODEL_RAN")
        elif dest.exists():
            raise ValueError("BSA280_NEW_FILE_RACE_OR_REPLACEMENT")
    for name,data in patch.items():
        dest=repo.joinpath(*name.split("/"))
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(data)
    return list(patch)

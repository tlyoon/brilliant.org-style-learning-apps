"""BOSLA V11: read-only pinned GitHub Pages patch rehearsal.

This does NOT create a remote branch, PR, push, merge or deploy.
It runs only after genuine source-bound V10 Chrome bundle acceptance.
"""
from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_public_deployment_scope import _DEST, _MAIN
from app_generator.runtime.v3_pinned_public_release_proposal import _FOLDER
from app_generator.runtime.v3_public_release_browser_acceptance import (
    _preflight as _v10_preflight, _V10, _STATUS as _V10_STATUS,
)
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint

_V11="V11_PINNED_NONDESTRUCTIVE_PRIVATE_PUBLIC_RELEASE_PATCH.json"
_PATCH="v11-rehearsed-pinned-public-release.patch"
_STATUS="PINNED_THREE_SECTION_PRIVATE_PUBLIC_PATCH_REHEARSED_NO_PUBLIC_WRITE"
_CHAPTER_ROUTES=("section-9-1","section-9-2","section-9-6")
_ALLOW_GIT={"clone","rev-parse","add","diff","apply","ls-remote"}


def _git(argv:list[str], *, cwd:Path|None=None, timeout:int=120)->bytes:
    if (len(argv)<2 or argv[0]!="git"
            or argv[1] not in _ALLOW_GIT):
        raise ValueError("V11_UNAUTHORIZED_GIT_ACTION")
    try:
        cp=subprocess.run(argv,cwd=cwd,capture_output=True,check=False,
                          timeout=timeout)
    except (OSError,subprocess.TimeoutExpired) as error:
        raise ValueError("V11_PRIVATE_GIT_OPERATION_UNAVAILABLE") from error
    if cp.returncode:
        raise ValueError("V11_PRIVATE_GIT_"+argv[1].upper()+"_FAILED")
    return cp.stdout


def _verify_receipt(folder:Path,v10_result:dict)->dict:
    receipt=_trusted_json(folder/_V10)
    if (receipt!=v10_result
            or receipt.get("status")!=_V10_STATUS
            or receipt.get("realHeadlessChromeRoutesPassed")!=3
            or receipt.get("privateProductionBundleFilesVerified")!=24
            or receipt.get("publicDeployExecuted") is not False
            or receipt.get("publicationAuthorized") is not False
            or receipt.get("integritySha256")!=_hash(
                {k:v for k,v in receipt.items() if k!="integritySha256"})):
        raise ValueError("V11_SIGNED_V10_PROOF_CHANGED")
    return receipt


def _make_patch(source:Path,destination:Path)->list[str]:
    for section in _CHAPTER_ROUTES:
        public=destination/section
        replacement=source/section
        if (public.is_symlink() or replacement.is_symlink()
                or not public.is_dir() or not replacement.is_dir()
                or any(p.is_symlink() for p in public.rglob("*"))
                or any(p.is_symlink() for p in replacement.rglob("*"))):
            raise ValueError("V11_UNSAFE_EXISTING_PUBLIC_ROUTE")
        shutil.rmtree(public)
        shutil.copytree(replacement,public)
    _git(["git","add","--",*_CHAPTER_ROUTES],cwd=destination)
    changed=_git(["git","diff","--cached","--name-only"],
                 cwd=destination).decode("utf8").splitlines()
    if (len(changed)!=21
            or not all(path.startswith(tuple(s+"/" for s in _CHAPTER_ROUTES))
                       for path in changed)
            or any(sum(p.startswith(s+"/") for p in changed)!=7
                   for s in _CHAPTER_ROUTES)
            or any(path.endswith(".nojekyll") for path in changed)):
        raise ValueError("V11_CHANGED_PATH_SCOPE_NOT_EXACT")
    _git(["git","diff","--cached","--check"],cwd=destination)
    return changed


def stage_exact_private_public_patch(
    repo:Path,private:Path,ready:dict,v9_result:dict,v10_result:dict,
)->dict:
    """Continue after real V10 with an immutable private-only patch preview."""
    folder,source,v9=_v10_preflight(repo,private,ready,v9_result)
    v10=_verify_receipt(folder,v10_result)
    if (v10.get("sourceV9ReceiptSha256")!=v9["integritySha256"]
            or v10.get("publicMainPinnedSha")!=_MAIN
            or v9.get("publicMainPinnedSha")!=_MAIN
            or v9.get("publicDestination")!=_DEST):
        raise ValueError("V11_V9_V10_PUBLIC_BASE_PROOF_MISMATCH")
    private_patch=folder/_PATCH
    private_receipt=folder/_V11
    if private_patch.is_symlink() or private_receipt.is_symlink():
        raise ValueError("V11_PRIVATE_PATCH_OR_RECEIPT_SYMLINK")
    target="https://github.com/"+_DEST+".git"
    # Keep temporary Git clones short: deep per-commit evidence paths
    # exceed Windows legacy MAX_PATH even on the owner-authorized Yoga6.
    with tempfile.TemporaryDirectory(prefix="bosla-v11-",dir=private) as temp:
        tempdir=Path(temp)
        checkout=tempdir/"site"
        _git(["git","clone","--depth","1","--branch","main",target,
              str(checkout)])
        initial=_git(["git","rev-parse","HEAD"],cwd=checkout).decode().strip()
        if initial!=_MAIN:
            raise ValueError("V11_EXISTING_PUBLIC_MAIN_REVISION_CHANGED")
        changed=_make_patch(source,checkout)
        patch=_git(["git","diff","--cached","--binary"],cwd=checkout)
        if not (1024<len(patch)<5_000_000):
            raise ValueError("V11_UNEXPECTED_BINARY_PATCH_SIZE")
        verify=tempdir/"verify"
        _git(["git","clone","--depth","1","--branch","main",target,str(verify)])
        if _git(["git","rev-parse","HEAD"],cwd=verify).decode().strip()!=_MAIN:
            raise ValueError("V11_INDEPENDENT_GIT_BASE_REVISION_CHANGED")
        temporary=tempdir/"release.patch"
        temporary.write_bytes(patch)
        _git(["git","apply","--check",str(temporary)],cwd=verify)
        remote=_git(["git","ls-remote","--heads",target,
                     "refs/heads/main"]).decode().split()
        if len(remote)!=2 or remote[0]!=_MAIN:
            raise ValueError("V11_PUBLIC_MAIN_CHANGED_DURING_REHEARSAL")
        if private_patch.exists():
            if private_patch.read_bytes()!=patch:
                raise ValueError("V11_EXISTING_PRIVATE_PATCH_CHANGED_ON_RESTART")
        else:
            fd,tmp=tempfile.mkstemp(prefix=".v11-patch-",dir=folder)
            try:
                with os.fdopen(fd,"wb") as out:
                    out.write(patch)
                    out.flush()
                    os.fsync(out.fileno())
                os.replace(tmp,private_patch)
            finally:
                Path(tmp).unlink(missing_ok=True)
    payload={
        "contract":"BOSLA_V11_PINNED_NONDESTRUCTIVE_PRIVATE_PUBLIC_PATCH_V1",
        "status":_STATUS,"gitHead":ready["gitHead"],
        "proposalSha256":ready["proposalSha256"],
        "sourceV10ReceiptSha256":v10["integritySha256"],
        "sourceV9ReceiptSha256":v9["integritySha256"],
        "publicDestination":_DEST,"publicMainPinnedSha":_MAIN,
        "changedSections":list(_CHAPTER_ROUTES),
        "changedFilePaths":changed,
        "changedFileCount":len(changed),"privatePatchBytes":len(patch),
        "privatePatchSha256":sha256(patch).hexdigest(),
        "gitApplyCheckAgainstIndependentCleanPinnedMain":True,
        "nextEligibleMilestone":"SCOPED_NONMERGING_PUBLIC_PR_PREPARATION",
        "newModelCalls":0,"publicPRCreated":False,
        "publicPushExecuted":False,"publicMergeExecuted":False,
        "publicDeployExecuted":False,"publicationAuthorized":False,
    }
    return _v6_checkpoint(private_receipt,payload)

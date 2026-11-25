"""BOSLA V12 — private reviewable PR proposal, never a remote Git write.

A genuine accepted V11 automatically dispatches exact-scope V12 in the
source-free normal worker. V12 produces a local immutable PR explanation
and signed proposal receipt. It does not create GitHub branches or PRs,
publish content, or reinstall the owner-retired Windows scheduler.
"""
from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
import re
import tempfile

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_public_release_browser_acceptance import _preflight as _v9_preflight
from app_generator.runtime.v3_private_public_patch_rehearsal import (
    _V11, _PATCH, _STATUS as _V11_STATUS, _CHAPTER_ROUTES, _git,
)
from app_generator.runtime.v3_public_deployment_scope import _DEST, _MAIN

_V12="V12_PRIVATE_NONMERGING_PR_READINESS.json"
_DRAFT="V12_PRIVATE_NONMERGING_PR_DRAFT.md"
_STATUS="PRIVATE_SCOPED_NONMERGING_PR_DRAFT_VERIFIED_NO_REMOTE_WRITE"
_ALLOWED=("section-9-1","section-9-2","section-9-6")


def _signed_v11(folder:Path,result:dict)->dict:
    receipt=_trusted_json(folder/_V11)
    if (receipt!=result or receipt.get("status")!=_V11_STATUS
            or receipt.get("changedFileCount")!=21
            or receipt.get("changedSections")!=list(_CHAPTER_ROUTES)
            or receipt.get("publicMainPinnedSha")!=_MAIN
            or receipt.get("publicDestination")!=_DEST
            or receipt.get("gitApplyCheckAgainstIndependentCleanPinnedMain") is not True
            or any(receipt.get(key) is not False for key in
                   ("publicPRCreated","publicPushExecuted","publicMergeExecuted",
                    "publicDeployExecuted","publicationAuthorized"))
            or receipt.get("integritySha256")!=_hash(
                {k:v for k,v in receipt.items() if k!="integritySha256"})):
        raise ValueError("V12_SIGNED_V11_PROOF_INVALID")
    return receipt


def _verify_patch_and_exact_scope(folder:Path,v11:dict)->list[str]:
    patch_file=folder/_PATCH
    if (patch_file.is_symlink() or not patch_file.is_file()
            or patch_file.stat().st_size>5_000_000):
        raise ValueError("V12_PRIVATE_PATCH_MISSING_OR_UNSAFE")
    patch=patch_file.read_bytes()
    if (len(patch)!=v11.get("privatePatchBytes")
            or sha256(patch).hexdigest()!=v11.get("privatePatchSha256")):
        raise ValueError("V12_PRIVATE_PATCH_HASH_CHANGED")
    headers=[line for line in patch.splitlines()
             if line.startswith(b"diff --git ")]
    if len(headers)!=21:
        raise ValueError("V12_PATCH_HEADERS_SCOPE_INVALID")
    paths=[]
    for line in headers:
        match=re.fullmatch(rb"diff --git a/(section-9-[0-9]/[A-Za-z0-9./_-]+) b/\1",line)
        if not match:
            raise ValueError("V12_PATCH_HEADER_UNSAFE_OR_MISMATCHED")
        path=match.group(1).decode("ascii")
        if (".." in Path(path).parts or not path.startswith(tuple(
                section+"/" for section in _ALLOWED))):
            raise ValueError("V12_PATCH_OUT_OF_SCOPE")
        paths.append(path)
    if (paths!=v11.get("changedFilePaths")
            or len(set(paths))!=21
            or any(sum(path.startswith(section+"/") for path in paths)!=7
                   for section in _ALLOWED)):
        raise ValueError("V12_PATCH_CHANGED_PATH_LIST_MISMATCH")
    return paths


def _persist_immutable_markdown(path:Path,content:str)->str:
    if path.is_symlink():
        raise ValueError("V12_DRAFT_IS_SYMLINK")
    payload=content.encode("utf8")
    if path.exists():
        if not path.is_file() or path.read_bytes()!=payload:
            raise ValueError("V12_EXISTING_DRAFT_CHANGED_ON_RESTART")
    else:
        fd,tmp=tempfile.mkstemp(prefix=".v12-draft-",dir=path.parent)
        try:
            with os.fdopen(fd,"wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp,path)
        finally:
            Path(tmp).unlink(missing_ok=True)
    return sha256(payload).hexdigest()


def stage_private_nonmerging_pr_draft(
    repo:Path,private:Path,ready:dict,v9_result:dict,v11_result:dict,
)->dict:
    """Stage the next private milestone after genuine V11; no remote write."""
    folder,source,v9=_v9_preflight(repo,private,ready,v9_result)
    v11=_signed_v11(folder,v11_result)
    if (v11.get("gitHead")!=ready.get("gitHead")
            or v11.get("proposalSha256")!=ready.get("proposalSha256")
            or v11.get("sourceV9ReceiptSha256")!=v9.get("integritySha256")):
        raise ValueError("V12_PROPOSAL_SOURCE_IDENTITY_CHANGED")
    paths=_verify_patch_and_exact_scope(folder,v11)
    target="https://github.com/"+_DEST+".git"
    remote=_git(["git","ls-remote","--heads",target,
                 "refs/heads/main"]).decode("ascii").split()
    if (len(remote)!=2 or remote[0]!=_MAIN
            or remote[1]!="refs/heads/main"):
        raise ValueError("V12_PUBLIC_BASE_CHANGED")
    digest=v11["privatePatchSha256"]
    branch="bosla/private-ch9-three-section-"+digest[:12]
    title="BOSLA Chapter 9: verified Sections 9.1, 9.2 and 9.6 (review only)"
    draft=(
        "# PRIVATE PROPOSAL — NOT A CREATED GITHUB PULL REQUEST\n\n"
        "This local draft is for an eventual **non-merging, review-only** change.\n"
        "It was produced from owner Yoga6 signed private V9–V11 receipts.\n\n"
        "## Proposed change\n\n"
        "Update the three existing public Chapter 9 routes: Section 9.1, "
        "Section 9.2, Section 9.6. Exactly 21 Git paths change (7 per route).\n"
        "No other public route, including Sections 9.3–9.5 or 9.7–9.9, changes.\n\n"
        "## Immutable provenance\n\n"
        "- Proposed branch (not created): `"+branch+"`\n"
        "- Base: `"+_DEST+"` public `main`, SHA `"+_MAIN+"`\n"
        "- BOSLA source head: `"+ready["gitHead"]+"`\n"
        "- Versioned course proposal: `"+ready["proposalSha256"]+"`\n"
        "- Signed V11 receipt: `"+v11["integritySha256"]+"`\n"
        "- Private patch SHA-256: `"+digest+"`\n"
        "- Git paths: 21, independent clean-base `git apply --check` passed.\n\n"
        "## Safety and acceptance\n\n"
        "The real 3-route Chrome acceptance and the 24-file private production "
        "bundle manifest were verified in predecessor evidence. This is NOT "
        "independent public release approval, automated publication, or a "
        "claim of a user/learner pilot. Old unresolved scientific/provider "
        "decisions remain unchanged. No GitHub branch was pushed; no PR "
        "was created or merged and no public deployment occurred.\n\n"
        "## Changed routes\n\n"
        + "".join("- `"+route+"`\n" for route in _ALLOWED)
        + "\n## Proposed title\n\n"+title+"\n"
    )
    draft_sha=_persist_immutable_markdown(folder/_DRAFT,draft)
    payload={
        "contract":"BOSLA_V12_PRIVATE_NONMERGING_PR_READINESS_V1",
        "status":_STATUS,
        "gitHead":ready["gitHead"],
        "proposalSha256":ready["proposalSha256"],
        "sourceV11ReceiptSha256":v11["integritySha256"],
        "publicDestination":_DEST,"publicMainPinnedSha":_MAIN,
        "proposedBranchNotCreated":branch,
        "proposedPullRequestTitle":title,
        "changedSections":list(_ALLOWED),
        "changedFileCount":len(paths),
        "privatePatchSha256":digest,
        "privateDraftSha256":draft_sha,
        "remoteMainStillPinned":True,
        "nextEligibleMilestone":"PUBLIC_NONMERGING_PR_AUTHORIZATION_OR_INDEPENDENT_OTHER_BOUNDARY",
        "paidModelCalls":0,"publicPRCreated":False,
        "publicPushExecuted":False,"publicMergeExecuted":False,
        "publicDeployExecuted":False,"publicationAuthorized":False,
        "scheduledTaskCreated":False,
    }
    return _v6_checkpoint(folder/_V12,payload)

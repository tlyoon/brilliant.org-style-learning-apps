"""BOSLA V13: idempotent public *draft PR*, never merge or deploy.

Reuse BSA228 non-auto-merge and BSA233 signed, scoped 21-file proposal.
Public writes are limited to an immutable review branch and draft PR.
Pre-call checkpoints and GitHub read-reconciliation make crash replay safe.
The owner-retired Yoga6 scheduled task is never recreated.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_private_nonmerging_pr_readiness import (
    _V12, _DRAFT, _STATUS as _V12_STATUS, _v9_preflight,
    _signed_v11, _verify_patch_and_exact_scope,
)
from app_generator.runtime.v3_private_public_patch_rehearsal import _PATCH
from app_generator.runtime.v3_public_deployment_scope import _DEST, _MAIN

_V13="V13_REAL_NONMERGING_DRAFT_PR_RECEIPT.json"
_PREPARE="V13_PRE_CALL_PUBLIC_DRAFT_PR.json"
_STATUS="SCOPED_PUBLIC_DRAFT_PR_OPEN_UNMERGED_MAIN_UNCHANGED"
_REPO="tlyoon/section-8-1-learning-app"
_REMOTE="https://github.com/"+_REPO+".git"
_GIT_SAFE={"clone","rev-parse","diff","apply","add","commit",
           "ls-remote","fetch","status","config","push"}
_ALLOWED_ROUTES=("section-9-1","section-9-2","section-9-6")


def _git(argv:list[str],cwd:Path|None=None,timeout:int=120)->str:
    if (len(argv)<2 or argv[0]!="git" or argv[1] not in _GIT_SAFE
            or (argv[1]=="push" and
                not (len(argv)==5 and argv[:3]==["git","push","--porcelain"]
                     and argv[3]=="origin"
                     and argv[4].startswith("HEAD:refs/heads/bosla/private-ch9-three-section-")))):
        raise ValueError("V13_UNAUTHORIZED_GIT_COMMAND")
    try:
        result=subprocess.run(argv,cwd=cwd,check=False,capture_output=True,
                              text=True,timeout=timeout,encoding="utf8",
                              errors="replace")
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise ValueError("V13_GIT_OPERATION_UNAVAILABLE_"+argv[1]) from exc
    if result.returncode:
        raise ValueError("V13_GIT_"+argv[1].upper()+"_FAILED")
    return result.stdout.strip()


def _gh(argv:list[str],*,timeout:int=60)->str:
    if not (argv[:2]==["gh","api"] and len(argv)>=4 and
            argv[2]=="--method" and argv[3]=="GET"
            or argv[:3]==["gh","pr","create"] and
            argv.count("--draft")==1 and "--repo" in argv and
            "--head" in argv and "--base" in argv and
            "--body-file" in argv and "--title" in argv):
        raise ValueError("V13_UNAUTHORIZED_GH_COMMAND")
    try:
        result=subprocess.run(argv,capture_output=True,text=True,
                              check=False,timeout=timeout,
                              encoding="utf8",errors="replace")
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise ValueError("V13_GH_COMMAND_UNAVAILABLE") from exc
    if result.returncode:
        raise ValueError("V13_GH_COMMAND_FAILED")
    return result.stdout.strip()


def _ls_remote(branch:str)->str|None:
    items=_git(["git","ls-remote","--heads",_REMOTE,
                "refs/heads/"+branch]).split()
    if not items:
        return None
    if (len(items)!=2 or not re.fullmatch("[0-9a-f]{40}",items[0])
            or items[1]!="refs/heads/"+branch):
        raise ValueError("V13_BAD_REMOTE_BRANCH_IDENTITY")
    return items[0]


def _public_pr_list(branch:str)->list[dict]:
    # An exact query plus independent field filtering prevents duplicate PRs.
    raw=_gh(["gh","api","--method","GET",
             "repos/"+_REPO+"/pulls?state=all&per_page=100"])
    data=json.loads(raw)
    if not isinstance(data,list):
        raise ValueError("V13_INVALID_PR_LIST")
    matches=[p for p in data if isinstance(p,dict)
             and p.get("head",{}).get("ref")==branch]
    return matches


def _ensure_public_main()->None:
    branch_sha=_ls_remote("main")
    if branch_sha!=_MAIN:
        raise ValueError("V13_PROTECTED_PUBLIC_MAIN_CHANGED")


def _make_body(v12:dict,v11:dict)->str:
    return (
        "## Review only — NOT merged or deployed\n\n"
        "This is a non-merging **draft** PR. It does not request "
        "automatic publication or bypass any remaining acceptance gate.\n\n"
        "Exactly 21 Git paths in Sections 9.1, 9.2 and 9.6 are staged. "
        "Existing Sections 9.3–9.5 and 9.7–9.9 remain unchanged.\n\n"
        "### Verifiable scope and evidence\n\n"
        "- Public base main SHA: `"+_MAIN+"`\n"
        "- BOSLA source head: `"+v12["gitHead"]+"`\n"
        "- Versioned proposal SHA: `"+v12["proposalSha256"]+"`\n"
        "- Signed private V12 receipt: `"+v12["integritySha256"]+"`\n"
        "- Signed V11 receipt: `"+v11["integritySha256"]+"`\n"
        "- Patch SHA-256: `"+v11["privatePatchSha256"]+"`\n"
        "- Source: genuine production release bundles and real Chrome "
        "acceptance, with independently verified pinned-base patch.\n\n"
        "Unresolved historical C3 generalization remains "
        "`FAILED_LIMITED_CAMPAIGN`. Public release remains unapproved. "
        "Please keep this PR unmerged until the separate release decision.\n"
    )


def _preflight(repo:Path,private:Path,ready:dict,v9_result:dict,
               v11_result:dict,v12_result:dict):
    if _DEST!=_REPO:
        raise ValueError("V13_PUBLIC_REPOSITORY_CHANGED")
    folder,_,v9=_v9_preflight(repo,private,ready,v9_result)
    v11=_signed_v11(folder,v11_result)
    paths=_verify_patch_and_exact_scope(folder,v11)
    v12=_trusted_json(folder/_V12)
    if (v12!=v12_result or v12.get("status")!=_V12_STATUS
            or v12.get("integritySha256")!=_hash(
                {k:v for k,v in v12.items() if k!="integritySha256"})
            or v12.get("sourceV11ReceiptSha256")!=v11["integritySha256"]
            or v12.get("publicDestination")!=_REPO
            or v12.get("publicMainPinnedSha")!=_MAIN
            or v12.get("gitHead")!=ready.get("gitHead")
            or v12.get("proposalSha256")!=ready.get("proposalSha256")
            or v12.get("changedSections")!=list(_ALLOWED_ROUTES)
            or v12.get("changedFileCount")!=21
            or v12.get("privatePatchSha256")!=v11["privatePatchSha256"]
            or not v12.get("remoteMainStillPinned")
            or v11.get("sourceV9ReceiptSha256")!=v9["integritySha256"]
            or any(v12.get(field) is not False for field in
                   ("publicPRCreated","publicPushExecuted",
                    "publicMergeExecuted","publicDeployExecuted",
                    "publicationAuthorized","scheduledTaskCreated"))):
        raise ValueError("V13_SIGNED_V12_RELEASE_SCOPE_INVALID")
    draft_file=folder/_DRAFT
    if (draft_file.is_symlink() or not draft_file.is_file()
            or sha256(draft_file.read_bytes()).hexdigest()!=v12["privateDraftSha256"]):
        raise ValueError("V13_V12_IMMUTABLE_DRAFT_CHANGED")
    branch=v12.get("proposedBranchNotCreated")
    if (not isinstance(branch,str)
            or not re.fullmatch(
                r"bosla/private-ch9-three-section-[0-9a-f]{12}",branch)
            or branch.split("-")[-1]!=v11["privatePatchSha256"][:12]):
        raise ValueError("V13_UNSAFE_BRANCH_IDENTITY")
    if len(paths)!=21:
        raise ValueError("V13_UNEXPECTED_CHANGES")
    return folder,v11,v12,branch,paths


def _verify_existing_pr(pr:dict,branch:str,expected_sha:str):
    if (pr.get("state")!="open" or pr.get("draft") is not True
            or pr.get("merged_at") is not None
            or pr.get("base",{}).get("ref")!="main"
            or pr.get("head",{}).get("ref")!=branch
            or pr.get("head",{}).get("sha")!=expected_sha
            or pr.get("head",{}).get("repo",{}).get("full_name")!=_REPO
            or pr.get("base",{}).get("repo",{}).get("full_name")!=_REPO
            or not isinstance(pr.get("number"),int)
            or not str(pr.get("html_url","")).startswith(
                "https://github.com/"+_REPO+"/pull/")):
        raise ValueError("V13_EXISTING_PUBLIC_PR_UNSAFE_OR_MODIFIED")
    return pr


def _verify_remote_branch_tree(checkout:Path,branch:str,expected_tree:str):
    _git(["git","fetch","--no-tags","origin","refs/heads/"+branch],
         cwd=checkout)
    real_tree=_git(["git","rev-parse","FETCH_HEAD^{tree}"],cwd=checkout)
    if real_tree!=expected_tree:
        raise ValueError("V13_PUBLIC_BRANCH_REMOTE_TREE_MISMATCH")
    return _git(["git","rev-parse","FETCH_HEAD"],cwd=checkout)


def _safe_pr_reconcile(branch:str,head:str)->dict|None:
    all_prs=_public_pr_list(branch)
    if len(all_prs)>1:
        raise ValueError("V13_DUPLICATE_PR_HISTORY_REQUIRES_RECONCILIATION")
    if not all_prs:
        return None
    return _verify_existing_pr(all_prs[0],branch,head)


def dispatch_scoped_nonmerging_public_pr(
    repo:Path,private:Path,ready:dict,
    v9_result:dict,v11_result:dict,v12_result:dict,
)->dict:
    """Advance the safe non-merging public PR stage in the normal worker."""
    folder,v11,v12,branch,paths=_preflight(
        repo,private,ready,v9_result,v11_result,v12_result)
    _ensure_public_main()
    patch=folder/_PATCH
    with tempfile.TemporaryDirectory(prefix="bosla-v13-",dir=private) as root:
        checkout=Path(root)/"site"
        _git(["git","clone","--depth","1","--branch","main",_REMOTE,
              str(checkout)])
        if _git(["git","rev-parse","HEAD"],cwd=checkout)!=_MAIN:
            raise ValueError("V13_LOCAL_PUBLIC_BASE_CHANGED")
        _git(["git","apply","--check","--index",str(patch)],cwd=checkout)
        _git(["git","apply","--index",str(patch)],cwd=checkout)
        observed=_git(["git","diff","--cached","--name-only"],
                      cwd=checkout).splitlines()
        if observed!=paths:
            raise ValueError("V13_APPLIED_PATH_SCOPE_CHANGED")
        _git(["git","diff","--cached","--check"],cwd=checkout)
        _git(["git","config","user.name","BOSLA Verified Review"],cwd=checkout)
        _git(["git","config","user.email","noreply@users.noreply.github.com"],
             cwd=checkout)
        _git(["git","commit","-m","Review only: signed Chapter9 9.1,9.2,9.6 "
              +v11["privatePatchSha256"][:12]],cwd=checkout)
        local_tree=_git(["git","rev-parse","HEAD^{tree}"],cwd=checkout)
        current=_ls_remote(branch)
        # PRE_CALL is deliberately durable before the first remote write.
        # If a past push/PR call is uncertain, always inspect remote state.
        _v6_checkpoint(folder/_PREPARE,{
            "status":"PUBLIC_DRAFT_PR_PRECALL_RECONCILE_BEFORE_RETRY",
            "gitHead":ready["gitHead"],
            "sourceV12ReceiptSha256":v12["integritySha256"],
            "branch":branch,"expectedCommitTree":local_tree,
            "publicBaseSha":_MAIN,"mergeProhibited":True,
            "deployProhibited":True,
        })
        if current is None:
            _ensure_public_main()
            try:
                _git(["git","push","--porcelain","origin",
                      "HEAD:refs/heads/"+branch],cwd=checkout)
            except ValueError:
                # Reconcile uncertain push outcome; never blindly replay.
                if _ls_remote(branch) is None:
                    raise
            current=_ls_remote(branch)
            if current is None:
                raise ValueError("V13_PUBLIC_BRANCH_PUSH_UNCONFIRMED")
        verified_head=_verify_remote_branch_tree(checkout,branch,local_tree)
        if verified_head!=current:
            raise ValueError("V13_PUBLIC_BRANCH_CHANGED_DURING_RECONCILIATION")
        _ensure_public_main()
        existing=_safe_pr_reconcile(branch,verified_head)
        if existing is None:
            body=_make_body(v12,v11)
            body_file=Path(root)/"pr-body.md"
            body_file.write_text(body,encoding="utf8")
            try:
                _gh(["gh","pr","create","--repo",_REPO,
                     "--head",branch,"--base","main",
                     "--title",v12["proposedPullRequestTitle"],
                     "--body-file",str(body_file),"--draft"])
            except ValueError:
                # A possibly consumed PR create can only be reconciled
                # through GitHub state, never replayed automatically.
                existing=_safe_pr_reconcile(branch,verified_head)
                if existing is None:
                    raise
            existing=_safe_pr_reconcile(branch,verified_head)
            if existing is None:
                raise ValueError("V13_PR_CREATE_UNCONFIRMED")
        _ensure_public_main()
        receipt={
            "contract":"BOSLA_V13_REAL_NONMERGING_DRAFT_PUBLIC_PR_V1",
            "status":_STATUS,
            "gitHead":ready["gitHead"],
            "proposalSha256":ready["proposalSha256"],
            "sourceV12ReceiptSha256":v12["integritySha256"],
            "sourceV11ReceiptSha256":v11["integritySha256"],
            "publicDestination":_REPO,
            "publicBaseMainPinnedSha":_MAIN,
            "publicReviewBranch":branch,
            "publicReviewBranchSha":verified_head,
            "publicReviewTreeSha":local_tree,
            "publicPullRequestNumber":existing["number"],
            "publicPullRequestUrl":existing["html_url"],
            "publicPullRequestDraft":True,
            "publicPullRequestOpen":True,
            "publicMergeExecuted":False,
            "publicDeployExecuted":False,
            "publicationAuthorized":False,
            "scheduledTaskCreated":False,
            "changedSections":list(_ALLOWED_ROUTES),
            "changedFileCount":len(paths),
            "privatePatchSha256":v11["privatePatchSha256"],
            "remoteBaseRecheckedAfterPr":True,
            "nextEligibleMilestone":
                "INDEPENDENT_UNMERGED_PR_DIFF_CI_AND_SOURCE_VERSION_RECONCILIATION",
        }
        return _v6_checkpoint(folder/_V13,receipt)

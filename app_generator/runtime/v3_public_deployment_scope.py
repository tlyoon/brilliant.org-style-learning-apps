"""BSA227: read-only V8 public destination/permission scope check.

Not a publisher: clone, read and auth-inspect only, never push, merge or
deploy. Genuine frozen V7 is required. The baseline describes the already
public Chapter9 revision observed on 20 November 2026, not test fixtures.
"""
from __future__ import annotations
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import tomllib

from app_generator.runtime.v3_five_stage_completion import (
    _BASE, _candidate_dir, _hash,
)
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json, _V7
from app_generator.runtime.v3_versioned_readiness import (
    _git_info, _git_clean, _hosted_runs, _exact_ci_success,
)

_DEST="tlyoon/section-8-1-learning-app"
_URL="https://tlyoon.github.io/section-8-1-learning-app/"
_MAIN="eb86fe8eb94ec33f8c0c055d2423b245e5898241"
_PUBLIC_BASE={
    "section-9-1":"aa7b82fa8f256d02e7af1bb0ddfa8b91020b82d100175c14a37834eedb51ff7e",
    "section-9-2":"cfe7bab820aa01ce71bd7a6a334c742101ebd10d8895cccd5f05d599030f971c",
    "section-9-3":"c71398079f56fb8c752d6d9fa849e3b40a500fd538f2bb4dcb62a665c624b3da",
    "section-9-4":"1f6e2568fb6cbd5a82a7563c12f627779644ef3a991eb861e791849c49abc4d2",
    "section-9-5":"9152cc86789dcb43f898bd9a4f3cdfe4ea8928c09dccbcaed76fc83cf328431a",
    "section-9-6":"1620d15e1d645c81301997f0e42d0efbad0a7b2d123eb6b11cba9ec8c04b027f",
}
_CHANGED={"section-9-1":1,"section-9-2":1,"section-9-3":0,
          "section-9-4":0,"section-9-5":0,"section-9-6":3}
_V8="V8_PUBLIC_DEPLOYMENT_SCOPE_AND_PERMISSION.json"
_STATUS="EXISTING_PUBLIC_SIX_SECTION_SCOPE_AND_PERMISSION_VERIFIED_NO_DEPLOY"
_SHA40=re.compile(r"^[0-9a-f]{40}$")


def _proc(argv:list[str], *,cwd:Path|None=None,timeout:int=120)->str:
    """Only callers' fixed read-only git/gh commands; never print credentials."""
    if (argv[:2] not in ([ "git", "clone" ],[ "git", "ls-remote" ],
                          [ "git", "rev-parse" ],[ "gh", "api" ])):
        raise ValueError("V8_PUBLIC_SCOPE_WRITING_COMMAND_FORBIDDEN")
    try:
        done=subprocess.run(argv,cwd=cwd,text=True,capture_output=True,
                            check=False,timeout=timeout)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise ValueError("V8_PUBLIC_SCOPE_REMOTE_READ_FAILED") from None
    if done.returncode!=0 or len(done.stdout)>20000:
        raise ValueError("V8_PUBLIC_SCOPE_REMOTE_READ_FAILED")
    return done.stdout.strip()


def _config(repo:Path)->dict:
    file=repo/"config"/"configure_project.toml"
    if file.is_symlink() or not file.is_file():
        raise ValueError("V8_PUBLIC_SCOPE_MISSING_CONFIG")
    with file.open("rb") as stream:
        cfg=tomllib.load(stream)
    settings=cfg.get("automation",{})
    # Public deployment routing is defined under [automation].
    if (settings.get("public_deploy_repository")!=_DEST
            or settings.get("public_deploy_base_url")!=_URL
            or settings.get("public_deploy_base_branch")!="main"):
        raise ValueError("V8_PUBLIC_SCOPE_WRONG_DESTINATION_CONFIG")
    return cfg


def _permissions()->dict:
    raw=_proc(["gh","api","repos/"+_DEST,"--jq",
               "{full_name: .full_name, default_branch: .default_branch, "
               "private: .private, push: .permissions.push, "
               "admin: .permissions.admin, homepage: .homepage}"],timeout=30)
    try:
        data=json.loads(raw)
    except ValueError:
        raise ValueError("V8_PUBLIC_SCOPE_INVALID_GITHUB_PERMISSION") from None
    if (data.get("full_name")!=_DEST or data.get("default_branch")!="main"
            or data.get("private") is not False
            or data.get("push") is not True
            or data.get("admin") is not True
            or data.get("homepage")!=_URL):
        raise ValueError("V8_PUBLIC_SCOPE_PERMISSION_OR_HOME_MISMATCH")
    return {"authenticatedPushPermissionVerified":True,
            "authenticatedAdminPermissionVerified":True,
            "pagesBaseUrlMatches":True}


def _json_package(path:Path)->tuple[bytes,dict]:
    if (path.is_symlink() or not path.is_file()
            or path.stat().st_size>2_000_000):
        raise ValueError("V8_PUBLIC_SCOPE_UNSAFE_PACKAGE")
    raw=path.read_bytes()
    item=json.loads(raw)
    if not isinstance(item,dict) or not isinstance(item.get("activities"),list):
        raise ValueError("V8_PUBLIC_SCOPE_INVALID_PACKAGE")
    return raw,item


def _compare_public(repo_root:Path, source:Path, v7:dict, *,
                    baseline:dict|None=None, expected_changes:dict|None=None)->list[dict]:
    """Pure file comparison for live gate and offline adversarial tests."""
    baseline=_PUBLIC_BASE if baseline is None else baseline
    expected_changes=_CHANGED if expected_changes is None else expected_changes
    rows=v7.get("releases")
    names=[f"section-9-{i}" for i in range(1,7)]
    if (not isinstance(rows,list) or len(rows)!=6 or
            [x.get("section") for x in rows if isinstance(x,dict)]!=names):
        raise ValueError("V8_PUBLIC_SCOPE_INVALID_V7_ROSTER")
    observed=[]
    for number,entry in enumerate(rows,1):
        section=f"section-9-{number}"
        public_path=repo_root/section/"content"/"package.json"
        private_path=source/"content"/"chapter-9"/section/"package.json"
        current,prev=_json_package(public_path)
        proposed,now=_json_package(private_path)
        pubhash=sha256(current).hexdigest()
        newhash=sha256(proposed).hexdigest()
        if (pubhash!=baseline.get(section)
                or newhash!=entry.get("packageSha256")):
            raise ValueError("V8_PUBLIC_SCOPE_UNEXPECTED_PUBLIC_OR_PRIVATE_BYTES")
        if (prev.get("packageId")!=now.get("packageId")
                or prev.get("status")!=now.get("status")
                or len(prev["activities"])!=18 or len(now["activities"])!=18):
            raise ValueError("V8_PUBLIC_SCOPE_PACKAGE_IDENTITY_OR_SIZE_CHANGED")
        old={a["id"]:a for a in prev["activities"]}
        new={a["id"]:a for a in now["activities"]}
        if len(old)!=18 or len(new)!=18 or old.keys()!=new.keys():
            raise ValueError("V8_PUBLIC_SCOPE_UNEXPECTED_ACTIVITY_ROSTER")
        changed=sum(old[k]!=new[k] for k in old)
        if changed!=expected_changes.get(section):
            raise ValueError("V8_PUBLIC_SCOPE_UNEXPECTED_CONTENT_CHANGE_COUNT")
        observed.append({
            "section":section,"publicPackageSha256":pubhash,
            "verifiedCandidateSha256":newhash,
            "currentAndCandidateHave18Activities":True,
            "sameActivityIdentities":True,
            "samePackageIdentity":True,
            "changedActivities":changed,
            "wouldReplacePublicBytes":pubhash!=newhash,
        })
    for number in (7,8,9):
        section=f"section-9-{number}"
        path=repo_root/section/"content"/"package.json"
        if not path.is_file() or path.is_symlink():
            raise ValueError("V8_PUBLIC_SCOPE_OTHER_CHAPTER9_ROUTES_MISSING")
    return observed


def verify_public_deployment_scope(repo:Path,private:Path,
                                    ready:dict,v7_result:dict)->dict:
    """Perform source-free authenticated GitHub read + pinned SHA diff only."""
    if (ready.get("status")!=
            "VERSIONED_SCIENCE_BROWSER_AND_CI_VERIFIED_UNADMITTED"
            or ready.get("exactHeadHostedCiSuccess") is not True
            or ready.get("codeWorkingTreeClean") is not True
            or ready.get("publicationAuthorized") is not False
            or v7_result.get("status")!=
            "SIX_REAL_PUBLIC_BUNDLE_BUILDS_VERIFIED_PRIVATE_NO_DEPLOY"
            or v7_result.get("realOriginalPublicBuilderInvocations")!=6):
        raise ValueError("V8_PUBLIC_SCOPE_GENUINE_V7_PREREQUISITE_MISSING")
    head=ready.get("gitHead"); proposal=ready.get("proposalSha256")
    if (not isinstance(head,str) or not _SHA40.fullmatch(head)
            or v7_result.get("gitHead")!=head
            or v7_result.get("proposalSha256")!=proposal
            or v7_result.get("publicationAuthorized") is not False
            or v7_result.get("publicDeployExecuted") is not False):
        raise ValueError("V8_PUBLIC_SCOPE_VERSION_MISMATCH")
    from app_generator.runtime.v3_versioned_readiness import _read_previous
    if _read_previous(private/"v3-current-versioned-evidence-readiness.json")!=ready:
        raise ValueError("V8_PUBLIC_SCOPE_READINESS_NOT_SAVED")
    githead,branch=_git_info(repo)
    if (githead!=head or not _git_clean(repo)
            or not _exact_ci_success(_hosted_runs(repo,branch),head)):
        raise ValueError("V8_PUBLIC_SCOPE_EXACT_CI_OR_CLEAN_GIT_MISSING")
    folder=private/_BASE/head/proposal
    signed=_trusted_json(folder/_V7)
    unsigned={k:v for k,v in signed.items() if k!="integritySha256"}
    if (signed.get("integritySha256")!=_hash(unsigned)
            or signed.get("status")!=v7_result.get("status")
            or signed.get("gitHead")!=head
            or signed.get("proposalSha256")!=proposal
            or signed.get("integritySha256")!=v7_result.get("integritySha256")):
        raise ValueError("V8_PUBLIC_SCOPE_V7_RECEIPT_MISMATCH")
    _config(repo)
    permission=_permissions()
    with tempfile.TemporaryDirectory(prefix="bosla-v8-public-scope-",dir=private) as temp:
        site=Path(temp)/"site"
        _proc(["git","clone","--depth","1","--branch","main",
               "https://github.com/"+_DEST+".git",str(site)],timeout=120)
        remote=_proc(["git","rev-parse","HEAD"],cwd=site,timeout=20)
        if remote!=_MAIN:
            raise ValueError("V8_PUBLIC_SCOPE_REMOTE_MAIN_CHANGED")
        rows=_compare_public(site,_candidate_dir(private,head,proposal),signed)
        follow=_proc(["git","ls-remote","--heads",
                      "https://github.com/"+_DEST+".git","refs/heads/main"],
                     timeout=30).split()
        if not follow or follow[0]!=remote:
            raise ValueError("V8_PUBLIC_SCOPE_REMOTE_CHANGED_DURING_AUDIT")
    result={
        "contract":"BOSLA_V8_PUBLIC_DEPLOYMENT_SCOPE_AND_PERMISSION_V1",
        "status":_STATUS,
        "gitHead":head,"proposalSha256":proposal,
        "sourceV7ReceiptSha256":signed["integritySha256"],
        "publicDestinationRepository":_DEST,
        "publicDestinationMainCommit":_MAIN,
        **permission,
        "existingPublicChapter9RoutesVerified":9,
        "packagesChecked":6,
        "alreadyIdenticalPackages":sum(not a["wouldReplacePublicBytes"] for a in rows),
        "packagesRequiringUpdates":sum(a["wouldReplacePublicBytes"] for a in rows),
        "individualChangedActivities":sum(a["changedActivities"] for a in rows),
        "scope":rows,
        "otherThreePublicChapter9RoutesRemainUntouched":True,
        "nextEligibleMilestone":"NON_DESTRUCTIVE_PINNED_PUBLIC_RELEASE_PROPOSAL",
        "newModelCalls":0,"publicPushExecuted":False,
        "publicMergeExecuted":False,"publicDeployExecuted":False,
        "publicationAuthorized":False,
    }
    return _v6_checkpoint(folder/_V8,result)

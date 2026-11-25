"""BSA229: materialize exact V8-scoped release proposal privately on Yoga6.

No public branch push, PR creation, merge, deploy or model/PDF calls.
All public Git operations are restricted to read-only clone/ls-remote.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import tempfile

from app_generator.runtime.academic_release import enforce_academic_release_gate
from app_generator.runtime.v3_five_stage_completion import _BASE, _candidate_dir, _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json, _V7
from app_generator.runtime import v3_public_deployment_scope as scope
from app_generator.runtime.v3_versioned_readiness import (
    _git_info, _git_clean, _hosted_runs, _exact_ci_success, _read_previous,
)
from scripts.build_public_release import build

_V9="V9_PINNED_NONDESTRUCTIVE_PUBLIC_RELEASE_PROPOSAL.json"
_STATUS="THREE_ROUTE_PRIVATE_PINNED_RELEASE_PROPOSAL_READY_NO_PUBLIC_WRITE"
_CHANGED=("section-9-1","section-9-2","section-9-6")
_FOLDER="v9-private-pinned-public-proposal"


def _manifest(root:Path)->list[dict]:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("V9_UNSAFE_LOCAL_PROPOSAL")
    files=sorted(p for p in root.rglob("*") if p.is_file())
    if any(p.is_symlink() for p in root.rglob("*")):
        raise ValueError("V9_UNSAFE_PROPOSAL_SYMLINK")
    paths=[p.relative_to(root).as_posix() for p in files]
    if len(paths)!=24 or not all(
            p.split("/")[0] in _CHANGED for p in paths):
        raise ValueError("V9_UNEXPECTED_PROPOSAL_FILE_ROSTER")
    return [{"path":name,"sha256":sha256(p.read_bytes()).hexdigest()}
            for name,p in zip(paths,files)]


def _verified_inputs(repo:Path,private:Path,ready:dict,v8_result:dict):
    if (ready.get("status")!=
            "VERSIONED_SCIENCE_BROWSER_AND_CI_VERIFIED_UNADMITTED"
            or ready.get("exactHeadHostedCiSuccess") is not True
            or ready.get("codeWorkingTreeClean") is not True
            or ready.get("publicationAuthorized") is not False
            or v8_result.get("status")!=scope._STATUS
            or v8_result.get("packagesChecked")!=6
            or v8_result.get("packagesRequiringUpdates")!=3
            or v8_result.get("individualChangedActivities")!=5
            or v8_result.get("publicDeployExecuted") is not False
            or v8_result.get("publicPushExecuted") is not False
            or v8_result.get("publicationAuthorized") is not False):
        raise ValueError("V9_SOURCE_BOUND_V8_PREREQUISITE_MISSING")
    head=ready.get("gitHead");proposal=ready.get("proposalSha256")
    if (head!=v8_result.get("gitHead") or
            proposal!=v8_result.get("proposalSha256") or
            _read_previous(private/"v3-current-versioned-evidence-readiness.json")!=ready):
        raise ValueError("V9_SOURCE_OR_READINESS_CHANGED")
    live_head,branch=_git_info(repo)
    if (head!=live_head or not _git_clean(repo)
            or not _exact_ci_success(_hosted_runs(repo,branch),head)):
        raise ValueError("V9_EXACT_HEAD_CI_OR_CLEAN_SOURCE_MISSING")
    folder=private/_BASE/head/proposal
    v8=_trusted_json(folder/scope._V8)
    v7=_trusted_json(folder/_V7)
    if (v8.get("integritySha256")!=_hash(
            {k:v for k,v in v8.items() if k!="integritySha256"})
            or v8!=v8_result
            or v8.get("sourceV7ReceiptSha256")!=v7.get("integritySha256")
            or v8.get("publicDestinationMainCommit")!=scope._MAIN
            or v8.get("publicDestinationRepository")!=scope._DEST
            or v7.get("integritySha256")!=_hash(
                {k:v for k,v in v7.items() if k!="integritySha256"})):
        raise ValueError("V9_SIGNED_PUBLIC_SCOPE_OR_V7_TAMPER")
    scope._config(repo)
    return folder,v7,v8


def stage_pinned_private_public_proposal(repo:Path,private:Path,
                                         ready:dict,v8_result:dict)->dict:
    """Actual production bundle builds in local private repository overlay."""
    folder,v7,v8=_verified_inputs(repo,private,ready,v8_result)
    source=_candidate_dir(private,ready["gitHead"],ready["proposalSha256"])
    release=folder/_FOLDER
    with tempfile.TemporaryDirectory(prefix="bosla-v9-private-",dir=private) as temp:
        scratch=Path(temp)
        site=scratch/"public-read-only"
        scope._proc(["git","clone","--depth","1","--branch","main",
                     "https://github.com/"+scope._DEST+".git",str(site)])
        remote=scope._proc(["git","rev-parse","HEAD"],cwd=site,timeout=30)
        if remote!=v8["publicDestinationMainCommit"]:
            raise ValueError("V9_PUBLIC_BASE_MAIN_DRIFT")
        evidence=scope._compare_public(site,source,v7)
        changed=tuple(x["section"] for x in evidence
                      if x["wouldReplacePublicBytes"])
        if changed!=_CHANGED:
            raise ValueError("V9_UNEXPECTED_PUBLIC_CHANGE_SCOPE")
        # No original source PDF or unreviewed raw repo package enters output.
        overlay=scratch/"source"
        for name in ("app","domains"):
            obj=repo/name
            if obj.is_symlink() or not obj.is_dir():
                raise ValueError("V9_UNSAFE_RUNTIME_SOURCE")
            shutil.copytree(obj,overlay/name)
        staging=scratch/"proposal"
        staging.mkdir()
        results=[]
        for name in changed:
            source_package=(source/"content"/"chapter-9"/name/"package.json")
            raw=source_package.read_bytes()
            attest=(folder/"native-v3-exact-attestations"/name/
                    "autonomous-v3-release-receipt.json")
            if source_package.is_symlink() or attest.is_symlink() or not attest.is_file():
                raise ValueError("V9_UNSAFE_EXACT_NATIVE_ATTESTATION")
            expected=next(row for row in v7["releases"] if row["section"]==name)
            if (sha256(raw).hexdigest()!=expected["packageSha256"]
                    or sha256(attest.read_bytes()).hexdigest()!=
                       next(row for row in _trusted_json(
                           folder/"V6_GENUINE_NATIVE_V3_RELEASE_ATTESTATION.json"
                           )["packages"] if row["section"]==name)["privateAttestationSha256"]):
                raise ValueError("V9_EXACT_PACKAGE_OR_ATTESTATION_CHANGED")
            result=enforce_academic_release_gate(repo,source_package,attest.parent)
            if result.get("artifactSha256")!=expected["packageSha256"]:
                raise ValueError("V9_NATIVE_RELEASE_GATE_FAILED")
            staged=(overlay/"content"/"chapter-9"/name/"package.json")
            staged.parent.mkdir(parents=True,exist_ok=True)
            staged.write_bytes(raw)
            bundle=staging/name
            build(bundle,staged,source_root=overlay,validation_dir=attest.parent)
            if (bundle/"content"/"package.json").read_bytes()!=raw:
                raise ValueError("V9_BUILDER_CHANGED_SOURCE_BYTES")
            index=(bundle/"index.html").read_text(encoding="utf8")
            if "LOCAL DRAFT PREVIEW" in index:
                raise ValueError("V9_BUILDER_LEFT_DRAFT_PREVIEW")
            old={p.relative_to(site/name).as_posix():sha256(p.read_bytes()).hexdigest()
                 for p in (site/name).rglob("*") if p.is_file()}
            new={p.relative_to(bundle).as_posix():sha256(p.read_bytes()).hexdigest()
                 for p in bundle.rglob("*") if p.is_file()}
            results.append({
                "section":name,
                "packageSha256":expected["packageSha256"],
                "publicRouteFilesBefore":len(old),
                "bundledRouteFilesAfter":len(new),
                "addedFiles":sorted(new.keys()-old.keys()),
                "removedFiles":sorted(old.keys()-new.keys()),
                "modifiedFiles":sorted(
                    k for k in old.keys()&new.keys() if old[k]!=new[k]),
            })
        allfiles=_manifest(staging)
        follow=scope._proc(["git","ls-remote","--heads",
                  "https://github.com/"+scope._DEST+".git","refs/heads/main"],
                  timeout=30).split()
        if len(follow)!=2 or follow[0]!=remote:
            raise ValueError("V9_PUBLIC_MAIN_DRIFT_BEFORE_PROPOSAL")
        if release.exists():
            existing=_manifest(release)
            if existing!=allfiles:
                raise ValueError("V9_PRIVATE_PROPOSAL_CHANGED_ON_RESTART")
        else:
            if release.is_symlink():
                raise ValueError("V9_PRIVATE_PROPOSAL_SYMLINK")
            os.replace(staging,release)
    manifest=_manifest(release)
    payload={
        "contract":"BOSLA_V9_PRIVATE_PINNED_PUBLIC_RELEASE_PROPOSAL_V1",
        "status":_STATUS,
        "gitHead":ready["gitHead"],"proposalSha256":ready["proposalSha256"],
        "sourceV8ReceiptSha256":v8["integritySha256"],
        "sourceV7ReceiptSha256":v7["integritySha256"],
        "publicDestination":scope._DEST,
        "publicMainPinnedSha":v8["publicDestinationMainCommit"],
        "changedPublicRoutes":list(_CHANGED),
        "productionReleaseBuilderInvocations":3,
        "privateFullRouteBundles":3,
        "releaseFileCount":len(manifest),
        "fileManifestSha256":_hash({"files":manifest}),
        "routeDiffs":results,
        "nextEligibleMilestone":"PINNED_PUBLIC_PROPOSAL_INTEGRATION_AND_BROWSER_SMOKE",
        "newModelCalls":0,"publicPRCreated":False,"publicPushExecuted":False,
        "publicMergeExecuted":False,"publicDeployExecuted":False,
        "publicationAuthorized":False,
    }
    return _v6_checkpoint(folder/_V9,payload)

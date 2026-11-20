"""BOSLA V14: independent authenticated public draft PR browser acceptance.

Runs after genuine V13 in the ordinary source-free worker. Reuses historical
BSA230 V10 Chrome checks and BSA234 scoped PR validation, but tests the
actual exact GitHub review branch, including unchanged Chapter9 routes.
Strictly read-only on GitHub. No PR merge, main push or public deployment.
"""
from __future__ import annotations

from hashlib import sha256
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import functools
import json
from pathlib import Path
import re
import subprocess
import tempfile
import threading

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_public_release_browser_acceptance import _console_health
from app_generator.runtime.v3_public_nonmerging_draft_pr import (
    _V13, _STATUS as _V13_STATUS, _REPO, _MAIN, _REMOTE,
    _preflight as _v13_preflight, _ls_remote, _gh,
)

_V14="V14_INDEPENDENT_PR_BRANCH_REAL_CHROME.json"
_STATUS="PR_EXACT_PUBLIC_GIT_BRANCH_NINE_ROUTES_ACTUAL_CHROME_PASS"
_ROUTES=tuple(f"section-9-{i}" for i in range(1,10))
_CHANGED=("section-9-1","section-9-2","section-9-6")


def _verify_v13(folder:Path,v13_result:dict,ready:dict)->dict:
    v13=_trusted_json(folder/_V13)
    if (v13!=v13_result or v13.get("status")!=_V13_STATUS
            or v13.get("integritySha256")!=_hash({
                k:v for k,v in v13.items() if k!="integritySha256"})
            or v13.get("gitHead")!=ready.get("gitHead")
            or v13.get("proposalSha256")!=ready.get("proposalSha256")
            or v13.get("publicDestination")!=_REPO
            or v13.get("publicBaseMainPinnedSha")!=_MAIN
            or v13.get("changedSections")!=list(_CHANGED)
            or v13.get("changedFileCount")!=21
            or v13.get("publicPullRequestDraft") is not True
            or v13.get("publicPullRequestOpen") is not True
            or v13.get("remoteBaseRecheckedAfterPr") is not True
            or any(v13.get(k) is not False for k in
                   ("publicMergeExecuted","publicDeployExecuted",
                    "publicationAuthorized","scheduledTaskCreated"))):
        raise ValueError("V14_GENUINE_SIGNED_V13_REQUIRED")
    branch=v13.get("publicReviewBranch")
    sha=v13.get("publicReviewBranchSha")
    tree=v13.get("publicReviewTreeSha")
    n=v13.get("publicPullRequestNumber")
    if (not isinstance(branch,str)
            or not re.fullmatch(
                r"bosla/private-ch9-three-section-[0-9a-f]{12}",branch)
            or not isinstance(sha,str)
            or not re.fullmatch(r"[0-9a-f]{40}",sha)
            or not isinstance(tree,str)
            or not re.fullmatch(r"[0-9a-f]{40}",tree)
            or type(n) is not int or n<1
            or v13.get("publicPullRequestUrl")!=
            f"https://github.com/{_REPO}/pull/{n}"
            or branch.rsplit("-",1)[-1]!=
            v13.get("privatePatchSha256","")[:12]):
        raise ValueError("V14_V13_BRANCH_OR_PR_IDENTITY_INVALID")
    return v13


def _check_pr_snapshot(pr:dict,v13:dict)->dict:
    if (not isinstance(pr,dict)
            or pr.get("state")!="open"
            or pr.get("draft") is not True
            or pr.get("merged_at") is not None
            or pr.get("number")!=v13["publicPullRequestNumber"]
            or pr.get("html_url")!=v13["publicPullRequestUrl"]
            or pr.get("head",{}).get("sha")!=v13["publicReviewBranchSha"]
            or pr.get("head",{}).get("ref")!=v13["publicReviewBranch"]
            or pr.get("head",{}).get("repo",{}).get("full_name")!=_REPO
            or pr.get("base",{}).get("sha")!=_MAIN
            or pr.get("base",{}).get("ref")!="main"
            or pr.get("base",{}).get("repo",{}).get("full_name")!=_REPO):
        raise ValueError("V14_PR_NO_LONGER_SAFE_DRAFT_OR_BASE_MOVED")
    return {"publicPullRequestNumber":pr["number"],
            "publicPullRequestUrl":pr["html_url"],
            "draft":True,"merged":False}


def _check_pr_diff(files:list,v13:dict)->list[str]:
    if not isinstance(files,list) or len(files)!=21:
        raise ValueError("V14_PR_DIFF_COUNT_CHANGED")
    paths=[x.get("filename") for x in files if isinstance(x,dict)]
    if (len(paths)!=21 or len(set(paths))!=21
            or any(not isinstance(p,str) for p in paths)
            or any(x.get("status") not in ("added","modified")
                   for x in files)
            or any(not p.startswith(tuple(c+"/" for c in _CHANGED))
                   for p in paths)
            or any(sum(p.startswith(c+"/") for p in paths)!=7
                   for c in _CHANGED)):
        raise ValueError("V14_PR_DIFF_SCOPE_OR_STATUSES_CHANGED")
    return paths


def _check_browser_state(state:dict,section:str,logs:list)->dict:
    if (section not in _ROUTES or not isinstance(state,dict)
            or state.get("path")!="/"+section+"/"
            or type(state.get("appTextChars")) is not int
            or state["appTextChars"]<100
            or type(state.get("buttons")) is not int
            or state["buttons"]<1
            or state.get("initialPlaceholder") is not False
            or state.get("failedLoading") is not False
            or _console_health(logs)["severeRuntimeErrors"]):
        raise ValueError("V14_ACTUAL_PUBLIC_PR_CHROME_ROUTE_OR_CONSOLE_FAILED")
    return {"section":section,"realChromeRendered":True,
            "buttonsAvailable":True,"packageLoaded":True}


def _read_gh_json(path:str):
    data=json.loads(_gh(["gh","api","--method","GET",
                         "repos/"+_REPO+"/"+path]))
    return data


def independent_public_pr_browser_acceptance(
    repo:Path,private:Path,ready:dict,
    v9_result:dict,v11_result:dict,v12_result:dict,v13_result:dict,
)->dict:
    """Exactly the genuine PR branch, nine real Chrome routes; read-only."""
    folder,v11,v12,branch,expected_paths=_v13_preflight(
        repo,private,ready,v9_result,v11_result,v12_result)
    v13=_verify_v13(folder,v13_result,ready)
    if (v13["sourceV12ReceiptSha256"]!=v12["integritySha256"]
            or v13["sourceV11ReceiptSha256"]!=v11["integritySha256"]
            or v13["privatePatchSha256"]!=v11["privatePatchSha256"]
            or v13["publicReviewBranch"]!=branch
            or v13["changedFileCount"]!=len(expected_paths)):
        raise ValueError("V14_SIGNED_PREDECESSOR_SOURCE_MISMATCH")
    if _ls_remote("main")!=_MAIN:
        raise ValueError("V14_PUBLIC_MAIN_MOVED")
    if _ls_remote(branch)!=v13["publicReviewBranchSha"]:
        raise ValueError("V14_PR_REMOTE_BRANCH_MOVED")
    n=v13["publicPullRequestNumber"]
    _check_pr_snapshot(_read_gh_json(f"pulls/{n}"),v13)
    paths=_check_pr_diff(
        _read_gh_json(f"pulls/{n}/files?per_page=100"),v13)
    if paths!=expected_paths:
        raise ValueError("V14_PR_DIFF_DOES_NOT_MATCH_SIGNED_PRIVATE_PATCH")
    commit=_read_gh_json("git/commits/"+v13["publicReviewBranchSha"])
    if (not isinstance(commit,dict)
            or commit.get("tree",{}).get("sha")!=v13["publicReviewTreeSha"]
            or not isinstance(commit.get("parents"),list)
            or len(commit["parents"])!=1
            or commit["parents"][0].get("sha")!=_MAIN):
        raise ValueError("V14_PR_TREE_OR_PARENT_NOT_PINNED_MAIN")

    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait

    with tempfile.TemporaryDirectory(prefix="bosla-v14-",dir=private) as tmp:
        checkout=Path(tmp)/"review-branch"
        proc=subprocess.run(
            ["git","clone","--depth","1","--branch",branch,_REMOTE,
             str(checkout)],
            capture_output=True,text=True,encoding="utf8",errors="replace",
            check=False,timeout=90)
        if proc.returncode:
            raise ValueError("V14_READ_ONLY_PUBLIC_BRANCH_CLONE_FAILED")
        cmd=subprocess.run(
            ["git","rev-parse","HEAD"],cwd=checkout,capture_output=True,
            text=True,encoding="utf8",errors="replace",check=True,timeout=20)
        if cmd.stdout.strip()!=v13["publicReviewBranchSha"]:
            raise ValueError("V14_CLONED_PUBLIC_BRANCH_SHA_CHANGED")

        options=Options()
        for flag in ("--headless=new","--no-first-run",
                     "--no-default-browser-check",
                     "--disable-background-networking",
                     "--disable-extensions","--disable-gpu",
                     "--window-size=1280,900"):
            options.add_argument(flag)
        options.set_capability("goog:loggingPrefs",{"browser":"ALL"})
        handler=functools.partial(SimpleHTTPRequestHandler,
                                  directory=str(checkout))
        server=ThreadingHTTPServer(("127.0.0.1",0),handler)
        server.daemon_threads=True
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        driver=None
        results=[]
        ignored=0
        try:
            driver=webdriver.Chrome(options=options)
            driver.set_page_load_timeout(35)
            url=f"http://127.0.0.1:{server.server_port}"
            for section in _ROUTES:
                driver.get(url+"/"+section+"/")
                WebDriverWait(driver,30).until(
                    lambda w: len(w.find_element(By.ID,"app").text.strip())>=100)
                state=driver.execute_script("""
                    const app=document.querySelector('#app');
                    const text=app.textContent || '';
                    return {path:location.pathname,appTextChars:text.length,
                        buttons:app.querySelectorAll('button').length,
                        initialPlaceholder:text.includes(
                            'Select a generated learning package to begin.'),
                        failedLoading:text.toLowerCase().includes('failed to load')};
                """)
                logs=driver.get_log("browser")
                results.append(_check_browser_state(state,section,logs))
                ignored+=_console_health(logs)["favicon404Ignored"]
        finally:
            if driver is not None:
                driver.quit()
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    if len(results)!=9 or [r["section"] for r in results]!=list(_ROUTES):
        raise ValueError("V14_NINE_ROUTE_BROWSER_COVERAGE_INCOMPLETE")
    if (_ls_remote("main")!=_MAIN
            or _ls_remote(branch)!=v13["publicReviewBranchSha"]):
        raise ValueError("V14_REMOTE_STATE_MOVED_DURING_ACCEPTANCE")
    _check_pr_snapshot(_read_gh_json(f"pulls/{n}"),v13)
    payload={
        "contract":"BOSLA_V14_REAL_PUBLIC_PR_BRANCH_INDEPENDENT_CHROME_V1",
        "status":_STATUS,
        "gitHead":ready["gitHead"],
        "proposalSha256":ready["proposalSha256"],
        "sourceV13ReceiptSha256":v13["integritySha256"],
        "sourceV12ReceiptSha256":v12["integritySha256"],
        "publicDestination":_REPO,
        "publicDraftPrNumber":n,
        "publicDraftPrUrl":v13["publicPullRequestUrl"],
        "publicReviewBranch":branch,
        "publicReviewBranchSha":v13["publicReviewBranchSha"],
        "publicReviewTreeSha":v13["publicReviewTreeSha"],
        "publicBaseMainPinnedSha":_MAIN,
        "actualRemoteGitHubDiffPaths":paths,
        "changedFileCount":21,
        "changedSections":list(_CHANGED),
        "realChromeRoutesPassed":9,
        "allRouteBrowserResults":results,
        "favicon404Ignored":ignored,
        "publicPrDraft":True,
        "publicPrOpen":True,
        "publicMergeExecuted":False,
        "publicDeployExecuted":False,
        "publicationAuthorized":False,
        "scheduledTaskCreated":False,
        "newModelCalls":0,
        "nextEligibleMilestone":
            "INDEPENDENT_PR_RELEASE_CI_SECURITY_AND_UNMERGED_REVIEW_GATE",
    }
    return _v6_checkpoint(folder/_V14,payload)

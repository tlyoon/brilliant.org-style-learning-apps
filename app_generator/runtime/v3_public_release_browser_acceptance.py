"""BSA230: release-mode private Chrome acceptance for genuine V9 three-route bundles.

Only loopback HTTP and local Chrome, no external AI/PDF, Git push,
public PR, merge or deploy. Favicon 404 is benign; runtime errors are not.
"""
from __future__ import annotations
from hashlib import sha256
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import functools
import json
from pathlib import Path
import re
import threading

from app_generator.runtime.v3_five_stage_completion import _BASE, _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_pinned_public_release_proposal import (
    _FOLDER, _V9, _STATUS as V9_STATUS, _manifest,
)
from app_generator.runtime.v3_versioned_readiness import (
    _git_info, _git_clean, _hosted_runs, _exact_ci_success, _read_previous,
)

_V10="V10_PRIVATE_RELEASE_BUNDLE_REAL_BROWSER_ACCEPTANCE.json"
_STATUS="THREE_PRIVATE_PRODUCTION_BUNDLES_REAL_CHROME_RENDERED_NO_PUBLIC_WRITE"
_SECTIONS=("section-9-1","section-9-2","section-9-6")
_FAVICON=re.compile(
    r"^http://127\.0\.0\.1:\d+/favicon\.ico - Failed to load resource: "
    r"the server responded with a status of 404 \(File not found\)$"
)


def _console_health(logs:list[dict])->dict:
    """Ignore only the historical harmless Chrome favicon request."""
    benign=0
    errors=[]
    for entry in logs:
        if str(entry.get("level","")).upper()!="SEVERE":
            continue
        msg=str(entry.get("message",""))
        if _FAVICON.fullmatch(msg):
            benign+=1
        else:
            errors.append({"class":"UNEXPECTED_BROWSER_SEVERE_LOG"})
    return {"favicon404Ignored":benign,"severeRuntimeErrors":errors}


def _check_page_state(state:dict)->dict:
    if (not isinstance(state,dict)
            or not state.get("path") in ["/"+s+"/" for s in _SECTIONS]
            or not isinstance(state.get("appTextChars"),int)
            or state["appTextChars"]<100
            or not isinstance(state.get("buttons"),int)
            or state["buttons"]<1
            or state.get("initialPlaceholder") is not False
            or state.get("failedLoading") is not False):
        raise ValueError("V10_PRIVATE_RELEASE_REAL_BROWSER_NOT_RENDERED")
    return {"route":state["path"].strip("/"),
            "realChromeRendered":True,"buttonsAvailable":True,
            "packageLoaded":True}


def _preflight(repo:Path,private:Path,ready:dict,v9_result:dict):
    if (ready.get("status")!=
            "VERSIONED_SCIENCE_BROWSER_AND_CI_VERIFIED_UNADMITTED"
            or ready.get("exactHeadHostedCiSuccess") is not True
            or ready.get("codeWorkingTreeClean") is not True
            or ready.get("publicationAuthorized") is not False
            or v9_result.get("status")!=V9_STATUS
            or v9_result.get("productionReleaseBuilderInvocations")!=3
            or v9_result.get("privateFullRouteBundles")!=3
            or v9_result.get("releaseFileCount")!=24
            or v9_result.get("changedPublicRoutes")!=list(_SECTIONS)
            or v9_result.get("publicPushExecuted") is not False
            or v9_result.get("publicMergeExecuted") is not False
            or v9_result.get("publicDeployExecuted") is not False
            or v9_result.get("publicationAuthorized") is not False):
        raise ValueError("V10_GENUINE_PRIVATE_V9_PREREQUISITE_MISSING")
    head=ready.get("gitHead");proposal=ready.get("proposalSha256")
    if (v9_result.get("gitHead")!=head
            or v9_result.get("proposalSha256")!=proposal
            or _read_previous(private/"v3-current-versioned-evidence-readiness.json")!=ready):
        raise ValueError("V10_SOURCE_READINESS_MISMATCH")
    live,branch=_git_info(repo)
    if (live!=head or not _git_clean(repo)
            or not _exact_ci_success(_hosted_runs(repo,branch),head)):
        raise ValueError("V10_EXACT_HEAD_CI_OR_CLEAN_MISSING")
    folder=private/_BASE/head/proposal
    saved=_trusted_json(folder/_V9)
    if (saved!=v9_result or saved.get("integritySha256")!=_hash(
            {k:v for k,v in saved.items() if k!="integritySha256"})):
        raise ValueError("V10_V9_SIGNED_RECEIPT_CHANGED")
    stage=folder/_FOLDER
    files=_manifest(stage)
    if _hash({"files":files})!=saved.get("fileManifestSha256"):
        raise ValueError("V10_PRIVATE_BUNDLE_CONTENT_CHANGED")
    for item in saved["routeDiffs"]:
        section=item["section"]
        if (section not in _SECTIONS or
                (stage/section/"content"/"package.json").is_symlink() or
                sha256((stage/section/"content"/"package.json").read_bytes()
                      ).hexdigest()!=item["packageSha256"]):
            raise ValueError("V10_ROUTE_OR_PACKAGE_BYTES_CHANGED")
    return folder,stage,saved


def run_private_release_browser_acceptance(
    repo:Path,private:Path,ready:dict,v9_result:dict,
)->dict:
    """Actually load the three production release bundles in headless Chrome."""
    folder,stage,saved=_preflight(repo,private,ready,v9_result)
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait

    options=Options()
    for flag in ("--headless=new","--no-first-run",
                 "--no-default-browser-check","--disable-background-networking",
                 "--disable-extensions","--disable-gpu",
                 "--window-size=1280,900"):
        options.add_argument(flag)
    options.set_capability("goog:loggingPrefs",{"browser":"ALL"})
    handler=functools.partial(SimpleHTTPRequestHandler,directory=str(stage))
    server=ThreadingHTTPServer(("127.0.0.1",0),handler)
    server.daemon_threads=True
    task=threading.Thread(target=server.serve_forever,daemon=True)
    task.start()
    driver=None
    results=[]
    ignored=0
    try:
        driver=webdriver.Chrome(options=options)
        driver.set_page_load_timeout(35)
        address=f"http://127.0.0.1:{server.server_port}"
        for section in _SECTIONS:
            driver.get(f"{address}/{section}/")
            WebDriverWait(driver,25).until(
                lambda d: len(d.find_element(By.ID,"app").text.strip())>=100)
            state=driver.execute_script("""
                const app=document.querySelector('#app');
                const text=app.textContent || '';
                return {path:location.pathname,appTextChars:text.length,
                    buttons:app.querySelectorAll('button').length,
                    initialPlaceholder:text.includes('Select a generated learning package to begin.'),
                    failedLoading:text.toLowerCase().includes('failed to load')};
            """)
            result=_check_page_state(state)
            healthy=_console_health(driver.get_log("browser"))
            if healthy["severeRuntimeErrors"]:
                raise ValueError("V10_PRIVATE_RELEASE_BROWSER_CONSOLE_FAILURE")
            ignored+=healthy["favicon404Ignored"]
            results.append(result)
    finally:
        if driver is not None:
            driver.quit()
        server.shutdown()
        server.server_close()
        task.join(timeout=3)
    if len(results)!=3 or [r["route"] for r in results]!=list(_SECTIONS):
        raise ValueError("V10_INCOMPLETE_THREE_ROUTE_BROWSER_COVERAGE")
    payload={
        "contract":"BOSLA_V10_THREE_BUNDLE_REAL_BROWSER_ACCEPTANCE_V1",
        "status":_STATUS,
        "gitHead":ready["gitHead"],
        "proposalSha256":ready["proposalSha256"],
        "sourceV9ReceiptSha256":saved["integritySha256"],
        "publicMainPinnedSha":saved["publicMainPinnedSha"],
        "privateProductionBundlesChecked":3,
        "privateProductionBundleFilesVerified":24,
        "realHeadlessChromeRoutesPassed":3,
        "browserResults":results,
        "exactFavicon404FilterApplied":True,
        "nextEligibleMilestone":"PINNED_NONMERGE_PUBLIC_PR_INTEGRATION",
        "newModelCalls":0,"publicPRCreated":False,
        "publicPushExecuted":False,"publicMergeExecuted":False,
        "publicDeployExecuted":False,"publicationAuthorized":False,
    }
    return _v6_checkpoint(folder/_V10,payload)

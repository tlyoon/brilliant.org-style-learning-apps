"""Source-free ACTUAL BOSLA Chapter9 six-section local candidate browser QA.

Staging is temporary and loopback-only. Unlike legacy RC1 synthetic smoke,
this checks the real 108-activity, two-correction UNADMITTED proposal,
actual authored trilingual strings and real browser activity interactions.
Never visits Gemini or treats a browser pass as independent scientific QA,
course version admission, learner pilot approval or publication.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_generator.runtime.v3_source_free_forward import read_source_free_checkpoint
from app_generator.runtime.v3_versioned_acceptance_scope import _encoded
from app_generator.validation.autonomous_completion import package_identity
from app_generator.domains import resolve_package_domain


def _source_bound_packages(private: Path) -> tuple[str, list[tuple[int, bytes, list]]]:
    checkpoint=read_source_free_checkpoint(private)
    if checkpoint is None or checkpoint["publicationAuthorized"] is not False:
        raise ValueError("V3_BROWSER_MISSING_SOURCE_FREE_CHECKPOINT")
    proposal_sha=checkpoint["proposalSha256"]
    if not isinstance(proposal_sha,str) or len(proposal_sha)!=64:
        raise ValueError("V3_BROWSER_NO_VERSIONED_COURSE_PROPOSAL")
    manifest_path=(private/"versioned-course-proposals"/proposal_sha/
                   "scope-proposal.json")
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("V3_BROWSER_MISSING_IMMUTABLE_PROPOSAL")
    doc=json.loads(manifest_path.read_text(encoding="utf8"))
    unsigned={k:v for k,v in doc.items() if k!="integritySha256"}
    if (doc.get("integritySha256") != proposal_sha
            or sha256(_encoded(unsigned)).hexdigest()!=proposal_sha
            or doc.get("versionedScopeAdmitted") is not False
            or doc.get("publicationAuthorized") is not False
            or not isinstance(doc.get("sections"),list)
            or len(doc["sections"])!=6
            or not isinstance(doc.get("section96UnrecoverableRoleReplacement"),dict)):
        raise ValueError("V3_BROWSER_INVALID_VERSIONED_PROPOSAL")
    # BSA218: a new source version for the two old uncertain roles is
    # permitted ONLY on independent saved two-Gemini evidence. Never allow
    # a manifest to redirect Chrome to unreviewed or arbitrary private data.
    final_two=doc.get("finalTwoNewVersionGenuineScience")
    proven_final=None
    if final_two is not None:
        from app_generator.runtime.v3_final_two_science import (
            verified_final_two_science,
        )
        proven_final=verified_final_two_science(
            ROOT/"content"/"chapter-9",ROOT,private)
        if (not isinstance(final_two,dict) or proven_final is None
                or final_two.get("reviewedNewSourceOnly") is not True
                or final_two.get("originalSection91Index0UnknownPreserved") is not True
                or final_two.get("originalSection96Index6UnknownPreserved") is not True
                or final_two.get("publicationAuthorized") is not False
                or final_two.get("versionedScopeAdmitted") is not False
                or final_two.get("proofs")!=proven_final["proofs"]):
            raise ValueError("V3_BROWSER_FINAL_TWO_NEEDS_GENUINE_NEW_ROLE_PROOF")
        for number,section in ((1,"section91"),(6,"section96")):
            row=doc["sections"][number-1]
            if row.get("proposedPackageSha256")!=(
                    proven_final[section]["candidatePackageSha256"]):
                raise ValueError("V3_BROWSER_FINAL_TWO_PROPOSED_SHA_MISMATCH")
    payload=[]
    for index,row in enumerate(doc["sections"],1):
        label=f"section-9-{index}"
        if row.get("section")!=label or row.get("activities")!=18:
            raise ValueError("V3_BROWSER_INVALID_SIX_SECTION_ROSTER")
        target=row["proposedPackageSha256"]
        if target==row["originalPackageSha256"]:
            source=ROOT/"content"/"chapter-9"/label/"package.json"
        elif label=="section-9-1" and proven_final is not None:
            source=private/"final-two-science-candidates"/label/target/"package.json"
        elif label=="section-9-2":
            source=private/"repair-proposals"/label/target/"package.json"
        elif label=="section-9-6" and proven_final is not None:
            # Existing corrected indices 5 and 9 remain byte-for-byte
            # identical to their genuinely approved parent revisions.
            science=doc.get("section96ScientificFailureReplacement")
            if (not isinstance(science,dict)
                    or science.get("changedActivityIndices")!=[5,9]
                    or science.get("originalIndex9ScientificFailurePreserved") is not True
                    or science.get("originalIndex6ProviderUnknownPreserved") is not True
                    or len(science.get("independentNewVersionGeminiEvidence",[]))!=2):
                raise ValueError("V3_BROWSER_FINAL_TWO_PRIOR_96_PROOF_CHANGED")
            source=private/"final-two-science-candidates"/label/target/"package.json"
        elif label=="section-9-6":
            science=doc.get("section96ScientificFailureReplacement")
            if science is not None:
                if (not isinstance(science,dict)
                        or science.get("newContentPackageSha256")!=target
                        or science.get("changedActivityIndices")!=[5,9]
                        or science.get("originalIndex9ScientificFailurePreserved") is not True
                        or science.get("originalIndex6ProviderUnknownPreserved") is not True
                        or science.get("publicationAuthorized") is not False
                        or science.get("versionedScopeAdmitted") is not False
                        or len(science.get("independentNewVersionGeminiEvidence",[]))!=2
                        or not all(
                            entry.get("genuineConsensusPass") is True
                            for entry in science["independentNewVersionGeminiEvidence"])):
                    raise ValueError("V3_BROWSER_UNTRUSTED_NEW_SCIENCE_PROPOSAL")
                source=private/"scientific-failure-rollforward"/label/target/"package.json"
            else:
                source=private/"historical-role-rollforward"/label/target/"package.json"
        else:
            raise ValueError("V3_BROWSER_UNREGISTERED_CHANGED_SECTION")
        if source.is_symlink() or not source.is_file() or source.stat().st_size>2_000_000:
            raise ValueError("V3_BROWSER_MISSING_SOURCE_PACKAGE")
        raw=source.read_bytes()
        digest,items=package_identity(raw)
        if digest!=target or len(items)!=18:
            raise ValueError("V3_BROWSER_SOURCE_SHA_NOT_PROPOSED_VERSION")
        payload.append((index,raw,items))
    return proposal_sha,payload


def _stage_site(site: Path, packages: list[tuple[int,bytes,list]]) -> None:
    from scripts.check_course_preview_browser import stage_site
    stage_site(site)
    cases=[]
    for number,raw,_ in packages:
        rel=f"content/chapter-9/section-9-{number}/package.json"
        target=site.joinpath(*rel.split("/"))
        target.write_bytes(raw)
        cases.append({"sectionNumber":number,"packagePath":rel,
                      "packageSha256":sha256(raw).hexdigest()})
    # Physics domain-specific visuals, not the synthetic empty stub.
    actual=json.loads(packages[0][1].decode("utf8"))
    domain=resolve_package_domain(ROOT,actual)
    visuals=domain.path("visuals","rendererScript")
    styles=domain.path("visuals","stylesheet")
    if not visuals.is_file() or not styles.is_file():
        raise ValueError("V3_BROWSER_MISSING_ACTUAL_PHYSICS_RENDERERS")
    shutil.copyfile(visuals,site/"app"/"domain-renderers.js")
    shutil.copyfile(styles,site/"app"/"domain-styles.css")
    git=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,
                       text=True,timeout=15,check=True).stdout.strip()
    if len(git)!=40 or set(git)-set("0123456789abcdef"):
        raise ValueError("V3_BROWSER_MISSING_GIT_PROVENANCE")
    roster={"scopeId":"sourcefree-pilot-real-chapter9-proposal",
            "baselineGitSha":git,"chapterNumber":9,
            "mode":"OFFLINE_EXISTING_PACKAGES_ONLY","cases":cases,
            "modelCallsAllowed":False,"pdfReadsAllowed":False,
            "publicationAllowed":False}
    (site/"local-pilot"/"roster.json").write_text(
        json.dumps(roster,sort_keys=True),encoding="utf8")


def _normalized(value: str) -> str:
    return " ".join(value.split())


def _exercise(site: Path, packages: list[tuple[int,bytes,list]]) -> dict:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import Select, WebDriverWait
    from scripts.audit_browser_visual import local_server
    options=webdriver.ChromeOptions()
    for arg in ("--headless=new","--disable-background-networking",
                "--no-first-run","--no-default-browser-check",
                "--disable-sync","--disable-extensions",
                "--no-sandbox","--disable-dev-shm-usage",
                "--proxy-server=direct://","--proxy-bypass-list=*"):
        options.add_argument(arg)
    options.add_argument("--user-data-dir="+str(site/"profile"))
    observations=0
    with local_server(site) as base:
        with webdriver.Chrome(options=options) as driver:
            driver.set_page_load_timeout(20)
            url=base+"/app/rc1-chapter9-draft.html"
            for width,height,mobile in ((390,844,True),(1280,800,False)):
                driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride",{
                    "width":width,"height":height,"deviceScaleFactor":1,
                    "mobile":mobile})
                driver.get(url)
                WebDriverWait(driver,15).until(
                    lambda d:d.find_element(By.ID,"course-select").is_enabled())
                for number,raw,items in packages:
                    Select(driver.find_element(By.ID,"course-select")
                           ).select_by_value(str(number))
                    WebDriverWait(driver,10).until(lambda d:
                        _normalized(items[0]["prompt"]["en"]) in
                        _normalized(d.find_element(
                            By.CSS_SELECTOR,"#app h1.question").text))
                    observations+=1
                    for language in ("ms","zh","en"):
                        Select(driver.find_element(By.ID,"locale")
                               ).select_by_value(language)
                        WebDriverWait(driver,10).until(lambda d:
                            _normalized(items[0]["prompt"][language]) in
                            _normalized(d.find_element(
                                By.CSS_SELECTOR,"#app h1.question").text))
                        observations+=1
                # Drive real first five original Section9.6 activities
                # through the actual answer/check/next UI, then verify the
                # scientifically clarified sixth candidate content.
                Select(driver.find_element(By.ID,"course-select")
                       ).select_by_value("6")
                items=packages[5][2]
                for index in range(5):
                    current=items[index]
                    if current.get("type")!="mcq":
                        raise ValueError("V3_BROWSER_FIRST_FIVE_NOT_MCQ")
                    correct=current["answerKey"]["correct"]
                    locator="#app .choices button.choice[data-value='"+correct+"']"
                    WebDriverWait(driver,10).until(
                        lambda d:d.find_element(By.CSS_SELECTOR,locator).is_enabled())
                    driver.find_element(By.CSS_SELECTOR,locator).click()
                    driver.find_element(By.ID,"check").click()
                    driver.find_element(By.ID,"check").click()
                    WebDriverWait(driver,10).until(lambda d:
                        _normalized(items[index+1]["prompt"]["en"]) in
                        _normalized(d.find_element(
                            By.CSS_SELECTOR,"#app h1.question").text))
                if _normalized(items[5]["prompt"]["en"]) not in (
                    _normalized(driver.find_element(
                        By.CSS_SELECTOR,"#app h1.question").text)):
                    raise ValueError("V3_BROWSER_REVISED_SIXTH_NOT_RENDERED")
                if "2 cm" not in items[5]["prompt"]["en"] or (
                        "8 cm" not in items[5]["prompt"]["en"]):
                    raise ValueError("V3_BROWSER_REVISED_PHYSICS_INPUT_MISSING")
                observations+=1
                # BSA-197: the previous 50 checks visited only each
                # section's first prompt and the first five original 9.6
                # MCQs. Exercise the ACTUAL full authoring set instead.
                # Skip is a user UI navigation action, not a reviewer PASS.
                # Each distinct activity in each locale is displayed on
                # both mobile and desktop. Never infer scientific validity.
                complete_locale_checks=0
                for section_number,raw,section_items in packages:
                    Select(driver.find_element(By.ID,"course-select")
                           ).select_by_value(str(section_number))
                    for activity_index,authored in enumerate(section_items):
                        Select(driver.find_element(By.ID,"locale")
                               ).select_by_value("en")
                        WebDriverWait(driver,10).until(lambda d:
                            _normalized(authored["prompt"]["en"]) in
                            _normalized(d.find_element(
                                By.CSS_SELECTOR,"#app h1.question").text))
                        for language in ("en","ms","zh"):
                            Select(driver.find_element(By.ID,"locale")
                                   ).select_by_value(language)
                            WebDriverWait(driver,10).until(lambda d:
                                _normalized(authored["prompt"][language]) in
                                _normalized(d.find_element(
                                    By.CSS_SELECTOR,"#app h1.question").text))
                            complete_locale_checks += 1
                            observations += 1
                        if driver.execute_script(
                                "return document.documentElement.scrollWidth > innerWidth + 1"):
                            raise ValueError(
                                "V3_BROWSER_ACTUAL_ACTIVITY_HORIZONTAL_OVERFLOW")
                        WebDriverWait(driver,10).until(
                            lambda d:d.find_element(By.ID,"skip").is_enabled())
                        driver.find_element(By.ID,"skip").click()
                    WebDriverWait(driver,10).until(
                        lambda d:d.find_element(By.ID,"restart").is_enabled())
                if complete_locale_checks != 108*3:
                    raise ValueError("V3_BROWSER_INCOMPLETE_REAL_ACTIVITY_LOCALES")
                browser=driver.execute_script("""
                  return {width:innerWidth,
                    scroll:document.documentElement.scrollWidth,
                    storage:localStorage.length+sessionStorage.length,
                    external:performance.getEntriesByType('resource').some(
                      e=>!e.name.startsWith(location.origin+'/'))};""")
                if (browser["width"]!=width
                        or browser["scroll"]>width+1
                        or browser["storage"]!=0
                        or browser["external"] is not False):
                    raise ValueError("V3_BROWSER_VIEWPORT_OR_PRIVACY_FAILURE")
    return {"renderedChecks":observations,"viewports":2,"locales":3,
            "all108ActivitiesVisited":True,
            "allLocaleViewportPromptChecks":108*3*2,
            "sourceFree":True,"publicationAuthorized":False,
            "originalModelVerdictsChanged":False}


def run(private: Path) -> dict:
    proposal,packages=_source_bound_packages(private)
    with tempfile.TemporaryDirectory(prefix="bosla-v3-real-unadmitted-browser-") as folder:
        site=Path(folder)
        _stage_site(site,packages)
        observed=_exercise(site,packages)
    return {"status":"ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS",
            "proposalSha256":proposal,"sections":len(packages),
            "activitiesInCandidate":sum(len(items) for _,_,items in packages),
            "genuineGeminiReviewsAdded":0,"learnerPilotAccepted":False,
            "versionedScopeAdmitted":False,**observed}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root",type=Path)
    args=parser.parse_args(argv)
    local=os.environ.get("LOCALAPPDATA")
    if not local:
        print(json.dumps({"status":"STOP_BROWSER_MISSING_LOCALAPPDATA",
                          "publicationAuthorized":False}))
        return 3
    private=(args.private_root or
             Path(local)/"Microvid"/"BoslaV3ReviewYoga6")
    if (private.is_symlink() or
            not private.resolve().is_relative_to(
                (Path(local)/"Microvid").resolve())):
        print(json.dumps({"status":"STOP_BROWSER_UNSAFE_PRIVATE_ROOT",
                          "publicationAuthorized":False}))
        return 3
    try:
        result=run(private)
    except Exception as exc:
        safe=str(exc)
        print(json.dumps({"status":"STOP_ACTUAL_CHAPTER9_BROWSER_QA",
                          "errorClass":type(exc).__name__,
                          "errorCode":safe if safe.startswith("V3_BROWSER_")
                              and len(safe)<128 else None,
                          "publicationAuthorized":False}))
        return 3
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())

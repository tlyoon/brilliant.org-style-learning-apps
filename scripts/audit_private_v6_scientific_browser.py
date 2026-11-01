"""Private, source-verified trilingual learner-surface scientific audit.

Checks that ALL 18 original-source activities visibly render their entire
localized question and interaction data, and that all nine MCQ correct answers
yield exactly their controlled corrected-v6 localized science feedback.
Does not establish free-text translation accuracy or academic approval.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster
from scripts.audit_browser_visual import stage_bundle,local_server

EXPECTED_V6_SHA="12aa856491536171756ce2dffcee30ccb26434d630088b46901c529fb2648fc6"
LANGS=("en","ms","zh")


def normalize_visible(value:str)->str:
    return " ".join(value.split())


def check_science_surface(activity:dict,locale:str,prompt:str,body:str)->None:
    if locale not in LANGS:
        raise ValueError("unsupported locale")
    expected=activity["prompt"][locale]
    if normalize_visible(prompt)!=normalize_visible(expected):
        raise ValueError("rendered scientific question differs from controlled locale")
    if locale=="ms" and re.search(r"\babadi\b",body,flags=re.I):
        raise ValueError("old incorrect eternal-for-conservative wording visible")
    if "\ufffd" in prompt:
        raise ValueError("replacement character in localized scientific question")
    if activity["type"]=="interactive":
        ix=activity["interaction"]
        items=ix.get("items",[])
        if not items:
            raise ValueError("interaction items missing")
        # Interaction selection/ordering is already independently physics-tested;
        # here ensure the learner can READ source-controlled translated labels.
        for item in items:
            translated=item["label"][locale]
            if normalize_visible(translated) not in normalize_visible(body):
                raise ValueError("localized interaction item is not visible")


def audit_v6_scientific_browser(*,package_file:Path,pdf_file:Path,
                               packets_file:Path,repository:Path)->dict:
    identity=verify_full_source_packet_roster(
        package_file=package_file,source_pdf=pdf_file,
        packets_file=packets_file,expected_count=18)
    if (identity["packageSha256"]!=EXPECTED_V6_SHA or
        identity["newlyReverifiedSourceActivities"]!=18 or
        identity["publicationAuthorized"] is not False):
        raise ValueError("corrected private source-v6 identity mismatch")
    package=json.loads(package_file.read_text(encoding="utf-8"))
    activities=package["activities"]
    if len(activities)!=18 or sum(x["type"]=="mcq" for x in activities)!=9:
        raise ValueError("private Section 9.4 roster mismatch")
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait,Select
    questions=0
    feedback=0
    itemchecks=0
    with tempfile.TemporaryDirectory(prefix="science-locale-browser-") as dirname:
        base=Path(dirname)
        site=base/"site";site.mkdir()
        stage_bundle(repository,package_file,site)
        options=webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-first-run")
        options.add_argument("--user-data-dir="+str(base/"chrome-profile"))
        with local_server(site) as url:
            driver=webdriver.Chrome(options=options)
            try:
                for activity in activities:
                    aid=activity["id"]
                    for lang in LANGS:
                        driver.get(url+"/index.html?"+urlencode({"activity":aid}))
                        WebDriverWait(driver,10).until(
                            lambda d:len(d.find_elements(By.CSS_SELECTOR,"#app .card h1.question"))==1)
                        Select(driver.find_element(By.ID,"locale")).select_by_value(lang)
                        question=driver.find_element(By.CSS_SELECTOR,"#app h1.question").text
                        body=driver.find_element(By.CSS_SELECTOR,"#app .card").text
                        check_science_surface(activity,lang,question,body)
                        questions+=1
                        if activity["type"]=="interactive":
                            itemchecks+=len(activity["interaction"]["items"])
                            continue
                        choices=driver.find_elements(By.CSS_SELECTOR,"#app .choices button")
                        expect=activity["answerKey"]["options"]
                        if len(choices)!=4 or len(expect)!=4:
                            raise ValueError("MCQ translated option count no longer four")
                        displayed=[normalize_visible(x.text) for x in choices]
                        controlled=[normalize_visible(x["label"][lang]) for x in expect]
                        if len(set(displayed))!=4 or sorted(displayed)!=sorted(controlled):
                            raise ValueError("rendered scientific MCQ options diverge from source")
                        good=next(x for x in expect if x["id"]==activity["answerKey"]["correct"])
                        target=next(b for b in choices if normalize_visible(b.text)==normalize_visible(good["label"][lang]))
                        target.click()
                        check=driver.find_element(By.ID,"check")
                        if not check.is_enabled():
                            raise ValueError("correct answer fails to enable check control")
                        check.click()
                        WebDriverWait(driver,4).until(
                            lambda d:len(d.find_elements(By.CSS_SELECTOR,"#app .feedback"))>0)
                        actual=driver.find_element(By.CSS_SELECTOR,"#app .feedback").text
                        if normalize_visible(activity["feedback"][lang]) not in normalize_visible(actual):
                            raise ValueError("localized scientific correctness feedback is not displayed")
                        if lang=="ms" and re.search(r"\babadi\b",actual,flags=re.I):
                            raise ValueError("scientifically incorrect conservative translation persisted")
                        feedback+=1
            finally:
                driver.quit()
    if (questions,feedback,itemchecks)!=(54,27,sum(len(a["interaction"]["items"]) for a in activities if a["type"]=="interactive")*3):
        raise ValueError("scientific UI coverage incomplete")
    return {
       "status":"SOURCE_BOUND_V6_TRILINGUAL_LEARNER_CONTENT_CHECK",
       "originalPdfSha256":identity["sourceSha256"],
       "privateV6PackageSha256":identity["packageSha256"],
       "originalSourceActivitiesReverified":18,
       "localizedQuestionSurfacesVerified":questions,
       "localizedMcqCorrectFeedbackVerified":feedback,
       "localizedInteractiveItemLabelsVerified":itemchecks,
       "malayIncorrectConservativeLexemesVisible":0,
       "translationSemanticEquivalenceProven":False,
       "fullScientificAcademicQA":"REVIEW_REQUIRED",
       "formalAcademicPASS":0,"publicationAuthorized":False,
    }


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("package","pdf","packets","repo","out"):
        p.add_argument("--"+k,type=Path,required=True)
    a=p.parse_args()
    try:
        output=a.out.resolve()
        if output.exists() or output.is_relative_to(ROOT) or not output.parent.is_dir():
            raise ValueError("new private receipt outside repository required")
        report=audit_v6_scientific_browser(
            package_file=a.package,pdf_file=a.pdf,
            packets_file=a.packets,repository=a.repo)
        with output.open("x",encoding="utf-8") as f:
            json.dump(report,f,ensure_ascii=True,indent=2)
            f.write("\n")
        print(json.dumps(report,ensure_ascii=True))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps({"status":"V6_SCIENTIFIC_BROWSER_BLOCKED",
            "errorType":type(exc).__name__,"academicQA":"REVIEW_REQUIRED",
            "publicationAuthorized":False}))
        return 2

if __name__=="__main__":
    raise SystemExit(main())

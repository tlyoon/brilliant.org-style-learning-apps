"""Private original-source-bound real-browser audit of solution explanations.

Checks that the complete scientific reasoning remains hidden before a valid
answer, then becomes visible as inert, locale-specific authored text after
the learner submits the correct MCQ or interactive response. No publication.
"""
from __future__ import annotations
import argparse,json,sys,tempfile
from pathlib import Path
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster
from scripts.audit_browser_visual import stage_bundle,local_server

V10_SHA="6d0a9179025aa177ec76e97a14c6ac93fc0f331472444f9f9ad9f48abb41044f"
V11_SHA="8218f38eca1601ca0ec97061a5f566caa2e465aef681d8931deb53c90cafae97"
PDF_SHA="08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578"


def select_correct(driver,activity):
    from selenium.webdriver.common.by import By
    mode=activity.get("interactionMode")
    if activity.get("type")=="mcq":
        driver.find_element(By.CSS_SELECTOR,
            '#app .choices button[data-value="'+activity["answerKey"]["correct"]+'"]').click()
    elif mode in ("classification","matching"):
        for place in activity["interaction"]["placements"]:
            driver.find_element(By.CSS_SELECTOR,
                '#app .target-choice[data-item-id="'+place["itemId"]+
                '"][data-target-id="'+place["targetId"]+'"]').click()
    elif mode=="selection":
        for item_id in activity["interaction"]["correctSelections"]:
            driver.find_element(By.CSS_SELECTOR,
                '#app .choices button[data-value="'+item_id+'"]').click()
    elif mode=="ordering":
        correct=activity["interaction"]["correctOrder"]
        for i,item_id in enumerate(correct):
            current=[r.get_attribute("data-item-id") for r in
                     driver.find_elements(By.CSS_SELECTOR,"#app .order-row")]
            pos=current.index(item_id)
            while pos>i:
                driver.find_element(By.CSS_SELECTOR,
                    '#app .order-control[data-item-id="'+item_id+
                    '"][data-delta="-1"]').click()
                pos-=1
    else:
        raise ValueError("unsupported interaction mode for source-bound QA")


def audit(*,package_file:Path,source_pdf:Path,packets_file:Path,
          repository:Path,candidate_revision:str="v10")->dict:
    expected_sha={"v10":V10_SHA,"v11":V11_SHA}.get(candidate_revision)
    if expected_sha is None:
        raise ValueError("only controlled private v10/v11 identities admitted")
    original=verify_full_source_packet_roster(
        package_file=package_file,source_pdf=source_pdf,
        packets_file=packets_file,expected_count=18)
    if (original["packageSha256"]!=expected_sha or
        original["sourceSha256"]!=PDF_SHA or
        original["newlyReverifiedSourceActivities"]!=18 or
        original["publicationAuthorized"] is not False):
        raise ValueError("original source/controlled private revision SHA drift")
    activities=json.loads(package_file.read_text("utf-8"))["activities"]
    if len(activities)!=18:
        raise ValueError("source-bound roster no longer 18 activities")
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait,Select
    count=0
    with tempfile.TemporaryDirectory(prefix="private-explanation-learner-") as tmp:
        root=Path(tmp)
        site=root/"site"
        site.mkdir()
        stage_bundle(repository,package_file,site)
        options=webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-extensions")
        options.add_argument("--user-data-dir="+str(root/"chrome"))
        with local_server(site) as url:
            driver=webdriver.Chrome(options=options)
            try:
                for activity in activities:
                    for lang in ("en","ms","zh"):
                        driver.get(url+"/index.html?"+urlencode({"activity":activity["id"]}))
                        WebDriverWait(driver,10).until(
                            lambda d:len(d.find_elements(By.CSS_SELECTOR,"#app h1.question"))==1)
                        Select(driver.find_element(By.ID,"locale")).select_by_value(lang)
                        if driver.find_elements(By.CSS_SELECTOR,"#app .scientific-reasoning"):
                            raise ValueError("full scientific reasoning exposed before answer")
                        select_correct(driver,activity)
                        check=driver.find_element(By.ID,"check")
                        if not check.is_enabled():
                            raise ValueError("correct interaction does not enable check")
                        check.click()
                        WebDriverWait(driver,5).until(
                            lambda d:len(d.find_elements(By.CSS_SELECTOR,
                                "#app .scientific-reasoning .reasoning-text"))==1)
                        expected=activity["explanation"][lang]
                        actual=driver.find_element(By.CSS_SELECTOR,
                            "#app .scientific-reasoning .reasoning-text").text
                        if " ".join(actual.split())!=" ".join(expected.split()):
                            raise ValueError("rendered scientific explanation is not controlled text")
                        if not driver.find_elements(By.CSS_SELECTOR,"#app .feedback[role='status']"):
                            raise ValueError("learner correct-answer feedback absent")
                        count+=1
            finally:
                driver.quit()
    if count!=54:
        raise ValueError("incomplete 18 by 3 real-browser explanation coverage")
    return {"status":"SOURCE_BOUND_PRIVATE_"+candidate_revision.upper()+"_CORRECT_ONLY_EXPLANATION_BROWSER",
            "originalPdfSha256":PDF_SHA,
            "controlledCandidateRevision":candidate_revision,
            "controlledCandidatePackageSha256":expected_sha,
            "privateV10PackageSha256":expected_sha if candidate_revision=="v10" else None,
            "originalSourceActivitiesReverified":18,
            "localizedCorrectOnlyExplanationSurfacesVerified":count,
            "reasoningHiddenBeforeAnswers":True,
            "localeSpecificOriginalExplanationsEqualRenderedText":True,
            "scientificSemanticEquivalenceFullyProven":False,
            "formalAcademicPASS":0,"academicQA":"REVIEW_REQUIRED",
            "publicationAuthorized":False}


def main()->int:
    p=argparse.ArgumentParser()
    for k in ("package","pdf","packets","repo","out"):
        p.add_argument("--"+k,type=Path,required=True)
    p.add_argument("--candidate-revision",choices=("v10","v11"),default="v10")
    a=p.parse_args()
    try:
        if a.out.exists() or a.out.resolve().is_relative_to(ROOT):
            raise ValueError("new external private receipt required")
        report=audit(package_file=a.package,source_pdf=a.pdf,
                     packets_file=a.packets,repository=a.repo,
                     candidate_revision=a.candidate_revision)
        with a.out.open("x",encoding="utf-8") as f:
            json.dump(report,f,ensure_ascii=True,indent=2)
            f.write("\n")
        print(json.dumps(report))
        return 0
    except (ValueError,KeyError,TypeError,OSError) as ex:
        print(json.dumps({"status":"PRIVATE_EXPLANATION_BROWSER_BLOCKED",
            "errorType":type(ex).__name__,"publicationAuthorized":False}))
        return 2
if __name__=="__main__":raise SystemExit(main())

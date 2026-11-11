"""Source-free Chrome proof of authentic player events -> RC1 chapter route.

The six package-shaped inputs are exclusively original synthetic fixtures.
This is NOT an original Chapter 9 browser/academic campaign, and confers
no scientific, multilingual, learner pilot or release approval.
"""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait

from scripts.audit_browser_visual import local_server
from scripts.check_course_preview_browser import stage_site, _synthetic_prompt


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="bosla-rc1-actual-player-synthetic-") as folder:
        site = Path(folder)
        stage_site(site)
        options = webdriver.ChromeOptions()
        for arg in ("--headless=new", "--disable-background-networking",
                    "--no-first-run", "--no-default-browser-check",
                    "--disable-sync", "--disable-extensions", "--no-sandbox",
                    "--disable-dev-shm-usage", "--proxy-server=direct://",
                    "--proxy-bypass-list=*"):
            options.add_argument(arg)
        options.add_argument("--user-data-dir=" + str(site / "profile"))
        with local_server(site) as base:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(15)
            try:
                url = base + "/app/rc1-chapter9-draft.html"
                for width, height, mobile in ((390, 844, True), (1280, 800, False)):
                    driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
                        "width":width, "height":height,
                        "deviceScaleFactor":1, "mobile":mobile,
                    })
                    driver.get(url)
                    WebDriverWait(driver, 10).until(
                        lambda d: d.find_element(By.ID, "course-select").is_enabled()
                    )
                    assert len(driver.find_elements(
                        By.CSS_SELECTOR, "#rc1-draft-list li")) == 6
                    summary = driver.find_element(By.ID, "rc1-draft-summary").text
                    assert "0 / 0" in summary and "0 / 6" in summary
                    # Use the REAL single-package player controls, not route
                    # simulator methods or forged evidence events.
                    Select(driver.find_element(By.ID, "course-select")).select_by_value("1")
                    WebDriverWait(driver, 10).until(
                        lambda d: _synthetic_prompt(1, "en") in
                        d.find_element(By.CSS_SELECTOR, "#app h1.question").text
                    )
                    driver.find_elements(By.CSS_SELECTOR,
                        "#app .choices button.choice")[0].click()
                    driver.find_element(By.ID, "check").click()
                    WebDriverWait(driver, 5).until(
                        lambda d: "1 / 1" in d.find_element(
                            By.ID, "rc1-draft-summary").text
                    )
                    assert "0 / 6" in driver.find_element(
                        By.ID, "rc1-draft-summary").text, (
                        "ANSWER_CHECK_ALONE_MUST_NOT_UNLOCK_PREREQUISITE"
                    )
                    assert "locked" in driver.find_elements(
                        By.CSS_SELECTOR, "#rc1-draft-list li")[1].text
                    driver.find_element(By.ID, "check").click()  # actual completed event
                    WebDriverWait(driver, 5).until(
                        lambda d: "1 / 6" in d.find_element(
                            By.ID, "rc1-draft-summary").text
                    )
                    assert "ready" in driver.find_elements(
                        By.CSS_SELECTOR, "#rc1-draft-list li")[1].text
                    assert "2" in driver.find_element(
                        By.ID, "rc1-draft-status").text

                    # First wrong then correct is assisted; never independent.
                    Select(driver.find_element(By.ID, "course-select")).select_by_value("2")
                    WebDriverWait(driver, 10).until(
                        lambda d: _synthetic_prompt(2, "en") in
                        d.find_element(By.CSS_SELECTOR, "#app h1.question").text
                    )
                    driver.find_elements(By.CSS_SELECTOR,
                        "#app .choices button.choice")[1].click()
                    driver.find_element(By.ID, "check").click()
                    WebDriverWait(driver, 5).until(
                        lambda d: "1 / 2" in d.find_element(
                            By.ID, "rc1-draft-summary").text
                    )
                    driver.find_element(By.ID, "check").click()  # try again
                    driver.find_elements(By.CSS_SELECTOR,
                        "#app .choices button.choice")[0].click()
                    driver.find_element(By.ID, "check").click()
                    driver.find_element(By.ID, "check").click()  # completed assisted
                    WebDriverWait(driver, 5).until(
                        lambda d: "assisted completions: 1" in
                        d.find_element(By.ID, "rc1-draft-summary").text
                    )
                    assert "1 / 6" in driver.find_element(
                        By.ID, "rc1-draft-summary").text
                    assert "locked" in driver.find_elements(
                        By.CSS_SELECTOR, "#rc1-draft-list li")[2].text, (
                        "ASSISTED_COMPLETION_MUST_NOT_UNLOCK_DOWNSTREAM"
                    )
                    browser = driver.execute_script("""
                        const reset=document.querySelector('#rc1-draft-reset');
                        return {width:innerWidth,scroll:document.documentElement.scrollWidth,
                          touch:reset.getBoundingClientRect().height,
                          stored:localStorage.length+sessionStorage.length,
                          external:performance.getEntriesByType('resource').some(
                            entry=>!entry.name.startsWith(location.origin+'/'))};
                    """)
                    assert browser["width"] == width
                    assert browser["scroll"] <= width + 1
                    assert browser["touch"] >= 44
                    assert browser["stored"] == 0
                    assert browser["external"] is False

                    # Clear all route observations, current draft package and
                    # anonymous player session counters together.
                    driver.find_element(By.ID, "rc1-draft-reset").click()
                    WebDriverWait(driver, 5).until(
                        lambda d: "0 / 0" in d.find_element(
                            By.ID, "rc1-draft-summary").text
                    )
                    assert "Select a subchapter above" in driver.find_element(
                        By.ID, "app").text
                    assert driver.find_element(By.ID, "rc1-draft-reset").get_attribute(
                        "disabled") is not None
                    assert driver.find_element(By.ID, "course-select").get_attribute(
                        "value") in ("", None)

                # Tamper with actual bytes of ONLY a synthetic staged package;
                # the existing exact-roster SHA boundary must still refuse
                # question rendering and therefore any course evidence.
                (site / "content/chapter-9/section-9-1/package.json").write_text(
                    "{}", encoding="utf-8"
                )
                driver.get(url)
                WebDriverWait(driver, 10).until(
                    lambda d: d.find_element(By.ID, "course-select").is_enabled()
                )
                Select(driver.find_element(By.ID, "course-select")).select_by_value("1")
                WebDriverWait(driver, 10).until(
                    lambda d: "Package bytes differ from the selected roster" in
                    d.find_element(By.ID, "app").text
                )
                assert "0 / 0" in driver.find_element(
                    By.ID, "rc1-draft-summary").text
                assert not driver.find_elements(By.CSS_SELECTOR,
                    "#app h1.question"), "TAMPERED_QUESTION_MUST_NOT_RENDER"
                print("RC1_REAL_PLAYER_SYNTHETIC_BROWSER_PASS: real first-check and "
                      "completion events, assisted exclusion, two viewports, "
                      "tamper refusal, no storage or third-party requests")
            finally:
                driver.quit()


if __name__ == "__main__":
    run()

"""One source-free RC1 course-routing engineering smoke (not learner acceptance).

Only original synthetic graph metadata and static code are staged to a
temporary localhost site. No original Chapter 9 package/PDF, real learner,
external model, credentials, public deployment or persistent evidence.
"""
from __future__ import annotations

from pathlib import Path
import json
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from scripts.audit_browser_visual import local_server

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "rc1-course-journey.html", "rc1-course-routing.js",
    "rc1-course-demo.js", "rc1-course-routing.css",
)
VIEWPORTS = ((390, 844, True), (1280, 800, False))


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="bosla-rc1-sourcefree-") as folder:
        staging = Path(folder)
        app = staging / "app"
        docs = staging / "docs"
        app.mkdir()
        docs.mkdir()
        for name in FILES:
            shutil.copyfile(ROOT / "app" / name, app / name)
        shutil.copyfile(ROOT / "docs" / "rc1_engineering_scope.json",
                        docs / "rc1_engineering_scope.json")
        options = webdriver.ChromeOptions()
        for flag in (
            "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
            "--disable-background-networking", "--disable-sync",
            "--disable-extensions", "--no-first-run",
            "--no-default-browser-check", "--proxy-server=direct://",
            "--proxy-bypass-list=*",
        ):
            options.add_argument(flag)
        options.add_argument("--user-data-dir=" + str(staging / "chrome-profile"))
        with local_server(staging) as base:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(20)
            try:
                url = base + "/app/rc1-course-journey.html"
                for width, height, mobile in VIEWPORTS:
                    driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
                        "width": width, "height": height,
                        "deviceScaleFactor": 1, "mobile": mobile,
                    })
                    driver.get(url)
                    WebDriverWait(driver, 12).until(
                        lambda d: len(d.find_elements(
                            By.CSS_SELECTOR, "#rc1-route .rc1-card")) == 6
                    )
                    first = driver.find_elements(
                        By.CSS_SELECTOR, "#rc1-route .rc1-card")[0]
                    assert "Vector reasoning" in driver.find_element(
                        By.ID, "rc1-status").text
                    assert first.find_elements(By.CSS_SELECTOR, "button")[0].is_enabled()
                    second = driver.find_elements(
                        By.CSS_SELECTOR, "#rc1-route .rc1-card")[1]
                    assert not second.find_elements(By.CSS_SELECTOR, "button")[0].is_enabled(), (
                        "SYNTHETIC_PREREQUISITE_WAS_NOT_LOCKED"
                    )
                    first.find_elements(By.CSS_SELECTOR, "button")[0].click()
                    WebDriverWait(driver, 5).until(
                        lambda d: "Motion representations" in d.find_element(
                            By.ID, "rc1-status").text
                    )
                    second = driver.find_elements(
                        By.CSS_SELECTOR, "#rc1-route .rc1-card")[1]
                    second.find_elements(By.CSS_SELECTOR, "button")[1].click()
                    assert "assisted practice" in driver.find_element(
                        By.ID, "rc1-status").text
                    first = driver.find_elements(
                        By.CSS_SELECTOR, "#rc1-route .rc1-card")[0]
                    first.find_elements(By.CSS_SELECTOR, "button")[2].click()
                    assert "review due" in driver.find_element(
                        By.ID, "rc1-status").text
                    driver.find_element(By.ID, "rc1-reset").click()
                    assert "Vector reasoning" in driver.find_element(
                        By.ID, "rc1-status").text
                    assert driver.find_element(By.ID, "rc1-reset").get_attribute(
                        "disabled") is not None
                    geometry = driver.execute_script("""
                        const button = document.querySelector('#rc1-route button');
                        return {
                          width: window.innerWidth,
                          height: window.innerHeight,
                          scrollWidth: document.documentElement.scrollWidth,
                          touchTargetHeight: button.getBoundingClientRect().height,
                          stored: localStorage.length + sessionStorage.length,
                          outside: performance.getEntriesByType('resource')
                            .some(item => !item.name.startsWith(location.origin + '/')),
                        };
                    """)
                    assert geometry["width"] == width
                    assert geometry["height"] == height
                    assert geometry["scrollWidth"] <= width + 1
                    assert geometry["touchTargetHeight"] >= 44
                    assert geometry["stored"] == 0
                    assert geometry["outside"] is False
                # Schema-valid but identity-tampered source-free scope must
                # fail before presenting a simulated recommended route.
                scope_file = docs / "rc1_engineering_scope.json"
                altered = json.loads(scope_file.read_text(encoding="utf-8"))
                altered["baselineGitSha"] = "b" * 40
                scope_file.write_text(json.dumps(altered), encoding="utf-8")
                driver.get(url)
                WebDriverWait(driver, 8).until(
                    lambda d: "unavailable or invalid" in d.find_element(
                        By.ID, "rc1-status").text
                )
                assert driver.find_elements(By.CSS_SELECTOR, "#rc1-route .rc1-card") == []
                assert driver.find_element(By.ID, "rc1-reset").get_attribute(
                    "disabled") is not None
            finally:
                driver.quit()
    print("RC1_SOURCEFREE_COURSE_ROUTING_BROWSER_PASS: six concepts, two viewports, "
          "synthetic independent/assisted/review, no storage, no external requests")


if __name__ == "__main__":
    run()

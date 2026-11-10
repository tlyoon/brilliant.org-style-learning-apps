"""Real headless-Chrome smoke of the local instructor preview with synthetic data.

This is NOT the denied private source/browser academic audit. It stages only
synthetic packages and public runtime files in a disposable loopback-only
server; never uses PDFs, private sources, AI calls or student data. Visual,
scientific and classroom acceptance remain NOT VERIFIED.
"""
from __future__ import annotations

from functools import partial
from hashlib import sha256
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import tempfile
from threading import Thread

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
LANGS = ("en", "ms", "zh")
SIZES = ((390, 844, True), (1280, 800, False))


def _synthetic_prompt(section: int, lang: str) -> str:
    stems = {
        "en": "Synthetic question",
        "ms": "Soalan sintetik",
        "zh": "合成问题",
    }
    return f"{stems[lang]} {section} {lang}"


def _fixture(section: int) -> bytes:
    texts = {lang: _synthetic_prompt(section, lang) for lang in LANGS}
    hints = {lang: "Test-only hint " + lang for lang in LANGS}
    feedback = {lang: "Test-only feedback " + lang for lang in LANGS}
    labels = {lang: "Test-only option " + lang for lang in LANGS}
    activities = []
    for kind in ("mcq", "interactive"):
        for level in ("easy", "moderate", "challenging"):
            for number in range(3):
                row = {
                    "id": f"{kind}-{level}-{number}",
                    "type": kind,
                    "difficulty": level,
                    "prompt": texts,
                    "hints": [hints],
                    "feedback": feedback,
                    "explanation": feedback,
                }
                if kind == "mcq":
                    row["answerKey"] = {
                        "correct": "a",
                        "options": [{"id": "a", "label": labels},
                                    {"id": "b", "label": feedback}],
                    }
                else:
                    row["interactionMode"] = "selection"
                    row["interaction"] = {
                        "items": [{"id": "a", "label": labels},
                                  {"id": "b", "label": feedback}],
                        "correctSelections": ["a"],
                    }
                activities.append(row)
    payload = {
        "packageId": f"chapter-9-section-9-{section}",
        "chapter": "Chapter 9",
        "subchapter": f"9.{section} synthetic test only",
        "status": "draft",
        "locales": list(LANGS),
        "sourceManifest": f"content/source-manifests/chapter-9-section-9-{section}.json",
        "activities": activities,
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:
        pass


def stage_site(root: Path) -> None:
    app = root / "app"
    app.mkdir()
    for filename in (
        "app.js", "styles.css", "visual-renderers.js",
        "course-preview.html", "course-preview.js", "course-preview.css",
    ):
        shutil.copyfile(ROOT / "app" / filename, app / filename)
    # Only empty domain hooks: no third-party assets or science data.
    (app / "domain-renderers.js").write_text("", encoding="utf-8")
    (app / "domain-styles.css").write_text("", encoding="utf-8")
    cases = []
    for section in range(1, 7):
        relative = f"content/chapter-9/section-9-{section}/package.json"
        raw = _fixture(section)
        target = root.joinpath(*relative.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        cases.append({
            "sectionNumber": section, "packagePath": relative,
            "packageSha256": sha256(raw).hexdigest(),
        })
    local = root / "local-pilot"
    local.mkdir()
    (local / "roster.json").write_text(json.dumps({
        "scopeId": "sourcefree-pilot-browser-smoke-synthetic",
        "baselineGitSha": "a" * 40,
        "chapterNumber": 9,
        "mode": "OFFLINE_EXISTING_PACKAGES_ONLY",
        "cases": cases,
        "modelCallsAllowed": False,
        "pdfReadsAllowed": False,
        "publicationAllowed": False,
    }), encoding="utf-8")


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="bosla-sourcefree-browser-") as folder:
        site = Path(folder)
        stage_site(site)
        handler = partial(QuietHandler, directory=str(site))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        options = webdriver.ChromeOptions()
        for flag in (
            "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
            "--disable-background-networking", "--disable-sync",
            "--disable-extensions", "--no-first-run",
            "--no-default-browser-check", "--proxy-server=direct://",
            "--proxy-bypass-list=*",
        ):
            options.add_argument(flag)
        options.add_argument("--user-data-dir=" + str(site / "browser-profile"))
        driver = None
        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(15)
            url = f"http://127.0.0.1:{server.server_port}/app/course-preview.html"
            checked = 0
            screenshots = []
            for width, height, mobile in SIZES:
                driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
                    "width": width, "height": height,
                    "deviceScaleFactor": 1, "mobile": mobile,
                })
                for lang in LANGS:
                    driver.get(url)
                    WebDriverWait(driver, 10).until(
                        lambda d: d.find_element(By.ID, "course-select").is_enabled()
                    )
                    assert len(driver.find_elements(By.CSS_SELECTOR, "#course-select option")) == 7
                    assert "Select a subchapter above" in driver.find_element(By.ID, "app").text, (
                        "EXTERNAL_SELECTION_MUST_START_AS_IDLE_NOT_ERROR"
                    )
                    Select(driver.find_element(By.ID, "locale")).select_by_value(lang)
                    Select(driver.find_element(By.ID, "course-select")).select_by_value("1")
                    try:
                        WebDriverWait(driver, 10).until(
                            lambda d: _synthetic_prompt(1, lang) in
                            d.find_element(By.CSS_SELECTOR, "#app h1.question").text
                        )
                    except Exception as exc:
                        # Synthetic-only DOM: no private source or student data.
                        visible = driver.find_element(By.ID, "app").text[:240]
                        console_errors = driver.execute_script(
                            "return document.readyState + ':' + "
                            "String(document.querySelector('#course-status')?.textContent)"
                        )
                        raise AssertionError(
                            "SOURCEFREE_PREVIEW_RENDER_FAILED: " + repr(visible) +
                            " STATUS=" + repr(console_errors)
                        ) from exc
                    assert driver.execute_script(
                        "return document.documentElement.scrollWidth <= "
                        "document.documentElement.clientWidth + 1"
                    ), "HORIZONTAL_OVERFLOW"
                    driver.find_element(By.ID, "hint").click()
                    WebDriverWait(driver, 10).until(
                        lambda d: "Test-only hint " + lang in d.find_element(
                            By.CSS_SELECTOR, "#app .feedback"
                        ).text
                    )
                    assert driver.execute_script(
                        "return document.activeElement?.id"
                    ) == "hint", "KEYBOARD_FOCUS_LOST_AFTER_HINT"
                    assert driver.find_element(
                        By.CSS_SELECTOR, "#app .feedback"
                    ).get_attribute("role") == "status", "HINT_NOT_LIVE_ANNOUNCED"
                    screenshots.append(sha256(driver.get_screenshot_as_png()).hexdigest())
                    checked += 1
                    if width == 390 and lang == "en":
                        # Existing synthetic course preview: independently
                        # exercise real keyboard focus after the normal card
                        # replacement for skip, check feedback, and next.
                        driver.find_element(By.ID, "skip").click()
                        assert driver.execute_script(
                            "return document.activeElement?.matches('#app h1.question')"
                        ), "KEYBOARD_FOCUS_LOST_AFTER_SKIP"
                        assert driver.find_element(
                            By.CSS_SELECTOR, "#app h1.question"
                        ).get_attribute("tabindex") == "-1"
                        driver.find_element(
                            By.CSS_SELECTOR, "#app .choices button.choice"
                        ).click()
                        driver.find_element(By.ID, "check").click()
                        assert driver.execute_script(
                            "return document.activeElement?.id"
                        ) == "check", "KEYBOARD_FOCUS_LOST_AFTER_CHECK"
                        driver.find_element(By.ID, "check").click()
                        assert driver.execute_script(
                            "return document.activeElement?.matches('#app h1.question')"
                        ), "KEYBOARD_FOCUS_LOST_AFTER_NEXT"
                        Select(driver.find_element(By.ID, "course-select")).select_by_value("")
                        _assert_idle = driver.find_element(By.ID, "app").text
                        assert "Select a subchapter above" in _assert_idle
                        assert not driver.find_elements(By.CSS_SELECTOR, "#app h1.question")
                        assert "activity=" not in driver.current_url, (
                            "STALE_ACTIVITY_DEEP_LINK_AFTER_DESELECTION"
                        )
                        Select(driver.find_element(By.ID, "course-select")).select_by_value("2")
                        WebDriverWait(driver, 10).until(
                            lambda d: _synthetic_prompt(2, "en") in
                            d.find_element(By.CSS_SELECTOR, "#app h1.question").text
                        )
                        assert "Not yet demonstrated" in driver.find_element(
                            By.CSS_SELECTOR, "#app .mastery-level"
                        ).text
            # Corrupt only synthetic fixture bytes, not a repository package.
            altered = site / "content/chapter-9/section-9-2/package.json"
            altered.write_bytes(_fixture(3))
            driver.get(url)
            WebDriverWait(driver, 10).until(
                lambda d: d.find_element(By.ID, "course-select").is_enabled()
            )
            Select(driver.find_element(By.ID, "course-select")).select_by_value("2")
            WebDriverWait(driver, 10).until(
                lambda d: "Package bytes differ from the selected roster" in
                d.find_element(By.ID, "app").text
            )
            assert not driver.find_elements(By.CSS_SELECTOR, "#app h1.question")
            assert checked == 6 and len(screenshots) == 6
            print(json.dumps({
                "status": "SOURCEFREE_REAL_BROWSER_PREVIEW_SMOKE_PASS",
                "localeViewportChecks": checked,
                "screenshotDigestsCaptured": len(screenshots),
                "tamperedPackageRejected": True,
                "academicQA": "REVIEW_REQUIRED",
                "classroomPilotReady": False,
                "publicationAuthorized": False,
            }))
        finally:
            if driver is not None:
                driver.quit()
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)


if __name__ == "__main__":
    run()

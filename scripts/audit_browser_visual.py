"""Read-only isolated headless Chrome smoke test for trusted visual activities.

Uses temporary local static assets, private Chrome profile and localhost-only
HTTP. Does not access Gemini, production browsers, publication or user assets.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import tempfile
from threading import Thread
from urllib.parse import urlencode


def stage_bundle(root: Path, package_path: Path, destination: Path) -> None:
    app = root / "app"
    for source_name in ("app.js", "styles.css", "visual-renderers.js"):
        shutil.copyfile(app / source_name, destination / source_name)
    document = (app / "index.html").read_text(encoding="utf-8")
    needle = 'data-package-url=""'
    if document.count(needle) != 1:
        raise ValueError("Player HTML lacks a unique safe package placeholder")
    (destination / "index.html").write_text(
        document.replace(needle, 'data-package-url="package.json"'), encoding="utf-8"
    )
    domain = root / "domains/university-level physics/visuals"
    shutil.copyfile(domain / "physics-renderers.js", destination / "domain-renderers.js")
    shutil.copyfile(domain / "physics-styles.css", destination / "domain-styles.css")
    shutil.copyfile(package_path, destination / "package.json")


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format, *args):
        del args


@contextmanager
def local_server(directory: Path):
    handler = partial(QuietHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:" + str(server.server_address[1])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def audit_browser(root: Path, package: Path) -> dict:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import Select, WebDriverWait

    data = json.loads(package.read_text(encoding="utf-8"))
    ids = [item["id"] for item in data.get("activities", []) if item.get("visualSpec")]
    problems = []
    checks = 0
    with tempfile.TemporaryDirectory(prefix="visual-browser-audit-") as scratch:
        base = Path(scratch)
        bundle = base / "site"
        bundle.mkdir()
        stage_bundle(root, package, bundle)
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-background-networking")
        options.add_argument("--no-first-run")
        options.add_argument("--user-data-dir=" + str(base / "chrome-profile"))
        with local_server(bundle) as url:
            driver = webdriver.Chrome(options=options)
            try:
                for width, height in ((1280, 800), (390, 844)):
                    driver.set_window_size(width, height)
                    for activity_id in ids:
                        driver.get(url + "/index.html?" + urlencode({"activity": activity_id}))
                        for locale in ("en", "ms", "zh"):
                            try:
                                Select(driver.find_element(By.ID, "locale")).select_by_value(locale)
                                WebDriverWait(driver, 8).until(
                                    lambda d: len(d.find_elements(By.CSS_SELECTOR, "figure.physics-visual")) > 0
                                )
                                status = driver.execute_script("""
                                    const figure = document.querySelector('figure.physics-visual');
                                    const card = figure?.closest('.card');
                                    const svg = figure?.querySelector('svg');
                                    return {
                                      fig: !!figure,
                                      svg: !!svg,
                                      desc: figure?.getAttribute('aria-label') || '',
                                      template: figure?.getAttribute('data-template') || '',
                                      semanticCount: figure?.querySelectorAll('[data-semantic-id]').length || 0,
                                      choices: !!card?.querySelector('.choices'),
                                      overflow: figure ? figure.scrollWidth > figure.clientWidth + 2 : false
                                    };
                                """)
                                checks += 1
                                if not status["svg"] or not status["desc"] or status["semanticCount"] < 1:
                                    raise ValueError("missing SVG, accessible label, or semantic nodes")
                                if status["overflow"]:
                                    raise ValueError("visual viewport horizontal overflow")
                                if not status["choices"]:
                                    raise ValueError("visual activity lost response controls")
                            except Exception as exc:
                                problems.append({
                                    "activityId": activity_id, "locale": locale,
                                    "viewportWidth": width, "reason": str(exc)[:300],
                                })
            finally:
                driver.quit()
    return {
        "outcome": "fail" if problems else "browser_dom_smoke_pass",
        "visualActivities": len(ids),
        "checks": checks,
        "issues": problems,
        "pixelQualityVerified": False,
        "fullAccessibilityVerified": False,
        "academicAccuracyVerified": False,
        "publicationAuthorized": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    opts = parser.parse_args()
    try:
        report = audit_browser(opts.repo_root.resolve(), opts.package.resolve())
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["outcome"] == "browser_dom_smoke_pass" else 1
    except Exception as exc:
        print(json.dumps({"outcome": "fail", "issues": [str(exc)[:500]], "publicationAuthorized": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

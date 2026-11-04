"""Read-only isolated headless Chrome smoke test for trusted visual activities.

Uses temporary local static assets, private Chrome profile and localhost-only
HTTP. Does not access Gemini, production browsers, publication or user assets.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import shutil
import struct
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


def capture_review_frame(driver, figure, output: Path, activity_id: str,
                         locale: str, width: int, index: int) -> dict:
    """Capture the ENTIRE SVG figure, even below the Chrome viewport.

    Selenium WebElement.screenshot_as_png silently clips below-the-fold SVGs.
    Use a restricted Chromium CDP full-page clip and validate PNG geometry.
    This is source evidence, not pixel-quality or academic acceptance.
    """
    safe = re.sub(r"[^a-zA-Z0-9_.-]", "_", activity_id)[:65]
    file = f"{index:03d}-{safe}-{locale}-{width}.png"
    bounds = driver.execute_script("""
        const r = arguments[0].getBoundingClientRect();
        return {x: r.left + window.scrollX, y: r.top + window.scrollY,
                width: r.width, height: r.height};
    """, figure)
    if (not isinstance(bounds, dict) or
            any(type(bounds.get(k)) not in (int,float) for k in
                ("x","y","width","height")) or
            bounds["width"] < 100 or bounds["height"] < 100 or
            bounds["width"] > 2500 or bounds["height"] > 2500):
        raise ValueError("invalid full-figure screenshot geometry")
    frame = driver.execute_cdp_cmd("Page.captureScreenshot", {
        "format":"png", "captureBeyondViewport":True,
        "clip":{**bounds,"scale":1},
    })
    data = base64.b64decode(frame["data"],validate=True)
    if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data)<100:
        raise ValueError("browser screenshot was not a complete PNG")
    actual_width,actual_height = struct.unpack(">II",data[16:24])
    if (abs(actual_width-bounds["width"])>2 or
            abs(actual_height-bounds["height"])>2):
        raise ValueError("browser screenshot cropped below the viewport")
    (output / file).write_bytes(data)
    return {
        "activityId":activity_id,"locale":locale,"viewportWidth":width,
        "file":file,"bytes":len(data),
        "sha256":hashlib.sha256(data).hexdigest(),
        "imageWidth":actual_width,"imageHeight":actual_height,
        "expectedFullFigureWidth":round(bounds["width"],2),
        "expectedFullFigureHeight":round(bounds["height"],2),
        "completeFigureCapture":True,
        "reviewStatus":"unreviewed",
    }


def audit_browser(root: Path, package: Path, *, evidence_root: Path | None = None) -> dict:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import Select, WebDriverWait

    data = json.loads(package.read_text(encoding="utf-8"))
    visual_specs = {item["id"]:item["visualSpec"] for item in data.get("activities", [])
                    if item.get("visualSpec")}
    ids = list(visual_specs)
    problems = []
    checks = 0
    keyboard_checks = 0
    mcq_ids = {item["id"] for item in data.get("activities", []) if item.get("type") == "mcq"}
    frames = []
    if evidence_root is not None:
        evidence_root = evidence_root.resolve()
        if evidence_root.is_relative_to(root.resolve()) or evidence_root.is_relative_to(package.parent.resolve()):
            raise ValueError("QA evidence must not overwrite repository or installed teaching assets")
        evidence_root.mkdir(parents=True, exist_ok=False)
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
                                    const spec = arguments[0] || {};
                                    const figure = document.querySelector('figure.physics-visual');
                                    const card = figure?.closest('.card');
                                    const svg = figure?.querySelector('svg');
                                    const labelNodes = [...(figure?.querySelectorAll(
                                      'text.physics-visual__vector-label, text.physics-visual__entity-label, text.physics-visual__energy-label'
                                    ) || [])];
                                    const boxes = labelNodes.map(n => n.getBBox());
                                    const labelCollision = boxes.some((a, i) => boxes.some((b, j) =>
                                      j > i && a.x < b.x + b.width - 2
                                      && b.x < a.x + a.width - 2
                                      && a.y < b.y + b.height - 2
                                      && b.y < a.y + a.height - 2));
                                    const svgRect = svg?.getBoundingClientRect();
                                    const allText = [...(svg?.querySelectorAll('text') || [])];
                                    const textInside = allText.every((n) => {
                                      const r = n.getBoundingClientRect();
                                      return r.width > 0 && r.height > 0 &&
                                        r.left >= svgRect.left - 2 &&
                                        r.right <= svgRect.right + 2 &&
                                        r.top >= svgRect.top - 2 &&
                                        r.bottom <= svgRect.bottom + 2;
                                    });
                                    const vectorsMatch = (spec.vectors || []).every(v => {
                                      const line = [...(svg?.querySelectorAll('line[data-semantic-id]') || [])]
                                        .find(n => n.getAttribute('data-semantic-id') === v.id);
                                      if (!line) return false;
                                      const dx = Number(line.getAttribute('x2')) -
                                                 Number(line.getAttribute('x1'));
                                      if (v.direction === 'right') return dx > 0;
                                      if (v.direction === 'left') return dx < 0;
                                      return true;
                                    });
                                    const energyLabels = [...(svg?.querySelectorAll(
                                      '.physics-visual__energy-label') || [])];
                                    const energyBaseline = svg?.querySelector(
                                      '.physics-visual__energy-baseline');
                                    const captionClearOfBaseline = !energyBaseline ||
                                      energyLabels.every(n =>
                                        n.getBBox().y >
                                        Number(energyBaseline.getAttribute('y1')) + 4);
                                    const energies = (spec.entities || [])
                                      .filter(x => x.kind === 'energy-component');
                                    const tracks = [...(svg?.querySelectorAll(
                                      '.physics-visual__energy-track') || [])];
                                    const energyBarsMatch = energies.every((item, i) => {
                                      const bar = [...(svg?.querySelectorAll(
                                        'rect[data-semantic-id]') || [])]
                                        .find(n => n.getAttribute('data-semantic-id') === item.id);
                                      const track = tracks[i];
                                      if (!bar || !track) return false;
                                      const fraction = Number(bar.getAttribute('height')) /
                                                       Number(track.getAttribute('height'));
                                      return Math.abs(fraction - Number(
                                        item.properties?.relativeAmount)) < 0.0001;
                                    });
                                    return {
                                      fig: !!figure,
                                      textInside: textInside,
                                      vectorsMatch: vectorsMatch,
                                      energyBarsMatch: energyBarsMatch,
                                      captionClearOfBaseline: captionClearOfBaseline,
                                      energyTopY: energyLabels.map(n=>n.getBBox().y),
                                      energyBaselineY: energyBaseline ?
                                        Number(energyBaseline.getAttribute('y1')) : null,
                                      energyLabelCount: svg?.querySelectorAll(
                                        '.physics-visual__energy-label').length || 0,
                                      phaseCaption: svg?.querySelector(
                                        '.physics-visual__phase')?.textContent || '',
                                      velocityLabelCollision: labelCollision,
                                      arrowLabelCount: figure?.querySelectorAll(
                                        'text.physics-visual__vector-label').length || 0,
                                      svg: !!svg,
                                      desc: figure?.getAttribute('aria-label') || '',
                                      template: figure?.getAttribute('data-template') || '',
                                      semanticCount: figure?.querySelectorAll('[data-semantic-id]').length || 0,
                                      choices: !!card?.querySelector('.choices'),
                                      overflow: figure ? figure.scrollWidth > figure.clientWidth + 2 : false
                                    };
                                """, visual_specs[activity_id])
                                checks += 1
                                if not status["svg"] or not status["desc"] or status["semanticCount"] < 1:
                                    raise ValueError("missing SVG, accessible label, or semantic nodes")
                                if status["overflow"]:
                                    raise ValueError("visual viewport horizontal overflow")
                                if status["velocityLabelCollision"]:
                                    raise ValueError("SVG entity/velocity labels overlap in browser")
                                if not status["choices"]:
                                    raise ValueError("visual activity lost response controls")
                                if not status["textInside"]:
                                    raise ValueError("SVG text lies outside the visible diagram")
                                if not status["vectorsMatch"]:
                                    raise ValueError("rendered velocity arrows contradict the supplied directions")
                                if not status["energyBarsMatch"]:
                                    raise ValueError("rendered energy fractions contradict visualSpec")
                                if not status["captionClearOfBaseline"]:
                                    raise ValueError("energy label crosses baseline: " +
                                        str(status["energyTopY"]) + "/" +
                                        str(status["energyBaselineY"]))
                                if status["template"] == "state.energy_bar" and status["energyLabelCount"] < 2:
                                    raise ValueError("energy labels missing from SVG")
                                phase=visual_specs[activity_id].get("semanticParameters",{}).get("phase")
                                if phase == "before":
                                    captions={"en":"Before","ms":"Sebelum pelanggaran",
                                              "zh":"\u78b0\u649e\u524d"}
                                    if status["phaseCaption"]!=captions[locale]:
                                        raise ValueError("collision phase is not localized")
                                if evidence_root is not None:
                                    figure = driver.find_element(By.CSS_SELECTOR, "figure.physics-visual")
                                    frames.append(capture_review_frame(
                                        driver, figure, evidence_root, activity_id, locale, width, checks,
                                    ))
                                if activity_id in mcq_ids:
                                    choice = driver.find_element(By.CSS_SELECTOR, ".choices button")
                                    choice.send_keys(Keys.ENTER)
                                    WebDriverWait(driver, 4).until(
                                        lambda d: len(d.find_elements(
                                            By.CSS_SELECTOR, ".choices button[aria-pressed='true']"
                                        )) > 0
                                    )
                                    if not driver.find_element(By.ID, "check").is_enabled():
                                        raise ValueError("keyboard-selected MCQ does not enable check answer")
                                    if not driver.execute_script(
                                        "return document.activeElement?.classList.contains('choice') "
                                        "&& document.activeElement?.getAttribute('aria-pressed') === 'true';"
                                    ):
                                        raise ValueError("MCQ keyboard activation loses answer-button focus")
                                    keyboard_checks += 1
                            except Exception as exc:
                                problems.append({
                                    "activityId": activity_id, "locale": locale,
                                    "viewportWidth": width, "reason": str(exc)[:300],
                                })
            finally:
                driver.quit()
    if evidence_root is not None:
        evidence = {
            "packageSha256": hashlib.sha256(package.read_bytes()).hexdigest(),
            "browserSmokeOutcome": ("fail" if problems else "browser_dom_smoke_pass"),
            "visualActivityCount": len(ids),
            "responsiveChecks": checks,
            "keyboardSelectionChecks": keyboard_checks,
            "issues": problems,
            "screenshots": frames,
            "pixelQualityReviewed": False,
            "academicAccuracyReviewed": False,
            "approval": "pending_independent_review",
        }
        (evidence_root / "review-manifest.json").write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return {
        "keyboardSelectionChecks": keyboard_checks,
        "screenshotsCaptured": len(frames),
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
    parser.add_argument("--evidence-root", type=Path, help="New private directory for unreviewed visual PNGs")
    opts = parser.parse_args()
    try:
        report = audit_browser(
            opts.repo_root.resolve(), opts.package.resolve(),
            evidence_root=opts.evidence_root,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["outcome"] == "browser_dom_smoke_pass" else 1
    except Exception as exc:
        print(json.dumps({"outcome": "fail", "issues": [str(exc)[:500]], "publicationAuthorized": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

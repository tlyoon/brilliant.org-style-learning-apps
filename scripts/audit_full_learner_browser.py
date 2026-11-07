"""One-shot local headless learner audit of an existing private candidate package.

No PDF, model request, external browsing, student data or publication. The
report contains only exact package hashes and sanitized browser observations.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import traceback
import re
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_generator.validation.learner_coverage_gate import audit_full_learner_coverage
from scripts.audit_browser_visual import local_server, stage_bundle


def _assert(condition: bool, category: str) -> None:
    if not condition:
        raise ValueError(category)


def _safe_failure_origin(exc: Exception) -> dict[str, str]:
    """Keep a traceback's code identity without paths, values or source text."""
    frames = traceback.extract_tb(exc.__traceback__)
    if not frames:
        return {"originModule": "unknown", "originFunction": "unknown"}
    last = frames[-1]
    module = Path(last.filename).name
    name = last.name
    if not (module.endswith(".py") and re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", module)):
        module = "unknown"
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,79}", name):
        name = "unknown"
    return {"originModule": module, "originFunction": name}


def _localized(value: object, lang: str) -> str:
    if isinstance(value, dict):
        return str(value.get(lang, "") or "").strip()
    return str(value or "").strip()


def _select_fresh_locale(driver, origin: str, activity_id: str, lang: str) -> None:
    """Reload before every locale check; selection state must not bleed across."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import Select, WebDriverWait

    driver.get(origin + "/index.html?" + urlencode({"activity": activity_id}))
    # Package fetch sets the select disabled until load finishes. Selenium
    # raises NotImplementedError if Select is asked to choose a disabled
    # option. Wait for BOTH the real question and enabled selector, rather
    # than racing the asynchronous package fetch after navigation.
    WebDriverWait(driver, 8).until(
        lambda d: d.find_element(By.ID, "locale").is_enabled()
        and bool(d.find_elements(By.CSS_SELECTOR, "#app h1.question"))
    )
    Select(driver.find_element(By.ID, "locale")).select_by_value(lang)


def _exercise(driver, activity: dict, lang: str) -> None:
    """Real keyboard interactions on the rendered, re-created DOM controls."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys

    hint = driver.find_element(By.ID, "hint")
    hint.send_keys(Keys.ENTER)
    _assert(bool(driver.find_elements(By.CSS_SELECTOR, "#app .feedback")),
            "HINT_NOT_RENDERED")
    expected = _localized((activity.get("hints") or [{}])[0], lang)
    _assert(bool(expected) and expected in driver.find_element(
        By.CSS_SELECTOR, "#app .feedback").text, "LOCALIZED_HINT_MISMATCH")

    mode = activity.get("interactionMode")
    if activity.get("type") == "mcq" or mode == "selection":
        button = driver.find_element(By.CSS_SELECTOR, "#app .choices button.choice")
        button.send_keys(Keys.ENTER)
        _assert(bool(driver.find_elements(
            By.CSS_SELECTOR, "#app .choices button[aria-pressed='true']")),
            "CHOICE_KEYBOARD_ACTIVATION_FAILED")
    elif mode in {"classification", "matching"}:
        items = activity.get("interaction", {}).get("items", [])
        for i in range(len(items)):
            groups = driver.find_elements(By.CSS_SELECTOR, "#app .interaction-group")
            _assert(len(groups) == len(items), "PLACEMENT_GROUPS_MISSING")
            buttons = groups[i].find_elements(By.CSS_SELECTOR, "button.target-choice")
            _assert(bool(buttons), "PLACEMENT_TARGET_MISSING")
            buttons[0].send_keys(Keys.ENTER)
        _assert(len(driver.find_elements(
            By.CSS_SELECTOR, "#app .target-choice[aria-pressed='true']"
        )) == len(items), "PLACEMENT_KEYBOARD_ACTIVATION_FAILED")
    elif mode == "ordering":
        before = [n.get_attribute("data-item-id") for n in driver.find_elements(
            By.CSS_SELECTOR, "#app .order-row")]
        buttons = driver.find_elements(
            By.CSS_SELECTOR, "#app .order-control[data-delta='1']")
        usable = [b for b in buttons if b.is_enabled()]
        _assert(bool(usable), "ORDERING_CONTROL_MISSING")
        usable[0].send_keys(Keys.ENTER)
        after = [n.get_attribute("data-item-id") for n in driver.find_elements(
            By.CSS_SELECTOR, "#app .order-row")]
        _assert(before != after, "ORDERING_KEYBOARD_ACTIVATION_FAILED")
    else:
        raise ValueError("UNKNOWN_INTERACTION_MODE")

    check = driver.find_element(By.ID, "check")
    _assert(check.is_enabled(), "ANSWER_NOT_COMPLETE")
    check.send_keys(Keys.ENTER)
    _assert(bool(driver.find_elements(
        By.CSS_SELECTOR, "#app .feedback[role='status']")),
        "ANSWER_FEEDBACK_NOT_RENDERED")


def audit_existing_candidate(
    package_path: Path, output_root: Path, *, max_errors: int = 8,
) -> dict:
    """Run at most one new isolated browser audit for this exact package hash."""
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait

    _assert(package_path.is_file() and not package_path.is_symlink(),
            "PACKAGE_NOT_REGULAR_FILE")
    raw = package_path.read_bytes()
    package = json.loads(raw.decode("utf-8"))
    activities = package.get("activities") if isinstance(package, dict) else None
    _assert(isinstance(activities, list) and bool(activities),
            "EMPTY_OR_INVALID_ACTIVITY_ROSTER")
    _assert(max_errors >= 1 and max_errors <= 20, "INVALID_ERROR_BOUND")
    digest = sha256(raw).hexdigest()
    audit_script_sha = sha256(Path(__file__).read_bytes()).hexdigest()
    player_sha = sha256((ROOT / "app" / "app.js").read_bytes()).hexdigest()
    _assert(not output_root.is_symlink(), "LINKED_PRIVATE_OUTPUT_ROOT")
    output_root = output_root.resolve(strict=True)
    _assert(output_root.is_dir(), "INVALID_PRIVATE_OUTPUT_ROOT")
    _assert(not output_root.is_relative_to(ROOT.resolve()) and
            not output_root.is_relative_to(package_path.parent.resolve()),
            "UNSAFE_OUTPUT_ROOT")
    destination = output_root / ("learner-browser-" + digest[:16])
    destination.mkdir(exist_ok=False)
    (destination / "started.json").write_text(json.dumps({
        "packageSha256": digest, "auditScriptSha256": audit_script_sha,
        "learnerPlayerSha256": player_sha,
        "mode": "ONE_SHOT_OFFLINE_LOCALHOST",
        "modelCallsAllowed": False, "pdfReadsAllowed": False,
        "publicationAuthorized": False,
    }, sort_keys=True) + "\n", encoding="utf-8")

    evidence = {"packageSha256": digest, "auditScriptSha256": audit_script_sha,
                "learnerPlayerSha256": player_sha,
                "publicationAuthorized": False, "checks": []}
    errors: list[dict] = []
    visual_count = sum(bool(a.get("visualSpec")) for a in activities)
    with tempfile.TemporaryDirectory(prefix="bosla-audit-", dir=output_root) as temp:
        site = Path(temp) / "site"
        site.mkdir()
        stage_bundle(ROOT, package_path, site)
        opts = webdriver.ChromeOptions()
        for option in ("--headless=new", "--disable-background-networking",
                       "--disable-extensions", "--disable-sync",
                       "--no-first-run", "--no-default-browser-check"):
            opts.add_argument(option)
        opts.add_argument("--user-data-dir=" + str(Path(temp) / "chrome-profile"))
        driver = webdriver.Chrome(options=opts)
        driver.set_page_load_timeout(15)
        try:
            with local_server(site) as origin:
                for width, height in ((390, 844), (1280, 800)):
                    driver.set_window_size(width, height)
                    for idx, activity in enumerate(activities):
                        if len(errors) >= max_errors:
                            break
                        # A new document per locale prevents a previously
                        # chosen answer being toggled off on language change.
                        # This is necessary for selection-mode activities:
                        # the product intentionally retains response state.
                        for lang in ("en", "ms", "zh"):
                            row = {
                                "activityId": activity["id"], "locale": lang,
                                "viewportWidth": width, "rendered": False,
                                "responsive": False, "keyboardOperable": False,
                                "answerInteractionExercised": False,
                            }
                            category = "UNKNOWN_BROWSER_FAILURE"
                            phase = "navigate_locale"
                            try:
                                _select_fresh_locale(driver, origin, activity["id"], lang)
                                phase = "wait_question"
                                WebDriverWait(driver, 6).until(
                                    lambda d: bool(d.find_elements(
                                        By.CSS_SELECTOR, "#app h1.question")))
                                phase = "read_question"
                                title = driver.find_element(
                                    By.CSS_SELECTOR, "#app h1.question").text.strip()
                                _assert(title == _localized(activity["prompt"], lang),
                                        "LOCALIZED_PROMPT_MISMATCH")
                                row["rendered"] = True
                                phase = "check_layout"
                                _assert(bool(driver.execute_script(
                                    "return document.documentElement.scrollWidth <= "
                                    "window.innerWidth + 2 && "
                                    "document.body.scrollWidth <= window.innerWidth + 2;"
                                )), "HORIZONTAL_OVERFLOW")
                                row["responsive"] = True
                                phase = "exercise"
                                _exercise(driver, activity, lang)
                                row["keyboardOperable"] = True
                                row["answerInteractionExercised"] = True
                                phase = "screenshot"
                                screenshot = driver.get_screenshot_as_png()
                                filename = f"{idx + 1:02d}-{lang}-{width}.png"
                                (destination / filename).write_bytes(screenshot)
                                row["screenshotSha256"] = sha256(screenshot).hexdigest()
                                row["screenshotFile"] = filename
                            except Exception as exc:
                                category = (
                                    str(exc) if isinstance(exc, ValueError)
                                    and str(exc).isupper() and len(str(exc)) <= 70
                                    else type(exc).__name__.upper()
                                )
                                errors.append({
                                    "activityIndex": idx + 1,
                                    "locale": lang, "viewportWidth": width,
                                    "category": category, "failurePhase": phase,
                                    **_safe_failure_origin(exc),
                                })
                            evidence["checks"].append(row)
                            if len(errors) >= max_errors:
                                break
                    if len(errors) >= max_errors:
                        break
        finally:
            driver.quit()
    coverage = audit_full_learner_coverage(package, evidence)
    report = {
        "status": "COMPLETE_BROWSER_COVERAGE_UNDER_INDEPENDENT_REVIEW"
                  if coverage["status"] == "COMPLETE_COVERAGE_METADATA_UNVERIFIED"
                  else "INCOMPLETE_BROWSER_COVERAGE",
        "packageSha256": digest,
        "auditScriptSha256": audit_script_sha,
        "learnerPlayerSha256": player_sha,
        "activityCount": len(activities),
        "visualSpecActivities": visual_count,
        "expectedBrowserChecks": coverage["expectedCheckCount"],
        "observedBrowserChecks": coverage["observedCheckCount"],
        "failedBrowserChecks": coverage["failedCheckCount"],
        "missingBrowserChecks": coverage["missingCheckCount"],
        "screenshotsCaptured": sum("screenshotSha256" in x for x in evidence["checks"]),
        "errors": errors,
        "browserExecutionWasLocal": True,
        "independentBrowserReviewComplete": False,
        "visualSemanticsVerified": False,
        "scientificAndTrilingualMeaningVerified": False,
        "technicalAcceptanceGranted": False,
        "academicAcceptanceGranted": False,
        "publicationAuthorized": False,
    }
    (destination / "learner-receipt.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    (destination / "summary.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--max-errors", type=int, default=8)
    args = parser.parse_args(argv)
    report = audit_existing_candidate(
        args.package, args.output_root, max_errors=args.max_errors)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"].startswith("COMPLETE_") else 2


if __name__ == "__main__":
    raise SystemExit(main())

"""BSA240: fail-closed real Chrome accessibility tree probe for public draft bundles.

Runs on loopback only, against immutable source-pinned review checkout or
source-free synthetic CI fixtures. Checks AX names, roles and HTML locale tags.
It is not a screen-reader user test, WCAG certification or release permission.
"""
from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

_ROLES = frozenset({
    "button", "combobox", "checkbox", "radio", "slider", "link",
    "textbox", "menuitem", "listbox", "switch",
})
_LOCALES = ("en", "ms", "zh")


class _LoopbackHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        return

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()


def inspect_control_names(raw: dict, *, page: str, locale: str) -> dict:
    """Analyze Chrome's real AX node list; fail if any active control is unnamed."""
    nodes = raw.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("BSA240_AX_TREE_EMPTY_OR_INVALID")
    controls = 0
    buttons = 0
    unnamed = []
    for node in nodes:
        if not isinstance(node, dict) or node.get("ignored") is True:
            continue
        role = node.get("role", {})
        kind = role.get("value", "") if isinstance(role, dict) else ""
        if str(kind).lower() not in _ROLES:
            continue
        controls += 1
        buttons += kind.lower() == "button"
        title = node.get("name", {})
        name = title.get("value", "") if isinstance(title, dict) else ""
        if not isinstance(name, str) or not name.strip():
            unnamed.append(str(kind))
    if unnamed:
        raise ValueError("BSA240_UNNAMED_ACCESSIBLE_CONTROL:" + ",".join(unnamed))
    if controls < 2 or buttons < 1:
        raise ValueError("BSA240_MISSING_INTERACTIVE_AX_CONTROLS")
    return {"page": page, "locale": locale, "controls": controls,
            "namedControls": controls, "unnamedControls": 0, "buttons": buttons}


def audit_real_chrome_accessibility_tree(checkout: Path, pages: tuple[tuple[str, str], ...]) -> dict:
    """Open true content in headless Chrome; no network beyond local loopback.

    pages holds (relative HTML page, relative package path). Blank package
    path means page loads its own signed public package normally.
    """
    if not pages:
        raise ValueError("BSA240_NO_PAGES")
    base = checkout.resolve(strict=True)
    for page, package in pages:
        if page.startswith("/") or ".." in Path(page).parts or not page.endswith(".html"):
            raise ValueError("BSA240_INVALID_PAGE_PATH")
        entry = base / page
        if (not entry.is_file() or entry.is_symlink() or
                not entry.resolve().is_relative_to(base)):
            raise ValueError("BSA240_INVALID_PAGE_FILE")
        if package and (package.startswith("/") or "://" in package or
                        package.startswith("javascript:")):
            raise ValueError("BSA240_UNSAFE_PACKAGE_PATH")
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import Select, WebDriverWait

    server = ThreadingHTTPServer(("127.0.0.1", 0),
                                 partial(_LoopbackHandler, directory=str(base)))
    server.daemon_threads = True
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    chrome = webdriver.ChromeOptions()
    for flag in ("--headless=new", "--no-first-run", "--no-default-browser-check",
                 "--disable-background-networking", "--disable-sync",
                 "--disable-extensions", "--disable-gpu", "--no-sandbox",
                 "--disable-dev-shm-usage", "--proxy-server=direct://",
                 "--proxy-bypass-list=*", "--window-size=1200,900"):
        chrome.add_argument(flag)
    driver = None
    reports = []
    try:
        driver = webdriver.Chrome(options=chrome)
        driver.set_page_load_timeout(35)
        driver.execute_cdp_cmd("Accessibility.enable", {})
        for page, package in pages:
            driver.get(f"http://127.0.0.1:{server.server_port}/{page}")
            if package:
                driver.execute_script("void window.loadPackage(arguments[0]);", package)
            WebDriverWait(driver, 35).until(
                lambda d: (len(d.find_element(By.ID, "app").text) > 100 and
                           d.find_element(By.ID, "locale").is_enabled() and
                           len(d.find_elements(By.CSS_SELECTOR, "#app button")) > 0))
            for locale in _LOCALES:
                Select(driver.find_element(By.ID, "locale")).select_by_value(locale)
                selected = driver.execute_script(
                    "return {lang:document.documentElement.lang,"
                    "selected:document.querySelector('#locale').value,"
                    "visible:document.querySelector('#app').textContent.length}")
                if (selected["lang"] != locale or selected["selected"] != locale or
                        selected["visible"] < 100):
                    raise ValueError("BSA240_DOCUMENT_LANGUAGE_OR_RENDER_MISMATCH")
                data = driver.execute_cdp_cmd("Accessibility.getFullAXTree", {})
                reports.append(inspect_control_names(data, page=page, locale=locale))
    finally:
        if driver is not None:
            driver.quit()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    if len(reports) != len(pages) * len(_LOCALES):
        raise ValueError("BSA240_INCOMPLETE_REAL_AX_CHECKS")
    return {
        "status": "BSA240_REAL_AX_CONTROL_NAMES_VERIFIED_NO_WCAG_CLAIM",
        "pagesAudited": len(pages),
        "localeAccessibilityTreeChecks": len(reports),
        "minimumNamedControls": min(item["namedControls"] for item in reports),
        "unnamedControls": 0,
        "documentLanguageMatches": len(reports),
        "fullScreenReaderWCAGCertification": False,
        "publicationAuthorized": False,
    }

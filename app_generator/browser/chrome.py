"""Open independent regular Chrome on Gemini before connecting automation."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen

from app_generator.config import GeneratorConfig
from app_generator.errors import BrowserError

GEMINI_HOME = "https://gemini.google.com/"


def chrome_executable() -> str:
    for name in ("chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        executable = shutil.which(name)
        if executable:
            return executable
    for variable in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        root = os.environ.get(variable)
        if root:
            candidate = Path(root) / "Google" / "Chrome" / "Application" / "chrome.exe"
            if candidate.is_file():
                return str(candidate)
    candidate = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if candidate.is_file():
        return str(candidate)
    raise BrowserError("Google Chrome was not found. Install Chrome before opening Gemini.")


def ready_debug_address(profile: Path) -> str:
    """Read only Chrome's port metadata, never profile cookies or credentials."""
    lines = (profile / "DevToolsActivePort").read_text(encoding="utf-8").splitlines()
    port = int(lines[0])
    browser_path = lines[1]
    if not 1 <= port <= 65535 or not browser_path.startswith("/devtools/browser/"):
        raise ValueError("Invalid Chrome debug metadata")
    address = f"127.0.0.1:{port}"
    with urlopen(f"http://{address}/json/version", timeout=1) as response:
        version = json.load(response)
    websocket = urlparse(version.get("webSocketDebuggerUrl", ""))
    if websocket.hostname not in {"127.0.0.1", "localhost"} or websocket.port != port or websocket.path != browser_path:
        raise ValueError("Chrome debug endpoint does not match the independent profile")
    with urlopen(f"http://{address}/json/list", timeout=1) as response:
        targets = json.load(response)
    if not any(target.get("type") == "page" for target in targets):
        raise ValueError("Independent Chrome has no page yet")
    return address


@dataclass
class ChromeSession:
    config: GeneratorConfig
    driver: Any | None = None
    _manual_process: Any | None = None
    _launched_address: str = ""

    def open_window(self) -> str:
        """Open ordinary Chrome for sign-in before any debug connection exists."""
        if self.config.browser_mode == "attach":
            return self.config.debugger_address
        if self._manual_process is not None and self._manual_process.poll() is None:
            return ""
        executable = chrome_executable()
        # Keep Gemini sign-in isolated from personal and legacy generator profiles.
        profile = self.config.chrome_profile_dir / "gemini-browser"
        profile.mkdir(parents=True, exist_ok=True)
        try:
            self._manual_process = subprocess.Popen(
                [executable, f"--user-data-dir={profile}", "--new-window", "--start-maximized",
                 "--no-first-run", "--no-default-browser-check", "--disable-notifications",
                 "--disable-background-mode", getattr(self.config, "gem_url", "") or GEMINI_HOME],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except OSError as exc:
            raise BrowserError("Independent Chrome could not be launched; check the Chrome installation.") from exc
        return ""

    def wait_for_manual_sign_in(self) -> None:
        """Let Google sign-in finish in regular Chrome before WebDriver attaches."""

        if self.config.browser_mode != "controlled":
            return
        login_name = getattr(self.config, "login_name", "the configured Google account")
        gem_url = getattr(self.config, "gem_url", "") or GEMINI_HOME
        edit_url = getattr(self.config, "gem_edit_url", "") or gem_url
        print(
            "Chrome is open on the configured Gemini Gem. If Google asks you to sign in, "
            f"use {login_name}. Finish sign-in, close that Chrome window, then return here and press Enter. "
            f"Gem: {gem_url} | Gem editor: {edit_url}",
            flush=True,
        )
        try:
            input("Press Enter after Gemini has loaded and the sign-in Chrome window is closed: ")
        except EOFError as exc:
            raise BrowserError(
                "Interactive Google sign-in is required before Selenium can connect. "
                "Run app generation from an interactive terminal and retry."
            ) from exc
        deadline = time.monotonic() + 15
        while self._manual_process is not None and self._manual_process.poll() is None:
            if time.monotonic() >= deadline:
                raise BrowserError(
                    "The sign-in Chrome window is still running. Close that dedicated window, "
                    "then retry so Selenium can reopen the profile safely."
                )
            time.sleep(0.25)
        self._manual_process = None

    def _open_automation_window(self) -> str:
        if self._launched_address:
            return self._launched_address
        executable = chrome_executable()
        profile = self.config.chrome_profile_dir / "gemini-browser"
        profile.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.Popen(
                [executable, f"--user-data-dir={profile}", "--remote-debugging-port=0",
                 "--remote-debugging-address=127.0.0.1", "--new-window", "--start-maximized",
                 "--no-first-run", "--no-default-browser-check", "--disable-notifications",
                 "--disable-background-mode", getattr(self.config, "gem_url", "") or GEMINI_HOME],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except OSError as exc:
            raise BrowserError("Independent Chrome could not be relaunched for automation.") from exc
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            try:
                self._launched_address = ready_debug_address(profile)
                return self._launched_address
            except (OSError, ValueError, IndexError, KeyError, TypeError):
                time.sleep(0.25)
        raise BrowserError(
            "Signed-in Chrome could not be reopened for automation within 15 seconds. "
            "Confirm that the sign-in window was closed before pressing Enter."
        )

    def start(self) -> Any:
        address = (
            self.config.debugger_address
            if self.config.browser_mode == "attach"
            else self._open_automation_window()
        )
        try:
            from selenium import webdriver
        except ImportError as exc:
            raise BrowserError("Selenium is not installed. Run: python -m pip install -r requirements-generator.txt") from exc
        options = webdriver.ChromeOptions()
        options.debugger_address = address
        try:
            self.driver = webdriver.Chrome(options=options)
        except Exception as exc:
            mode = "independent Gemini window" if self.config.browser_mode == "controlled" else "debugger address"
            raise BrowserError(f"Chrome automation could not connect to the configured {mode}.") from exc
        return self.driver

    def close(self) -> None:
        if self.driver is not None:
            try:
                if self.config.browser_mode == "controlled":
                    try:
                        self.driver.execute_cdp_cmd("Browser.close", {})
                    except Exception:
                        # Chrome may already have been closed by the operator.
                        pass
                    self.driver.quit()
                elif getattr(self.driver, "service", None) is not None:
                    self.driver.service.stop()
            finally:
                self.driver = None
                self._launched_address = ""

    def __enter__(self) -> Any:
        return self.start()

    def __exit__(self, *_: object) -> None:
        self.close()

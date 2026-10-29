"""Two academically separate fresh Gemini conversations in one verified login.

Uses an existing authorized Chrome profile WITHOUT copying credentials or
reusing authoring conversation content. These sessions are conversation-
independent, not independent provider accounts or independent models.
"""
from __future__ import annotations

from dataclasses import replace
import os
import subprocess
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse
from uuid import uuid4

from app_generator.browser.account import GoogleAccountVerifier
from app_generator.browser.chrome import ChromeSession
from app_generator.config import GeneratorConfig
from app_generator.gemini.client import GeminiClient
from app_generator.validation.autonomous_ai_review import ReviewerSession

NEUTRAL_URL = "https://gemini.google.com/app"
ROLES = ("physics", "semantics")


def existing_profile_in_use(profile: Path) -> bool:
    """Fail closed if an independently owned Chrome has the original profile.

    The authorized project runs on Windows. Inspect only Chrome process
    command-line profile paths; never read browser storage, cookies or tabs.
    """
    if os.name != "nt":
        raise ValueError("shared authenticated Chrome session is Windows-only")
    script = (
        "$p=$env:BRILLIANT_REVIEW_PROFILE_CHECK;"
        "$hits=@(Get-CimInstance Win32_Process -Filter 'Name=\"chrome.exe\"' |"
        "Where-Object { $_.CommandLine -and "
        "$_.CommandLine.Contains('--user-data-dir=') -and "
        "$_.CommandLine.Contains($p) });"
        "if($hits.Count -gt 0){'BUSY'}else{'FREE'}"
    )
    environment={**os.environ,"BRILLIANT_REVIEW_PROFILE_CHECK":str(profile.resolve())}
    try:
        run=subprocess.run(
            ["powershell.exe","-NoProfile","-NonInteractive","-Command",script],
            capture_output=True,text=True,timeout=15,env=environment,
        )
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise ValueError("cannot verify exclusive ownership of original Chrome profile") from exc
    state=run.stdout.strip()
    if run.returncode or state not in ("FREE","BUSY"):
        raise ValueError("original Chrome profile ownership check did not finish reliably")
    return state=="BUSY"


class BoundFreshConversation:
    """Bind each role to the distinct tab it created, never an author tab."""

    def __init__(self, driver: Any, client: Any, handle: str,
                 protected_handles: set[str]):
        if not handle or handle in protected_handles:
            raise ValueError("reviewer handle must be a new owned browser tab")
        self.driver = driver
        self.client = client
        self.handle = handle
        self.protected_handles = frozenset(protected_handles)

    def ask(self, prompt: str, *, stage: str | None = None) -> str:
        if not stage or not stage.startswith("academic-"):
            raise ValueError("review tabs accept only academic review prompts")
        if self.handle not in self.driver.window_handles:
            raise ValueError("review browser tab no longer exists")
        if self.handle in self.protected_handles:
            raise ValueError("protected browser tab must not be used")
        self.driver.switch_to.window(self.handle)
        url = urlparse(self.driver.current_url)
        if url.scheme != "https" or url.netloc != "gemini.google.com":
            raise ValueError("review browser tab navigated outside Gemini")
        # No model-selection fallback that might resubmit after a
        # possibly accepted request.
        return self.client.conversation.ask(prompt)


class ExistingLoginReviewerFactory:
    """Single attached, already-authorized browser; independent fresh tabs.

    Caller must ensure the original authorized Chrome profile is not
    concurrently owned by another workflow. We never extract, duplicate,
    or inspect browser cookies, tokens, or prior chat contents.
    """

    def __init__(self, config: GeneratorConfig, source_pdf: Path, *,
                 chrome_factory: Callable[..., Any] = ChromeSession,
                 client_factory: Callable[..., Any] = GeminiClient,
                 account_verifier: Callable[..., Any] = GoogleAccountVerifier,
                 profile_busy: Callable[[Path], bool] = existing_profile_in_use):
        if config.browser_mode != "controlled" or config.llm_backend != "gemini_browser":
            raise ValueError("existing-login review requires controlled non-API Gemini browser")
        if not config.chrome_profile_dir.is_absolute():
            raise ValueError("authorized original browser profile must be absolute")
        if not config.chrome_profile_dir.is_dir():
            raise ValueError("authorized original browser profile does not exist")
        if config.chrome_profile_dir.resolve().is_relative_to(config.repo_root.resolve()):
            raise ValueError("browser profile cannot be inside Git checkout")
        if not source_pdf.is_file() or source_pdf.read_bytes()[:5] != b"%PDF-":
            raise ValueError("original authorized controlled source PDF required")
        self.config = replace(config, gem_url=NEUTRAL_URL, gem_edit_url=NEUTRAL_URL)
        self.pdf = source_pdf
        self.chrome_factory = chrome_factory
        self.client_factory = client_factory
        self.account_verifier = account_verifier
        self.profile_busy = profile_busy
        self.chrome: Any = None
        self.driver: Any = None
        self.protected: set[str] = set()
        self.owned: dict[str, str] = {}
        self.open_activity: str | None = None
        self._used_session_ids: set[str] = set()

    def open_pair(self, activity_id: str) -> tuple[ReviewerSession, ReviewerSession]:
        if not activity_id or self.open_activity is not None:
            raise ValueError("previous review must finish before next activity")
        self.close()
        if self.profile_busy(self.config.chrome_profile_dir/"gemini-browser"):
            raise ValueError("authorized authoring Chrome profile is currently in use by another process")
        self.chrome = self.chrome_factory(self.config)
        try:
            self.driver = self.chrome.start()
            # Preserve the original browser tabs BEFORE checking their URL.
            # Chrome session restoration may select an unrelated starting
            # page even though the explicit launch URL was neutral Gemini.
            # Never navigate, inspect private text, or close a restored tab.
            self.protected = set(self.driver.window_handles)
            if not self.protected:
                raise ValueError("owned browser missing protected starting tab")
            origin = urlparse(self.driver.current_url)
            if origin.scheme != "https" or origin.netloc != "gemini.google.com":
                # Open a NEW owned tab for noninteractive account verification.
                # Do not re-purpose any previous authoring or unrelated tab.
                self.driver.switch_to.new_window("tab")
                probe_handle = self.driver.current_window_handle
                if not probe_handle or probe_handle in self.protected:
                    raise ValueError("account-verification tab is not exclusively owned")
                self.owned["account-verification"] = probe_handle
                self.driver.get(NEUTRAL_URL)
                origin = urlparse(self.driver.current_url)
                if origin.scheme != "https" or origin.netloc != "gemini.google.com":
                    raise ValueError("fresh account-verification tab did not open Gemini")
            # Verify only the visible active Google account on a Gemini tab,
            # before attaching the controlled textbook to any conversation.
            self.account_verifier(self.driver, self.config.login_name, 12).verify()
            sessions = []
            for role in ROLES:
                self.driver.switch_to.new_window("tab")
                handle = self.driver.current_window_handle
                if handle in self.protected or handle in self.owned.values():
                    raise ValueError("review browser returned duplicate or protected tab")
                self.owned[role] = handle
                client = self.client_factory(self.driver, self.config)
                client.open_conversation_select_model_and_attach(self.pdf)
                if urlparse(self.driver.current_url).netloc != "gemini.google.com":
                    raise ValueError("new source conversation not at Gemini")
                if not handle == self.driver.current_window_handle:
                    raise ValueError("new conversation replaced review tab")
                session_id = uuid4().hex
                if session_id in self._used_session_ids:
                    raise ValueError("reviewer session id reused")
                self._used_session_ids.add(session_id)
                sessions.append(ReviewerSession(
                    "gemini-existing-login-"+role, session_id,
                    BoundFreshConversation(self.driver,client,handle,self.protected),
                ))
            if len({s.conversation.handle for s in sessions}) != 2:
                raise ValueError("two independent conversation tabs required")
            self.open_activity=activity_id
            return tuple(sessions)
        except Exception:
            self.close()
            raise

    def close(self) -> None:
        try:
            if self.driver is not None:
                for handle in list(self.owned.values()):
                    try:
                        if handle in self.driver.window_handles:
                            self.driver.switch_to.window(handle)
                            self.driver.close()
                    except Exception:
                        pass
        finally:
            self.owned.clear()
            self.protected.clear()
            self.open_activity=None
            if self.chrome is not None:
                try:
                    self.chrome.close()
                finally:
                    self.chrome=None
                    self.driver=None

    def __enter__(self) -> "ExistingLoginReviewerFactory":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

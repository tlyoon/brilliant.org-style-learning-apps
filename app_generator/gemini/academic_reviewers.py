"""Independent, no-API Selenium Gemini reviewers using distinct browser contexts.

The authoring client's mutable Gem, Chrome user-data directory and active
conversation must never be shared with academic reviewers. Each reviewer
opens its own new conversation and attaches the original controlled PDF.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from app_generator.browser.chrome import ChromeSession
from app_generator.config import GeneratorConfig
from app_generator.gemini.client import GeminiClient
from app_generator.validation.autonomous_ai_review import ReviewerSession


class ReviewerBrowser:
    """Owns only the Chrome automation process started for this role."""

    def __init__(self, role: str, config: GeneratorConfig, source_pdf: Path,
                 *, chrome_factory: Callable[..., Any] = ChromeSession,
                 client_factory: Callable[..., Any] = GeminiClient):
        if role not in ("physics", "semantics", "repair"):
            raise ValueError("unknown independent academic reviewer role")
        if config.browser_mode != "controlled":
            raise ValueError("academic reviewers require separate controlled Chrome profiles")
        source_pdf = source_pdf.resolve()
        if not source_pdf.is_file() or source_pdf.read_bytes()[:5] != b"%PDF-":
            raise ValueError("authorized local PDF required for independent academic reviewer")
        if not config.chrome_profile_dir.is_absolute():
            raise ValueError("Chrome profile must be an absolute controlled path")
        self.role = role
        self.config = replace(
            config, chrome_profile_dir=config.chrome_profile_dir / "academic-reviewers" / role
        )
        self.pdf = source_pdf
        self.chrome_factory = chrome_factory
        self.client_factory = client_factory
        self.chrome = None
        self.client = None

    def open(self) -> Any:
        if self.client is not None:
            raise ValueError("review browser already open")
        chrome = self.chrome_factory(self.config)
        self.chrome = chrome
        try:
            driver = chrome.start()
            client = self.client_factory(driver, self.config)
            # No Gem edit/synchronization: independence from the authoring
            # system prompt is necessary to avoid merely repeating its claims.
            client.open_conversation_select_model_and_attach(self.pdf)
            self.client = client
            return client
        except Exception:
            self.close()
            raise

    def close(self) -> None:
        if self.chrome is not None:
            try:
                self.chrome.close()
            finally:
                self.client = None
                self.chrome = None


class DirectGeminiReviewer:
    """Avoids GeminiClient model-fallback resubmission after an ambiguous send."""

    def __init__(self, client: Any):
        self.client = client

    def ask(self, prompt: str, *, stage: str | None = None) -> str:
        if not stage or not stage.startswith("academic-"):
            raise ValueError("reviewer cannot be used for generation or other stages")
        return self.client.conversation.ask(prompt)


class IndependentReviewerFactory:
    """Provision two verified distinct browser clients per activity.

    Start/close under a short-lived context. This class deliberately does
    not log in interactively or reuse the protected generator's Chrome
    session; if a dedicated profile is not authenticated it fails closed.
    """

    def __init__(self, config: GeneratorConfig, source_pdf: Path,
                 *, browser_factory: Callable[..., ReviewerBrowser] = ReviewerBrowser,
                 author_driver: Any = None):
        self.config = config
        self.source_pdf = source_pdf
        self.browser_factory = browser_factory
        self.author_driver = author_driver
        self._browsers: list[ReviewerBrowser] = []
        self._used_sessions: set[str] = set()

    def open_pair(self, activity_id: str) -> tuple[ReviewerSession, ReviewerSession]:
        if not isinstance(activity_id, str) or not activity_id:
            raise ValueError("activity id required")
        if self._browsers:
            raise ValueError("close prior reviewer pair before provisioning new one")
        browsers = []
        try:
            for role in ("physics", "semantics"):
                browser = self.browser_factory(role, self.config, self.source_pdf)
                browsers.append(browser)
                browser.open()
            clients = [b.client for b in browsers]
            if (clients[0] is clients[1] or
                getattr(clients[0], "driver", None) is getattr(clients[1], "driver", None) or
                any(getattr(c, "driver", None) is self.author_driver
                    for c in clients if self.author_driver is not None)):
                raise ValueError("academic reviewers cannot share driver or authoring browser")
            profiles=[str(b.config.chrome_profile_dir.resolve()) for b in browsers]
            if len(set(profiles)) != 2 or any(
                profile == str(self.config.chrome_profile_dir.resolve()) for profile in profiles
            ):
                raise ValueError("academic reviewer Chrome profile isolation failed")
            ids=[uuid4().hex for _ in browsers]
            if any(x in self._used_sessions for x in ids):
                raise ValueError("repeated academic reviewer session identity")
            self._used_sessions.update(ids)
            self._browsers = browsers
            return (
                ReviewerSession("gemini-physics",ids[0],DirectGeminiReviewer(clients[0])),
                ReviewerSession("gemini-semantics",ids[1],DirectGeminiReviewer(clients[1])),
            )
        except Exception:
            for b in reversed(browsers):
                b.close()
            raise

    def close(self) -> None:
        try:
            for b in reversed(self._browsers):
                b.close()
        finally:
            self._browsers = []

    def __enter__(self) -> "IndependentReviewerFactory":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

"""Generated-text-only V3 reviewer sessions using the historical owned Gemini login.

Reuses the successful source-free Gemini probe's profile-ownership, visible
account verification, fresh-tab redirect and isolation patterns. This is an
opt-in provider for *independently authorized* operations; creating/importing
it cannot grant or bypass any earlier external execution denial. No PDF, Gem
editor, credentials, model fallback, or author tabs enter reviewer prompts.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse
from uuid import uuid4

from app_generator.browser.account import GoogleAccountVerifier
from app_generator.browser.chrome import ChromeSession
from app_generator.gemini.conversation import GemConversationPage
from app_generator.gemini.existing_login_reviewers import (
    NEUTRAL_URL, existing_profile_in_use,
)
from app_generator.validation.autonomous_ai_review import ReviewerSession


def _on_neutral_gemini(driver: Any) -> bool:
    parsed = urlparse(driver.current_url)
    return parsed.scheme == "https" and parsed.netloc == "gemini.google.com"


class V3OwnedGeneratedConversation:
    """Only one newly owned, role-bound conversation accepts V3 prompts."""

    def __init__(self, driver: Any, page: Any, handle: str, protected: set[str]):
        if not handle or handle in protected:
            raise ValueError("V3_REVIEWER_MUST_OWN_NEW_TAB")
        self.driver, self.page, self.handle = driver, page, handle
        self.protected = frozenset(protected)

    def ask(self, prompt: str, *, stage: str | None = None) -> str:
        if stage != "academic-v3-autonomous" or not isinstance(prompt, str):
            raise ValueError("V3_GENERATED_REVIEW_ONLY")
        if self.handle not in self.driver.window_handles or self.handle in self.protected:
            raise ValueError("V3_REVIEW_TAB_OWNERSHIP_LOST")
        self.driver.switch_to.window(self.handle)
        if not _on_neutral_gemini(self.driver):
            raise ValueError("V3_REVIEW_TAB_LEFT_GEMINI")
        # One request, no fallback/resubmission. Existing V3 engine marks
        # ambiguous or uncaptured outcomes and refuses replay on restart.
        return self.page.ask(prompt)


class V3ExistingLoginSessions:
    """Provide two verified distinct source-free chats to the normal V3 engine.

    The caller must obtain separate platform authorization for the *exact*
    previously denied execution intent before setting external_operation_authorized.
    A local boolean is a fail-closed admission guard, NOT an authority grant.
    A browser session is opened only inside the already-approved execution.
    """

    def __init__(
        self, config: Any, *, external_operation_authorized: bool = False,
        generated_content_transfer_allowed: bool = False,
        chrome_factory: Callable[..., Any] = ChromeSession,
        verifier_factory: Callable[..., Any] = GoogleAccountVerifier,
        page_factory: Callable[..., Any] = GemConversationPage,
        profile_busy: Callable[[Path], bool] = existing_profile_in_use,
    ) -> None:
        self.config = config
        self.external_operation_authorized = external_operation_authorized
        self.generated_content_transfer_allowed = generated_content_transfer_allowed
        self.chrome_factory = chrome_factory
        self.verifier_factory = verifier_factory
        self.page_factory = page_factory
        self.profile_busy = profile_busy
        self.chrome = None
        self.driver = None
        self.protected: set[str] = set()
        self.owned: list[str] = []
        self.active_activity = None

    def open_pair(self, activity_id: str) -> tuple[ReviewerSession, ReviewerSession]:
        if self.external_operation_authorized is not True:
            raise ValueError("V3_EXTERNAL_AUTHORIZATION_REQUIRED")
        if self.generated_content_transfer_allowed is not True:
            raise ValueError("V3_GENERATED_CONTENT_MODEL_TRANSFER_NOT_ALLOWED")
        if not isinstance(activity_id, str) or not activity_id:
            raise ValueError("V3_REVIEW_ACTIVITY_REQUIRED")
        if self.chrome is not None or self.active_activity is not None:
            raise ValueError("V3_REVIEW_PROVIDER_ALREADY_ACTIVE")
        cfg = self.config
        if (cfg.browser_mode != "controlled" or cfg.llm_backend != "gemini_browser"
                or not cfg.chrome_profile_dir.is_absolute()):
            raise ValueError("V3_CONTROLLED_GEMINI_CONFIG_REQUIRED")
        profile = cfg.chrome_profile_dir / "gemini-browser"
        if (not profile.is_dir() or profile.resolve().is_relative_to(
                cfg.repo_root.resolve())):
            raise ValueError("V3_EXISTING_AUTHORIZED_PROFILE_REQUIRED")
        if self.profile_busy(profile):
            raise ValueError("V3_GEMINI_PROFILE_BUSY")
        # Reuse the neutral no-PDF launch; never synchronize a Gem prompt or
        # enter the old PDF-attaching ExistingLoginReviewerFactory.
        neutral = replace(cfg, gem_url=NEUTRAL_URL, gem_edit_url=NEUTRAL_URL)
        self.chrome = self.chrome_factory(neutral)
        try:
            self.driver = self.chrome.start()
            driver = self.driver
            self.protected = set(driver.window_handles)
            if not self.protected:
                raise ValueError("V3_NO_PROTECTED_ORIGINAL_TABS")
            if not _on_neutral_gemini(driver):
                # One bounded navigation recovery BEFORE any model submission.
                # Retain discarded owned tabs until cleanup; never touch author tabs.
                for _ in range(2):
                    self._create_owned_tab()
                    driver.get(NEUTRAL_URL)
                    if _on_neutral_gemini(driver):
                        break
                else:
                    raise ValueError("V3_GEMINI_NEUTRAL_NAVIGATION_FAILED")
            self.verifier_factory(driver, cfg.login_name, 12).verify()
            sessions: list[ReviewerSession] = []
            for role in ("physics", "semantics"):
                handle = self._create_owned_tab()
                page = self.page_factory(
                    driver, NEUTRAL_URL, cfg.ui_timeout_seconds,
                    cfg.response_timeout_seconds,
                )
                page.open_new()
                if not _on_neutral_gemini(driver):
                    raise ValueError("V3_REVIEW_TAB_LEFT_GEMINI")
                if driver.current_window_handle != handle:
                    raise ValueError("V3_REVIEW_TAB_OWNERSHIP_LOST")
                conversation = V3OwnedGeneratedConversation(
                    driver, page, handle, self.protected,
                )
                sessions.append(ReviewerSession(
                    "v3-gemini-" + role, uuid4().hex, conversation,
                ))
            if len({s.conversation.handle for s in sessions}) != 2:
                raise ValueError("V3_DISTINCT_REVIEW_CONTEXTS_REQUIRED")
            self.active_activity = activity_id
            return tuple(sessions)
        except BaseException:
            self.close()
            raise

    def _create_owned_tab(self) -> str:
        driver = self.driver
        driver.switch_to.new_window("tab")
        handle = driver.current_window_handle
        if not handle or handle in self.protected or handle in self.owned:
            raise ValueError("V3_REVIEWER_MUST_OWN_NEW_TAB")
        self.owned.append(handle)
        return handle

    def close(self) -> None:
        try:
            if self.driver is not None:
                for handle in reversed(self.owned):
                    try:
                        if handle in self.driver.window_handles:
                            self.driver.switch_to.window(handle)
                            self.driver.close()
                    except Exception:
                        pass
        finally:
            self.owned.clear()
            self.protected.clear()
            self.active_activity = None
            try:
                if self.chrome is not None:
                    self.chrome.close()
            finally:
                self.chrome = None
                self.driver = None

    def __enter__(self) -> "V3ExistingLoginSessions":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

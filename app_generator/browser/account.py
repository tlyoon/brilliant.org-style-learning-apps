"""Verify the authenticated Google account without storing authentication secrets."""

from __future__ import annotations

import time
from typing import Any

from app_generator.browser.common import find_all
from app_generator.errors import AuthenticationRequired, WrongAccountError

ACCOUNT_CONTROLS = (
    ("css selector", 'button[aria-label*="Google Account"]'),
    ("css selector", 'a[aria-label*="Google Account"]'),
    ("css selector", 'button[aria-label*="@"]'),
)
SIGN_IN = (
    ("css selector", 'a[href*="accounts.google.com"][href*="signin"]'),
    ("xpath", '//a[contains(translate(normalize-space(.), "SIGN", "sign"), "sign in")]'),
)


class GoogleAccountVerifier:
    def __init__(self, driver: Any, expected_email: str, timeout: int) -> None:
        self.driver = driver
        self.expected = expected_email.casefold()
        self.timeout = timeout

    def _visible_account_text(self) -> str:
        fragments: list[str] = []
        for element in find_all(self.driver, ACCOUNT_CONTROLS):
            fragments.extend((element.get_attribute("aria-label") or "", element.text or ""))
        return " ".join(fragments)

    def verify(self) -> None:
        deadline = time.monotonic() + self.timeout
        announced = False
        while time.monotonic() < deadline:
            account_text = self._visible_account_text()
            if self.expected in account_text.casefold():
                return
            sign_in_visible = bool(find_all(self.driver, SIGN_IN))
            if sign_in_visible and not announced:
                print(f"Sign in to Google in the opened Chrome window as {self.expected}. Waiting up to {self.timeout} seconds...")
                announced = True
            time.sleep(2)
        text = self._visible_account_text()
        if text and "@" in text:
            raise WrongAccountError(f"Gemini is open under a different Google account; expected {self.expected}")
        raise AuthenticationRequired(f"Google sign-in was not verified for {self.expected} within {self.timeout} seconds")

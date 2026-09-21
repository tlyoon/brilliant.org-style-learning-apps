"""Verify the authenticated Google account without storing authentication secrets."""

from __future__ import annotations

import re
import time
from typing import Any

from app_generator.browser.common import find_all
from app_generator.errors import AuthenticationRequired, WrongAccountError

ACCOUNT_CONTROLS = (
    ("css selector", 'button[aria-label*="Google Account"]'),
    ("css selector", 'a[aria-label*="Google Account"]'),
)
EMAIL = re.compile(r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9.-]+\.[a-z]{2,}", re.IGNORECASE)
SIGN_IN = (
    ("css selector", 'a[href*="accounts.google.com"][href*="signin"]'),
    ("xpath", '//a[contains(translate(normalize-space(.), "SIGN", "sign"), "sign in")]'),
)


class GoogleAccountVerifier:
    def __init__(self, driver: Any, expected_email: str, timeout: int) -> None:
        self.driver = driver
        self.expected = expected_email.casefold()
        self.timeout = timeout

    def _visible_account_emails(self) -> set[str]:
        emails: set[str] = set()
        for element in find_all(self.driver, ACCOUNT_CONTROLS):
            try:
                if element.is_displayed():
                    label = element.get_attribute("aria-label") or ""
                    emails.update(email.casefold() for email in EMAIL.findall(label))
            except Exception:
                # Account controls can be replaced while sign-in completes.
                continue
        return emails

    def verify(self) -> None:
        deadline = time.monotonic() + self.timeout
        announced = False
        while time.monotonic() < deadline:
            account_emails = self._visible_account_emails()
            # Never accept a hidden chooser entry, substring, or ambiguous set
            # of accounts as proof of the currently authenticated identity.
            if account_emails == {self.expected}:
                return
            sign_in_visible = any(element.is_displayed() for element in find_all(self.driver, SIGN_IN))
            if sign_in_visible and not announced:
                print(f"Sign in to Google in the opened Chrome window as {self.expected}. Waiting up to {self.timeout} seconds...")
                announced = True
            time.sleep(2)
        if self._visible_account_emails():
            raise WrongAccountError(f"Gemini is open under a different Google account; expected {self.expected}")
        raise AuthenticationRequired(f"Google sign-in was not verified for {self.expected} within {self.timeout} seconds")

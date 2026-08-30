"""Gem editor page object for idempotent and authoritative project configuration."""

from __future__ import annotations

import logging
import time
from typing import Any

from app_generator.browser.common import element_text, find_all, find_first, replace_element_text
from app_generator.errors import GemAccessError, GemIdentityError, UiContractError
from app_generator.gemini import selectors

LOGGER = logging.getLogger("app_generator.gemini.editor")


def is_placeholder(value: str) -> bool:
    normalized = " ".join(value.split()).casefold()
    return normalized in {"", "to be included"}


class GemEditorPage:
    def __init__(self, driver: Any, gem_url: str, edit_url: str, timeout: int) -> None:
        self.driver = driver
        self.gem_url = gem_url
        self.edit_url = edit_url
        self.url = edit_url or gem_url
        self.timeout = timeout

    def navigate(self) -> None:
        self.driver.get(self.url)

    def enter_editor(self) -> None:
        if find_all(self.driver, selectors.NAME_FIELD):
            return
        if self.edit_url:
            find_first(self.driver, selectors.NAME_FIELD, self.timeout)
            return
        try:
            find_first(self.driver, selectors.EDIT_GEM_BUTTON, self.timeout, clickable=True).click()
            find_first(self.driver, selectors.NAME_FIELD, self.timeout)
            self.url = str(getattr(self.driver, "current_url", self.gem_url))
        except UiContractError as exc:
            raise GemAccessError(
                "The Gem opened, but no accessible Edit Gem control was found. "
                "Confirm that the configured account owns or can edit the Gem, or set gem_edit_url explicitly."
            ) from exc

    def verify_identity(self, expected_name: str) -> None:
        """Legacy identity guard retained for callers that still require name-only verification."""

        actual = element_text(find_first(self.driver, selectors.NAME_FIELD, self.timeout))
        if " ".join(actual.split()).casefold() != " ".join(expected_name.split()).casefold():
            raise GemIdentityError(f"Expected Gem {expected_name!r}, but the editor name is {actual!r}")

    def synchronize_configuration(self, name: str, description: str, instructions: str) -> bool:
        """Converge Name, Description and Instructions to project-authoritative values.

        The configured edit URL and verified Google account establish which Gem is being edited.
        The editable fields are therefore treated as project state: differing values are replaced,
        one Save/Update is issued, and all three values are read back after reopening the editor.
        """

        fields = {
            "Name": (selectors.NAME_FIELD, name),
            "Description": (selectors.DESCRIPTION_FIELD, description),
            "Instructions": (selectors.INSTRUCTIONS_FIELD, instructions),
        }
        changed = False
        for label, (locators, desired) in fields.items():
            if not desired.strip():
                raise UiContractError(f"Configured Gem {label} must not be empty")
            try:
                element = find_first(self.driver, locators, self.timeout)
            except UiContractError as exc:
                raise UiContractError(f"Gem editor opened, but the {label} field was not found") from exc
            current = element_text(element)
            if current.strip() != desired.strip():
                LOGGER.info("Updating Gem %s to match project configuration", label)
                replace_element_text(self.driver, element, desired)
                changed = True

        if changed:
            button = find_first(self.driver, selectors.SAVE_BUTTON, self.timeout, clickable=True)
            editor_url = self.url
            url_before_update = str(getattr(self.driver, "current_url", editor_url))
            button.click()
            # Update normally returns to the Gem conversation. Wait for that navigation
            # to finish before reopening the editor; otherwise a late redirect can win
            # a race with driver.get(editor_url).
            redirect_deadline = time.monotonic() + min(self.timeout, 10)
            while time.monotonic() < redirect_deadline:
                if str(getattr(self.driver, "current_url", "")) != url_before_update:
                    break
                time.sleep(0.25)
            self.driver.get(editor_url)
            find_first(self.driver, selectors.NAME_FIELD, self.timeout)
            for label, (locators, desired) in fields.items():
                actual = element_text(find_first(self.driver, locators, self.timeout))
                if actual.strip() != desired.strip():
                    raise UiContractError(f"Gem {label} did not persist after Save/Update")
        return changed

    def initialize_configuration(self, description: str, instructions: str) -> bool:
        """Legacy fill-if-placeholder behavior retained for compatibility.

        New live generation uses synchronize_configuration(), which treats all three editable
        fields as authoritative project configuration.
        """

        fields = {
            "Description": (selectors.DESCRIPTION_FIELD, description),
            "Instructions": (selectors.INSTRUCTIONS_FIELD, instructions),
        }
        changed = False
        for label, (locators, desired) in fields.items():
            try:
                element = find_first(self.driver, locators, self.timeout)
            except UiContractError as exc:
                raise UiContractError(f"Gem editor opened, but the {label} field was not found") from exc
            current = element_text(element)
            if is_placeholder(current):
                replace_element_text(self.driver, element, desired)
                changed = True
            elif current.strip() != desired.strip():
                LOGGER.warning("Preserving meaningful existing Gem %s content", label)
        if changed:
            button = find_first(self.driver, selectors.SAVE_BUTTON, self.timeout, clickable=True)
            editor_url = self.url
            url_before_update = str(getattr(self.driver, "current_url", editor_url))
            button.click()
            redirect_deadline = time.monotonic() + min(self.timeout, 10)
            while time.monotonic() < redirect_deadline:
                if str(getattr(self.driver, "current_url", "")) != url_before_update:
                    break
                time.sleep(0.25)
            self.driver.get(editor_url)
            find_first(self.driver, selectors.NAME_FIELD, self.timeout)
            for label, (locators, desired) in fields.items():
                actual = element_text(find_first(self.driver, locators, self.timeout))
                if actual.strip() != desired.strip():
                    raise UiContractError(f"Gem {label} did not persist after Save/Update")
        return changed

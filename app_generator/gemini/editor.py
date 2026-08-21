"""Gem editor page object for idempotent Description/Instructions setup."""

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
        actual = element_text(find_first(self.driver, selectors.NAME_FIELD, self.timeout))
        if " ".join(actual.split()).casefold() != " ".join(expected_name.split()).casefold():
            raise GemIdentityError(f"Expected Gem {expected_name!r}, but the editor name is {actual!r}")

    def initialize_configuration(self, description: str, instructions: str) -> bool:
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
                replace_element_text(element, desired)
                changed = True
            elif current.strip() != desired.strip():
                LOGGER.warning("Preserving meaningful existing Gem %s content", label)
        if changed:
            button = find_first(self.driver, selectors.SAVE_BUTTON, self.timeout, clickable=True)
            button.click()
            time.sleep(2)
            self.driver.refresh()
            for label, (locators, desired) in fields.items():
                actual = element_text(find_first(self.driver, locators, self.timeout))
                if actual.strip() != desired.strip():
                    raise UiContractError(f"Gem {label} did not persist after Save/Update")
        return changed

"""Fresh Gem conversation with model selection and per-job PDF attachment."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from app_generator.browser.common import element_text, find_all, find_first, replace_element_text
from app_generator.errors import ResponseContractError, UiContractError
from app_generator.gemini import selectors
from app_generator.gemini.models import ModelOption


class GemConversationPage:
    def __init__(self, driver: Any, url: str, ui_timeout: int, response_timeout: int) -> None:
        self.driver = driver
        self.url = url
        self.ui_timeout = ui_timeout
        self.response_timeout = response_timeout

    def open_new(self) -> None:
        self.driver.get(self.url)
        find_first(self.driver, selectors.COMPOSER, self.ui_timeout)
        if find_all(self.driver, selectors.MODEL_RESPONSES):
            find_first(self.driver, selectors.NEW_CHAT_BUTTON, self.ui_timeout, clickable=True).click()
            self.driver.get(self.url)
            find_first(self.driver, selectors.COMPOSER, self.ui_timeout)
        if find_all(self.driver, selectors.MODEL_RESPONSES):
            raise UiContractError("Gemini did not open a fresh conversation for the claimed source job")

    def discover_models(self) -> list[ModelOption]:
        selector = find_first(self.driver, selectors.MODEL_SELECTOR, self.ui_timeout, clickable=True)
        selector.click()
        time.sleep(0.5)
        options: list[ModelOption] = []
        for index, element in enumerate(find_all(self.driver, selectors.MODEL_OPTIONS)):
            label = " ".join((element.text or "").split())
            if not label:
                continue
            aria_checked = (element.get_attribute("aria-checked") or "").casefold() == "true"
            disabled = element.get_attribute("aria-disabled") == "true" or not element.is_enabled()
            description = element.get_attribute("aria-label") or ""
            options.append(ModelOption(label, description, aria_checked, "recommended" in description.casefold(), disabled, index))
        try:
            from selenium.webdriver.common.keys import Keys
            selector.send_keys(Keys.ESCAPE)
        except ImportError:
            pass
        if not options:
            raise UiContractError("The model selector opened, but no model options could be parsed")
        return options

    def select_model(self, label: str) -> None:
        find_first(self.driver, selectors.MODEL_SELECTOR, self.ui_timeout, clickable=True).click()
        candidates = [
            element for element in find_all(self.driver, selectors.MODEL_OPTIONS)
            if " ".join((element.text or "").split()) == label
        ]
        if len(candidates) != 1:
            raise UiContractError(f"Expected exactly one selectable model labelled {label!r}, found {len(candidates)}")
        candidates[0].click()

    def attach_pdf(self, path: Path) -> None:
        if path.suffix.casefold() != ".pdf" or not path.is_file():
            raise UiContractError(f"Conversation attachment is not an existing PDF: {path}")
        find_first(self.driver, selectors.ATTACH_BUTTON, self.ui_timeout, clickable=True).click()
        deadline = time.monotonic() + self.ui_timeout
        upload_action_clicked = False
        file_input = None
        while time.monotonic() < deadline and file_input is None:
            inputs = find_all(self.driver, selectors.CONVERSATION_FILE_INPUT)
            if inputs:
                file_input = inputs[0]
                break
            actions = find_all(self.driver, selectors.CONVERSATION_UPLOAD_ACTION)
            if actions and not upload_action_clicked:
                actions[0].click()
                upload_action_clicked = True
            time.sleep(0.25)
        if file_input is None:
            raise UiContractError("Gem conversation opened, but no file-upload input was found")
        file_input.send_keys(str(path.resolve()))

        expected = path.name.casefold()
        while time.monotonic() < deadline:
            labels = [element_text(item).casefold() for item in find_all(self.driver, selectors.ATTACHMENT_LABELS)]
            if any(expected in label for label in labels) and not find_all(self.driver, selectors.ATTACHMENT_PROCESSING):
                return
            time.sleep(0.5)
        raise UiContractError(f"Gemini did not finish attaching {path.name!r} before timeout")

    def ask(self, prompt: str) -> str:
        before = find_all(self.driver, selectors.MODEL_RESPONSES)
        composer = find_first(self.driver, selectors.COMPOSER, self.ui_timeout)
        replace_element_text(composer, prompt)
        find_first(self.driver, selectors.SEND_BUTTON, self.ui_timeout, clickable=True).click()
        deadline = time.monotonic() + self.response_timeout
        last_text = ""
        stable_since = time.monotonic()
        while time.monotonic() < deadline:
            responses = find_all(self.driver, selectors.MODEL_RESPONSES)
            if len(responses) > len(before):
                current = element_text(responses[-1])
                if current and current == last_text:
                    if time.monotonic() - stable_since >= 2:
                        return current
                else:
                    last_text = current
                    stable_since = time.monotonic()
            time.sleep(0.5)
        if last_text:
            raise ResponseContractError("Gemini response did not reach a stable completed state before timeout")
        raise ResponseContractError("No Gemini model response appeared before timeout")

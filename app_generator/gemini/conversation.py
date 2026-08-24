"""Fresh Gem conversation with model selection and per-job PDF attachment."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from app_generator.browser.common import element_text, find_all, find_first, replace_element_text
from app_generator.errors import ResponseContractError, UiContractError
from app_generator.gemini import selectors
from app_generator.gemini.models import ModelOption

NON_JSON_STABLE_POLLS = 60


def _response_text(driver: Any, element: Any) -> str:
    variants: list[str] = []
    try:
        variants.append(element_text(element))
    except Exception:
        pass
    try:
        rendered = driver.execute_script(
            "return {innerText: arguments[0].innerText || '', textContent: arguments[0].textContent || ''}",
            element,
        )
        if isinstance(rendered, dict):
            variants.extend(str(rendered.get(key, "")).strip() for key in ("innerText", "textContent"))
    except Exception:
        pass
    return max(variants, key=len, default="")


def _complete_json_frame(text: str) -> str | None:
    # A response wrapper can contain more than one prior frame. The final
    # complete frame is the current answer.
    begin = text.rfind("BEGIN_JSON")
    if begin >= 0:
        end = text.find("END_JSON", begin + len("BEGIN_JSON"))
        if end >= 0:
            return text[begin : end + len("END_JSON")]

    # Every generator contract requests an object. If Gemini omits or visually
    # transforms the sentinel lines, decode only from the first object opener.
    # Never fall through to a nested object while the outer response is still
    # streaming: doing so can submit the next prompt before Gemini is ready.
    start = text.find("{")
    if start < 0:
        return None
    try:
        value, length = json.JSONDecoder(strict=False).raw_decode(text[start:])
    except json.JSONDecodeError:
        return None
    if not isinstance(value, dict):
        return None
    end = start + length
    return f"BEGIN_JSON\n{text[start:end]}\nEND_JSON"


def _visible_signal(driver: Any, locators: tuple[tuple[str, str], ...]) -> bool:
    for by, selector in locators:
        try:
            elements = driver.find_elements(by, selector)
        except Exception:
            continue
        for element in elements:
            try:
                if element.is_displayed():
                    return True
            except Exception:
                continue
    return False


def _generation_signals(driver: Any) -> tuple[bool, bool]:
    """Return visible active-generation and completed-response UI signals."""

    return (
        _visible_signal(driver, selectors.GENERATION_ACTIVE),
        _visible_signal(driver, selectors.RESPONSE_COMPLETE),
    )


def _direct_element_signature(driver: Any, locators: tuple[tuple[str, str], ...]) -> set[tuple[str, str]]:
    signature: set[tuple[str, str]] = set()
    for by, selector in locators:
        try:
            elements = driver.find_elements(by, selector)
        except Exception:
            continue
        for index, element in enumerate(elements):
            try:
                if not element.is_displayed():
                    continue
                key = str(getattr(element, "id", "") or f"{by}:{selector}:{index}")
                signature.add((key, _response_text(driver, element)))
            except Exception:
                continue
    return signature


def _composer_is_empty(driver: Any, composer: Any) -> bool:
    try:
        value = composer.get_attribute("value")
        if value is not None:
            return not str(value).strip()
    except Exception:
        pass
    try:
        rendered = driver.execute_script(
            "return (arguments[0].innerText || arguments[0].textContent || '').trim()",
            composer,
        )
        return not str(rendered or "").strip()
    except Exception:
        return False


class GemConversationPage:
    def __init__(self, driver: Any, url: str, ui_timeout: int, response_timeout: int) -> None:
        self.driver = driver
        self.url = url
        self.ui_timeout = ui_timeout
        self.response_timeout = response_timeout

    def open_new(self) -> None:
        self.driver.get(self.url)
        find_first(self.driver, selectors.COMPOSER, self.ui_timeout)
        # A Gem landing page can contain introductory content represented by
        # the same elements as model responses. Prior user messages are the
        # reliable signal that this is an existing conversation.
        if find_all(self.driver, selectors.USER_MESSAGES):
            find_first(self.driver, selectors.NEW_CHAT_BUTTON, self.ui_timeout, clickable=True).click()
            self.driver.get(self.url)
            find_first(self.driver, selectors.COMPOSER, self.ui_timeout)
        if find_all(self.driver, selectors.USER_MESSAGES):
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
        # Open the conversation's attachment menu before resolving a file
        # input. Gemini can keep unrelated hidden file inputs elsewhere in the
        # page, so selecting a pre-existing generic input is unsafe.
        find_first(self.driver, selectors.ATTACH_BUTTON, self.ui_timeout, clickable=True).click()
        menu_deadline = time.monotonic() + self.ui_timeout
        upload_action_clicked = False
        file_input = None
        while time.monotonic() < menu_deadline and file_input is None:
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

        attachment_timeout = max(self.ui_timeout, min(self.response_timeout, 180))
        deadline = time.monotonic() + attachment_timeout
        while time.monotonic() < deadline:
            previews = find_all(self.driver, selectors.ATTACHMENT_PREVIEW)
            loading = find_all(self.driver, selectors.ATTACHMENT_LOADING)
            ready = find_all(self.driver, selectors.ATTACHMENT_READY)
            try:
                preview_visible = any(item.is_displayed() for item in previews)
                loading_visible = any(item.is_displayed() for item in loading)
                ready_visible = any(item.is_displayed() for item in ready)
            except Exception:
                # Angular replaces the preview subtree when loading completes;
                # reacquire all nodes on the next poll if one becomes stale.
                time.sleep(0.25)
                continue
            if preview_visible and ready_visible and not loading_visible:
                return
            time.sleep(0.25)
        raise UiContractError(
            f"Gemini did not finish attaching {path.name!r} within {attachment_timeout} seconds"
        )

    def _confirm_prompt_submitted(
        self,
        composer: Any,
        send_button: Any,
        before_user_messages: set[tuple[str, str]],
    ) -> bool:
        """Verify submission and recover from Gemini click controls that silently no-op."""

        saw_generation_active = False

        def acknowledged() -> bool:
            nonlocal saw_generation_active
            active, _ = _generation_signals(self.driver)
            saw_generation_active = saw_generation_active or active
            if active:
                return True
            if _composer_is_empty(self.driver, composer):
                return True
            current_user_messages = _direct_element_signature(self.driver, selectors.USER_MESSAGES)
            return bool(current_user_messages - before_user_messages)

        def wait_for_acknowledgement(seconds: float) -> bool:
            if acknowledged():
                return True
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                if acknowledged():
                    return True
                time.sleep(0.25)
            return acknowledged()

        retry_window = max(1.0, min(float(self.ui_timeout), 3.0))
        if wait_for_acknowledgement(retry_window):
            return saw_generation_active

        # Selenium click can report success while Gemini ignores it. Reacquire
        # the current Angular control and invoke its click handler directly.
        send_button = find_first(
            self.driver,
            selectors.SEND_BUTTON,
            max(self.ui_timeout, min(self.response_timeout, 180)),
            clickable=True,
        )
        self.driver.execute_script("arguments[0].click()", send_button)
        if wait_for_acknowledgement(retry_window):
            return saw_generation_active

        # The composer is known to contain the exact intended prompt. A native
        # Enter is the final bounded fallback and matches the working manual UI
        # interaction without resending if either earlier attempt succeeded.
        try:
            from selenium.webdriver.common.keys import Keys
        except ImportError as exc:
            raise UiContractError("Selenium is unavailable for the native Gemini submit fallback") from exc
        composer.send_keys(Keys.ENTER)
        if wait_for_acknowledgement(max(retry_window, float(self.ui_timeout))):
            return saw_generation_active
        raise UiContractError(
            "Gemini did not acknowledge prompt submission: the composer remained populated, "
            "no new user message appeared, and generation did not start"
        )

    def ask(self, prompt: str) -> str:
        before = find_all(self.driver, selectors.MODEL_RESPONSES)
        before_user_messages = _direct_element_signature(self.driver, selectors.USER_MESSAGES)
        before_by_key: dict[str, str] = {}
        before_texts: set[str] = set()
        before_frames: set[str] = set()
        for index, response in enumerate(before):
            try:
                text = _response_text(self.driver, response)
                key = str(getattr(response, "id", "") or f"position:{index}")
                before_by_key[key] = text
                if text:
                    before_texts.add(text)
                    frame = _complete_json_frame(text)
                    if frame is not None:
                        before_frames.add(frame)
            except Exception:
                continue
        composer = find_first(self.driver, selectors.COMPOSER, self.ui_timeout)
        replace_element_text(self.driver, composer, prompt)
        send_timeout = max(self.ui_timeout, min(self.response_timeout, 180))
        send_button = find_first(self.driver, selectors.SEND_BUTTON, send_timeout, clickable=True)
        try:
            send_button.click()
        except Exception as exc:
            if exc.__class__.__name__ != "ElementClickInterceptedException":
                raise
            # Gemini currently overlays part of the enabled send button with
            # its persistent microphone/button wrapper at some window sizes.
            # A DOM click invokes the same enabled control without relying on
            # the obscured screen coordinate.
            self.driver.execute_script("arguments[0].click()", send_button)
        saw_generation_active = self._confirm_prompt_submitted(
            composer,
            send_button,
            before_user_messages,
        )
        deadline = time.monotonic() + self.response_timeout
        previous_by_key: dict[str, str] = {}
        observed_count = 0
        longest_observed = 0
        unchanged_non_json_polls = 0
        previous_text_signature: tuple[str, ...] = ()
        while time.monotonic() < deadline:
            generation_active, response_complete = _generation_signals(self.driver)
            saw_generation_active = saw_generation_active or generation_active
            generation_finished = not generation_active and (
                saw_generation_active or response_complete
            )
            responses = find_all(self.driver, selectors.MODEL_RESPONSES)
            current_by_key: dict[str, str] = {}
            for index, response in enumerate(responses):
                try:
                    candidate = _response_text(self.driver, response)
                    key = str(getattr(response, "id", "") or f"position:{index}")
                except Exception:
                    continue
                changed = (
                    candidate != before_by_key[key]
                    if key in before_by_key
                    else not key.startswith("position:") or candidate not in before_texts
                )
                if candidate and changed:
                    current_by_key[key] = candidate
            observed_count = max(observed_count, len(current_by_key))
            longest_observed = max(
                longest_observed,
                max((len(text) for text in current_by_key.values()), default=0),
            )
            for key, current in current_by_key.items():
                if previous_by_key.get(key) != current:
                    continue
                frame = _complete_json_frame(current)
                genuinely_new_element = key not in before_by_key and not key.startswith("position:")
                if (
                    generation_finished
                    and frame is not None
                    and (frame not in before_frames or genuinely_new_element)
                ):
                    return frame
            text_signature = tuple(sorted(set(current_by_key.values())))
            if text_signature and text_signature == previous_text_signature:
                unchanged_non_json_polls += 1
                if generation_finished and unchanged_non_json_polls >= NON_JSON_STABLE_POLLS:
                    raise ResponseContractError(
                        "Gemini response stabilized without complete parseable JSON "
                        f"(changed candidates={len(current_by_key)}, longest text={longest_observed} characters)"
                    )
            else:
                unchanged_non_json_polls = 0
            previous_text_signature = text_signature
            previous_by_key = current_by_key
            time.sleep(0.5)
        if observed_count:
            state = "still generating" if _generation_signals(self.driver)[0] else "without a completion signal"
            raise ResponseContractError(
                "Gemini model responses were visible but none exposed complete parseable JSON before timeout "
                f"({state}; changed candidates={observed_count}, longest text={longest_observed} characters)"
            )
        raise ResponseContractError("No Gemini model response appeared before timeout")

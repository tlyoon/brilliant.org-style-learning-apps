"""Lazy Selenium imports and resilient locator helpers."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app_generator.errors import BrowserError, UiContractError

Locator = tuple[str, str]


def selenium_modules() -> dict[str, Any]:
    try:
        from selenium.common.exceptions import TimeoutException
        from selenium.webdriver.support import expected_conditions as ec
        from selenium.webdriver.support.ui import WebDriverWait
    except ImportError as exc:
        raise BrowserError("Selenium is not installed. Run: python -m pip install -r requirements-generator.txt") from exc
    return {"TimeoutException": TimeoutException, "ec": ec, "WebDriverWait": WebDriverWait}


def find_first(driver: Any, locators: Iterable[Locator], timeout: int, *, clickable: bool = False) -> Any:
    modules = selenium_modules()
    locators = tuple(locators)

    def first_available(current_driver: Any) -> Any:
        for by, selector in locators:
            try:
                elements = current_driver.find_elements(by, selector)
            except Exception:
                continue
            for element in elements:
                try:
                    if not element.is_displayed():
                        continue
                    if clickable and not element.is_enabled():
                        continue
                    return element
                except Exception:
                    # Gemini frequently replaces controls while its Angular UI
                    # settles. Ignore a transient/stale candidate and continue
                    # checking every alternative during the same poll.
                    continue
        return False

    try:
        return modules["WebDriverWait"](driver, timeout).until(first_available)
    except modules["TimeoutException"] as exc:
        attempted = "; ".join(f"{by}={selector}" for by, selector in locators)
        raise UiContractError("No matching visible control was found. Tried: " + attempted) from exc


def find_all(driver: Any, locators: Iterable[Locator]) -> list[Any]:
    seen: set[str] = set()
    elements: list[Any] = []
    for by, selector in locators:
        for element in driver.find_elements(by, selector):
            key = getattr(element, "id", None) or f"{by}:{selector}:{len(elements)}"
            if key not in seen:
                seen.add(key)
                elements.append(element)
    return elements


def element_text(element: Any) -> str:
    value = element.get_attribute("value")
    return str(value if value is not None else element.text).strip()


def replace_element_text(driver: Any, element: Any, text: str) -> None:
    try:
        mode = driver.execute_script(
            """
            const element = arguments[0];
            const text = arguments[1];
            element.focus();
            if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement) {
                const prototype = element instanceof HTMLTextAreaElement
                    ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
                const setter = Object.getOwnPropertyDescriptor(prototype, "value").set;
                setter.call(element, text);
                element.dispatchEvent(new InputEvent("input", {
                    bubbles: true, inputType: "insertFromPaste",
                }));
                element.dispatchEvent(new Event("change", {bubbles: true}));
                return "value";
            }
            if (element.isContentEditable) {
                element.replaceChildren();
                element.dispatchEvent(new InputEvent("input", {
                    bubbles: true, inputType: "deleteContentBackward",
                }));
                const selection = window.getSelection();
                const range = document.createRange();
                range.selectNodeContents(element);
                range.collapse(false);
                selection.removeAllRanges();
                selection.addRange(range);
                return "contenteditable";
            }
            return "";
            """,
            element,
            text,
        )
        if mode == "value":
            return
        if mode == "contenteditable":
            # CDP's native text insertion follows Chrome's real editing path,
            # so Angular receives the same events as a paste without the
            # per-character cost and timeout risk of WebElement.send_keys.
            driver.execute_cdp_cmd("Input.insertText", {"text": text})
            rendered = driver.execute_script(
                "return {textContent: arguments[0].textContent || '', innerText: arguments[0].innerText || ''}",
                element,
            )
            def normalize(value: Any) -> str:
                return (
                    str(value)
                    .replace("\r\n", "\n")
                    .replace("\r", "\n")
                    .replace("\u00a0", " ")
                    .replace("\u200b", "")
                    .rstrip("\n")
                )

            expected = normalize(text)
            actuals = [normalize(rendered.get(key, "")) for key in ("innerText", "textContent")]
            content_matches = expected in actuals or expected.replace("\n", "") in {
                value.replace("\n", "") for value in actuals
            }
            if not content_matches:
                def mismatch_index(value: str) -> int:
                    for index, (actual_char, expected_char) in enumerate(zip(value, expected)):
                        if actual_char != expected_char:
                            return index
                    return min(len(value), len(expected))

                detail = ", ".join(
                    f"{key} length={len(value)} mismatch={mismatch_index(value)}"
                    for key, value in zip(("innerText", "textContent"), actuals)
                )
                raise UiContractError(
                    f"Gemini composer text did not match the intended prompt (expected length={len(expected)}; {detail})"
                )
            return
    except UiContractError:
        raise
    except Exception as exc:
        # Retain keyboard input as a compatibility fallback for UI variants
        # that reject scripted value replacement.
        if len(text) > 4096:
            raise UiContractError("Browser could not insert the large Gemini prompt in one operation") from exc
    if len(text) > 4096:
        raise UiContractError("Gemini's composer rejected one-operation insertion of a large prompt")
    try:
        from selenium.webdriver.common.keys import Keys
    except ImportError as exc:
        raise BrowserError("Selenium is not installed") from exc
    element.click()
    element.send_keys(Keys.CONTROL, "a")
    element.send_keys(text)

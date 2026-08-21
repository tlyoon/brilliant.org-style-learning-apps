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
    errors: list[str] = []
    locators = tuple(locators)
    per_locator = max(1, timeout // max(1, len(locators)))
    for locator in locators:
        try:
            condition = modules["ec"].element_to_be_clickable(locator) if clickable else modules["ec"].visibility_of_element_located(locator)
            return modules["WebDriverWait"](driver, per_locator).until(condition)
        except modules["TimeoutException"]:
            errors.append(f"{locator[0]}={locator[1]}")
    raise UiContractError("No matching visible control was found. Tried: " + "; ".join(errors))


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


def replace_element_text(element: Any, text: str) -> None:
    try:
        from selenium.webdriver.common.keys import Keys
    except ImportError as exc:
        raise BrowserError("Selenium is not installed") from exc
    element.click()
    element.send_keys(Keys.CONTROL, "a")
    element.send_keys(text)

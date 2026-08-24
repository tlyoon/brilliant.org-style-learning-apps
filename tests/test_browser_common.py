import unittest
from unittest.mock import patch

from app_generator.browser.common import find_first, replace_element_text
from app_generator.errors import UiContractError


class BrowserCommonTests(unittest.TestCase):
    class Timeout(Exception):
        pass

    class Wait:
        def __init__(self, driver, timeout):
            self.driver = driver
            self.timeout = timeout

        def until(self, condition):
            result = condition(self.driver)
            if result:
                return result
            raise BrowserCommonTests.Timeout()

    class Element:
        def __init__(self, *, displayed=True, enabled=True):
            self.displayed = displayed
            self.enabled = enabled

        def is_displayed(self):
            return self.displayed

        def is_enabled(self):
            return self.enabled

    class Driver:
        def __init__(self, results):
            self.results = results
            self.calls = []

        def find_elements(self, by, selector):
            self.calls.append((by, selector))
            return self.results.get((by, selector), [])

    def modules(self):
        return {
            "TimeoutException": self.Timeout,
            "WebDriverWait": self.Wait,
        }

    def test_alternative_locators_are_checked_in_one_wait_poll(self):
        target = self.Element()
        driver = self.Driver({("css", "second"): [target]})
        with patch("app_generator.browser.common.selenium_modules", return_value=self.modules()):
            actual = find_first(driver, (("css", "first"), ("css", "second")), 30)
        self.assertIs(target, actual)
        self.assertEqual([("css", "first"), ("css", "second")], driver.calls)

    def test_clickable_lookup_skips_disabled_candidates(self):
        disabled = self.Element(enabled=False)
        enabled = self.Element(enabled=True)
        driver = self.Driver({("css", "first"): [disabled], ("css", "second"): [enabled]})
        with patch("app_generator.browser.common.selenium_modules", return_value=self.modules()):
            actual = find_first(
                driver,
                (("css", "first"), ("css", "second")),
                30,
                clickable=True,
            )
        self.assertIs(enabled, actual)

    def test_timeout_reports_every_attempted_locator(self):
        driver = self.Driver({})
        with patch("app_generator.browser.common.selenium_modules", return_value=self.modules()):
            with self.assertRaisesRegex(UiContractError, "css=first; xpath=second"):
                find_first(driver, (("css", "first"), ("xpath", "second")), 30)

    def test_replace_text_uses_single_scripted_input_operation(self):
        element = self.Element()

        class ScriptDriver:
            def __init__(self):
                self.calls = []

            def execute_script(self, script, target, text):
                self.calls.append((script, target, text))
                return "value"

        driver = ScriptDriver()
        replace_element_text(driver, element, "a large prompt")
        self.assertEqual(1, len(driver.calls))
        self.assertIs(element, driver.calls[0][1])
        self.assertEqual("a large prompt", driver.calls[0][2])

    def test_replace_contenteditable_uses_native_cdp_text_insertion(self):
        element = self.Element()

        class ScriptDriver:
            def __init__(self):
                self.cdp_calls = []
                self.script_calls = 0

            def execute_script(self, _script, _target, _text=None):
                self.script_calls += 1
                return (
                    "contenteditable"
                    if self.script_calls == 1
                    else {"textContent": "large prompt", "innerText": "large prompt"}
                )

            def execute_cdp_cmd(self, command, params):
                self.cdp_calls.append((command, params))

        driver = ScriptDriver()
        replace_element_text(driver, element, "large prompt")
        self.assertEqual(
            [("Input.insertText", {"text": "large prompt"})],
            driver.cdp_calls,
        )

    def test_replace_contenteditable_accepts_dom_line_block_transformation(self):
        element = self.Element()

        class ScriptDriver:
            def __init__(self):
                self.script_calls = 0

            def execute_script(self, _script, _target, _text=None):
                self.script_calls += 1
                return (
                    "contenteditable"
                    if self.script_calls == 1
                    else {"textContent": "firstsecond", "innerText": "first\n\nsecond"}
                )

            def execute_cdp_cmd(self, _command, _params):
                return None

        replace_element_text(ScriptDriver(), element, "first\nsecond")


if __name__ == "__main__":
    unittest.main()

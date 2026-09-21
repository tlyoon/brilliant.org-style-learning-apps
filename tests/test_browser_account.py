import unittest
from unittest.mock import Mock, patch

from app_generator.browser.account import ACCOUNT_CONTROLS, GoogleAccountVerifier
from app_generator.errors import AuthenticationRequired, WrongAccountError


class GoogleAccountVerifierTests(unittest.TestCase):
    expected = "operator@example.com"

    def element(self, email, *, displayed=True):
        element = Mock()
        element.is_displayed.return_value = displayed
        element.get_attribute.return_value = f"Google Account: Operator ({email})"
        return element

    def verify(self, elements, *, timeout=1):
        driver = Mock()
        driver.find_elements.side_effect = lambda by, selector: (
            elements if (by, selector) == ACCOUNT_CONTROLS[0] else []
        )
        with patch("app_generator.browser.account.time.monotonic", side_effect=[0, 0, 2]):
            with patch("app_generator.browser.account.time.sleep"):
                GoogleAccountVerifier(driver, self.expected, timeout).verify()

    def test_visible_exact_active_account_is_accepted_case_insensitively(self):
        self.verify([self.element(self.expected.upper())])

    def test_hidden_expected_account_does_not_mask_visible_wrong_account(self):
        with self.assertRaises(WrongAccountError):
            self.verify([
                self.element(self.expected, displayed=False),
                self.element("other@example.org"),
            ])

    def test_multiple_visible_accounts_are_not_proof_of_active_identity(self):
        with self.assertRaises(WrongAccountError):
            self.verify([self.element(self.expected), self.element("other@example.org")])

    def test_email_substring_is_not_accepted(self):
        with self.assertRaises(WrongAccountError):
            self.verify([self.element("not-" + self.expected)])

    def test_hidden_account_alone_requires_authentication(self):
        with self.assertRaises(AuthenticationRequired):
            self.verify([self.element(self.expected, displayed=False)])

    def test_alternate_account_in_control_body_is_not_accepted(self):
        element = self.element("other@example.org")
        element.text = self.expected
        with self.assertRaises(WrongAccountError):
            self.verify([element])

    def test_generic_email_buttons_are_not_active_account_controls(self):
        self.assertNotIn(("css selector", 'button[aria-label*="@"]'), ACCOUNT_CONTROLS)

    def test_stale_account_control_is_ignored_until_next_poll(self):
        stale = self.element(self.expected)
        stale.is_displayed.side_effect = RuntimeError("stale")
        self.verify([stale, self.element(self.expected)])


if __name__ == "__main__":
    unittest.main()

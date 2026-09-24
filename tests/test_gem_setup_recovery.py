import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app_generator.errors import UiContractError
from app_generator.runtime.orchestrator import _configure_gem_with_session_recovery


class GemSetupRecoveryTests(unittest.TestCase):
    def test_configure_restarts_browser_once_after_ui_contract_failure(self):
        config = SimpleNamespace()
        browser = Mock()
        client = Mock()
        client.configure_gem.side_effect = UiContractError("synthetic bad attached session")
        replacement_browser = Mock()
        driver = object()
        replacement_browser.start.return_value = driver
        replacement = Mock()
        chrome_factory = Mock(return_value=replacement_browser)
        client_factory = Mock(return_value=replacement)
        lease_guard = Mock()

        actual_browser, actual_client = _configure_gem_with_session_recovery(
            browser,
            client,
            config,
            chrome_factory=chrome_factory,
            client_factory=client_factory,
            lease_guard=lease_guard,
        )

        lease_guard.ensure_owned.assert_called_once_with()
        browser.close.assert_called_once_with()
        replacement_browser.start.assert_called_once_with()
        client_factory.assert_called_once_with(driver, config)
        replacement.open_editor_and_verify_account.assert_called_once_with()
        replacement.configure_gem.assert_called_once_with()
        self.assertIs(actual_browser, replacement_browser)
        self.assertIs(actual_client, replacement)

    def test_second_ui_contract_failure_is_not_hidden(self):
        config = SimpleNamespace()
        browser = Mock()
        client = Mock()
        client.configure_gem.side_effect = UiContractError("first")
        replacement_browser = Mock()
        replacement_browser.start.return_value = object()
        replacement = Mock()
        replacement.configure_gem.side_effect = UiContractError("second")

        with self.assertRaisesRegex(UiContractError, "second"):
            _configure_gem_with_session_recovery(
                browser,
                client,
                config,
                chrome_factory=Mock(return_value=replacement_browser),
                client_factory=Mock(return_value=replacement),
            )


if __name__ == "__main__":
    unittest.main()

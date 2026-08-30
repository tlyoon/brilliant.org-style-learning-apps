import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from app_generator.errors import ResponseContractError, TransientGeminiError, UiContractError
from app_generator.gemini.client import GeminiClient, RecoveringGeminiClient


class GeneratorGeminiClientTests(unittest.TestCase):
    def config(self, *, allow_unknown_model_fallback):
        return SimpleNamespace(
            gem_url="https://gemini.google.com/gem/test",
            gem_edit_url="https://gemini.google.com/gems/edit/test",
            ui_timeout_seconds=1,
            response_timeout_seconds=1,
            model_preference_patterns=(r"pro", r"flash"),
            allow_unknown_model_fallback=allow_unknown_model_fallback,
        )

    def test_missing_model_picker_uses_default_when_policy_allows_it(self):
        client = GeminiClient(Mock(), self.config(allow_unknown_model_fallback=True))
        client.conversation = Mock()
        client.conversation.discover_models.side_effect = UiContractError("picker unavailable")

        with self.assertLogs("app_generator.gemini", level="WARNING"):
            selected = client.open_conversation_select_model_and_attach(Path("source.pdf"))

        self.assertEqual("Gem default (model selector unavailable)", selected)
        client.conversation.open_new.assert_called_once_with()
        client.conversation.select_model.assert_not_called()
        client.conversation.attach_pdf.assert_called_once_with(Path("source.pdf"))

    def test_missing_model_picker_remains_an_error_under_strict_policy(self):
        client = GeminiClient(Mock(), self.config(allow_unknown_model_fallback=False))
        client.conversation = Mock()
        client.conversation.discover_models.side_effect = UiContractError("picker unavailable")

        with self.assertRaisesRegex(UiContractError, "picker unavailable"):
            client.open_conversation_select_model_and_attach(Path("source.pdf"))

        client.conversation.select_model.assert_not_called()
        client.conversation.attach_pdf.assert_not_called()

    def test_transient_error_captures_diagnostic_and_relaunches(self):
        with self.subTest("first client fails and replacement succeeds"):
            first = Mock()
            first.ask.side_effect = TransientGeminiError("temporary")
            first.driver.save_screenshot.return_value = True
            replacement = Mock()
            replacement.ask.return_value = 'BEGIN_JSON\n{"ok": true}\nEND_JSON'
            restart = Mock(return_value=replacement)

            with self.assertLogs("app_generator.gemini", level="WARNING"):
                recovering = RecoveringGeminiClient(
                    first,
                    restart,
                    max_restarts=2,
                    diagnostics_dir=Path("diagnostics"),
                )
                response = recovering.ask("prompt")

            self.assertIn('"ok": true', response)
            restart.assert_called_once_with()
            first.driver.save_screenshot.assert_called_once()
            replacement.ask.assert_called_once_with("prompt")

    def test_transient_error_stops_after_bounded_restarts(self):
        first = Mock()
        first.ask.side_effect = TransientGeminiError("temporary")
        first.driver.save_screenshot.return_value = True
        replacement = Mock()
        replacement.ask.side_effect = TransientGeminiError("temporary again")
        replacement.driver.save_screenshot.return_value = True

        recovering = RecoveringGeminiClient(
            first,
            Mock(return_value=replacement),
            max_restarts=1,
            diagnostics_dir=Path("diagnostics"),
        )
        with self.assertLogs("app_generator.gemini", level="WARNING"):
            with self.assertRaises(TransientGeminiError):
                recovering.ask("prompt")

        self.assertEqual(1, recovering.restart_count)
        first.driver.save_screenshot.assert_called_once()
        replacement.driver.save_screenshot.assert_called_once()

    def test_response_contract_error_relaunches_and_retries_the_same_prompt(self):
        first = Mock()
        first.ask.side_effect = ResponseContractError("incomplete JSON")
        first.driver.save_screenshot.return_value = True
        replacement = Mock()
        replacement.ask.return_value = 'BEGIN_JSON\n{"ok": true}\nEND_JSON'
        restart = Mock(return_value=replacement)

        recovering = RecoveringGeminiClient(
            first,
            restart,
            max_restarts=3,
            diagnostics_dir=Path("diagnostics"),
        )
        with self.assertLogs("app_generator.gemini", level="WARNING") as logs:
            response = recovering.ask("same prompt")

        self.assertIn('"ok": true', response)
        self.assertEqual(1, recovering.restart_count)
        restart.assert_called_once_with()
        replacement.ask.assert_called_once_with("same prompt")
        self.assertTrue(any("RESPONSE_CONTRACT_ERROR (1/3)" in entry for entry in logs.output))

    def test_response_contract_error_stops_after_three_relaunches(self):
        clients = [Mock() for _ in range(4)]
        for client in clients:
            client.ask.side_effect = ResponseContractError("incomplete JSON")
            client.driver.save_screenshot.return_value = True
        replacements = iter(clients[1:])

        recovering = RecoveringGeminiClient(
            clients[0],
            lambda: next(replacements),
            max_restarts=3,
            diagnostics_dir=Path("diagnostics"),
        )
        with self.assertLogs("app_generator.gemini", level="WARNING"):
            with self.assertRaises(ResponseContractError):
                recovering.ask("same prompt")

        self.assertEqual(3, recovering.restart_count)
        for client in clients:
            client.ask.assert_called_once_with("same prompt")
            client.driver.save_screenshot.assert_called_once()


if __name__ == "__main__":
    unittest.main()

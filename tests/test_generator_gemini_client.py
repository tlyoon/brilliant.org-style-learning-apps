import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from app_generator.errors import UiContractError
from app_generator.gemini.client import GeminiClient


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


if __name__ == "__main__":
    unittest.main()

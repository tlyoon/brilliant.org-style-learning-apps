import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app_generator.errors import UiContractError
from app_generator.gemini.client import GeminiClient
from app_generator.gemini.editor import GemEditorPage


class Element:
    def __init__(self, value="", on_click=None):
        self.value = value
        self.text = value
        self.on_click = on_click
        self.clicked = False

    def get_attribute(self, name):
        return self.value if name == "value" else None

    def click(self):
        self.clicked = True
        if self.on_click:
            self.on_click()


class Driver:
    def __init__(self):
        self.current_url = "https://gemini.google.com/gems/edit/test"
        self.loaded_urls = []

    def get(self, url):
        self.loaded_urls.append(url)
        self.current_url = url


class GemConfigurationConvergenceTests(unittest.TestCase):
    def test_identical_fields_are_not_saved(self):
        driver = Driver()
        page = GemEditorPage(
            driver,
            "https://gemini.google.com/gem/test",
            "https://gemini.google.com/gems/edit/test",
            1,
        )
        name = Element("Configured name")
        description = Element("Configured description")
        instructions = Element("Configured instructions")

        with (
            patch(
                "app_generator.gemini.editor.find_first",
                side_effect=[name, description, instructions],
            ),
            patch("app_generator.gemini.editor.replace_element_text") as replace_text,
        ):
            changed = page.synchronize_configuration(
                "Configured name",
                "Configured description",
                "Configured instructions",
            )

        self.assertFalse(changed)
        replace_text.assert_not_called()
        self.assertEqual([], driver.loaded_urls)

    def test_differing_fields_are_replaced_saved_once_and_reverified(self):
        driver = Driver()
        page = GemEditorPage(
            driver,
            "https://gemini.google.com/gem/test",
            "https://gemini.google.com/gems/edit/test",
            1,
        )
        name = Element("Old name")
        description = Element("Old meaningful description")
        instructions = Element("Old meaningful instructions")
        save = Element(on_click=lambda: setattr(driver, "current_url", "https://gemini.google.com/gem/test"))

        def replace_text(_driver, element, desired):
            element.value = desired
            element.text = desired

        with (
            patch(
                "app_generator.gemini.editor.find_first",
                side_effect=[
                    name,
                    description,
                    instructions,
                    save,
                    name,
                    name,
                    description,
                    instructions,
                ],
            ),
            patch("app_generator.gemini.editor.replace_element_text", side_effect=replace_text) as replace_call,
        ):
            changed = page.synchronize_configuration(
                "Configured name",
                "Configured description",
                "Configured instructions",
            )

        self.assertTrue(changed)
        self.assertEqual(3, replace_call.call_count)
        self.assertTrue(save.clicked)
        self.assertEqual("Configured name", name.value)
        self.assertEqual("Configured description", description.value)
        self.assertEqual("Configured instructions", instructions.value)
        self.assertEqual(["https://gemini.google.com/gems/edit/test"], driver.loaded_urls)

    def test_client_reads_authoritative_files_from_config_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            config_dir = repo_root / "config"
            config_dir.mkdir()
            (config_dir / "gem_description.txt").write_text(
                "Configured description\n", encoding="utf-8"
            )
            (config_dir / "gem_instructions.md").write_text(
                "Configured instructions\n", encoding="utf-8"
            )
            config = SimpleNamespace(
                gem_url="https://gemini.google.com/gem/test",
                gem_edit_url="https://gemini.google.com/gems/edit/test",
                ui_timeout_seconds=1,
                response_timeout_seconds=1,
                repo_root=repo_root,
                gem_name="Configured name",
                model_preference_patterns=(r"pro",),
                allow_unknown_model_fallback=True,
            )
            client = GeminiClient(Mock(), config)
            client.editor = Mock()

            client.configure_gem()

        client.editor.synchronize_configuration.assert_called_once_with(
            "Configured name",
            "Configured description",
            "Configured instructions",
        )

    def test_client_rejects_missing_project_gem_files(self):
        with tempfile.TemporaryDirectory() as directory:
            config = SimpleNamespace(
                gem_url="https://gemini.google.com/gem/test",
                gem_edit_url="https://gemini.google.com/gems/edit/test",
                ui_timeout_seconds=1,
                response_timeout_seconds=1,
                repo_root=Path(directory),
                gem_name="Configured name",
                model_preference_patterns=(r"pro",),
                allow_unknown_model_fallback=True,
            )
            client = GeminiClient(Mock(), config)
            client.editor = Mock()

            with self.assertRaisesRegex(UiContractError, "config/gem_description.txt"):
                client.configure_gem()


if __name__ == "__main__":
    unittest.main()

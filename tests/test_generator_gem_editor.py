import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app_generator.gemini.conversation import GemConversationPage
from app_generator.gemini.editor import GemEditorPage, is_placeholder
from app_generator.prompts import gem_description, gem_instructions


class GeneratorGemEditorTests(unittest.TestCase):
    class Element:
        def __init__(self, value=""):
            self.value = value
            self.text = value
            self.clicked = False

        def get_attribute(self, name):
            return self.value if name == "value" else None

        def click(self):
            self.clicked = True

        def send_keys(self, *values):
            value = values[-1]
            if isinstance(value, str) and len(value) > 1:
                self.value = value
                self.text = value

    class Driver:
        def __init__(self):
            self.refreshed = False

        def refresh(self):
            self.refreshed = True

    def test_placeholder_detection_is_idempotent(self):
        for value in ("", "  ", "to be included", " To   Be Included "):
            self.assertTrue(is_placeholder(value))
        self.assertFalse(is_placeholder("Meaningful manual instructions"))

    def test_reusable_gem_configuration_contains_attachment_contract(self):
        self.assertIn("calculator-free", gem_description())
        instructions = gem_instructions()
        self.assertIn("current conversation", instructions)
        self.assertIn("BEGIN_JSON", instructions)
        self.assertIn("Malay", instructions)
        self.assertNotIn("attached under Knowledge", instructions)

    def test_meaningful_existing_configuration_is_preserved_without_save(self):
        driver = self.Driver()
        page = GemEditorPage(driver, "https://gemini.google.com/gem/test", "https://gemini.google.com/gem/test/edit", 1)
        description = self.Element("Manual description")
        instructions = self.Element("Manual instructions")
        with patch("app_generator.gemini.editor.find_first", side_effect=[description, instructions]) as finder:
            self.assertFalse(page.initialize_configuration("Generated description", "Generated instructions"))
        self.assertEqual(2, finder.call_count)
        self.assertFalse(driver.refreshed)

    def test_placeholder_configuration_is_saved_and_reverified(self):
        driver = self.Driver()
        page = GemEditorPage(driver, "https://gemini.google.com/gem/test", "https://gemini.google.com/gem/test/edit", 1)
        description = self.Element("to be included")
        instructions = self.Element(" ")
        save = self.Element()
        with patch(
            "app_generator.gemini.editor.find_first",
            side_effect=[description, instructions, save, description, instructions],
        ):
            self.assertTrue(page.initialize_configuration("Generated description", "Generated instructions"))
        self.assertTrue(save.clicked)
        self.assertTrue(driver.refreshed)

    def test_conversation_attachment_uses_absolute_pdf_path(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pdf"
            source.write_bytes(b"%PDF-synthetic")
            add = self.Element()
            file_input = self.Element()
            label = self.Element("source.pdf")
            page = GemConversationPage(self.Driver(), "https://gemini.google.com/gem/test", 2, 2)
            with (
                patch("app_generator.gemini.conversation.find_first", return_value=add),
                patch("app_generator.gemini.conversation.find_all", side_effect=[[file_input], [label], []]),
            ):
                page.attach_pdf(source)
            self.assertTrue(add.clicked)
            self.assertEqual(str(source.resolve()), file_input.value)


if __name__ == "__main__":
    unittest.main()

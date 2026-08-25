import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app_generator.gemini.conversation import GemConversationPage
from app_generator.gemini.editor import GemEditorPage, is_placeholder
from app_generator.prompts import gem_description, gem_instructions


class GeneratorGemEditorTests(unittest.TestCase):
    class Element:
        def __init__(self, value="", on_click=None, attributes=None, stale=False):
            self.value = value
            self.text = value
            self.clicked = False
            self.on_click = on_click
            self.attributes = attributes or {}
            self.stale = stale

        def get_attribute(self, name):
            if self.stale:
                raise RuntimeError("synthetic stale element")
            return self.value if name == "value" else self.attributes.get(name)

        def is_displayed(self):
            if self.stale:
                raise RuntimeError("synthetic stale element")
            return True

        def click(self):
            self.clicked = True
            if self.on_click:
                self.on_click()

        def send_keys(self, *values):
            value = values[-1]
            if isinstance(value, str) and len(value) > 1:
                self.value = value
                self.text = value

    class Driver:
        def __init__(self):
            self.refreshed = False
            self.loaded_urls = []
            self.current_url = "https://gemini.google.com/gem/test/edit"

        def refresh(self):
            self.refreshed = True

        def get(self, url):
            self.loaded_urls.append(url)
            self.current_url = url

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

    def test_single_activity_prompt_forbids_other_batch_ids(self):
        from app_generator.prompts import activity_batch_prompt

        prompt = activity_batch_prompt(
            {},
            [{"id": "mcq-easy-1"}],
            source_location="synthetic",
        )
        self.assertIn("array must have length 1", prompt)
        self.assertIn("contain only the supplied ID mcq-easy-1", prompt)

    def test_activity_prompt_includes_only_referenced_analysis_entries(self):
        from app_generator.prompts import activity_batch_prompt

        analysis = {
            "prerequisites": [
                {"id": "needed-prerequisite", "description": "keep"},
                {"id": "unused-prerequisite", "description": "omit"},
            ],
            "misconceptionCatalogue": [
                {"id": "needed-misconception", "description": "keep"},
                {"id": "unused-misconception", "description": "omit"},
            ],
            "learningObjectives": ["large unrelated context"],
        }
        prompt = activity_batch_prompt(
            analysis,
            [{
                "id": "mcq-easy-1",
                "prerequisiteId": "needed-prerequisite",
                "misconceptions": ["needed-misconception"],
            }],
            source_location="synthetic",
        )
        self.assertIn("needed-prerequisite", prompt)
        self.assertIn("needed-misconception", prompt)
        self.assertNotIn("unused-prerequisite", prompt)
        self.assertNotIn("unused-misconception", prompt)
        self.assertNotIn("large unrelated context", prompt)

    def test_meaningful_existing_configuration_is_preserved_without_save(self):
        driver = self.Driver()
        page = GemEditorPage(driver, "https://gemini.google.com/gem/test", "https://gemini.google.com/gem/test/edit", 1)
        description = self.Element("Manual description")
        instructions = self.Element("Manual instructions")
        with patch("app_generator.gemini.editor.find_first", side_effect=[description, instructions]) as finder:
            self.assertFalse(page.initialize_configuration("Generated description", "Generated instructions"))
        self.assertEqual(2, finder.call_count)
        self.assertFalse(driver.refreshed)
        self.assertEqual([], driver.loaded_urls)

    def test_placeholder_configuration_is_saved_and_reverified(self):
        driver = self.Driver()
        page = GemEditorPage(driver, "https://gemini.google.com/gem/test", "https://gemini.google.com/gem/test/edit", 1)
        description = self.Element("to be included")
        instructions = self.Element(" ")
        save = self.Element(on_click=lambda: setattr(driver, "current_url", "https://gemini.google.com/gem/test"))
        name = self.Element("app content generator")
        with patch(
            "app_generator.gemini.editor.find_first",
            side_effect=[description, instructions, save, name, description, instructions],
        ):
            self.assertTrue(page.initialize_configuration("Generated description", "Generated instructions"))
        self.assertTrue(save.clicked)
        self.assertFalse(driver.refreshed)
        self.assertEqual(["https://gemini.google.com/gem/test/edit"], driver.loaded_urls)

    def test_conversation_attachment_uses_absolute_pdf_path(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pdf"
            source.write_bytes(b"%PDF-synthetic")
            add = self.Element()
            upload = self.Element()
            file_input = self.Element()
            preview = self.Element()
            ready = self.Element()
            page = GemConversationPage(self.Driver(), "https://gemini.google.com/gem/test", 2, 2)
            with (
                patch("app_generator.gemini.conversation.find_first", return_value=add),
                patch(
                    "app_generator.gemini.conversation.find_all",
                    side_effect=[[], [upload], [file_input], [preview], [], [ready]],
                ),
            ):
                page.attach_pdf(source)
            self.assertTrue(add.clicked)
            self.assertTrue(upload.clicked)
            self.assertEqual(str(source.resolve()), file_input.value)

    def test_conversation_attachment_opens_menu_before_using_existing_file_input(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pdf"
            source.write_bytes(b"%PDF-synthetic")
            add = self.Element()
            file_input = self.Element()
            preview = self.Element()
            ready = self.Element()
            page = GemConversationPage(self.Driver(), "https://gemini.google.com/gem/test", 2, 2)
            with (
                patch("app_generator.gemini.conversation.find_first", return_value=add),
                patch(
                    "app_generator.gemini.conversation.find_all",
                    side_effect=[[file_input], [preview], [], [ready]],
                ),
            ):
                page.attach_pdf(source)
            self.assertTrue(add.clicked)
            self.assertEqual(str(source.resolve()), file_input.value)

    def test_conversation_attachment_waits_until_spinner_is_replaced_by_text(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pdf"
            source.write_bytes(b"%PDF-synthetic")
            add = self.Element()
            file_input = self.Element()
            preview = self.Element()
            loading = self.Element()
            ready = self.Element()
            page = GemConversationPage(self.Driver(), "https://gemini.google.com/gem/test", 2, 2)
            with (
                patch("app_generator.gemini.conversation.find_first", return_value=add),
                patch(
                    "app_generator.gemini.conversation.find_all",
                    side_effect=[
                        [file_input],
                        [preview], [loading], [],
                        [preview], [], [ready],
                    ],
                ),
                patch("app_generator.gemini.conversation.time.sleep"),
            ):
                page.attach_pdf(source)
            self.assertEqual(str(source.resolve()), file_input.value)


if __name__ == "__main__":
    unittest.main()

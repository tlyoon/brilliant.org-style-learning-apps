import unittest
from unittest.mock import Mock, patch

from app_generator.gemini import selectors
from app_generator.gemini.editor import GemEditorPage


class GemEditorReadinessTests(unittest.TestCase):
    def test_current_gem_editor_controls_are_supported(self):
        self.assertIn(
            ("css selector", 'textarea[placeholder*="Describe your Gem"]'),
            selectors.DESCRIPTION_FIELD,
        )
        self.assertIn(
            (
                "css selector",
                'rich-textarea[data-test-id="instruction-rich-input-field"] '
                '[contenteditable="true"]',
            ),
            selectors.INSTRUCTIONS_FIELD,
        )

    def test_edit_url_uses_editor_content_instead_of_name_as_ready_signal(self):
        driver = Mock()
        page = GemEditorPage(
            driver,
            'https://gemini.google.com/gem/test',
            'https://gemini.google.com/gems/edit/test',
            1,
        )

        with (
            patch('app_generator.gemini.editor.find_all', return_value=[]),
            patch('app_generator.gemini.editor.find_first') as find_first,
        ):
            page.enter_editor()

        find_first.assert_called_once_with(driver, selectors.EDITOR_FIELD, 1)


if __name__ == '__main__':
    unittest.main()

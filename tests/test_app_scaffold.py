import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
EXAMPLE = ROOT / "content" / "examples" / "conceptual-forces.json"
SECTION_1_1 = ROOT / "content" / "chapter-1" / "section-1-1" / "package.json"


class AppScaffoldTests(unittest.TestCase):
    def test_entrypoint_has_accessible_runtime_hooks(self):
        html = (APP / "index.html").read_text(encoding="utf-8")
        self.assertIn('name="viewport"', html)
        self.assertIn('aria-live="polite"', html)
        self.assertIn('aria-label="Language"', html)

    def test_player_requires_an_explicit_external_package(self):
        javascript = (APP / "app.js").read_text(encoding="utf-8")
        self.assertNotIn("content/chapter-1/section-1-1/package.json", javascript)
        self.assertIn("data-package-url", javascript)
        self.assertIn("loadPackage()", javascript)

    def test_entrypoint_identifies_the_review_prototype(self):
        html = (APP / "index.html").read_text(encoding="utf-8")
        self.assertIn("Review prototype", html)
        self.assertNotIn("Section 1.1", html)

    def test_existing_section_one_package_remains_in_review(self):
        package = json.loads(SECTION_1_1.read_text(encoding="utf-8"))
        self.assertEqual("review", package["status"])

    def test_player_does_not_use_inner_html(self):
        javascript = (APP / "app.js").read_text(encoding="utf-8")
        self.assertNotIn("innerHTML", javascript)
        self.assertIn("textContent", javascript)

    def test_example_is_original_conceptual_draft(self):
        package = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        self.assertEqual("draft", package["status"])
        self.assertEqual({"en", "ms", "zh"}, set(package["locales"]))
        self.assertGreaterEqual(len(package["activities"]), 3)
        for activity in package["activities"]:
            self.assertTrue(activity["calculatorFree"])
            self.assertFalse(activity["numericAnswerRequired"])
            self.assertTrue(activity["provenance"]["originalContent"])
            self.assertGreaterEqual(len(activity["answerKey"]["options"]), 2)


if __name__ == "__main__":
    unittest.main()

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
EXAMPLE = ROOT / "content" / "examples" / "conceptual-forces.json"


class AppScaffoldTests(unittest.TestCase):
    def test_entrypoint_has_accessible_runtime_hooks(self):
        html = (APP / "index.html").read_text(encoding="utf-8")
        self.assertIn('name="viewport"', html)
        self.assertIn('aria-live="polite"', html)
        self.assertIn('aria-label="Language"', html)

    def test_player_loads_external_package(self):
        javascript = (APP / "app.js").read_text(encoding="utf-8")
        self.assertIn("content/examples/conceptual-forces.json", javascript)
        self.assertIn("fetch(DEFAULT_PACKAGE)", javascript)

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

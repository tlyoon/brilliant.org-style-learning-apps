import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_content", ROOT / "scripts" / "validate_content.py")
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class ContentValidationTests(unittest.TestCase):
    def load(self, name):
        return json.loads((ROOT / "tests" / "fixtures" / name).read_text(encoding="utf-8"))

    def activity(self, index, atype, difficulty):
        localized = {"en": "Choose the conceptual relationship.", "ms": "Pilih hubungan konsep.", "zh": "选择概念关系。"}
        return {
            "id": f"activity-{index}", "type": atype, "difficulty": difficulty,
            "calculatorFree": True, "numericAnswerRequired": False,
            "objective": "Classify a relationship", "prompt": localized,
            "answerKey": {"correct": "a"}, "hints": [localized], "feedback": localized,
            "provenance": {"sourceLocation": "synthetic", "originalContent": True},
        }

    def test_valid_draft(self):
        self.assertEqual([], validator.validate_package(self.load("valid-draft.json")))

    def test_calculator_activity_is_rejected(self):
        errors = validator.validate_package(self.load("invalid-calculator.json"))
        self.assertTrue(any("calculator-free" in error for error in errors))
        self.assertTrue(any("numerical answer" in error for error in errors))

    def test_publishable_distribution(self):
        package = self.load("valid-draft.json")
        package["status"] = "publishable"
        package["activities"] = [
            self.activity(i, atype, difficulty)
            for i, (atype, difficulty) in enumerate(
                (atype, difficulty)
                for atype in ("mcq", "interactive")
                for difficulty in ("easy", "moderate", "challenging")
                for _ in range(3)
            )
        ]
        self.assertEqual([], validator.validate_package(package))


if __name__ == "__main__":
    unittest.main()


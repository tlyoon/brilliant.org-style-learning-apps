import importlib.util
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

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
            "answerKey": {
                "correct": "a",
                "options": [
                    {"id": "a", "label": localized},
                    {"id": "b", "label": localized},
                ],
            },
            "hints": [localized], "feedback": localized,
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

    def test_options_are_required_and_non_empty(self):
        for options in (None, []):
            with self.subTest(options=options):
                package = self.load("valid-draft.json")
                activity = self.activity(1, "mcq", "easy")
                if options is None:
                    del activity["answerKey"]["options"]
                else:
                    activity["answerKey"]["options"] = options
                package["activities"] = [activity]
                errors = validator.validate_package(package)
                self.assertTrue(any("options must be a non-empty array" in error for error in errors))

    def test_option_ids_are_required_and_unique(self):
        package = self.load("valid-draft.json")
        activity = self.activity(1, "mcq", "easy")
        activity["answerKey"]["options"][0].pop("id")
        activity["answerKey"]["options"].append(activity["answerKey"]["options"][1].copy())
        package["activities"] = [activity]
        errors = validator.validate_package(package)
        self.assertTrue(any("id must be non-empty" in error for error in errors))
        self.assertTrue(any("id is duplicated" in error for error in errors))

    def test_option_labels_require_all_locales(self):
        package = self.load("valid-draft.json")
        activity = self.activity(1, "mcq", "easy")
        activity["answerKey"]["options"][0]["label"]["ms"] = ""
        package["activities"] = [activity]
        errors = validator.validate_package(package)
        self.assertTrue(any("options[0].label.ms must be non-empty" in error for error in errors))

    def test_correct_answer_must_match_exactly_one_option(self):
        package = self.load("valid-draft.json")
        activity = self.activity(1, "mcq", "easy")
        activity["answerKey"]["correct"] = "missing"
        package["activities"] = [activity]
        errors = validator.validate_package(package)
        self.assertTrue(any("correct must match exactly one option ID" in error for error in errors))

    def test_invalid_locale_types_are_reported_without_throwing(self):
        for locales in (None, 7, {"en": True}, "en,ms,zh"):
            with self.subTest(locales=locales):
                package = self.load("valid-draft.json")
                package["locales"] = locales
                errors = validator.validate_package(package)
                self.assertTrue(any("locales must be an array" in error for error in errors))

    def test_main_continues_after_malformed_package(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            malformed = Path(directory) / "malformed.json"
            subsequent = Path(directory) / "subsequent.json"
            malformed.write_text(json.dumps({"locales": None}), encoding="utf-8")
            subsequent_package = self.load("valid-draft.json")
            subsequent_package["status"] = "invalid"
            subsequent.write_text(json.dumps(subsequent_package), encoding="utf-8")
            output = StringIO()
            with patch.object(validator, "package_paths", return_value=[malformed, subsequent]):
                with redirect_stdout(output):
                    result = validator.main()
            self.assertEqual(1, result)
            self.assertIn("malformed.json: locales must be an array", output.getvalue())
            self.assertIn("subsequent.json: invalid status", output.getvalue())

    def test_all_example_packages_remain_valid(self):
        for path in (ROOT / "content" / "examples").glob("*.json"):
            with self.subTest(path=path.name):
                package = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual([], validator.validate_package(package, path.name))

if __name__ == "__main__":
    unittest.main()


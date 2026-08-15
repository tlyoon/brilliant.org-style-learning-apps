import copy
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

    def activity(self, index, atype="mcq", difficulty="easy"):
        localized = {
            "en": "Choose the conceptual relationship.",
            "ms": "Pilih hubungan konsep.",
            "zh": "选择概念关系。",
        }
        return {
            "id": f"activity-{index}", "type": atype, "difficulty": difficulty,
            "calculatorFree": True, "numericAnswerRequired": False,
            "objective": "Classify a relationship", "prompt": copy.deepcopy(localized),
            "answerKey": {
                "correct": "a",
                "options": [
                    {"id": "a", "label": copy.deepcopy(localized)},
                    {"id": "b", "label": copy.deepcopy(localized)},
                ],
            },
            "hints": [copy.deepcopy(localized)], "feedback": copy.deepcopy(localized),
            "misconceptions": ["confuses-related-concepts"],
            "provenance": {"sourceLocation": "synthetic", "originalContent": True},
        }

    def package_with_activity(self):
        package = self.load("valid-draft.json")
        package["activities"] = [self.activity(1)]
        return package

    def test_valid_draft(self):
        self.assertEqual([], validator.validate_package(self.load("valid-draft.json")))

    def test_schema_rejects_empty_top_level_fields(self):
        cases = {
            "packageId": "",
            "chapter": "",
            "learningObjectives": [],
            "sourceManifest": "",
        }
        for field, value in cases.items():
            with self.subTest(field=field):
                package = self.load("valid-draft.json")
                package[field] = value
                errors = validator.validate_package(package)
                self.assertTrue(any(f"package.{field}" in error for error in errors), errors)

    def test_schema_rejects_missing_required_fields(self):
        package = self.load("valid-draft.json")
        del package["chapter"]
        errors = validator.validate_package(package)
        self.assertTrue(any("'chapter' is a required property" in error for error in errors))

    def test_schema_rejects_invalid_nested_structures(self):
        package = self.package_with_activity()
        package["activities"][0]["prompt"] = ["not", "localized"]
        errors = validator.validate_package(package)
        self.assertTrue(any("package.activities[0].prompt" in error for error in errors))

    def test_schema_rejects_unexpected_fields(self):
        for target in ("package", "activity"):
            with self.subTest(target=target):
                package = self.package_with_activity()
                container = package if target == "package" else package["activities"][0]
                container["unexpected"] = True
                errors = validator.validate_package(package)
                self.assertTrue(any("Additional properties are not allowed" in error for error in errors))

    def test_calculator_flags_are_rejected_by_schema(self):
        errors = validator.validate_package(self.load("invalid-calculator.json"))
        self.assertTrue(any("calculatorFree" in error for error in errors))
        self.assertTrue(any("numericAnswerRequired" in error for error in errors))

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
                package = self.package_with_activity()
                if options is None:
                    del package["activities"][0]["answerKey"]["options"]
                else:
                    package["activities"][0]["answerKey"]["options"] = options
                errors = validator.validate_package(package)
                self.assertTrue(any("answerKey" in error and "options" in error for error in errors))

    def test_option_ids_are_required_and_unique(self):
        package = self.package_with_activity()
        package["activities"][0]["answerKey"]["options"][0].pop("id")
        errors = validator.validate_package(package)
        self.assertTrue(any("'id' is a required property" in error for error in errors))

        package = self.package_with_activity()
        duplicate = copy.deepcopy(package["activities"][0]["answerKey"]["options"][1])
        duplicate["label"]["en"] = "A distinct label with the same ID."
        package["activities"][0]["answerKey"]["options"].append(duplicate)
        errors = validator.validate_package(package)
        self.assertTrue(any("id is duplicated" in error for error in errors))

    def test_option_labels_require_all_locales(self):
        package = self.package_with_activity()
        package["activities"][0]["answerKey"]["options"][0]["label"]["ms"] = ""
        errors = validator.validate_package(package)
        self.assertTrue(any("options[0].label.ms" in error for error in errors))

    def test_correct_answer_must_match_exactly_one_option(self):
        package = self.package_with_activity()
        package["activities"][0]["answerKey"]["correct"] = "missing"
        errors = validator.validate_package(package)
        self.assertTrue(any("correct must match exactly one option ID" in error for error in errors))

    def test_invalid_locale_types_are_reported_without_throwing(self):
        for locales in (None, 7, {"en": True}, "en,ms,zh"):
            with self.subTest(locales=locales):
                package = self.load("valid-draft.json")
                package["locales"] = locales
                errors = validator.validate_package(package)
                self.assertTrue(any("package.locales" in error and "array" in error for error in errors))

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
            self.assertIn("malformed.json", output.getvalue())
            self.assertIn("subsequent.json", output.getvalue())

    def test_numerical_requests_are_rejected_in_every_locale(self):
        prohibited = {
            "en": "Calculate the numerical value.",
            "ms": "Kirakan nilai berangka.",
            "zh": "计算这个数值。",
        }
        for locale, prompt in prohibited.items():
            with self.subTest(locale=locale):
                package = self.package_with_activity()
                package["activities"][0]["prompt"][locale] = prompt
                errors = validator.validate_package(package)
                self.assertTrue(any(f"prompt.{locale}" in error for error in errors), errors)

    def test_valid_conceptual_multilingual_prompts_pass(self):
        self.assertEqual([], validator.validate_package(self.package_with_activity()))

    def test_all_example_packages_remain_valid(self):
        for path in (ROOT / "content" / "examples").glob("*.json"):
            with self.subTest(path=path.name):
                package = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual([], validator.validate_package(package, path.name))

    def test_referenced_manifest_must_exist(self):
        package = self.load("valid-draft.json")
        package["sourceManifest"] = "content/source-manifests/missing.json"
        errors = validator.validate_package(package)
        self.assertTrue(any("referenced manifest does not exist" in error for error in errors))

    def test_referenced_manifest_must_be_valid_json(self):
        package = self.load("valid-draft.json")
        package["sourceManifest"] = "content/source-manifests/malformed.json"
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            manifest_root = Path(directory)
            (manifest_root / "malformed.json").write_text("{not json", encoding="utf-8")
            with patch.object(validator, "MANIFEST_ROOT", manifest_root):
                errors = validator.validate_package(package)
        self.assertTrue(any("cannot read a valid JSON manifest" in error for error in errors))

    def test_referenced_manifest_requires_complete_meaningful_metadata(self):
        base_manifest = json.loads(
            (ROOT / "content" / "source-manifests" / "source-manifest.example.json").read_text(encoding="utf-8")
        )
        cases = {
            "missing": {key: value for key, value in base_manifest.items() if key != "reviewer"},
            "empty": {**base_manifest, "reviewer": ""},
            "todo": {**base_manifest, "reviewer": "TODO"},
            "tbd": {**base_manifest, "edition": "TBD"},
            "generic-example": {**base_manifest, "heading": "Generic examples"},
        }
        for name, manifest in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
                manifest_root = Path(directory)
                (manifest_root / "candidate.json").write_text(json.dumps(manifest), encoding="utf-8")
                package = self.load("valid-draft.json")
                package["sourceManifest"] = "content/source-manifests/candidate.json"
                with patch.object(validator, "MANIFEST_ROOT", manifest_root):
                    errors = validator.validate_package(package)
                self.assertNotEqual([], errors)

    def test_valid_referenced_manifest_passes(self):
        package = self.load("valid-draft.json")
        self.assertEqual([], validator.validate_package(package))

    def test_misconception_targets_are_required_and_meaningful(self):
        for value in (None, [], [""], ["   "], ["todo"], ["generic misconception"]):
            with self.subTest(value=value):
                package = self.package_with_activity()
                if value is None:
                    del package["activities"][0]["misconceptions"]
                else:
                    package["activities"][0]["misconceptions"] = value
                errors = validator.validate_package(package)
                self.assertTrue(any("misconceptions" in error for error in errors), errors)

if __name__ == "__main__":
    unittest.main()

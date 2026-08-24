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
SECTION_1_1 = ROOT / "content" / "chapter-1" / "section-1-1" / "package.json"
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
        package = json.loads(SECTION_1_1.read_text(encoding="utf-8"))
        package["status"] = "publishable"
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

    def test_numerical_requests_are_rejected_in_interaction_labels(self):
        package = json.loads(SECTION_1_1.read_text(encoding="utf-8"))
        interactive = next(activity for activity in package["activities"] if activity["type"] == "interactive")
        prohibited = {
            "en": "Calculate the numerical value.",
            "ms": "Kirakan nilai berangka.",
            "zh": "计算这个数值。",
        }
        for locale, label in prohibited.items():
            with self.subTest(locale=locale):
                candidate = copy.deepcopy(package)
                changed = next(activity for activity in candidate["activities"] if activity["id"] == interactive["id"])
                changed["interaction"]["items"][0]["label"][locale] = label
                errors = validator.validate_package(candidate)
                self.assertTrue(
                    any(f"interaction.items[0].label.{locale}" in error for error in errors),
                    errors,
                )

    def test_valid_conceptual_multilingual_prompts_pass(self):
        self.assertEqual([], validator.validate_package(self.package_with_activity()))

    def test_valid_draft_interactive_does_not_require_review_catalogue(self):
        package = self.package_with_activity()
        activity = package["activities"][0]
        activity["type"] = "interactive"
        activity.pop("answerKey")
        activity["interactionMode"] = "selection"
        activity["interaction"] = {
            "items": [
                {"id": "a", "label": copy.deepcopy(activity["prompt"])},
                {"id": "b", "label": copy.deepcopy(activity["feedback"])},
                {"id": "c", "label": copy.deepcopy(activity["hints"][0])},
            ],
            "correctSelections": ["a", "c"],
        }
        activity["diagnosticRules"] = [{
            "misconception": "confuses-related-concepts",
            "condition": {"kind": "selection", "itemId": "b", "selected": True},
        }]
        self.assertEqual([], validator.validate_package(package))

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

    def test_section_1_1_pack_is_complete_and_valid(self):
        package = json.loads(SECTION_1_1.read_text(encoding="utf-8"))
        self.assertEqual([], validator.validate_package(package, "section-1-1"))
        self.assertEqual("review", package["status"])
        self.assertEqual(18, len(package["activities"]))
        distribution = {
            (activity["type"], activity["difficulty"])
            for activity in package["activities"]
        }
        self.assertEqual(
            {
                (activity_type, difficulty)
                for activity_type in ("mcq", "interactive")
                for difficulty in ("easy", "moderate", "challenging")
            },
            distribution,
        )
        for activity_type in ("mcq", "interactive"):
            for difficulty in ("easy", "moderate", "challenging"):
                count = sum(
                    activity["type"] == activity_type and activity["difficulty"] == difficulty
                    for activity in package["activities"]
                )
                self.assertEqual(3, count, (activity_type, difficulty))

    def test_section_1_1_pack_has_review_ready_learning_support(self):
        package = json.loads(SECTION_1_1.read_text(encoding="utf-8"))
        catalogue = {item["id"] for item in package["misconceptionCatalogue"]}
        prerequisites = {item["id"] for item in package["prerequisites"]}
        self.assertTrue(package["evidencePolicy"]["preserveFirstAttempt"])
        self.assertTrue(package["evidencePolicy"]["assistedSuccessSeparate"])
        for activity in package["activities"]:
            self.assertGreaterEqual(len(activity["hints"]), 2)
            self.assertEqual({"en", "ms", "zh"}, set(activity["answerLogic"]))
            self.assertEqual({"en", "ms", "zh"}, set(activity["explanation"]))
            self.assertEqual({"en", "ms", "zh"}, set(activity["accessibilityText"]))
            self.assertIn(activity["prerequisiteRecovery"]["prerequisiteId"], prerequisites)
            self.assertTrue(set(activity["misconceptions"]).issubset(catalogue))
            if activity["type"] == "interactive":
                self.assertIn("interactionMode", activity)
                self.assertIn("interaction", activity)
                self.assertNotIn("answerKey", activity)
                self.assertGreaterEqual(len(activity["interaction"]["items"]), 3)
            else:
                self.assertNotIn("interactionMode", activity)
                self.assertIn("answerKey", activity)
                self.assertNotIn("interaction", activity)

    def test_review_rejects_single_choice_disguised_as_interactive(self):
        package = json.loads(SECTION_1_1.read_text(encoding="utf-8"))
        interactive = next(activity for activity in package["activities"] if activity["type"] == "interactive")
        del interactive["interaction"]
        del interactive["interactionMode"]
        interactive["answerKey"] = copy.deepcopy(package["activities"][0]["answerKey"])
        errors = validator.validate_package(package)
        self.assertTrue(any("interaction" in error for error in errors), errors)

    def test_interaction_solution_references_are_complete(self):
        package = json.loads(SECTION_1_1.read_text(encoding="utf-8"))
        classification = next(
            activity for activity in package["activities"]
            if activity.get("interactionMode") == "classification"
        )
        classification["interaction"]["placements"][0]["targetId"] = "missing-target"
        errors = validator.validate_package(package)
        self.assertTrue(any("targetId must reference a declared target" in error for error in errors), errors)

    def test_schema_enforces_mode_specific_interaction_shapes(self):
        package = json.loads(SECTION_1_1.read_text(encoding="utf-8"))
        cases = {
            "classification": ("correctOrder", ["shared-light-procedure", "personal-hand-span", "stretching-ribbon"]),
            "ordering": ("targets", [{"id": "extra", "label": {"en": "extra", "ms": "tambahan", "zh": "额外"}}]),
            "selection": ("placements", [
                {"itemId": "person-dependent", "targetId": "missing"},
                {"itemId": "reference-drifts", "targetId": "missing"},
                {"itemId": "shared-label-not-size", "targetId": "missing"},
            ]),
        }
        for mode, (field, value) in cases.items():
            with self.subTest(mode=mode):
                candidate = copy.deepcopy(package)
                activity = next(item for item in candidate["activities"] if item.get("interactionMode") == mode)
                activity["interaction"][field] = value
                errors = validator.validate_package(candidate)
                self.assertTrue(any("interaction" in error for error in errors), errors)

    def test_diagnostic_rules_must_reference_incorrect_responses(self):
        package = json.loads(SECTION_1_1.read_text(encoding="utf-8"))
        classification = next(
            activity for activity in package["activities"]
            if activity.get("interactionMode") == "classification"
        )
        classification["diagnosticRules"][0]["condition"] = {
            "kind": "placement", "itemId": "personal-hand-span", "targetId": "unsuitable",
        }
        errors = validator.validate_package(package)
        self.assertTrue(any("must describe an incorrect placement" in error for error in errors), errors)

    def test_ordering_diagnostic_with_item_missing_from_solution_reports_error(self):
        package = json.loads(SECTION_1_1.read_text(encoding="utf-8"))
        ordering = next(
            activity for activity in package["activities"]
            if activity.get("interactionMode") == "ordering"
        )
        ordering["interaction"]["correctOrder"] = []
        errors = validator.validate_package(package)
        self.assertTrue(any("correctOrder" in error for error in errors), errors)

    def test_schema_version_marks_interaction_contract(self):
        package = self.load("valid-draft.json")
        package["schemaVersion"] = "1.0"
        errors = validator.validate_package(package)
        self.assertTrue(any("schemaVersion" in error and "1.1" in error for error in errors), errors)

    def test_review_package_requires_extended_authoring_fields(self):
        package = json.loads(SECTION_1_1.read_text(encoding="utf-8"))
        for field in ("prerequisites", "misconceptionCatalogue", "evidencePolicy", "reviewRecord"):
            with self.subTest(field=field):
                candidate = copy.deepcopy(package)
                del candidate[field]
                errors = validator.validate_package(candidate)
                self.assertTrue(any(field in error for error in errors), errors)

    def test_review_record_may_resolve_inside_any_chapter(self):
        package = self.load("valid-draft.json")
        package["reviewRecord"] = "content/chapter-8/section-8-1/review-record.md"
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            content_root = Path(directory) / "content"
            record = content_root / "chapter-8" / "section-8-1" / "review-record.md"
            record.parent.mkdir(parents=True)
            record.write_text("# Synthetic review record\n", encoding="utf-8")
            with patch.object(validator, "ROOT", Path(directory)), patch.object(validator, "CONTENT", content_root):
                errors = validator.validate_package(package)
        self.assertEqual([], errors)

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

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app_generator.errors import ResponseContractError
from app_generator.generation.assembler import assemble_package, validate_activity_batch, validate_plan
from app_generator.generation.extraction import parse_json_response
from app_generator.generation.protocol import GenerationProtocol
from app_generator.runtime.run_context import RunContext


class GeneratorProtocolTests(unittest.TestCase):
    class Conversation:
        def __init__(self, responses):
            self.responses = iter(responses)

        def ask(self, prompt):
            return next(self.responses)

    def plan(self):
        activities = []
        for kind in ("mcq", "interactive"):
            for difficulty in ("easy", "moderate", "challenging"):
                for index in range(3):
                    activities.append({
                        "id": f"{kind}-{difficulty}-{index}",
                        "type": kind,
                        "difficulty": difficulty,
                        "objective": f"Objective {kind} {difficulty} {index}",
                        "misconceptions": ["misconception-one"],
                        "prerequisiteId": "prerequisite-one",
                        "interactionMode": None if kind == "mcq" else "classification",
                    })
        return {"activities": activities}

    @staticmethod
    def validate_mock_batch(batch, planned):
        activities = batch.get("activities", []) if isinstance(batch, dict) else []
        if len(activities) != len(planned):
            raise ResponseContractError("wrong mock batch length")
        return activities

    def test_json_contract_accepts_sentinels_and_rejects_prose(self):
        self.assertEqual({"ok": True}, parse_json_response('BEGIN_JSON\n{"ok": true}\nEND_JSON'))
        with self.assertRaises(ResponseContractError):
            parse_json_response('Here it is\nBEGIN_JSON\n{"ok": true}\nEND_JSON')
        with self.assertRaises(ResponseContractError):
            parse_json_response('BEGIN_JSON\n{"ok": true}')

    def test_json_contract_normalizes_literal_control_characters_inside_strings(self):
        parsed = parse_json_response('BEGIN_JSON\n{"line": "first\nsecond"}\nEND_JSON')
        self.assertEqual({"line": "first\nsecond"}, parsed)
        self.assertEqual('{"line": "first\\nsecond"}', json.dumps(parsed))

    def test_json_contract_still_rejects_other_malformed_json(self):
        with self.assertRaises(ResponseContractError):
            parse_json_response('BEGIN_JSON\n{"broken": ]}\nEND_JSON')

    def test_source_analysis_contract_rejects_wrong_valid_json_shape(self):
        wrong = {
            "packageId": "chapter-8-section-8-1",
            "activities": [{} for _ in range(18)],
        }
        self.assertFalse(GenerationProtocol._valid_source_analysis(wrong))
        valid = {
            "sectionTitle": "Conceptual Energy Transfers",
            "learningObjectives": ["Objective"],
            "prerequisites": [{
                "id": "prerequisite",
                "description": {"en": "Description", "ms": "Huraian", "zh": "Description"},
                "recovery": {"en": "Review", "ms": "Ulang kaji", "zh": "Review"},
            }],
            "misconceptionCatalogue": [{
                "id": "misconception",
                "description": {"en": "Description", "ms": "Huraian", "zh": "Description"},
            }],
            "scopeNotes": {"includedConcepts": ["included"], "excludedConcepts": ["excluded"]},
        }
        self.assertTrue(GenerationProtocol._valid_source_analysis(valid))

    def test_source_analysis_contract_rejects_prerequisite_without_recovery(self):
        analysis = {
            "sectionTitle": "Conceptual Energy Transfers",
            "learningObjectives": ["Objective"],
            "prerequisites": [{
                "id": "prerequisite",
                "description": {"en": "Description", "ms": "Huraian", "zh": "Description"},
            }],
            "misconceptionCatalogue": [{
                "id": "misconception",
                "description": {"en": "Description", "ms": "Huraian", "zh": "Description"},
            }],
            "scopeNotes": {"includedConcepts": ["included"], "excludedConcepts": ["excluded"]},
        }
        self.assertFalse(GenerationProtocol._valid_source_analysis(analysis))

    def test_invalid_cached_source_analysis_discards_dependent_parsed_stages(self):
        invalid = {
            "sectionTitle": "Conceptual Energy Transfers",
            "learningObjectives": ["Objective"],
            "prerequisites": [{
                "id": "prerequisite",
                "description": {"en": "Description", "ms": "Huraian", "zh": "Description"},
            }],
            "misconceptionCatalogue": [{
                "id": "misconception",
                "description": {"en": "Description", "ms": "Huraian", "zh": "Description"},
            }],
            "scopeNotes": {"includedConcepts": ["included"], "excludedConcepts": ["excluded"]},
        }
        corrected = {
            **invalid,
            "prerequisites": [{
                **invalid["prerequisites"][0],
                "recovery": {"en": "Review", "ms": "Ulang kaji", "zh": "Review"},
            }],
        }
        response = "BEGIN_JSON\n" + json.dumps(corrected) + "\nEND_JSON"
        with tempfile.TemporaryDirectory() as directory:
            context = RunContext.create(Path(directory))
            context.save_stage("source-analysis", invalid)
            context.save_stage("activity-plan", {"activities": []})
            protocol = GenerationProtocol(self.Conversation([response]), context)

            self.assertEqual(corrected, protocol._source_analysis({}))
            self.assertIsNone(context.load_stage("activity-plan"))

    def test_source_analysis_removes_fields_outside_package_schema(self):
        analysis = {
            "learningObjectives": ["Objective"],
            "prerequisites": [{
                "id": "prerequisite",
                "title": {"en": "Title", "ms": "Tajuk", "zh": "标题"},
                "description": {"en": "Description", "ms": "Huraian", "zh": "描述"},
                "recovery": {"en": "Review", "ms": "Ulang kaji", "zh": "复习"},
            }],
            "misconceptionCatalogue": [{
                "id": "misconception",
                "title": {"en": "Title", "ms": "Tajuk", "zh": "标题"},
                "description": {"en": "Description", "ms": "Huraian", "zh": "描述"},
            }],
            "scopeNotes": {"includedConcepts": ["included"], "excludedConcepts": ["excluded"]},
        }
        normalized = GenerationProtocol._normalize_source_analysis(analysis)
        self.assertNotIn("title", normalized["prerequisites"][0])
        self.assertNotIn("title", normalized["misconceptionCatalogue"][0])
        self.assertIn("title", analysis["prerequisites"][0])

    def test_plan_distribution_and_stable_assembly(self):
        plan = self.plan()
        validate_plan(plan)
        analysis = {
            "learningObjectives": ["Understand the concept"],
            "prerequisites": [{"id": "prerequisite-one"}],
            "misconceptionCatalogue": [{"id": "misconception-one"}],
        }
        generated = []
        for item in reversed(plan["activities"]):
            activity = {
                "id": item["id"], "type": item["type"], "difficulty": item["difficulty"],
                "objective": item["objective"], "misconceptions": item["misconceptions"],
                "prerequisiteRecovery": {"prerequisiteId": item["prerequisiteId"]},
            }
            if item["interactionMode"] is not None:
                activity["interactionMode"] = item["interactionMode"]
            generated.append(activity)
        config = SimpleNamespace(
            package_id="chapter-8-section-8-1", chapter="Chapter", subchapter="Topic",
            review_relative_path=Path("content/chapter-8/section-8-1/review-record.md"),
            manifest_relative_path=Path("content/source-manifests/chapter-8-section-8-1.json"),
        )
        package = assemble_package(config, analysis, plan, [{"activities": generated}])
        self.assertEqual([item["id"] for item in plan["activities"]], [item["id"] for item in package["activities"]])
        self.assertEqual("draft", package["status"])

    def test_plan_normalizes_embedded_reference_objects_to_ids(self):
        plan = self.plan()
        plan["activities"][0]["misconceptions"] = [{"id": "misconception-one"}]
        plan["activities"][0]["prerequisiteId"] = {"id": "prerequisite-one"}
        normalized = validate_plan(plan)
        self.assertEqual(["misconception-one"], normalized[0]["misconceptions"])
        self.assertEqual("prerequisite-one", normalized[0]["prerequisiteId"])

    def test_plan_uses_supplied_fallback_for_null_prerequisite(self):
        plan = self.plan()
        plan["activities"][0]["prerequisiteId"] = None
        normalized = validate_plan(plan, fallback_prerequisite_id="prerequisite-one")
        self.assertEqual("prerequisite-one", normalized[0]["prerequisiteId"])

    def test_assembly_rejects_changes_to_planned_references(self):
        plan = self.plan()
        first = plan["activities"][0]
        generated = [{
            "id": item["id"], "type": item["type"], "difficulty": item["difficulty"],
            "objective": item["objective"], "misconceptions": item["misconceptions"],
            "prerequisiteRecovery": {"prerequisiteId": item["prerequisiteId"]},
            **({"interactionMode": item["interactionMode"]} if item["interactionMode"] else {}),
        } for item in plan["activities"]]
        generated[0]["misconceptions"] = ["renamed"]
        config = SimpleNamespace(
            package_id="chapter-8-section-8-1", chapter="Chapter", subchapter="Topic",
            review_relative_path=Path("content/chapter-8/section-8-1/review-record.md"),
            manifest_relative_path=Path("content/source-manifests/chapter-8-section-8-1.json"),
        )
        analysis = {
            "learningObjectives": ["Objective"], "prerequisites": [{"id": "prerequisite-one"}],
            "misconceptionCatalogue": [{"id": "misconception-one"}],
        }
        with self.assertRaises(ResponseContractError):
            assemble_package(config, analysis, plan, [{"activities": generated}])

    def test_activity_batch_rejects_alternate_recovery_shape(self):
        item = self.plan()["activities"][0]
        alternate = {
            "activities": [{
                "id": item["id"],
                "type": item["type"],
                "difficulty": item["difficulty"],
                "objective": item["objective"],
                "misconceptions": item["misconceptions"],
                "prerequisiteId": item["prerequisiteId"],
                "prerequisiteRecovery": {"en": "Review", "ms": "Ulang kaji", "zh": "复习"},
            }],
        }
        with self.assertRaisesRegex(ResponseContractError, "planned prerequisite"):
            validate_activity_batch(alternate, [item])

    def test_activity_batch_normalizes_item_wrappers_in_selection_solution(self):
        item = {
            **self.plan()["activities"][9],
            "interactionMode": "selection",
        }
        localized = {"en": "Text", "ms": "Teks", "zh": "文本"}
        activity = {
            "id": item["id"],
            "type": "interactive",
            "difficulty": item["difficulty"],
            "calculatorFree": True,
            "numericAnswerRequired": False,
            "objective": item["objective"],
            "prompt": localized,
            "hints": [localized, localized],
            "feedback": localized,
            "answerLogic": localized,
            "explanation": localized,
            "interactionMode": "selection",
            "interaction": {
                "items": [
                    {"id": f"item-{index}", "label": localized}
                    for index in range(3)
                ],
                "correctSelections": [{"itemId": "item-0"}, {"itemId": "item-1"}],
            },
            "diagnosticRules": [{
                "misconception": "misconception-one",
                "condition": {"kind": "selection", "itemId": "item-2", "selected": True},
            }],
            "prerequisiteRecovery": {
                "prerequisiteId": "prerequisite-one",
                "prompt": localized,
            },
            "misconceptions": ["misconception-one"],
            "accessibilityText": localized,
            "provenance": {"sourceLocation": "synthetic", "originalContent": True},
        }
        validate_activity_batch({"activities": [activity]}, [item])
        self.assertEqual(
            ["item-0", "item-1"],
            activity["interaction"]["correctSelections"],
        )

    def test_truncated_batch_falls_back_to_single_activities_and_retains_raw_response(self):
        planned = self.plan()["activities"][:3]
        responses = ["BEGIN_JSON\n{", "BEGIN_JSON\n{", *[
            'BEGIN_JSON\n{"activities": [{"id": "' + item["id"] + '"}]}\nEND_JSON'
            for item in planned
        ]]
        with tempfile.TemporaryDirectory() as directory:
            context = RunContext.create(Path(directory))
            protocol = GenerationProtocol(self.Conversation(responses), context)
            with patch(
                "app_generator.generation.protocol.validate_activity_batch",
                side_effect=self.validate_mock_batch,
            ):
                batch = protocol._activity_batch("mcq-easy", {}, planned, "synthetic")
            self.assertEqual([item["id"] for item in planned], [item["id"] for item in batch["activities"]])
            self.assertTrue((context.batches / "mcq-easy.response.txt").is_file())
            self.assertTrue((context.batches / "mcq-easy.json").is_file())

    def test_single_activity_fallback_regenerates_invalid_cached_stage(self):
        planned = self.plan()["activities"][:1]
        item = planned[0]
        responses = [
            'BEGIN_JSON\n{"activities": [{"id": "' + item["id"] + '"}]}\nEND_JSON',
        ]
        with tempfile.TemporaryDirectory() as directory:
            context = RunContext.create(Path(directory))
            stage_name = f"mcq-easy-{item['id']}"
            context.save_stage(stage_name, {"activities": [{}, {}, {}]})
            protocol = GenerationProtocol(self.Conversation(responses), context)
            with patch(
                "app_generator.generation.protocol.validate_activity_batch",
                side_effect=self.validate_mock_batch,
            ):
                batch = protocol._activity_batch("mcq-easy", {}, planned, "synthetic")
            self.assertEqual([item["id"]], [entry["id"] for entry in batch["activities"]])
            self.assertEqual(1, len(context.load_stage(stage_name)["activities"]))

    def test_single_activity_fallback_retries_json_parse_failure(self):
        planned = self.plan()["activities"][:1]
        item = planned[0]
        responses = [
            'BEGIN_JSON\n{"activities": [{"broken": "\\invalid"}]}\nEND_JSON',
            'BEGIN_JSON\n{"activities": [{"id": "' + item["id"] + '"}]}\nEND_JSON',
        ]
        with tempfile.TemporaryDirectory() as directory:
            context = RunContext.create(Path(directory))
            stage_name = f"mcq-easy-{item['id']}"
            context.save_stage(stage_name, {"activities": [{}, {}, {}]})
            protocol = GenerationProtocol(self.Conversation(responses), context)
            with patch(
                "app_generator.generation.protocol.validate_activity_batch",
                side_effect=self.validate_mock_batch,
            ):
                batch = protocol._activity_batch("mcq-easy", {}, planned, "synthetic")
            self.assertEqual(item["id"], batch["activities"][0]["id"])

    def test_audit_stage_discards_wrong_shape_and_retries(self):
        responses = [
            "BEGIN_JSON\n{}\nEND_JSON",
            'BEGIN_JSON\n{"findings": []}\nEND_JSON',
        ]
        with tempfile.TemporaryDirectory() as directory:
            context = RunContext.create(Path(directory))
            protocol = GenerationProtocol(self.Conversation(responses), context)
            audit = protocol._audit_stage("audit", lambda: "prompt")
            self.assertEqual({"findings": []}, audit)
            self.assertEqual({"findings": []}, context.load_stage("audit"))

    def test_repair_contract_rejects_internal_id_renames(self):
        original = {
            "id": "activity", "type": "mcq", "difficulty": "easy", "objective": "Objective",
            "misconceptions": ["misconception"],
            "prerequisiteRecovery": {"prerequisiteId": "prerequisite"},
            "answerKey": {"options": [{"id": "a"}, {"id": "b"}]},
        }
        replacement = {**original, "answerKey": {"options": [{"id": "a"}, {"id": "renamed"}]}}
        with self.assertRaises(ValueError):
            GenerationProtocol._assert_stable_activity_contract(original, replacement)

    def test_repair_contract_allows_additive_internal_id(self):
        original = {
            "id": "activity", "type": "interactive", "difficulty": "easy",
            "objective": "Objective", "interactionMode": "matching",
            "misconceptions": ["misconception"],
            "prerequisiteRecovery": {"prerequisiteId": "prerequisite"},
            "interaction": {"items": [{"id": "a"}, {"id": "b"}]},
        }
        replacement = {
            **original,
            "interaction": {"items": [{"id": "a"}, {"id": "b"}, {"id": "c"}]},
        }
        GenerationProtocol._assert_stable_activity_contract(original, replacement)

    def test_repair_rejects_ordering_solution_that_omits_item_ids(self):
        activity = {
            "id": "ordering", "type": "interactive", "interactionMode": "ordering",
            "interaction": {
                "items": [{"id": "first"}, {"id": "second"}, {"id": "third"}],
                "correctOrder": ["first", "second"],
            },
        }
        with self.assertRaisesRegex(ResponseContractError, "every item ID"):
            GenerationProtocol._assert_complete_interaction_solution(activity)

    def test_repair_stage_discards_identity_change_and_retries(self):
        item = self.plan()["activities"][0]
        original = {
            "id": item["id"], "type": item["type"], "difficulty": item["difficulty"],
            "objective": item["objective"], "misconceptions": item["misconceptions"],
            "prerequisiteRecovery": {"prerequisiteId": item["prerequisiteId"]},
        }
        wrong = {**original, "id": "changed-id"}
        corrected = dict(original)
        responses = [
            "BEGIN_JSON\n" + json.dumps(wrong) + "\nEND_JSON",
            "BEGIN_JSON\n" + json.dumps(corrected) + "\nEND_JSON",
        ]
        with tempfile.TemporaryDirectory() as directory:
            context = RunContext.create(Path(directory))
            protocol = GenerationProtocol(self.Conversation(responses), context)
            validated_plans = []
            with patch(
                "app_generator.generation.protocol.validate_activity_batch",
                side_effect=lambda batch, planned: validated_plans.extend(planned),
            ):
                replacement = protocol._repair_stage("repair", original, lambda: "prompt")
            self.assertEqual(item["id"], replacement["id"])
            self.assertEqual(item["id"], context.load_stage("repair")["id"])
            self.assertEqual(item["prerequisiteId"], validated_plans[0]["prerequisiteId"])


if __name__ == "__main__":
    unittest.main()

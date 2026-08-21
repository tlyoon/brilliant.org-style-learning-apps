import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app_generator.errors import ResponseContractError
from app_generator.generation.assembler import assemble_package, validate_plan
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

    def test_json_contract_accepts_sentinels_and_rejects_prose(self):
        self.assertEqual({"ok": True}, parse_json_response('BEGIN_JSON\n{"ok": true}\nEND_JSON'))
        with self.assertRaises(ResponseContractError):
            parse_json_response('Here it is\nBEGIN_JSON\n{"ok": true}\nEND_JSON')
        with self.assertRaises(ResponseContractError):
            parse_json_response('BEGIN_JSON\n{"ok": true}')

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

    def test_truncated_batch_falls_back_to_single_activities_and_retains_raw_response(self):
        planned = self.plan()["activities"][:3]
        responses = ["BEGIN_JSON\n{", *[
            'BEGIN_JSON\n{"activities": [{"id": "' + item["id"] + '"}]}\nEND_JSON'
            for item in planned
        ]]
        with tempfile.TemporaryDirectory() as directory:
            context = RunContext.create(Path(directory))
            protocol = GenerationProtocol(self.Conversation(responses), context)
            batch = protocol._activity_batch("mcq-easy", {}, planned, "synthetic")
            self.assertEqual([item["id"] for item in planned], [item["id"] for item in batch["activities"]])
            self.assertTrue((context.batches / "mcq-easy.response.txt").is_file())
            self.assertTrue((context.batches / "mcq-easy.json").is_file())

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


if __name__ == "__main__":
    unittest.main()

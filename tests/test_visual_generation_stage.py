import json
import tempfile
import unittest
from pathlib import Path

from app_generator.domains import resolve_domain
from app_generator.errors import ResponseContractError
from app_generator.generation.protocol import GenerationProtocol
from app_generator.runtime.run_context import RunContext
from app_generator.visuals.generation import (
    attach_visual_documents,
    selected_visual_activity_ids,
    visual_generation_catalog,
)
from tests.test_visual_contracts import activity, plan, spec


ROOT = Path(__file__).resolve().parents[1]


class Conversation:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.stages = []
        self.prompts = []

    def ask(self, prompt, *, stage=None):
        self.stages.append(stage)
        self.prompts.append(prompt)
        payload = next(self.responses)
        return "BEGIN_JSON\n" + json.dumps(payload, ensure_ascii=False) + "\nEND_JSON"


def package():
    return {
        "schemaVersion": "1.1",
        "packageId": "visual-stage-test",
        "domain": resolve_domain(ROOT).identity(),
        "activities": [activity()],
    }


def plans():
    return {
        "activities": [
            {"activityId": "visual-test", "visualPlan": plan()}
        ]
    }


def specs():
    return {
        "activities": [
            {"activityId": "visual-test", "visualSpec": spec()}
        ]
    }


class VisualGenerationStageTests(unittest.TestCase):
    def test_catalog_exposes_only_available_trusted_templates(self):
        catalog = visual_generation_catalog(resolve_domain(ROOT))
        self.assertEqual(
            {
                "mechanics.cart_collision_1d",
                "mechanics.free_body_2d",
                "graph.cartesian_qualitative",
                "state.energy_bar",
                "mechanics.motion_1d_slider",
            },
            {item["id"] for item in catalog["availableTemplates"]},
        )
        self.assertTrue(catalog["styleProfiles"])
        self.assertTrue(catalog["simulationModels"])

    def test_visual_documents_attach_without_rewriting_activity_content(self):
        original = package()
        result = attach_visual_documents(ROOT, original, plans(), specs())

        self.assertNotIn("visualPlan", original["activities"][0])
        self.assertEqual(
            original["activities"][0]["prompt"],
            result["activities"][0]["prompt"],
        )
        self.assertEqual(
            original["activities"][0]["answerKey"],
            result["activities"][0]["answerKey"],
        )
        self.assertEqual(plan(), result["activities"][0]["visualPlan"])
        self.assertEqual(spec(), result["activities"][0]["visualSpec"])

    def test_plan_batch_must_cover_exact_package_activity_ids(self):
        invalid = {
            "activities": [
                {"activityId": "wrong-id", "visualPlan": plan()}
            ]
        }
        with self.assertRaisesRegex(ResponseContractError, "must match the package activity IDs exactly"):
            selected_visual_activity_ids(package(), invalid)

    def test_visual_generation_retries_invalid_batch_then_uses_domain_prompt(self):
        with tempfile.TemporaryDirectory() as directory:
            context = RunContext.create(Path(directory))
            context.save_stage("source-analysis", {"sectionTitle": "Synthetic"})
            invalid = {
                "activities": [
                    {"activityId": "wrong-id", "visualPlan": plan()}
                ]
            }
            conversation = Conversation([invalid, plans(), specs()])
            protocol = GenerationProtocol(
                conversation,
                context,
                domain_profile=resolve_domain(ROOT),
            )

            result = protocol._visualize_package(package())

        self.assertEqual(
            ["visual-plans", "visual-plans", "visual-specs"],
            conversation.stages,
        )
        self.assertIn("TRUSTED SUBJECT-DOMAIN EXTENSION", conversation.prompts[0])
        self.assertIn("visualPlan", result["activities"][0])
        self.assertIn("visualSpec", result["activities"][0])

    def test_invalid_spec_retries_without_replanning_and_uses_exact_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            context = RunContext.create(Path(directory))
            context.save_stage("source-analysis", {"sectionTitle": "Synthetic"})
            invalid_specs = specs()
            invalid_specs["activities"][0]["visualSpec"]["accessibility"]["reducedMotionStrategy"] = (
                "static_fallback"
            )
            conversation = Conversation([plans(), invalid_specs, specs()])
            protocol = GenerationProtocol(
                conversation,
                context,
                domain_profile=resolve_domain(ROOT),
            )
            result = protocol._visualize_package(package())

        self.assertEqual(
            ["visual-plans", "visual-specs", "visual-specs"],
            conversation.stages,
        )
        self.assertEqual(spec(), result["activities"][0]["visualSpec"])
        self.assertIn("AUTHORITATIVE VISUAL SPEC SCHEMA:", conversation.prompts[1])
        self.assertIn('"reducedMotionStrategy"', conversation.prompts[1])
        self.assertIn('"kind"', conversation.prompts[1])
        self.assertIn("static_fallback", conversation.prompts[2])

    def test_visual_generation_runs_after_text_semantic_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            context = RunContext.create(Path(directory))
            context.save_stage("source-analysis", {"sectionTitle": "Synthetic"})
            conversation = Conversation([
                {"findings": []},
                {"findings": []},
                plans(),
                specs(),
            ])
            protocol = GenerationProtocol(
                conversation,
                context,
                domain_profile=resolve_domain(ROOT),
            )

            result, findings = protocol.audit_and_repair(package())

        self.assertEqual([], findings)
        self.assertEqual(
            [
                "semantic-audit-01",
                "whole-package-audit",
                "visual-plans",
                "visual-specs",
            ],
            conversation.stages,
        )
        self.assertIn("visualSpec", result["activities"][0])


if __name__ == "__main__":
    unittest.main()

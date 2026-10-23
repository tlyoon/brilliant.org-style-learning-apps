import copy
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
    partition_visual_specs,
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
        self.assertEqual(
            {item["id"] for item in catalog["availableTemplates"]},
            set(catalog["rendererGuidance"]),
        )
        self.assertEqual(
            "energy-component",
            catalog["rendererGuidance"]["state.energy_bar"]["requiredEntities"]["kind"],
        )

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

    def test_saved_energy_bar_failure_is_rejected_by_renderer(self):
        item = activity()
        item["visualPlan"] = plan("energy_bar", "state.energy_bar")
        item["visualSpec"] = spec("energy_bar", "state.energy_bar")
        item["visualSpec"]["states"] = [
            {"id": "state-initial", "values": {"kinetic": 0.6}},
            {"id": "state-later", "values": {"kinetic": 0.4}},
        ]
        # Matches the real Section 9.4 failure class: structurally plausible
        # output with no energy-component entities for the energy-bar renderer.
        item["visualSpec"]["entities"] = [
            {"id": "kinetic", "kind": "cart", "label": {"en": "Kinetic", "ms": "Kinetik", "zh": "??"}}
        ]
        candidate = package()
        candidate["activities"] = [item]
        from app_generator.visuals.validation import visual_contract_errors
        errors = visual_contract_errors(ROOT, candidate)
        self.assertTrue(
            any("energy-bar renderer requires one to four energy-component entities" in e for e in errors),
            errors,
        )

    def test_energy_bar_snake_case_alias_fails_with_actionable_diagnostic(self):
        domain = resolve_domain(ROOT)
        validator = domain.load_module("validation", "visualValidatorModule").visual_spec_errors
        good_spec = {
            "template": "state.energy_bar",
            "entities": [
                {"id": "kinetic", "kind": "energy-component", "properties": {"relativeAmount": 0.6}},
                {"id": "elastic", "kind": "energy-component", "properties": {"relativeAmount": 0.4}},
            ],
        }
        self.assertEqual([], validator(good_spec, "visualSpec"))
        invalid_spec = copy.deepcopy(good_spec)
        # Distilled from the actual Section 9.4 model reply, without storing
        # unreviewed generated academic content or private run artifacts.
        for entity in invalid_spec["entities"]:
            entity["properties"]["relative_amount"] = entity["properties"].pop("relativeAmount")
        failures = validator(invalid_spec, "visualSpec")
        self.assertEqual(4, len(failures), failures)
        self.assertEqual(2, sum("invalid alias" in e for e in failures))
        self.assertTrue(all("relativeAmount" in e for e in failures))
        self.assertTrue(all("camelCase" in e for e in failures))

    def test_energy_bar_prompt_requires_exact_case_sensitive_field_name(self):
        from app_generator.prompts import visual_specs_prompt
        catalog = visual_generation_catalog(resolve_domain(ROOT))
        schema = json.loads((ROOT / "content/schema/visual-spec.schema.json").read_text(encoding="utf-8"))
        instruction = visual_specs_prompt(
            package(),
            {"activities": [{"activityId": "visual-test", "visualPlan": plan("energy_bar", "state.energy_bar")}]},
            catalog,
            visual_spec_schema=schema,
            target_activity_ids={"visual-test"},
            correction_errors=[
                "visualSpec.entities[0].properties.relative_amount: invalid alias; "
                "use exactly properties.relativeAmount (camelCase)"
            ],
        )
        self.assertIn("properties.relativeAmount", instruction)
        self.assertIn("properties.relative_amount is INVALID", instruction)
        self.assertIn('"relativeAmount":0.6', instruction)
        self.assertIn('"requiredEntityProperties"', instruction)
        self.assertIn("invalid alias", instruction)

    def test_repair_only_invalid_visual_and_reuse_other_valid_spec(self):
        first = activity()
        second = copy.deepcopy(first)
        second["id"] = "visual-test-second"
        base = package()
        base["activities"] = [first, second]
        first_plan = plan()
        second_plan = plan()
        all_plans = {"activities": [
            {"activityId": first["id"], "visualPlan": first_plan},
            {"activityId": second["id"], "visualPlan": second_plan},
        ]}
        correct_first = spec()
        correct_second = spec()
        invalid_second = copy.deepcopy(correct_second)
        invalid_second["entities"][0]["kind"] = "body"
        batch = {"activities": [
            {"activityId": first["id"], "visualSpec": correct_first},
            {"activityId": second["id"], "visualSpec": invalid_second},
        ]}
        valid, failures = partition_visual_specs(ROOT, base, all_plans, batch)
        self.assertEqual({first["id"]}, set(valid))
        self.assertEqual(1, len(failures))
        self.assertIn("cart-collision renderer", failures[0])

        correction = {"activities": [
            {"activityId": second["id"], "visualSpec": correct_second},
        ]}
        with tempfile.TemporaryDirectory() as directory:
            context = RunContext.create(Path(directory))
            context.save_stage("source-analysis", {"sectionTitle": "Synthetic"})
            conversation = Conversation([all_plans, batch, correction])
            protocol = GenerationProtocol(
                conversation, context, domain_profile=resolve_domain(ROOT),
            )
            result = protocol._visualize_package(base)
            self.assertEqual(["visual-plans", "visual-specs", "visual-specs-repair"], conversation.stages)
            self.assertIn(first["id"], conversation.prompts[2])
            self.assertIn(second["id"], conversation.prompts[2])
            self.assertNotIn('"id": "' + first["id"] + '"', conversation.prompts[2])
            self.assertEqual(correct_first, result["activities"][0]["visualSpec"])
            self.assertEqual(correct_second, result["activities"][1]["visualSpec"])
            self.assertIsNone(context.load_stage("visual-specs-validated"))

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

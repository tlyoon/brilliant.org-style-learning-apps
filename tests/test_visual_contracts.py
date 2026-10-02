import copy
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from app_generator.validation.schema_validation import validate_schemas
from app_generator.visuals.validation import visual_contract_errors, visual_registry_errors
from app_generator.visuals.verification import (
    PhysicsVerificationRequest,
    PhysicsVerificationResult,
    assert_matching_result,
)

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_content_visual", ROOT / "scripts" / "validate_content.py")
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


def localized(text: str) -> dict[str, str]:
    return {"en": text, "ms": f"MS {text}", "zh": f"ZH {text}"}


def activity() -> dict:
    return {
        "id": "visual-test", "type": "mcq", "difficulty": "easy",
        "calculatorFree": True, "numericAnswerRequired": False,
        "objective": "Compare the motion directions of two carts",
        "prompt": localized("Choose the consistent motion description."),
        "answerKey": {
            "correct": "a",
            "options": [
                {"id": "a", "label": localized("The carts approach each other.")},
                {"id": "b", "label": localized("Both carts move right.")},
            ],
        },
        "hints": [localized("Compare the arrows.")],
        "feedback": localized("Use direction rather than speed."),
        "misconceptions": ["direction-confusion"],
        "provenance": {"sourceLocation": "synthetic visual fixture", "originalContent": True},
    }


def plan(mode="scene_diagram", template="mechanics.cart_collision_1d") -> dict:
    return {
        "schemaVersion": "1.0",
        "activityIntent": {
            "learningObjective": "Compare the motion directions of two carts",
            "reasoningTarget": "Relate velocity direction to relative approach motion",
            "misconceptionTargets": ["direction-confusion"],
            "difficulty": "easy",
        },
        "representationAssessment": {
            "visualValue": 3, "simulationValue": 1, "hallucinationRisk": 0,
            "templateCoverage": 3, "visualRequired": True,
            "rationale": "Direction arrows carry the relevant spatial relationship.",
        },
        "selectedMode": mode,
        "selectedTemplate": template,
        "fallbackMode": "structured_interaction",
        "renderStrategy": "deterministic_semantic",
        "aestheticIntent": {
            "styleProfile": "physics-clean-v1",
            "tone": "playful-academic",
            "compositionPriority": "concept-first",
            "backgroundComplexity": "minimal",
        },
        "generatedAssetPolicy": {
            "imageRole": "none",
            "answerCriticalLayer": "deterministic-renderer",
            "requiresMultimodalAudit": False,
            "allowSearchGrounding": False,
            "imageModelProfile": "none",
        },
        "verificationRequirements": {
            "physicsComputation": "deterministic-engine",
            "referenceGrounding": "source-corpus",
            "finalMultimodalAudit": False,
            "requireIndependentCrosscheck": True,
        },
        "groundedFactsUsed": ["fact-cart-a", "fact-cart-b"],
        "learnerTask": "Compare the two velocity directions.",
    }


def spec(mode="scene_diagram", template="mechanics.cart_collision_1d") -> dict:
    return {
        "schemaVersion": "1.0", "mode": mode, "template": template,
        "semanticParameters": {"phase": "before", "track_orientation": "horizontal"},
        "entities": [
            {"id": "cart-a", "kind": "cart", "label": localized("Cart A")},
            {"id": "cart-b", "kind": "cart", "label": localized("Cart B")},
        ],
        "relations": [{"id": "approach", "kind": "approaches", "sourceId": "cart-a", "targetId": "cart-b"}],
        "accessibility": {
            "description": localized("Two carts on one track with opposing velocity directions."),
            "colorIndependent": True, "reducedMotionStrategy": "not-applicable",
        },
        "grounding": [
            {"factId": "fact-cart-a", "origin": "source_fact", "appliesTo": ["cart-a"]},
            {"factId": "fact-cart-b", "origin": "source_fact", "appliesTo": ["cart-b"]},
            {"factId": "template-track", "origin": "template_invariant", "appliesTo": ["approach"]},
        ],
        "fallback": {"mode": "structured_interaction", "reason": "Retain the direction-comparison task."},
        "validation": {"answerRelevantIds": ["cart-a", "cart-b", "approach"], "forbidAnswerLeakage": True},
    }


def package_with_visual() -> dict:
    package = json.loads((ROOT / "tests" / "fixtures" / "valid-draft.json").read_text(encoding="utf-8"))
    item = activity()
    item["visualPlan"] = plan()
    item["visualSpec"] = spec()
    package["activities"] = [item]
    return package


class VisualContractTests(unittest.TestCase):
    def test_visual_registries_are_valid_and_fail_closed(self):
        self.assertEqual([], visual_registry_errors(ROOT))
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            temp_root = Path(directory)
            (temp_root / "content").mkdir()
            shutil.copytree(ROOT / "content" / "visuals", temp_root / "content" / "visuals")
            models_path = temp_root / "content" / "visuals" / "simulation-model-registry.json"
            models = json.loads(models_path.read_text(encoding="utf-8"))
            models["models"][0]["controllableVariableIds"] = ["imaginary-variable"]
            models_path.write_text(json.dumps(models), encoding="utf-8")
            errors = visual_registry_errors(temp_root)
            self.assertTrue(any("controllable variables" in error for error in errors), errors)

    def test_available_visual_templates_bind_exact_trusted_renderers(self):
        registry = json.loads((ROOT / "content" / "visuals" / "template-registry.json").read_text(encoding="utf-8"))
        available = {item["id"]: item for item in registry["templates"] if item["implementationStatus"] == "available"}
        self.assertEqual(
            {
                "mechanics.cart_collision_1d": ("cart-collision-v1", "1.0.0"),
                "mechanics.free_body_2d": ("free-body-v1", "1.0.0"),
                "graph.cartesian_qualitative": ("qualitative-graph-v1", "1.0.0"),
                "state.energy_bar": ("energy-bar-v1", "1.0.0"),
            },
            {key: (value["rendererId"], value["rendererVersion"]) for key, value in available.items()},
        )

    def test_renderer_specific_semantic_contracts_fail_closed(self):
        package = package_with_visual()
        package["activities"][0]["visualSpec"]["entities"][0]["kind"] = "spaceship"
        errors = validator.validate_package(package)
        self.assertTrue(any("cart-collision renderer requires" in error for error in errors), errors)

        package = package_with_visual()
        item = package["activities"][0]
        item["visualPlan"] = plan("energy_bar", "state.energy_bar")
        item["visualSpec"] = {
            "schemaVersion": "1.0", "mode": "energy_bar", "template": "state.energy_bar",
            "entities": [
                {"id": "kinetic", "kind": "energy-component", "label": localized("Kinetic"), "properties": {"relativeAmount": 1.4}}
            ],
            "accessibility": {"description": localized("An energy bar."), "colorIndependent": True, "reducedMotionStrategy": "not-applicable"},
            "grounding": [{"factId": "fact-cart-a", "origin": "source_fact", "appliesTo": ["kinetic"]}],
            "fallback": {"mode": "structured_interaction", "reason": "Use a textual energy comparison."},
            "validation": {"answerRelevantIds": ["kinetic"], "forbidAnswerLeakage": True},
        }
        errors = validator.validate_package(package)
        self.assertTrue(any("relativeAmount" in error for error in errors), errors)

    def test_planned_renderer_template_cannot_be_selected_for_public_content(self):
        package = package_with_visual()
        item = package["activities"][0]
        item["visualPlan"] = plan("parameter_simulation", "mechanics.motion_1d_slider")
        item["visualPlan"]["renderStrategy"] = "deterministic_simulation"
        item["visualSpec"] = {
            "schemaVersion": "1.0", "mode": "parameter_simulation", "template": "mechanics.motion_1d_slider",
            "entities": [{"id": "cart-a", "kind": "cart"}],
            "controls": [{"id": "speed", "kind": "slider", "variableId": "velocity", "label": localized("Velocity"), "min": -2, "max": 2, "default": 1, "step": 0.5}],
            "states": [{"id": "start", "values": {"position": 0, "velocity": 1, "time": 0}}],
            "simulation": {"id": "motion", "modelId": "kinematics.motion_1d", "variableIds": ["position", "velocity", "time"], "invariantIds": []},
            "accessibility": {"description": localized("A motion simulation."), "colorIndependent": True, "reducedMotionStrategy": "instant-state"},
            "grounding": [{"factId": "fact-cart-a", "origin": "source_fact", "appliesTo": ["cart-a"]}],
            "fallback": {"mode": "scene_diagram", "template": "mechanics.cart_collision_1d", "reason": "Use a static scene."},
            "validation": {"answerRelevantIds": ["cart-a"], "forbidAnswerLeakage": True},
        }
        errors = validator.validate_package(package)
        self.assertTrue(any("is not yet available" in error for error in errors), errors)

    def test_visual_schemas_are_valid_draft_2020_12(self):
        for name in ("visual-plan.schema.json", "visual-spec.schema.json"):
            schema = json.loads((ROOT / "content" / "schema" / name).read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)

    def test_legacy_package_without_visual_fields_remains_valid(self):
        legacy = json.loads((ROOT / "tests" / "fixtures" / "valid-draft.json").read_text(encoding="utf-8"))
        legacy["activities"] = [activity()]
        self.assertEqual([], validator.validate_package(legacy))
        self.assertEqual([], visual_contract_errors(ROOT, legacy))

    def test_valid_visual_plan_and_spec_pass_repository_validation(self):
        self.assertEqual([], validator.validate_package(package_with_visual()))

    def test_visual_spec_without_plan_is_rejected(self):
        package = package_with_visual()
        del package["activities"][0]["visualPlan"]
        errors = validator.validate_package(package)
        self.assertTrue(any("visualPlan: required whenever visualSpec is present" in error for error in errors), errors)

    def test_plan_must_match_activity_intent(self):
        package = package_with_visual()
        package["activities"][0]["visualPlan"]["activityIntent"]["difficulty"] = "challenging"
        errors = validator.validate_package(package)
        self.assertTrue(any("activityIntent.difficulty" in error for error in errors), errors)

    def test_unknown_or_wrong_mode_template_is_rejected(self):
        package = package_with_visual()
        package["activities"][0]["visualPlan"]["selectedTemplate"] = "unknown.template"
        package["activities"][0]["visualSpec"]["template"] = "unknown.template"
        errors = validator.validate_package(package)
        self.assertTrue(any("unknown trusted template" in error for error in errors), errors)

        package = package_with_visual()
        package["activities"][0]["visualPlan"]["selectedTemplate"] = "mechanics.free_body_2d"
        package["activities"][0]["visualSpec"]["template"] = "mechanics.free_body_2d"
        errors = validator.validate_package(package)
        self.assertTrue(any("template mode 'vector_diagram' does not match" in error for error in errors), errors)

    def test_visual_references_must_resolve(self):
        package = package_with_visual()
        package["activities"][0]["visualSpec"]["relations"][0]["targetId"] = "ghost-cart"
        errors = validator.validate_package(package)
        self.assertTrue(any("sourceId and targetId must reference" in error for error in errors), errors)

    def test_visual_element_ids_are_unique_across_families(self):
        package = package_with_visual()
        package["activities"][0]["visualSpec"]["relations"][0]["id"] = "cart-a"
        errors = validator.validate_package(package)
        self.assertTrue(any("unique across visual element families" in error for error in errors), errors)

    def test_raw_coordinates_and_executable_markup_are_rejected(self):
        package = package_with_visual()
        package["activities"][0]["visualSpec"]["semanticParameters"]["x"] = 25
        errors = validator.validate_package(package)
        self.assertTrue(any("raw rendering/code field is forbidden" in error for error in errors), errors)

        package = package_with_visual()
        package["activities"][0]["visualPlan"]["learnerTask"] = "<script>alert(1)</script>"
        errors = validator.validate_package(package)
        self.assertTrue(any("executable or markup-like content is forbidden" in error for error in errors), errors)

    def test_graph_requires_one_x_and_one_y_axis(self):
        package = package_with_visual()
        item = package["activities"][0]
        item["visualPlan"] = plan("graph_plot", "graph.cartesian_qualitative")
        item["visualSpec"] = {
            "schemaVersion": "1.0", "mode": "graph_plot", "template": "graph.cartesian_qualitative",
            "axes": [
                {"id": "axis-a", "role": "x", "quantity": "time", "label": localized("Time"), "scale": "qualitative"},
                {"id": "axis-b", "role": "x", "quantity": "position", "label": localized("Position"), "scale": "qualitative"},
            ],
            "graphSeries": [
                {"id": "series-a", "xAxisId": "axis-a", "yAxisId": "axis-b", "shape": "increasing-linear"}
            ],
            "accessibility": {"description": localized("A qualitative graph."), "colorIndependent": True, "reducedMotionStrategy": "not-applicable"},
            "grounding": [{"factId": "fact-cart-a", "origin": "source_fact", "appliesTo": ["axis-a"]}],
            "fallback": {"mode": "structured_interaction", "reason": "Describe the graph relationship textually."},
            "validation": {"answerRelevantIds": ["axis-a"], "forbidAnswerLeakage": True},
        }
        errors = validator.validate_package(package)
        self.assertTrue(any("exactly one x axis and one y axis" in error for error in errors), errors)

    def test_simulation_control_range_and_fallback_are_checked(self):
        package = package_with_visual()
        item = package["activities"][0]
        item["visualPlan"] = plan("parameter_simulation", "mechanics.motion_1d_slider")
        item["visualSpec"] = {
            "schemaVersion": "1.0", "mode": "parameter_simulation", "template": "mechanics.motion_1d_slider",
            "entities": [{"id": "cart-a", "kind": "cart"}],
            "controls": [{"id": "speed-control", "kind": "slider", "variableId": "velocity", "label": localized("Speed"), "min": 2, "max": 1, "default": 3, "step": 0.5}],
            "states": [{"id": "initial-state", "values": {"position": 0, "velocity": 3, "time": 0}}],
            "simulation": {
                "id": "motion-sim", "modelId": "kinematics.motion_1d",
                "variableIds": ["position", "velocity", "time"], "invariantIds": []
            },
            "accessibility": {"description": localized("A cart with an adjustable speed."), "colorIndependent": True, "reducedMotionStrategy": "instant-state"},
            "grounding": [{"factId": "fact-cart-a", "origin": "source_fact", "appliesTo": ["cart-a"]}],
            "fallback": {"mode": "parameter_simulation", "reason": "Invalid seeded fallback."},
            "validation": {"answerRelevantIds": ["cart-a"], "forbidAnswerLeakage": True},
        }
        errors = validator.validate_package(package)
        self.assertTrue(any("min must be less than max" in error for error in errors), errors)
        self.assertTrue(any("must lie within the declared range" in error for error in errors), errors)
        self.assertTrue(any("requires a non-simulation fallback" in error for error in errors), errors)

    def test_simulation_model_and_controls_must_use_trusted_registry(self):
        package = package_with_visual()
        item = package["activities"][0]
        item["visualPlan"] = plan("parameter_simulation", "mechanics.motion_1d_slider")
        item["visualPlan"]["renderStrategy"] = "deterministic_simulation"
        item["visualPlan"]["generatedAssetPolicy"] = {
            "imageRole": "none", "answerCriticalLayer": "deterministic-renderer",
            "requiresMultimodalAudit": False, "allowSearchGrounding": False,
            "imageModelProfile": "none",
        }
        item["visualSpec"] = {
            "schemaVersion": "1.0", "mode": "parameter_simulation", "template": "mechanics.motion_1d_slider",
            "entities": [{"id": "cart-a", "kind": "cart"}],
            "controls": [{"id": "time-control", "kind": "slider", "variableId": "time", "label": localized("Time"), "min": 0, "max": 10, "default": 0, "step": 1}],
            "states": [{"id": "initial-state", "values": {"position": 0, "velocity": 1, "time": 0}}],
            "simulation": {"id": "motion-sim", "modelId": "kinematics.motion_1d", "variableIds": ["position", "velocity", "time"], "invariantIds": []},
            "accessibility": {"description": localized("A one-dimensional motion scene."), "colorIndependent": True, "reducedMotionStrategy": "instant-state"},
            "grounding": [{"factId": "fact-cart-a", "origin": "source_fact", "appliesTo": ["cart-a"]}],
            "fallback": {"mode": "scene_diagram", "template": "mechanics.cart_collision_1d", "reason": "Show a static state."},
            "validation": {"answerRelevantIds": ["cart-a"], "forbidAnswerLeakage": True},
        }
        errors = validator.validate_package(package)
        self.assertTrue(any("not controllable in model" in error for error in errors), errors)

        item["visualSpec"]["controls"][0]["variableId"] = "velocity"
        item["visualSpec"]["simulation"]["modelId"] = "unknown.model"
        errors = validator.validate_package(package)
        self.assertTrue(any("unknown trusted simulation model" in error for error in errors), errors)

    def test_source_grounding_must_be_declared_by_plan(self):
        package = package_with_visual()
        package["activities"][0]["visualSpec"]["grounding"].append(
            {"factId": "fact-undisclosed", "origin": "source_fact", "appliesTo": ["cart-a"]}
        )
        errors = validator.validate_package(package)
        self.assertTrue(any("source facts missing from visualPlan.groundedFactsUsed" in error for error in errors), errors)

    def test_hybrid_gemini_base_keeps_answer_critical_content_deterministic(self):
        package = package_with_visual()
        plan_data = package["activities"][0]["visualPlan"]
        plan_data["renderStrategy"] = "hybrid_generated_base"
        plan_data["generatedAssetPolicy"] = {
            "imageRole": "hybrid-base",
            "answerCriticalLayer": "deterministic-overlay",
            "requiresMultimodalAudit": True,
            "allowSearchGrounding": False,
            "imageModelProfile": "balanced",
        }
        plan_data["verificationRequirements"]["finalMultimodalAudit"] = True
        self.assertEqual([], validator.validate_package(package))

        plan_data["generatedAssetPolicy"]["answerCriticalLayer"] = "none"
        errors = validator.validate_package(package)
        self.assertTrue(any("deterministic-overlay" in error for error in errors), errors)

    def test_gemini_illustration_cannot_be_answer_critical(self):
        package = package_with_visual()
        plan_data = package["activities"][0]["visualPlan"]
        plan_data["renderStrategy"] = "gemini_illustration"
        plan_data["generatedAssetPolicy"] = {
            "imageRole": "contextual-illustration",
            "answerCriticalLayer": "none",
            "requiresMultimodalAudit": True,
            "allowSearchGrounding": False,
            "imageModelProfile": "premium",
        }
        plan_data["verificationRequirements"]["finalMultimodalAudit"] = True
        self.assertEqual([], validator.validate_package(package))

        plan_data["generatedAssetPolicy"]["answerCriticalLayer"] = "deterministic-overlay"
        errors = validator.validate_package(package)
        self.assertTrue(any("'none' was expected" in error for error in errors), errors)

    def test_generated_imagery_requires_final_multimodal_audit(self):
        package = package_with_visual()
        plan_data = package["activities"][0]["visualPlan"]
        plan_data["renderStrategy"] = "hybrid_generated_base"
        plan_data["generatedAssetPolicy"] = {
            "imageRole": "hybrid-base",
            "answerCriticalLayer": "deterministic-overlay",
            "requiresMultimodalAudit": True,
            "allowSearchGrounding": False,
            "imageModelProfile": "balanced",
        }
        errors = validator.validate_package(package)
        self.assertTrue(any("finalMultimodalAudit" in error for error in errors), errors)

    def test_search_grounding_must_be_explicit_in_verification_policy(self):
        package = package_with_visual()
        plan_data = package["activities"][0]["visualPlan"]
        plan_data["renderStrategy"] = "hybrid_generated_base"
        plan_data["generatedAssetPolicy"] = {
            "imageRole": "hybrid-base",
            "answerCriticalLayer": "deterministic-overlay",
            "requiresMultimodalAudit": True,
            "allowSearchGrounding": True,
            "imageModelProfile": "balanced",
        }
        plan_data["verificationRequirements"]["finalMultimodalAudit"] = True
        errors = validator.validate_package(package)
        self.assertTrue(any("referenceGrounding" in error for error in errors), errors)

    def test_unknown_style_profile_is_rejected(self):
        package = package_with_visual()
        package["activities"][0]["visualPlan"]["aestheticIntent"]["styleProfile"] = "unknown-style"
        errors = validator.validate_package(package)
        self.assertTrue(any("unknown style profile" in error for error in errors), errors)

    def test_template_rejects_unapproved_render_strategy(self):
        package = package_with_visual()
        plan_data = package["activities"][0]["visualPlan"]
        plan_data["selectedMode"] = "graph_plot"
        plan_data["selectedTemplate"] = "graph.cartesian_qualitative"
        plan_data["renderStrategy"] = "hybrid_generated_base"
        plan_data["generatedAssetPolicy"] = {
            "imageRole": "hybrid-base",
            "answerCriticalLayer": "deterministic-overlay",
            "requiresMultimodalAudit": True,
            "allowSearchGrounding": False,
            "imageModelProfile": "balanced",
        }
        plan_data["verificationRequirements"]["finalMultimodalAudit"] = True
        errors = validator.validate_package(package)
        self.assertTrue(any("not allowed by trusted template" in error for error in errors), errors)

    def test_nonvisual_assessment_can_stop_without_visual_spec(self):
        package = package_with_visual()
        item = package["activities"][0]
        visual_plan = item["visualPlan"]
        visual_plan["selectedMode"] = "none"
        visual_plan["selectedTemplate"] = None
        visual_plan["representationAssessment"]["visualRequired"] = False
        visual_plan["renderStrategy"] = "none"
        visual_plan["generatedAssetPolicy"] = {
            "imageRole": "none",
            "answerCriticalLayer": "none",
            "requiresMultimodalAudit": False,
            "allowSearchGrounding": False,
            "imageModelProfile": "none",
        }
        visual_plan["verificationRequirements"] = {
            "physicsComputation": "none",
            "referenceGrounding": "source-corpus",
            "finalMultimodalAudit": False,
            "requireIndependentCrosscheck": False,
        }
        del item["visualSpec"]
        self.assertEqual([], validator.validate_package(package))

    def test_provider_neutral_verifier_contract_links_request_and_result(self):
        request = PhysicsVerificationRequest(
            activity_id="visual-test",
            check_id="momentum-invariant",
            kind="conservation_invariant",
            statement="Total momentum is unchanged for the isolated two-cart system.",
        )
        result = PhysicsVerificationResult(
            check_id="momentum-invariant",
            passed=True,
            provider="wolfram",
            summary="Symbolic momentum before and after is equivalent under the declared assumptions.",
        )
        assert_matching_result(request, result)
        with self.assertRaises(ValueError):
            assert_matching_result(
                request,
                PhysicsVerificationResult(
                    check_id="different-check", passed=True, provider="wolfram", summary="Mismatch seed"
                ),
            )
        with self.assertRaises(ValueError):
            PhysicsVerificationRequest(
                activity_id="visual-test", check_id="bad", kind="draw-pretty-image", statement="Bad kind"
            )

    def test_generation_schema_validation_enforces_visual_contract(self):
        package = package_with_visual()
        package["activities"][0]["visualSpec"]["relations"][0]["targetId"] = "ghost-cart"
        manifest = json.loads((ROOT / "content" / "source-manifests" / "source-manifest.example.json").read_text(encoding="utf-8"))
        errors = validate_schemas(ROOT, package, manifest)
        self.assertTrue(any("targetId must reference" in error or "sourceId and targetId" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()

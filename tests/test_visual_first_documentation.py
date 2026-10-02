import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class VisualFirstDocumentationTests(unittest.TestCase):
    def text(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_decision_0024_is_accepted_and_declarative(self):
        text = self.text("docs/decisions/0024-visual-first-physics-learning.md")
        self.assertIn("## Status\n\nAccepted.", text)
        self.assertIn("visual-interactive reasoning experiences", text)
        self.assertIn("declarative specifications", text)
        self.assertIn("shall not generate arbitrary executable JavaScript", text)
        self.assertIn("question ? visual ? physics consistency validation", text)

    def test_product_keeps_stage_zero_contract_while_planning_migration(self):
        text = self.text("docs/PRODUCT_REQUIREMENTS.md")
        self.assertIn("18 activities", text)
        self.assertIn("nine multiple-choice and nine interactive", text)
        self.assertIn("visual-value assessment", text)
        self.assertIn("versioned declarative visual specification", text)
        self.assertIn("compatibility requirement", text)

    def test_content_rules_reject_decorative_or_hallucinated_visuals(self):
        text = self.text("docs/CONTENT_RULES.md")
        self.assertIn("Visuals are instructional content, not decoration", text)
        self.assertIn("simplify or use a safe fallback rather than inventing unsupported detail", text)
        self.assertIn("Question text, answer logic, visual specification, and rendered physical meaning must agree", text)
        self.assertIn("Source figures may be reused/cropped only", text)

    def test_blueprint_stage_two_is_visual_interactive(self):
        text = self.text("docs/10_STAGE_BLUEPRINT.md")
        self.assertIn("# Stage 2 ? Visual-Interactive Activity Framework", text)
        self.assertIn("visual-value / simulation-value assessment", text)
        self.assertIn("Decision 0024", text)
        self.assertIn("unsupported visual requests fail safely", text)

    def test_visual_design_contract_has_algorithm_validation_and_fallback(self):
        text = self.text("docs/VISUAL_INTERACTION_DESIGN.md")
        for phrase in (
            "visual value",
            "simulation value",
            "hallucination risk",
            "template coverage",
            "Cross-modal validation",
            "Failure and fallback policy",
            "parameter_simulation",
        ):
            self.assertIn(phrase, text)

    def test_prompt_contract_forbids_pixels_and_arbitrary_code(self):
        text = self.text("docs/VISUAL_GENERATION_PROMPT_SPEC.md")
        self.assertIn("Do not emit executable JavaScript, SVG markup, HTML, CSS, image pixels, or animation frames", text)
        self.assertIn("Stage D ? cross-modal semantic audit", text)
        self.assertIn("Source-figure association prompt guardrail", text)
        self.assertIn("force a picture on every activity", text)

    def test_visual_tool_orchestration_separates_provider_roles(self):
        text = self.text("docs/VISUAL_TOOL_ORCHESTRATION.md")
        for phrase in (
            "Gemini",
            "Wolfram",
            "Replit",
            "hybrid_generated_base",
            "deterministic_simulation",
            "final multimodal audit",
            "answer-critical",
            "A prettier image never outranks a correct one",
        ):
            self.assertIn(phrase, text)
        self.assertIn("development-time template-incubation environment", text)
        self.assertIn("not a per-activity production dependency", text)

    def test_architecture_and_ai_workflow_include_visual_pipeline(self):
        architecture = self.text("docs/ARCHITECTURE.md")
        workflow = self.text("docs/AI_WORKFLOW.md")
        self.assertIn("Visual planner producing declarative, versioned visual specifications", architecture)
        self.assertIn("final multimodal question ? answer ? rendered-visual audit", architecture)
        self.assertIn("Wolfram", workflow)
        self.assertIn("Replit", workflow)
        self.assertIn("visual-value/simulation-value assessment", workflow)
        self.assertIn("simplification or fallback rather than invention", workflow)


if __name__ == "__main__":
    unittest.main()

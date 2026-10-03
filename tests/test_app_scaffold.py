import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
EXAMPLE = ROOT / "content" / "examples" / "conceptual-forces.json"
SECTION_1_1 = ROOT / "content" / "chapter-1" / "section-1-1" / "package.json"


class AppScaffoldTests(unittest.TestCase):
    def test_entrypoint_has_accessible_runtime_hooks(self):
        html = (APP / "index.html").read_text(encoding="utf-8")
        self.assertIn('name="viewport"', html)
        self.assertIn('aria-live="polite"', html)
        self.assertIn('aria-label="Language"', html)

    def test_player_requires_an_explicit_external_package(self):
        javascript = (APP / "app.js").read_text(encoding="utf-8")
        self.assertNotIn("content/chapter-1/section-1-1/package.json", javascript)
        self.assertIn("data-package-url", javascript)
        self.assertIn("loadPackage()", javascript)

    def test_entrypoint_has_no_blanket_review_notice(self):
        html = (APP / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("Review prototype", html)
        self.assertNotIn("qualified human review", html)
        self.assertNotIn("not approved for publication", html)
        self.assertNotIn("Section 1.1", html)

    def test_entrypoint_has_selector_without_visible_banner_or_language_label(self):
        html = (APP / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('class="brand"', html)
        self.assertNotIn(">Interactive Learning<", html)
        self.assertNotIn("<label>Language", html)
        self.assertIn('<select id="locale" aria-label="Language">', html)
        self.assertIn('<option value="en">English</option>', html)

    def test_question_and_action_control_layout_contract(self):
        css = (APP / "styles.css").read_text(encoding="utf-8")
        self.assertIn(".choice, .interaction-item { font-size: 1rem; }", css)
        self.assertIn(".question { font-size: 1.25rem;", css)
        self.assertIn(".action-row { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));", css)

    def test_existing_section_one_package_remains_in_review(self):
        package = json.loads(SECTION_1_1.read_text(encoding="utf-8"))
        self.assertEqual("review", package["status"])

    def test_visual_runtime_loads_domain_assets_before_generic_bridge_and_player(self):
        html = (APP / "index.html").read_text(encoding="utf-8")
        domain_position = html.index('src="domain-renderers.js"')
        bridge_position = html.index('src="visual-renderers.js"')
        player_position = html.index('src="app.js"')
        self.assertLess(domain_position, bridge_position)
        self.assertLess(bridge_position, player_position)
        bridge = (APP / "visual-renderers.js").read_text(encoding="utf-8")
        self.assertIn("DomainVisuals", bridge)
        self.assertNotIn("mechanics.cart_collision_1d", bridge)
        renderer = (ROOT / "domains" / "university-level physics" / "visuals" / "physics-renderers.js").read_text(encoding="utf-8")
        for template in ("mechanics.cart_collision_1d", "mechanics.free_body_2d", "graph.cartesian_qualitative", "state.energy_bar"):
            self.assertIn(template, renderer)
        self.assertNotIn("innerHTML", renderer)
        generic_css = (APP / "styles.css").read_text(encoding="utf-8")
        domain_css = (ROOT / "domains" / "university-level physics" / "visuals" / "physics-styles.css").read_text(encoding="utf-8")
        self.assertNotIn(".physics-visual__svg", generic_css)
        self.assertIn("--visual-accent-1", domain_css)
        self.assertIn(".physics-visual__svg", domain_css)

    def test_player_does_not_use_inner_html(self):
        javascript = (APP / "app.js").read_text(encoding="utf-8")
        self.assertNotIn("innerHTML", javascript)
        self.assertIn("textContent", javascript)

    def test_example_is_original_conceptual_draft(self):
        package = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        self.assertEqual("draft", package["status"])
        self.assertEqual({"en", "ms", "zh"}, set(package["locales"]))
        self.assertGreaterEqual(len(package["activities"]), 3)
        for activity in package["activities"]:
            self.assertTrue(activity["calculatorFree"])
            self.assertFalse(activity["numericAnswerRequired"])
            self.assertTrue(activity["provenance"]["originalContent"])
            self.assertGreaterEqual(len(activity["answerKey"]["options"]), 2)


if __name__ == "__main__":
    unittest.main()

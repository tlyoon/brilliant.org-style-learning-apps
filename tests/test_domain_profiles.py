import json
import shutil
import tempfile
import unittest
from pathlib import Path

from app_generator.domains import domain_registry_errors, load_domain_registry, resolve_domain

ROOT = Path(__file__).resolve().parents[1]


class DomainProfileTests(unittest.TestCase):
    def test_default_domain_is_university_level_physics(self):
        registry = load_domain_registry(ROOT)
        self.assertEqual("university-level-physics", registry["defaultDomainId"])
        profile = resolve_domain(ROOT)
        self.assertEqual("university-level-physics", profile.id)
        self.assertEqual("University-level Physics", profile.display_name)
        self.assertEqual("1.0.0", profile.profile_version)
        self.assertEqual(ROOT / "domains" / "university-level physics", profile.directory)

    def test_registered_domain_assets_are_complete(self):
        self.assertEqual([], domain_registry_errors(ROOT))
        profile = resolve_domain(ROOT)
        for section, key in (
            ("instructions", "sourceAnalysis"),
            ("instructions", "activityGeneration"),
            ("instructions", "visualGeneration"),
            ("instructions", "semanticAudit"),
            ("instructions", "repair"),
            ("rules", "content"),
            ("rules", "visual"),
            ("visuals", "templateRegistry"),
            ("visuals", "styleProfiles"),
            ("visuals", "rendererScript"),
            ("visuals", "stylesheet"),
            ("simulations", "modelRegistry"),
            ("simulations", "modelsModule"),
            ("validation", "visualValidatorModule"),
            ("verification", "policy"),
        ):
            self.assertTrue(profile.path(section, key).is_file(), f"{section}.{key}")

    def test_physics_specific_runtime_and_models_are_domain_owned(self):
        profile = resolve_domain(ROOT)
        renderer = profile.path("visuals", "rendererScript").read_text(encoding="utf-8")
        validator = profile.path("validation", "visualValidatorModule").read_text(encoding="utf-8")
        models = profile.path("simulations", "modelsModule").read_text(encoding="utf-8")
        self.assertIn("mechanics.cart_collision_1d", renderer)
        self.assertIn("mechanics.motion_1d_slider", validator)
        self.assertIn("evaluate_motion_1d", models)
        generic_validation = (ROOT / "app_generator" / "visuals" / "validation.py").read_text(encoding="utf-8")
        generic_runtime = (ROOT / "app" / "visual-renderers.js").read_text(encoding="utf-8")
        self.assertNotIn("mechanics.cart_collision_1d", generic_validation)
        self.assertNotIn("mechanics.cart_collision_1d", generic_runtime)

    def test_template_is_not_an_active_domain(self):
        registry = load_domain_registry(ROOT)
        self.assertNotIn("_template", {item["path"] for item in registry["domains"]})
        draft = json.loads((ROOT / "domains" / "_template" / "domain.json.example").read_text(encoding="utf-8"))
        self.assertEqual("draft", draft["status"])

    def test_registered_draft_domain_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            temp_root = Path(directory)
            shutil.copytree(ROOT / "domains", temp_root / "domains")
            profile_path = temp_root / "domains" / "university-level physics" / "domain.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            profile["status"] = "draft"
            profile_path.write_text(json.dumps(profile), encoding="utf-8")
            errors = domain_registry_errors(temp_root)
            self.assertTrue(any("not active" in error or "status must be active" in error for error in errors), errors)

    def test_registry_rejects_path_escape(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            temp_root = Path(directory)
            shutil.copytree(ROOT / "domains", temp_root / "domains")
            registry_path = temp_root / "domains" / "registry.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["domains"][0]["path"] = "../outside"
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            errors = domain_registry_errors(temp_root)
            self.assertTrue(any("escapes domains" in error or "does not exist" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()

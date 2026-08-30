import tempfile
import unittest
from pathlib import Path

from app_generator.config import load_config
from scripts.configure_project import render_project_configuration
from scripts import sync_workstation


ROOT = Path(__file__).resolve().parents[1]


class ProjectRecyclabilityTests(unittest.TestCase):
    def test_recycled_authority_contains_no_previous_service_identity(self):
        source = (ROOT / sync_workstation.PROJECT_CONFIG_RELATIVE_PATH).read_text(encoding="utf-8")
        rendered = render_project_configuration(
            source,
            {
                "project_name": "CleanProject",
                "source_root_url": "https://drive.google.com/open?id=clean-folder",
                "gem_url": "https://gemini.google.com/gem/clean-project",
                "login_name": "clean@example.com",
                "gem_name": "Clean Project generator",
            },
        )
        for previous_value in (
            "BrilliantContentGenerator",
            "1BqdcGJR3usQvItCNMC997fkcXaScNYqc",
            "1dZR01a7xJ9pveqo55MwzfuPV2i_tUQvJ",
            "815996ef2eef",
            "tlyoon@gmail.com",
            "BRILLIANT_GENERATOR_",
        ):
            self.assertNotIn(previous_value, rendered)

    def materialize(self, project_name: str, folder_id: str, state_root: Path):
        source = (ROOT / sync_workstation.PROJECT_CONFIG_RELATIVE_PATH).read_text(encoding="utf-8")
        configured = render_project_configuration(
            source,
            {
                "project_name": project_name,
                "source_root_url": f"https://drive.google.com/open?id={folder_id}",
                "gem_url": f"https://gemini.google.com/gem/{project_name.casefold()}",
                "gem_edit_url": f"https://gemini.google.com/gems/edit/{project_name.casefold()}",
                "login_name": f"{project_name.casefold()}@example.com",
                "gem_name": f"{project_name} generator",
            },
        )
        rendered = sync_workstation.render_project_config(
            configured.encode("utf-8"),
            repo_root=ROOT,
            state_root=state_root,
        )
        path = state_root.parent / f"{project_name}.local.toml"
        path.write_text(rendered, encoding="utf-8")
        return load_config(path, environ={})

    def test_two_projects_materialize_without_identity_or_state_leakage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            alpha = self.materialize("AlphaPhysics", "alpha-folder-id", root / "AlphaPhysics")
            beta = self.materialize("BetaMechanics", "beta-folder-id", root / "BetaMechanics")

        self.assertEqual("ALPHA_PHYSICS_GENERATOR_", alpha.env_prefix)
        self.assertEqual("BETA_MECHANICS_GENERATOR_", beta.env_prefix)
        self.assertNotEqual(alpha.state_dir, beta.state_dir)
        self.assertNotEqual(alpha.chrome_profile_dir, beta.chrome_profile_dir)
        self.assertNotEqual(alpha.drive_oauth_client_file, beta.drive_oauth_client_file)
        self.assertEqual("ALPHA_PHYSICS_COORDINATOR_TOKEN", alpha.coordinator_token_env)
        self.assertEqual("BETA_MECHANICS_COORDINATOR_TOKEN", beta.coordinator_token_env)
        self.assertNotEqual(alpha.sourcepath, beta.sourcepath)
        self.assertNotEqual(alpha.gem_url, beta.gem_url)
        self.assertNotEqual(alpha.gem_edit_url, beta.gem_edit_url)
        self.assertFalse(alpha.git_publish)
        self.assertFalse(alpha.git_auto_merge)
        self.assertFalse(beta.git_publish)
        self.assertFalse(beta.git_auto_merge)
        self.assertEqual("alpha-physics-section-15-1", alpha.for_subchapter("15.1").source_id)
        self.assertEqual("beta-mechanics-section-15-1", beta.for_subchapter("15.1").source_id)

    def test_current_project_values_are_not_embedded_in_runtime_defaults(self):
        forbidden = (
            "1BqdcGJR3usQvItCNMC997fkcXaScNYqc",
            "1dZR01a7xJ9pveqo55MwzfuPV2i_tUQvJ",
            "tlyoon@gmail.com",
        )
        runtime_files = tuple((ROOT / "app_generator").rglob("*.py"))
        runtime_files += (
            ROOT / "scripts" / "configure_project.py",
            ROOT / "scripts" / "sync_workstation.py",
        )
        for path in runtime_files:
            text = path.read_text(encoding="utf-8")
            for value in forbidden:
                self.assertNotIn(value, text, str(path.relative_to(ROOT)))


if __name__ == "__main__":
    unittest.main()

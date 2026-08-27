import tempfile
import unittest
from pathlib import Path

from app_generator.project import (
    ProjectIdentityError,
    environment_prefix,
    identity_from_payload,
    load_project_identity,
    state_root_for,
)


class ProjectIdentityTests(unittest.TestCase):
    def test_camel_case_project_name_derives_environment_prefix(self):
        self.assertEqual(
            "BRILLIANT_CONTENT_GENERATOR",
            environment_prefix("BrilliantContentGenerator"),
        )
        self.assertEqual("ANOTHER_PHYSICS_PROJECT", environment_prefix("AnotherPhysicsProject"))

    def test_windows_state_root_uses_project_name(self):
        root = state_root_for(
            "AnotherPhysicsProject",
            environ={"LOCALAPPDATA": r"C:\Users\person\AppData\Local"},
        )
        self.assertEqual("AnotherPhysicsProject", root.name)
        self.assertIn("AppData", str(root))

    def test_non_windows_state_root_is_project_scoped(self):
        root = state_root_for(
            "AnotherPhysicsProject",
            environ={},
            home=Path("/home/person"),
        )
        self.assertEqual(
            Path("/home/person/.local/state/AnotherPhysicsProject"),
            root,
        )

    def test_identity_exposes_all_project_derived_paths(self):
        identity = identity_from_payload(
            {"project": {"project_name": "ExampleProject"}},
            environ={"LOCALAPPDATA": "/local"},
        )
        self.assertEqual(Path("/local/ExampleProject/workstation-sync.toml"), identity.settings_path)
        self.assertEqual("drive-oauth-client.json", identity.oauth_client_file.name)
        self.assertEqual("chrome-profile", identity.chrome_profile_dir.name)
        self.assertEqual("runs", identity.runs_dir.name)

    def test_invalid_project_name_is_rejected(self):
        with self.assertRaises(ProjectIdentityError):
            environment_prefix("../unsafe")

    def test_load_identity_from_toml(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project.toml"
            path.write_text('[project]\nproject_name = "ExampleProject"\n', encoding="utf-8")
            identity = load_project_identity(path, environ={"LOCALAPPDATA": "/local"})
        self.assertEqual("EXAMPLE_PROJECT", identity.env_prefix)

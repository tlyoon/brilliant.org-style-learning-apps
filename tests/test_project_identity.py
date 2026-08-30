import tempfile
import unittest
from pathlib import Path

from app_generator.project import (
    ProjectIdentityError,
    environment_prefix,
    identity_from_payload,
    load_project_identity,
    project_slug,
    state_root_for,
)


class ProjectIdentityTests(unittest.TestCase):
    def test_camel_case_project_name_derives_environment_prefix_and_slug(self):
        self.assertEqual("MY_LEARNING_PROJECT", environment_prefix("MyLearningProject"))
        self.assertEqual("my-learning-project", project_slug("MyLearningProject"))
        self.assertEqual("ANOTHER_SUBJECT_PROJECT", environment_prefix("AnotherSubjectProject"))
        self.assertEqual("another-subject-project", project_slug("AnotherSubjectProject"))

    def test_windows_state_root_uses_project_name(self):
        root = state_root_for(
            "AnotherSubjectProject",
            environ={"LOCALAPPDATA": r"C:\Users\person\AppData\Local"},
        )
        self.assertEqual("AnotherSubjectProject", root.name)
        self.assertIn("AppData", str(root))

    def test_non_windows_state_root_is_project_scoped(self):
        root = state_root_for(
            "AnotherSubjectProject",
            environ={},
            home=Path("/home/person"),
        )
        self.assertEqual(
            Path("/home/person/.local/state/AnotherSubjectProject"),
            root,
        )

    def test_identity_exposes_all_project_derived_values(self):
        identity = identity_from_payload(
            {"project": {"project_name": "ExampleProject"}},
            environ={"LOCALAPPDATA": "/local"},
        )
        self.assertEqual("example-project", identity.slug)
        self.assertEqual(Path("/local/ExampleProject/workstation-sync.toml"), identity.settings_path)
        self.assertEqual("drive-oauth-client.json", identity.oauth_client_file.name)
        self.assertEqual("chrome-profile", identity.chrome_profile_dir.name)
        self.assertEqual("runs", identity.runs_dir.name)
        tokens = identity.tokens(repo_root=Path("/repo"))
        self.assertEqual("example-project", tokens["${PROJECT_SLUG}"])
        self.assertEqual("EXAMPLE_PROJECT", tokens["${PROJECT_ENV_PREFIX}"])

    def test_invalid_project_name_is_rejected(self):
        with self.assertRaises(ProjectIdentityError):
            environment_prefix("../unsafe")

    def test_load_identity_from_toml(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project.toml"
            path.write_text('[project]\nproject_name = "ExampleProject"\n', encoding="utf-8")
            identity = load_project_identity(path, environ={"LOCALAPPDATA": "/local"})
        self.assertEqual("EXAMPLE_PROJECT", identity.env_prefix)
        self.assertEqual("example-project", identity.slug)

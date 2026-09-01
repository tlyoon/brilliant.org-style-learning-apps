import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app_generator.config import load_config
from app_generator.coordinator.managed import ManagedCoordinatorRuntime, ensure_managed_coordinator
from app_generator.coordinator.protocol import REQUIRED_COORDINATOR_VERSION
from app_generator.coordinator.verified import ensure_coordinator_ready
from app_generator.errors import CoordinatorError


class ManagedCoordinatorTests(unittest.TestCase):
    def make_config(self, root: Path, *, coordinator_url: str = ""):
        repo = root / "repo"
        (repo / "content" / "schema").mkdir(parents=True)
        (repo / "AGENTS.md").write_text("# test\n", encoding="utf-8")
        path = root / "project.toml"
        path.write_text(
            "[project]\n"
            'project_name = "ManagedProject"\n'
            "[placeholders]\n"
            'sourcepath = "https://drive.google.com/open?id=managed-source-root"\n'
            'pdf_subchapter_path = "8.1"\n'
            'target_filename = "source.pdf"\n'
            'target_file = "{sourcepath}/**/{pdf_subchapter_path}/{target_filename}"\n'
            "[source_tree]\n"
            'source_id_prefix = "managed"\n'
            "[gemini]\n"
            'gem_url = "https://gemini.google.com/gem/test"\n'
            'gem_name = "generator"\n'
            'login_name = "owner@example.com"\n'
            "[paths]\n"
            f"chrome_profile_dir = {json.dumps(str(root / 'state' / 'chrome-profile'))}\n"
            f"state_dir = {json.dumps(str(root / 'state' / 'runs'))}\n"
            f"drive_oauth_client_file = {json.dumps(str(root / 'state' / 'credentials' / 'client.json'))}\n"
            f"drive_token_file = {json.dumps(str(root / 'state' / 'credentials' / 'token.json'))}\n"
            "[automation]\n"
            'selection_mode = "auto"\n'
            f"coordinator_url = {json.dumps(coordinator_url)}\n"
            'coordinator_token_env = "MANAGED_PROJECT_COORDINATOR_TOKEN"\n'
            "[repository]\n"
            f"repo_root = {json.dumps(str(repo))}\n"
            "[git]\n"
            "git_publish = true\n"
            "[run]\n"
            'package_id = "chapter-{chapter_number}-section-{section_slug}"\n'
            'chapter = "Chapter {chapter_number}"\n'
            'subchapter = "{subchapter_id}"\n'
            'chapter_dir = "chapter-{chapter_number}"\n'
            'section_dir = "section-{section_slug}"\n'
            'learning_boundary = "Controlled {subchapter_id}"\n'
            'source_id = "{source_id_prefix}-section-{section_slug}"\n'
            'edition = "Edition"\n'
            'heading = "Section {subchapter_id}"\n'
            'page_range = "Complete PDF"\n'
            'reviewer = "Reviewer"\n'
            'rights_note = "Controlled access"\n',
            encoding="utf-8",
        )
        return load_config(path, environ={})

    def runtime(self):
        return ManagedCoordinatorRuntime(
            project_name="ManagedProject",
            coordinator_version=REQUIRED_COORDINATOR_VERSION,
            coordinator_url="https://script.google.com/macros/s/deployment/exec",
            worker_token="private-worker-token",
            script_id="script-id",
            deployment_id="deployment-id",
            spreadsheet_id="spreadsheet-id",
            checkpoint_folder_id="checkpoint-folder-id",
        )

    def test_empty_coordinator_url_selects_repository_managed_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.make_config(Path(directory))
            self.assertEqual("github_actions", config.coordinator_management)
            self.assertEqual("", config.coordinator_url)

    def test_explicit_coordinator_url_preserves_external_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.make_config(
                Path(directory),
                coordinator_url="https://script.google.com/macros/s/existing/exec",
            )
            self.assertEqual("external", config.coordinator_management)

    def test_current_runtime_is_applied_without_deployment_request(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.make_config(Path(directory))
            old = os.environ.pop(config.coordinator_token_env, None)
            try:
                with patch(
                    "app_generator.coordinator.managed.discover_managed_runtime",
                    return_value=self.runtime(),
                ), patch(
                    "app_generator.coordinator.managed.trigger_managed_deployment",
                    side_effect=AssertionError("deployment should not be requested"),
                ):
                    ready = ensure_managed_coordinator(config)
                self.assertEqual(self.runtime().coordinator_url, ready.coordinator_url)
                self.assertEqual("private-worker-token", os.environ[config.coordinator_token_env])
            finally:
                if old is None:
                    os.environ.pop(config.coordinator_token_env, None)
                else:
                    os.environ[config.coordinator_token_env] = old

    def test_unhealthy_current_runtime_requests_one_serialized_repair(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.make_config(Path(directory))
            ready = config.__class__(**{**config.__dict__, "coordinator_url": self.runtime().coordinator_url})
            attempts = {"health": 0, "deploy": 0}

            class FakeCoordinator:
                def __init__(self, supplied):
                    self.supplied = supplied

                def health(self, *, require_checkpoints=False):
                    attempts["health"] += 1
                    if attempts["health"] == 1:
                        raise CoordinatorError("temporarily unhealthy")

            def deploy(_config):
                attempts["deploy"] += 1

            with patch(
                "app_generator.coordinator.verified.ensure_managed_coordinator",
                return_value=ready,
            ), patch(
                "app_generator.coordinator.verified.CoordinatorClient",
                FakeCoordinator,
            ), patch(
                "app_generator.coordinator.verified.trigger_managed_deployment",
                deploy,
            ):
                result = ensure_coordinator_ready(config, sleeper=lambda seconds: None)
            self.assertEqual(ready.coordinator_url, result.coordinator_url)
            self.assertEqual(1, attempts["deploy"])
            self.assertEqual(2, attempts["health"])

    def test_workflow_serializes_manual_ensure_requests(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github" / "workflows" / "ensure-coordinator.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("group: managed-coordinator-${{ inputs.project_name }}", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertNotIn("  push:\n", workflow)
        self.assertIn("COORDINATOR_ADMIN_TOKEN_JSON: ${{ secrets.COORDINATOR_ADMIN_TOKEN_JSON }}", workflow)

    def test_apps_script_manifest_is_token_protected_public_webapp(self):
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads(
            (root / "coordinator" / "apps-script" / "appsscript.json").read_text(encoding="utf-8")
        )
        self.assertEqual("ANYONE_ANONYMOUS", manifest["webapp"]["access"])
        self.assertEqual("USER_DEPLOYING", manifest["webapp"]["executeAs"])


if __name__ == "__main__":
    unittest.main()

import os
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

from app_generator.config import load_config
from scripts import sync_configured_workstation as configured_sync


class ConfiguredWorkstationSyncTests(unittest.TestCase):
    def setUp(self):
        self._project_config_relative_path = configured_sync.core.PROJECT_CONFIG_RELATIVE_PATH
        self._managed_config_header = configured_sync.core.MANAGED_CONFIG_HEADER
        self._allowed_project_keys = configured_sync.core.ALLOWED_PROJECT_KEYS
        self.addCleanup(self._restore_core_globals)

    def _restore_core_globals(self):
        configured_sync.core.PROJECT_CONFIG_RELATIVE_PATH = self._project_config_relative_path
        configured_sync.core.MANAGED_CONFIG_HEADER = self._managed_config_header
        configured_sync.core.ALLOWED_PROJECT_KEYS = self._allowed_project_keys

    def test_configure_core_selects_dedicated_project_authority(self):
        configured_sync.configure_core()
        self.assertEqual(
            Path("config") / "configure_project.toml",
            configured_sync.core.PROJECT_CONFIG_RELATIVE_PATH,
        )
        self.assertIn("compatibility", configured_sync.core.ALLOWED_PROJECT_KEYS)
        self.assertEqual(
            {"legacy_environment_prefix"},
            configured_sync.core.ALLOWED_PROJECT_KEYS["compatibility"],
        )

    def test_authoritative_config_round_trip_preserves_local_identity_and_main_source_root(self):
        configured_sync.configure_core()
        authority = Path(__file__).resolve().parents[1] / "config" / "configure_project.toml"
        raw = authority.read_text(encoding="utf-8")
        source_root = tomllib.loads(raw)["placeholders"]["sourcepath"]
        raw = raw.replace('oauth_login = "tlyoon@gmail.com"', 'oauth_login = "oauth@example.com"')
        raw = raw.replace('login_name = "tlyoon@gmail.com"', 'login_name = "default@example.com"')

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repo = base / "repo"
            state = base / "state"
            (repo / "content" / "schema").mkdir(parents=True)
            (repo / "AGENTS.md").write_text("# Synthetic repository\n", encoding="utf-8")
            source = repo / configured_sync.core.PROJECT_CONFIG_RELATIVE_PATH
            source.parent.mkdir(parents=True)
            source.write_text(raw, encoding="utf-8")
            generated = repo / "project.local.toml"
            generated.write_text(
                '[local_gemini]\nlogin_name = "local@example.com"\n'
                'gem_url = "https://gemini.google.com/gem/local"\n'
                'gem_edit_url = "https://gemini.google.com/gems/edit/local"\n',
                encoding="utf-8",
            )
            settings = configured_sync.core.SyncSettings(
                settings_path=state / "workstation-sync.toml", repo_root=repo,
                remote="origin", branch="main", project_name="BrilliantContentGenerator",
                env_prefix="BRILLIANT_CONTENT_GENERATOR", state_root=state,
                project_config_file=source, login_name="oauth@example.com",
                oauth_client_file=state / "credentials" / "drive-oauth-client.json",
                oauth_token_file=state / "credentials" / "drive-oauth-token.json",
                generated_config_file=generated, run_tests=True, run_doctor=True,
            )

            with patch.dict(os.environ, {"LOCALAPPDATA": str(base)}, clear=True):
                for _ in range(2):
                    configured_sync.core.install_project_config(settings)
                    config = load_config(generated, environ={})
                    self.assertEqual("oauth@example.com", config.oauth_login)
                    self.assertEqual("local@example.com", config.login_name)
                    self.assertEqual(source_root, config.sourcepath)
                    self.assertEqual("https://gemini.google.com/gem/local", config.gem_url)
                    self.assertEqual("https://gemini.google.com/gems/edit/local", config.gem_edit_url)
                    self.assertEqual(state / "runs", config.state_dir)
                    self.assertEqual("local@example.com", config.for_subchapter("8.6").login_name)
                    self.assertEqual("oauth@example.com", config.for_subchapter("8.6").oauth_login)
                    self.assertFalse(generated.with_name("project.local.toml.part").exists())

    def test_post_sync_subprocess_stays_on_configured_wrapper(self):
        calls = []

        def original_run(arguments, *args, **kwargs):
            calls.append(arguments)
            return 0

        run = configured_sync._configured_subprocess_run(original_run)
        run([
            "python",
            str(Path("scripts") / "sync_workstation.py"),
            "--settings",
            r"C:\state\workstation-sync.toml",
            "--post-sync",
            "--quick",
        ])
        self.assertEqual(
            [
                "python",
                "-m",
                "scripts.sync_configured_workstation",
                "--settings",
                r"C:\state\workstation-sync.toml",
                "--post-sync",
                "--quick",
            ],
            calls[0],
        )


if __name__ == "__main__":
    unittest.main()

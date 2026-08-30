import unittest
from pathlib import Path

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

    def test_post_sync_subprocess_stays_on_configured_wrapper(self):
        calls = []

        def original_run(arguments, *args, **kwargs):
            calls.append(arguments)
            return 0

        run = configured_sync._configured_subprocess_run(original_run)
        run([
            "python",
            r"C:\repo\scripts\sync_workstation.py",
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

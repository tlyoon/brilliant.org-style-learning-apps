import tempfile
import tomllib
import unittest
from pathlib import Path

from scripts.sync_workstation import _write_initial_settings, load_settings


DRIVE_URL = "https://drive.google.com/open?id=1BqdcGJR3usQvItCNMC997fkcXaScNYqc&usp=drive_fs"


class WorkstationSyncTests(unittest.TestCase):
    def test_initial_settings_remove_quotes_pasted_around_drive_url(self):
        with tempfile.TemporaryDirectory() as directory:
            settings_path = Path(directory) / "workstation-sync.toml"

            _write_initial_settings(
                settings_path,
                projects_folder_url=f'"{DRIVE_URL}"',
                login_name="person@example.com",
                branch="main",
            )

            with settings_path.open("rb") as handle:
                payload = tomllib.load(handle)
            self.assertEqual(DRIVE_URL, payload["drive"]["projects_folder_url"])

    def test_load_settings_repairs_preexisting_quoted_drive_url(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings_path = root / "workstation-sync.toml"
            settings_path.write_text(
                "\n".join(
                    (
                        "[repository]",
                        'remote = "origin"',
                        'branch = "main"',
                        "[drive]",
                        f'projects_folder_url = "\\\"{DRIVE_URL}\\\""',
                        'login_name = "person@example.com"',
                        "[output]",
                        'generated_config_file = "generator.shared.local.toml"',
                    )
                ),
                encoding="utf-8",
            )

            settings = load_settings(settings_path, repo_root=root)

            self.assertEqual(DRIVE_URL, settings.projects_folder_url)


if __name__ == "__main__":
    unittest.main()

import hashlib
import tempfile
import tomllib
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app_generator.config import load_config as load_generator_config
from scripts.sync_workstation import (
    MAX_PROJECT_CONFIG_BYTES,
    PROJECT_CONFIG_RELATIVE_PATH,
    SyncSettings,
    WorkstationSyncError,
    _read_project_config,
    _write_initial_settings,
    install_project_config,
    load_settings,
    render_project_config,
)


SOURCE_URL = "https://drive.google.com/open?id=1BqdcGJR3usQvItCNMC997fkcXaScNYqc&usp=drive_fs"
GEM_URL = "https://gemini.google.com/gem/1dZR01a7xJ9pveqo55MwzfuPV2i_tUQvJ?usp=sharing"


def _settings(root: Path, *, login_name: str = "person@example.com") -> SyncSettings:
    credential_root = root.parent / "workstation-credentials"
    return SyncSettings(
        settings_path=root.parent / "workstation-sync.toml",
        repo_root=root,
        remote="origin",
        branch="main",
        project_config_file=root / PROJECT_CONFIG_RELATIVE_PATH,
        login_name=login_name,
        oauth_client_file=credential_root / "drive-oauth-client.json",
        oauth_token_file=credential_root / "drive-oauth-token.json",
        generated_config_file=root / "generator.shared.local.toml",
        run_tests=True,
        run_doctor=True,
    )


class WorkstationSyncTests(unittest.TestCase):
    def test_tracked_project_config_is_accepted_by_the_synchronizer(self):
        root = Path(__file__).resolve().parents[1]
        source = root / PROJECT_CONFIG_RELATIVE_PATH

        with tempfile.TemporaryDirectory() as directory:
            rendered = render_project_config(
                source.read_bytes(),
                repo_root=root,
                state_root=Path(directory),
            )
            rendered_path = Path(directory) / "generator.shared.local.toml"
            rendered_path.write_text(rendered, encoding="utf-8")
            config = load_generator_config(rendered_path)

        payload = tomllib.loads(rendered)
        self.assertEqual(root.resolve(), Path(payload["repository"]["repo_root"]).resolve())
        self.assertEqual(SOURCE_URL, payload["placeholders"]["sourcepath"])
        self.assertEqual(GEM_URL, payload["placeholders"]["gemini-gem"])
        self.assertEqual("8.1", payload["placeholders"]["pdf_subchapter_path"])
        self.assertEqual("tlyoon@gmail.com", config.login_name)
        self.assertEqual(SOURCE_URL, config.sourcepath)

    def test_project_name_is_present_in_the_active_configuration(self):
        root = Path(__file__).resolve().parents[1]
        with (root / PROJECT_CONFIG_RELATIVE_PATH).open("rb") as handle:
            payload = tomllib.load(handle)

        self.assertEqual("BrilliantContentGenerator", payload["project"]["project_name"])

    def test_project_configuration_rejects_invalid_project_name(self):
        raw = (
            b'[project]\nproject_name = "not valid"\n'
            b'[placeholders]\nloginname = "person@example.com"\n'
            b'[repository]\nrepo_root = "${REPO_ROOT}"\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(WorkstationSyncError, "project.project_name"):
                render_project_config(raw, repo_root=Path(directory), state_root=Path(directory))

    def test_batch_entrypoint_has_no_projects_folder_dependency(self):
        entrypoint = Path(__file__).resolve().parents[1] / "sync-workstation.cmd"
        content = entrypoint.read_text(encoding="utf-8")

        self.assertNotIn("BRILLIANT_SYNC_PROJECTS_FOLDER_URL", content)
        self.assertNotIn("--projects-folder", content)
        self.assertIn('set "BRILLIANT_SYNC_LOGIN_NAME=tlyoon@gmail.com"', content)
        self.assertIn('set "BRILLIANT_SYNC_BRANCH=main"', content)
        command = next(line for line in content.splitlines() if line.startswith("python scripts\\sync_workstation.py"))
        self.assertIn('--login-name "%BRILLIANT_SYNC_LOGIN_NAME%"', command)
        self.assertIn('--branch "%BRILLIANT_SYNC_BRANCH%"', command)
        self.assertTrue(command.endswith(" %*"), "explicit arguments must override the defaults")

    def test_initial_settings_do_not_reference_projects_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            settings_path = Path(directory) / "workstation-sync.toml"

            _write_initial_settings(
                settings_path,
                login_name="person@example.com",
                branch="main",
            )

            with settings_path.open("rb") as handle:
                payload = tomllib.load(handle)
            self.assertEqual("person@example.com", payload["drive"]["login_name"])
            self.assertNotIn("projects_folder_url", payload["drive"])
            self.assertNotIn("project_config_name", payload["drive"])

    def test_load_settings_tolerates_obsolete_projects_fields(self):
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
                        'projects_folder_url = "https://drive.google.com/drive/folders/legacy"',
                        'project_config_name = "generator.shared.toml"',
                        'login_name = "person@example.com"',
                        "[output]",
                        'generated_config_file = "generator.shared.local.toml"',
                    )
                ),
                encoding="utf-8",
            )

            settings = load_settings(settings_path, repo_root=root)

            self.assertEqual(root / PROJECT_CONFIG_RELATIVE_PATH, settings.project_config_file)
            self.assertEqual("person@example.com", settings.login_name)

    def test_read_project_config_rejects_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = _settings(Path(directory))

            with self.assertRaisesRegex(WorkstationSyncError, "missing or not a regular file"):
                _read_project_config(settings)

    def test_read_project_config_rejects_oversized_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / PROJECT_CONFIG_RELATIVE_PATH
            source.parent.mkdir(parents=True)
            source.write_bytes(b"x" * (MAX_PROJECT_CONFIG_BYTES + 1))

            with self.assertRaisesRegex(WorkstationSyncError, "256 KiB"):
                _read_project_config(_settings(root))

    def test_install_uses_tracked_config_and_writes_managed_local_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / PROJECT_CONFIG_RELATIVE_PATH
            source.parent.mkdir(parents=True)
            raw = (
                b'[project]\nproject_name = "ExampleProject"\n'
                b'[placeholders]\nloginname = "person@example.com"\n'
                b'[repository]\nrepo_root = "${REPO_ROOT}"\n'
            )
            source.write_bytes(raw)
            settings = _settings(root)

            with patch(
                "app_generator.config.load_config",
                return_value=SimpleNamespace(login_name="person@example.com"),
            ):
                digest = install_project_config(settings)

            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            installed = settings.generated_config_file.read_text(encoding="utf-8")
            self.assertTrue(installed.startswith("# Managed by scripts/sync_workstation.py"))
            self.assertIn(root.resolve().as_posix(), installed)
            installed_payload = tomllib.loads(installed)
            self.assertEqual(
                str(settings.oauth_client_file),
                installed_payload["workstation"]["drive_oauth_client_file"],
            )
            self.assertEqual(
                str(settings.oauth_token_file),
                installed_payload["workstation"]["drive_token_file"],
            )

    def test_install_rejects_machine_and_shared_account_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / PROJECT_CONFIG_RELATIVE_PATH
            source.parent.mkdir(parents=True)
            source.write_text(
                '[project]\nproject_name = "ExampleProject"\n'
                '[placeholders]\nloginname = "person@example.com"\n'
                '[repository]\nrepo_root = "${REPO_ROOT}"\n',
                encoding="utf-8",
            )
            settings = _settings(root)

            with patch(
                "app_generator.config.load_config",
                return_value=SimpleNamespace(login_name="different@example.com"),
            ):
                with self.assertRaisesRegex(WorkstationSyncError, "workstation settings expect"):
                    install_project_config(settings)

            self.assertFalse(settings.generated_config_file.exists())

    def test_tracked_config_excludes_machine_local_and_secret_fields(self):
        root = Path(__file__).resolve().parents[1]
        with (root / PROJECT_CONFIG_RELATIVE_PATH).open("rb") as handle:
            payload = tomllib.load(handle)
        keys = {key for table in payload.values() for key in table}

        for forbidden in (
            "drive_oauth_client_file",
            "drive_token_file",
            "chrome_profile_dir",
            "debugger_address",
            "state_dir",
            "worker_id",
            "source_files",
        ):
            self.assertNotIn(forbidden, keys)


if __name__ == "__main__":
    unittest.main()

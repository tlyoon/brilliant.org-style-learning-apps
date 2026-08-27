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
    _parser,
)


SOURCE_URL = "https://drive.google.com/open?id=1BqdcGJR3usQvItCNMC997fkcXaScNYqc&usp=drive_fs"
GEM_URL = "https://gemini.google.com/gem/1dZR01a7xJ9pveqo55MwzfuPV2i_tUQvJ?usp=sharing"


def _settings(root: Path, *, login_name: str = "person@example.com") -> SyncSettings:
    state_root = root.parent / "BrilliantContentGenerator"
    credential_root = state_root / "credentials"
    return SyncSettings(
        settings_path=root.parent / "workstation-sync.toml",
        repo_root=root,
        remote="origin",
        branch="main",
        project_name="BrilliantContentGenerator",
        env_prefix="BRILLIANT_CONTENT_GENERATOR",
        state_root=state_root,
        project_config_file=root / PROJECT_CONFIG_RELATIVE_PATH,
        login_name=login_name,
        oauth_client_file=credential_root / "drive-oauth-client.json",
        oauth_token_file=credential_root / "drive-oauth-token.json",
        generated_config_file=root / "project.local.toml",
        run_tests=True,
        run_doctor=True,
    )


class WorkstationSyncTests(unittest.TestCase):
    def test_initialization_only_flag_is_available(self):
        args = _parser().parse_args(["--init-settings-only"])
        self.assertTrue(args.init_settings_only)

    def test_tracked_project_config_is_accepted_by_the_synchronizer(self):
        root = Path(__file__).resolve().parents[1]
        source = root / PROJECT_CONFIG_RELATIVE_PATH

        with tempfile.TemporaryDirectory() as directory:
            rendered = render_project_config(
                source.read_bytes(),
                repo_root=root,
                state_root=Path(directory),
            )
            rendered_path = Path(directory) / "project.local.toml"
            rendered_path.write_text(rendered, encoding="utf-8")
            config = load_generator_config(rendered_path)

        payload = tomllib.loads(rendered)
        self.assertEqual(root.resolve(), Path(payload["repository"]["repo_root"]).resolve())
        self.assertEqual(SOURCE_URL, payload["placeholders"]["sourcepath"])
        self.assertEqual(GEM_URL, payload["placeholders"]["gemini-gem"])
        self.assertEqual("8.1", payload["placeholders"]["pdf_subchapter_path"])
        self.assertEqual("tlyoon@gmail.com", config.login_name)
        self.assertEqual(SOURCE_URL, config.sourcepath)
        self.assertEqual(
            "BRILLIANT_CONTENT_GENERATOR_COORDINATOR_TOKEN",
            config.coordinator_token_env,
        )
        self.assertEqual(Path(directory).resolve() / "runs", config.state_dir)
        recycled = config.for_subchapter("15.1")
        self.assertEqual("chapter-15-section-15-1", recycled.package_id)
        self.assertEqual("chapter-15", recycled.chapter_dir)
        self.assertEqual("section-15-1", recycled.section_dir)
        self.assertEqual("serway-section-15-1", recycled.source_id)

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
            b'[paths]\nstate_root = "${STATE_ROOT}"\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(WorkstationSyncError, "project.project_name"):
                render_project_config(raw, repo_root=Path(directory), state_root=Path(directory))

    def test_batch_entrypoint_has_no_projects_folder_dependency(self):
        entrypoint = Path(__file__).resolve().parents[1] / "sync-workstation.cmd"
        content = entrypoint.read_text(encoding="utf-8")

        self.assertNotIn("BRILLIANT_SYNC_PROJECTS_FOLDER_URL", content)
        self.assertNotIn("--projects-folder", content)
        self.assertNotIn("BRILLIANT_SYNC_", content)
        command = next(line for line in content.splitlines() if line.startswith("python scripts\\sync_workstation.py"))
        self.assertEqual("python scripts\\sync_workstation.py %*", command)

    def test_initial_settings_do_not_reference_projects_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            settings_path = Path(directory) / "workstation-sync.toml"

            _write_initial_settings(
                settings_path,
                login_name="person@example.com",
                branch="main",
                project_name="ExampleProject",
            )

            with settings_path.open("rb") as handle:
                payload = tomllib.load(handle)
            self.assertEqual("person@example.com", payload["drive"]["login_name"])
            self.assertEqual("ExampleProject", payload["project"]["project_name"])
            self.assertNotIn("projects_folder_url", payload["drive"])
            self.assertNotIn("shared_config_name", payload["drive"])

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
                        'shared_config_name = "generator.shared.toml"',
                        'login_name = "person@example.com"',
                        "[output]",
                        'generated_config_file = "project.local.toml"',
                    )
                ),
                encoding="utf-8",
            )

            settings = load_settings(
                settings_path,
                repo_root=root,
                project_name="BrilliantContentGenerator",
            )

            self.assertEqual(root / PROJECT_CONFIG_RELATIVE_PATH, settings.project_config_file)
            self.assertEqual("person@example.com", settings.login_name)

    def test_load_settings_rejects_another_projects_settings_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings_path = root / "workstation-sync.toml"
            settings_path.write_text(
                '[project]\nproject_name = "AnotherProject"\n'
                '[drive]\nlogin_name = "person@example.com"\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(WorkstationSyncError, "belong to"):
                load_settings(
                    settings_path,
                    repo_root=root,
                    project_name="BrilliantContentGenerator",
                )

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
                b'[project]\nproject_name = "BrilliantContentGenerator"\n'
                b'[placeholders]\nloginname = "person@example.com"\n'
                b'[repository]\nrepo_root = "${REPO_ROOT}"\n'
                b'[paths]\n'
                b'state_root = "${STATE_ROOT}"\n'
                b'workstation_settings = "${STATE_ROOT}/workstation-sync.toml"\n'
                b'drive_oauth_client_file = "${STATE_ROOT}/credentials/drive-oauth-client.json"\n'
                b'drive_token_file = "${STATE_ROOT}/credentials/drive-oauth-token.json"\n'
                b'chrome_profile_dir = "${STATE_ROOT}/chrome-profile"\n'
                b'state_dir = "${STATE_ROOT}/runs"\n'
            )
            source.write_bytes(raw)
            settings = _settings(root)

            with patch(
                "app_generator.config.load_config",
                return_value=SimpleNamespace(
                    login_name="person@example.com",
                    drive_oauth_client_file=settings.oauth_client_file,
                    drive_token_file=settings.oauth_token_file,
                    chrome_profile_dir=settings.state_root / "chrome-profile",
                    state_dir=settings.state_root / "runs",
                ),
            ):
                digest = install_project_config(settings)

            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            installed = settings.generated_config_file.read_text(encoding="utf-8")
            self.assertTrue(installed.startswith("# Managed by scripts/sync_workstation.py"))
            self.assertIn(root.resolve().as_posix(), installed)
            installed_payload = tomllib.loads(installed)
            self.assertEqual(
                settings.oauth_client_file.as_posix(),
                installed_payload["paths"]["drive_oauth_client_file"],
            )
            self.assertEqual(
                settings.oauth_token_file.as_posix(),
                installed_payload["paths"]["drive_token_file"],
            )

    def test_install_rejects_machine_and_project_account_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / PROJECT_CONFIG_RELATIVE_PATH
            source.parent.mkdir(parents=True)
            source.write_text(
                '[project]\nproject_name = "BrilliantContentGenerator"\n'
                '[placeholders]\nloginname = "person@example.com"\n'
                '[repository]\nrepo_root = "${REPO_ROOT}"\n'
                '[paths]\nstate_root = "${STATE_ROOT}"\n'
                'workstation_settings = "${STATE_ROOT}/workstation-sync.toml"\n'
                'drive_oauth_client_file = "${STATE_ROOT}/credentials/drive-oauth-client.json"\n'
                'drive_token_file = "${STATE_ROOT}/credentials/drive-oauth-token.json"\n'
                'chrome_profile_dir = "${STATE_ROOT}/chrome-profile"\n'
                'state_dir = "${STATE_ROOT}/runs"\n',
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
            "debugger_address",
            "worker_id",
            "source_files",
        ):
            self.assertNotIn(forbidden, keys)
        for value in payload["paths"].values():
            self.assertTrue(str(value).startswith("${STATE_ROOT}"))


if __name__ == "__main__":
    unittest.main()

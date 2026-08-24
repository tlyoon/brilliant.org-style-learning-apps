import tempfile
import tomllib
import unittest
from pathlib import Path

from scripts.sync_workstation import WorkstationSyncError, load_settings, render_shared_config


SHARED = b'''[placeholders]
sourcepath = "https://drive.google.com/open?id=1234567890abcdef"
gemini-gem = "https://gemini.google.com/gem/example"
loginname = "worker@example.com"
pdf_subchapter_path = "8.1"
target_filename = "source.pdf"
target_file = "{sourcepath}/**/{pdf_subchapter_path}/{target_filename}"

[repository]
repo_root = "${REPO_ROOT}"

[run]
package_id = "chapter-8-section-8-1"
chapter = "Chapter 8"
subchapter = "Section 8.1"
chapter_dir = "chapter-8"
section_dir = "section-8-1"
learning_boundary = "Energy concepts"
source_id = "serway-section-8-1"
edition = "Controlled edition"
heading = "Section 8.1"
page_range = "Controlled section"
reviewer = "Content owner"
rights_note = "Authorized original transformation only."
'''


class WorkstationSyncTests(unittest.TestCase):
    def test_shared_config_renders_only_portable_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            state = Path(directory) / "state"
            rendered = render_shared_config(SHARED, repo_root=root, state_root=state)
            self.assertIn(root.resolve().as_posix(), rendered)
            self.assertNotIn("${REPO_ROOT}", rendered)
            self.assertTrue(rendered.startswith("# Managed by"))

    def test_shared_config_rejects_credential_paths(self):
        unsafe = SHARED + b'''\n[google_drive]\n drive_oauth_client_file = "secret.json"\n'''
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(WorkstationSyncError, "disallowed key"):
                render_shared_config(
                    unsafe,
                    repo_root=Path(directory) / "repo",
                    state_root=Path(directory) / "state",
                )

    def test_shared_config_requires_explicit_repository_root(self):
        unsafe = SHARED.replace(
            b'''[repository]\nrepo_root = "${REPO_ROOT}"\n\n''',
            b"",
        )
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(WorkstationSyncError, "repository"):
                render_shared_config(
                    unsafe,
                    repo_root=Path(directory) / "repo",
                    state_root=Path(directory) / "state",
                )

    def test_machine_settings_expand_and_keep_output_in_repo(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            settings_file = Path(directory) / "settings.toml"
            settings_file.write_text(
                '''[repository]
remote = "origin"
branch = "main"
[drive]
projects_folder_url = "https://drive.google.com/open?id=1234567890abcdef"
login_name = "worker@example.com"
[output]
generated_config_file = "generator.shared.local.toml"
[checks]
run_tests = true
run_doctor = false
''',
                encoding="utf-8",
            )
            settings = load_settings(settings_file, repo_root=root)
            self.assertEqual(root.resolve(), settings.repo_root)
            self.assertEqual(root / "generator.shared.local.toml", settings.generated_config_file)
            self.assertFalse(settings.run_doctor)

    def test_machine_settings_reject_oauth_material_inside_repo(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            settings_file = Path(directory) / "settings.toml"
            settings_file.write_text(
                f'''[repository]
remote = "origin"
branch = "main"
[drive]
projects_folder_url = "https://drive.google.com/open?id=1234567890abcdef"
login_name = "worker@example.com"
oauth_client_file = "{(root / 'oauth-client.json').as_posix()}"
[output]
generated_config_file = "generator.shared.local.toml"
''',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(WorkstationSyncError, "outside the repository"):
                load_settings(settings_file, repo_root=root)

    def test_checked_in_shared_example_is_valid_toml(self):
        example = Path("config/generator.shared.example.toml")
        with example.open("rb") as handle:
            payload = tomllib.load(handle)
        self.assertEqual("${REPO_ROOT}", payload["repository"]["repo_root"])


if __name__ == "__main__":
    unittest.main()

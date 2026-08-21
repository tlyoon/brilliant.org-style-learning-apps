import json
import tempfile
import unittest
from pathlib import Path

from app_generator.config import load_config
from app_generator.errors import ConfigurationError, RepositoryCompatibilityError


class GeneratorConfigTests(unittest.TestCase):
    def make_config(self, root: Path, source_files: list[Path]) -> Path:
        repo = root / "repo"
        (repo / "content" / "schema").mkdir(parents=True)
        (repo / "AGENTS.md").write_text("# test\n", encoding="utf-8")
        config = root / "generator.toml"
        quoted_sources = ", ".join(json.dumps(str(path)) for path in source_files)
        config.write_text(
            "[gemini]\n"
            'gem_url = "https://gemini.google.com/gem/test"\n'
            'gem_edit_url = "https://gemini.google.com/gem/test/edit"\n'
            'gem_name = "app content generator"\n'
            'login_name = "file@example.com"\n'
            "[repository]\n"
            f"repo_root = {json.dumps(str(repo))}\n"
            "[run]\n"
            'package_id = "chapter-8-section-8-1"\n'
            'chapter = "Chapter"\n'
            'subchapter = "8.1 Topic"\n'
            'chapter_dir = "chapter-8"\n'
            'section_dir = "section-8-1"\n'
            'learning_boundary = "Controlled boundary"\n'
            f"source_files = [{quoted_sources}]\n"
            'source_id = "source-eight-one"\n'
            'edition = "Edition"\n'
            'heading = "Heading"\n'
            'page_range = "1-3"\n'
            'reviewer = "Reviewer"\n'
            'rights_note = "Controlled access"\n',
            encoding="utf-8",
        )
        return config

    def test_precedence_cli_then_environment_then_file_then_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.pdf"
            source.write_bytes(b"synthetic")
            path = self.make_config(root, [source])
            config = load_config(
                path,
                cli_overrides={"login_name": "cli@example.com"},
                environ={"BRILLIANT_GENERATOR_LOGIN_NAME": "env@example.com", "BRILLIANT_GENERATOR_LOG_LEVEL": "debug"},
            )
            self.assertEqual("cli@example.com", config.login_name)
            self.assertEqual("DEBUG", config.log_level)
            self.assertEqual(4, config.max_repair_attempts)

    def test_current_manifest_contract_rejects_multiple_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = [root / "a.pdf", root / "b.pdf"]
            for source in sources:
                source.write_bytes(b"synthetic")
            with self.assertRaises(RepositoryCompatibilityError):
                load_config(self.make_config(root, sources), environ={})

    def test_requested_remote_placeholders_are_loaded_and_aliased(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            (repo / "content" / "schema").mkdir(parents=True)
            (repo / "AGENTS.md").write_text("# test\n", encoding="utf-8")
            config_path = root / "remote.toml"
            config_path.write_text(
                "[placeholders]\n"
                'sourcepath = "https://drive.google.com/open?id=1BqdcGJR3usQvItCNMC997fkcXaScNYqc"\n'
                'gemini-gem = "https://gemini.google.com/gem/remote"\n'
                'loginname = "tlyoon@gmail.com"\n'
                'pdf_subchapter_path = "8.1"\n'
                'target_filename = "source.pdf"\n'
                'target_file = "{sourcepath}/**/{pdf_subchapter_path}/{target_filename}"\n'
                "[repository]\n"
                f"repo_root = {json.dumps(str(repo))}\n"
                "[run]\n"
                'package_id = "chapter-8-section-8-1"\n'
                'chapter = "Chapter"\n'
                'subchapter = "8.1 Topic"\n'
                'chapter_dir = "chapter-8"\n'
                'section_dir = "section-8-1"\n'
                'learning_boundary = "Controlled boundary"\n'
                'source_id = "source-eight-one"\n'
                'edition = "Edition"\n'
                'heading = "Heading"\n'
                'page_range = "1-3"\n'
                'reviewer = "Reviewer"\n'
                'rights_note = "Controlled access"\n',
                encoding="utf-8",
            )
            config = load_config(config_path, environ={})
            self.assertTrue(config.uses_google_drive)
            self.assertEqual("https://gemini.google.com/gem/remote", config.gem_url)
            self.assertEqual("tlyoon@gmail.com", config.login_name)
            self.assertIn("/**/8.1/source.pdf", config.target_locator)

    def test_run_state_cannot_be_stored_inside_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.pdf"
            source.write_bytes(b"synthetic")
            path = self.make_config(root, [source])
            with self.assertRaises(ConfigurationError):
                load_config(
                    path,
                    environ={"BRILLIANT_GENERATOR_STATE_DIR": str(root / "repo" / "generator-runs")},
                )

    def test_distributed_templates_materialize_for_a_claimed_subchapter(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            (repo / "content" / "schema").mkdir(parents=True)
            (repo / "AGENTS.md").write_text("# test\n", encoding="utf-8")
            path = root / "distributed.toml"
            path.write_text(
                "[repository]\n"
                f"repo_root = {json.dumps(str(repo))}\n"
                "[automation]\n"
                'selection_mode = "distributed"\n'
                'coordinator_url = "https://script.google.com/macros/s/test/exec"\n'
                "[git]\n"
                "git_publish = true\n"
                "[run]\n"
                'package_id = "chapter-{chapter_number}-section-{section_slug}"\n'
                'chapter = "Chapter {chapter_number}"\n'
                'subchapter = "Section {subchapter_id}"\n'
                'chapter_dir = "chapter-{chapter_number}"\n'
                'section_dir = "section-{section_slug}"\n'
                'learning_boundary = "Controlled {subchapter_id}"\n'
                'source_id = "serway-section-{section_slug}"\n'
                'edition = "Edition"\n'
                'heading = "Section {subchapter_id}"\n'
                'page_range = "Complete PDF"\n'
                'reviewer = "Reviewer"\n'
                'rights_note = "Controlled access"\n',
                encoding="utf-8",
            )
            config = load_config(path, environ={})
            selected = config.for_subchapter("12.3")
            self.assertEqual("chapter-12-section-12-3", selected.package_id)
            self.assertEqual("section-12-3", selected.section_dir)
            self.assertEqual("Section 12.3", selected.subchapter)


if __name__ == "__main__":
    unittest.main()

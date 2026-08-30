import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RepositoryRuleTests(unittest.TestCase):
    def test_authoritative_files_exist(self):
        required = [
            "AGENTS.md", "docs/CONTEXT_INDEX.md", "docs/PRODUCT_REQUIREMENTS.md",
            "docs/CONTENT_RULES.md", "docs/LEARNING_DESIGN.md",
            "docs/SECURITY_AND_PRIVACY.md", "content/schema/content-package.schema.json",
            "content/schema/source-manifest.schema.json", "config/project.toml",
        ]
        for path in required:
            self.assertTrue((ROOT / path).is_file(), path)
        for legacy in (
            "config/generator.shared.toml",
            "config/generator.shared.example.toml",
            "config/generator.example.toml",
            "config/generator.distributed.example.toml",
        ):
            self.assertFalse((ROOT / legacy).exists(), legacy)
        self.assertFalse((ROOT / "config/configure_project.toml").exists())

    def test_project_configuration_has_one_tracked_authority(self):
        authorities = sorted((ROOT / "config").glob("*project*.toml"))
        self.assertEqual([ROOT / "config" / "project.toml"], authorities)

    def test_current_project_release_builder_is_outside_generic_scripts(self):
        self.assertFalse((ROOT / "scripts" / "build_section_8_1_public_release.py").exists())
        self.assertTrue(
            (ROOT / "project_extensions" / "brilliant_content_generator" / "build_public_review.py").is_file()
        )

    def test_no_legacy_course_name(self):
        pattern = re.compile(r"zca[ _-]?101", re.I)
        for path in ROOT.rglob("*"):
            if path.is_file() and ".git" not in path.parts:
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                self.assertIsNone(pattern.search(text), str(path.relative_to(ROOT)))

    def test_sensitive_artifacts_are_ignored(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for rule in (
            ".env",
            "*.pdf",
            "student-data/",
            "source-pdfs/",
            "generator*.local*.toml",
            "project.local*.toml",
        ):
            self.assertIn(rule, ignore)


if __name__ == "__main__":
    unittest.main()


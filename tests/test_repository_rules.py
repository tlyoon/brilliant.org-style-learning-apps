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
            "content/schema/source-manifest.schema.json",
        ]
        for path in required:
            self.assertTrue((ROOT / path).is_file(), path)

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
        ):
            self.assertIn(rule, ignore)


if __name__ == "__main__":
    unittest.main()


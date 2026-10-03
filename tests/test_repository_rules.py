import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RepositoryRuleTests(unittest.TestCase):
    def test_authoritative_files_exist(self):
        required = [
            "AGENTS.md", "docs/CONTEXT_INDEX.md", "docs/PRODUCT_REQUIREMENTS.md",
            "docs/CONTENT_RULES.md", "docs/LEARNING_DESIGN.md",
            "docs/VISUAL_INTERACTION_DESIGN.md", "docs/VISUAL_GENERATION_PROMPT_SPEC.md",
            "docs/VISUAL_TOOL_ORCHESTRATION.md", "docs/DOMAIN_PROFILES.md",
            "docs/decisions/0024-visual-first-physics-learning.md", "docs/decisions/0025-domain-profile-architecture.md",
            "docs/decisions/0026-stage0-textbook-domain-discovery.md", "app_generator/domains/discovery.py",
            "docs/SECURITY_AND_PRIVACY.md", "app/visual-renderers.js",
            "content/schema/content-package.schema.json",
            "content/schema/source-manifest.schema.json", "content/schema/visual-plan.schema.json",
            "content/schema/visual-spec.schema.json", "domains/registry.json",
            "domains/university-level physics/domain.json",
            "domains/university-level physics/visuals/template-registry.json",
            "domains/university-level physics/visuals/style-profiles.json",
            "domains/university-level physics/simulations/model-registry.json",
            "config/project.toml",
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


import tempfile
import unittest
from pathlib import Path

from scripts.build_public_release import build


ROOT = Path(__file__).resolve().parents[1]
QUICKSTART = ROOT / "docs" / "PDF_TO_APP_QUICKSTART.md"


class DocumentationQuickstartTests(unittest.TestCase):
    def test_quickstart_exists_and_is_linked_from_root_readme(self):
        self.assertTrue(QUICKSTART.is_file())
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("docs/PDF_TO_APP_QUICKSTART.md", root_readme)

    def test_quickstart_uses_current_tracked_project_authority(self):
        text = QUICKSTART.read_text(encoding="utf-8")
        config_readme = (ROOT / "config" / "README.md").read_text(encoding="utf-8")
        authority = "config/configure_project.toml"
        self.assertIn(authority, text)
        self.assertIn("`configure_project.toml` is the normal tracked authority", config_readme)

    def test_quickstart_covers_the_complete_lifecycle_and_safety_boundary(self):
        text = QUICKSTART.read_text(encoding="utf-8")
        required = (
            "source.pdf",
            "scripts\\configure_project.py",
            "sync_configured_workstation --init-settings-only",
            "app_generator doctor",
            "app_generator run --pdf-subchapter-path",
            "learning-design.md",
            "review-record.md",
            "scripts\\build_public_release.py",
            "http.server",
            "GitHub Pages",
            "git_publish = false",
            "git_auto_merge = false",
            "Never commit or copy these into Git",
            "source PDFs",
            "OAuth client",
            "human review",
        )
        for phrase in required:
            self.assertIn(phrase, text, phrase)

    def test_quickstart_referenced_core_files_exist(self):
        for relative in (
            "docs/GENERIC_PROJECT_SETUP.md",
            "docs/WORKSTATION_SYNC.md",
            "app_generator/README.md",
            "config/README.md",
            "scripts/configure_project.py",
            "scripts/build_public_release.py",
            "sync-workstation.cmd",
            "config/configure_project.toml",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_documented_generic_release_builder_produces_expected_minimal_bundle(self):
        package = ROOT / "content" / "chapter-1" / "section-1-1" / "package.json"
        self.assertTrue(package.is_file())
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "release"
            build(output, package)
            for relative in (
                "index.html",
                ".nojekyll",
                "app/app.js",
                "app/styles.css",
                "content/package.json",
            ):
                self.assertTrue((output / relative).is_file(), relative)
            self.assertFalse((output / "review-record.md").exists())
            self.assertFalse((output / "source-manifest.json").exists())


if __name__ == "__main__":
    unittest.main()

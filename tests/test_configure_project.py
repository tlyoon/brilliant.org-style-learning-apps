import tomllib
import unittest
from pathlib import Path

from scripts.configure_project import ProjectConfigurationError, render_project_configuration


ROOT = Path(__file__).resolve().parents[1]
CURRENT_SOURCE_ROOT = "https://drive.google.com/drive/folders/1xiYsp3pe3bcWV9W_ikarnjo_i_EsAPaA"


class ConfigureProjectTests(unittest.TestCase):
    def template(self) -> str:
        return """[project]
project_name = "OldProject"
[placeholders]
sourcepath = "https://drive.google.com/open?id=old"
gemini-gem = "https://gemini.google.com/gem/old"
loginname = "old@example.com"
[gemini]
gem_name = "old gem"
[source_tree]
source_id_prefix = "${PROJECT_SLUG}"
[compatibility]
legacy_environment_prefix = "OLD_GENERATOR_"
[repository]
repo_root = "${REPO_ROOT}"
[paths]
state_root = "${STATE_ROOT}"
"""

    def values(self) -> dict[str, str]:
        return {
            "project_name": "NewSubjectProject",
            "source_root_url": "https://drive.google.com/open?id=new",
            "gem_url": "https://gemini.google.com/gem/new",
            "login_name": "new@example.com",
            "gem_name": "new content generator",
        }

    def test_render_updates_only_explicit_project_inputs(self):
        rendered = render_project_configuration(self.template(), self.values())
        payload = tomllib.loads(rendered)
        self.assertEqual("NewSubjectProject", payload["project"]["project_name"])
        self.assertEqual(self.values()["source_root_url"], payload["placeholders"]["sourcepath"])
        self.assertEqual(self.values()["gem_url"], payload["placeholders"]["gemini-gem"])
        self.assertEqual("${STATE_ROOT}", payload["paths"]["state_root"])
        self.assertEqual("${REPO_ROOT}", payload["repository"]["repo_root"])
        self.assertEqual("${PROJECT_SLUG}", payload["source_tree"]["source_id_prefix"])
        self.assertEqual("", payload["compatibility"]["legacy_environment_prefix"])

    def test_current_project_has_one_authoritative_source_root_placeholder(self):
        payload = tomllib.loads((ROOT / "config" / "configure_project.toml").read_text(encoding="utf-8"))
        placeholders = payload["placeholders"]
        self.assertEqual(CURRENT_SOURCE_ROOT, placeholders["sourcepath"])
        self.assertEqual(
            "{sourcepath}/**/{pdf_subchapter_path}/{target_filename}",
            placeholders["target_file"],
        )
        source_root_keys = {
            key for key in placeholders
            if key.casefold() in {"sourcepath", "source_root", "source_root_url", "root_folder_id"}
        }
        self.assertEqual({"sourcepath"}, source_root_keys)

    def test_target_is_a_selector_beneath_source_root(self):
        payload = tomllib.loads((ROOT / "config" / "configure_project.toml").read_text(encoding="utf-8"))
        placeholders = payload["placeholders"]
        locator = placeholders["target_file"].format(
            sourcepath=placeholders["sourcepath"].rstrip("/"),
            pdf_subchapter_path=placeholders["pdf_subchapter_path"].strip("/\\"),
            target_filename=placeholders["target_filename"],
        )
        self.assertTrue(locator.startswith(CURRENT_SOURCE_ROOT + "/"))
        self.assertIn("/8.1/", locator)

    def test_invalid_hosts_are_rejected(self):
        values = self.values()
        values["source_root_url"] = "https://example.com/not-drive"
        with self.assertRaisesRegex(ProjectConfigurationError, "drive.google.com"):
            render_project_configuration(self.template(), values)

    def test_missing_editable_key_is_rejected(self):
        with self.assertRaisesRegex(ProjectConfigurationError, "gemini.gem_name"):
            render_project_configuration(self.template().replace('gem_name = "old gem"\n', ""), self.values())


if __name__ == "__main__":
    unittest.main()

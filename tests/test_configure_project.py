import tomllib
import unittest

from scripts.configure_project import ProjectConfigurationError, render_project_configuration


class ConfigureProjectTests(unittest.TestCase):
    def template(self) -> str:
        return """[project]
project_name = "OldProject"
[placeholders]
sourcepath = "https://drive.google.com/open?id=old"
gemini-gem = "https://gemini.google.com/gem/old"
loginname = "old@example.com"
[gemini]
gem_edit_url = "https://gemini.google.com/gems/edit/old"
gem_name = "old gem"
[source_tree]
source_id_prefix = "${PROJECT_SLUG}"
[compatibility]
legacy_environment_prefix = "OLD_GENERATOR_"
[git]
git_publish = true
git_auto_merge = true
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
            "gem_edit_url": "https://gemini.google.com/gems/edit/new",
            "login_name": "new@example.com",
            "gem_name": "new content generator",
        }

    def test_render_updates_only_explicit_project_inputs(self):
        rendered = render_project_configuration(self.template(), self.values())
        payload = tomllib.loads(rendered)
        self.assertEqual("NewSubjectProject", payload["project"]["project_name"])
        self.assertEqual(self.values()["source_root_url"], payload["placeholders"]["sourcepath"])
        self.assertEqual(self.values()["gem_url"], payload["placeholders"]["gemini-gem"])
        self.assertEqual(self.values()["gem_edit_url"], payload["gemini"]["gem_edit_url"])
        self.assertEqual("${STATE_ROOT}", payload["paths"]["state_root"])
        self.assertEqual("${REPO_ROOT}", payload["repository"]["repo_root"])
        self.assertEqual("${PROJECT_SLUG}", payload["source_tree"]["source_id_prefix"])
        self.assertEqual("", payload["compatibility"]["legacy_environment_prefix"])
        self.assertFalse(payload["git"]["git_publish"])
        self.assertFalse(payload["git"]["git_auto_merge"])

    def test_omitted_edit_url_clears_stale_editor(self):
        values = self.values()
        values.pop("gem_edit_url")
        rendered = render_project_configuration(self.template(), values)
        self.assertEqual("", tomllib.loads(rendered)["gemini"]["gem_edit_url"])

    def test_invalid_hosts_are_rejected(self):
        values = self.values()
        values["source_root_url"] = "https://example.com/not-drive"
        with self.assertRaisesRegex(ProjectConfigurationError, "drive.google.com"):
            render_project_configuration(self.template(), values)

        values = self.values()
        values["gem_edit_url"] = "https://example.com/not-gemini"
        with self.assertRaisesRegex(ProjectConfigurationError, "gemini.google.com"):
            render_project_configuration(self.template(), values)

    def test_missing_editable_key_is_rejected(self):
        with self.assertRaisesRegex(ProjectConfigurationError, "gemini.gem_name"):
            render_project_configuration(self.template().replace('gem_name = "old gem"\n', ""), self.values())


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path

from app_generator.cli import _parser
from app_generator.config import DEFAULTS
from scripts.check_documentation_impact import (
    documentation_present,
    documentation_required,
)


ROOT = Path(__file__).resolve().parents[1]
QUICKSTART = ROOT / "docs" / "PDF_TO_APP_QUICKSTART.md"
WORKSTATION = ROOT / "docs" / "WORKSTATION_SYNC.md"
AUTO = ROOT / "docs" / "CONTINUOUS_AUTO_TESTING.md"
CONFIG_README = ROOT / "config" / "README.md"


class DocumentationCurrencyTests(unittest.TestCase):
    def _text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def test_current_cli_selection_modes_and_coordinator_commands_are_documented(self):
        parser = _parser()
        subparsers_action = next(
            action for action in parser._actions
            if hasattr(action, "choices") and isinstance(action.choices, dict)
        )
        command_names = set(subparsers_action.choices)
        combined = "\n".join(
            self._text(path) for path in (QUICKSTART, WORKSTATION, AUTO, CONFIG_README)
        )
        for command in ("coordinator-status", "coordinator-bootstrap", "coordinator-ensure"):
            self.assertIn(command, command_names)
            self.assertIn(command, combined)

        run_parser = subparsers_action.choices["run"]
        selection = next(
            action for action in run_parser._actions
            if action.dest == "selection_mode"
        )
        self.assertEqual(set(selection.choices), {"specific", "auto", "distributed"})
        for mode in selection.choices:
            self.assertIn(mode, combined)

    def test_managed_coordinator_default_is_reflected_in_docs(self):
        self.assertEqual(DEFAULTS["coordinator_management"], "github_actions")
        text = self._text(CONFIG_README)
        self.assertIn('coordinator_url = ""', text)
        self.assertIn("repository-managed", text)
        self.assertIn("explicit", text)
        self.assertIn("external", text)

    def test_generated_local_config_filename_is_not_assumed(self):
        combined = self._text(QUICKSTART) + "\n" + self._text(WORKSTATION)
        self.assertIn("generator.shared.local.toml", combined)
        self.assertIn("filename printed", combined)
        self.assertIn("--config", combined)
        self.assertIn("project.local.toml", combined)

    def test_stale_manual_auto_branch_procedure_is_removed(self):
        text = self._text(AUTO)
        self.assertNotIn("feature/continuous-auto-mode", text)
        self.assertNotIn("CHECKPOINT_FOLDER_ID", text)
        self.assertNotIn("Update the Apps Script deployment", text)
        self.assertIn("repository-managed", text)

    def test_documentation_impact_classifier_requires_docs_for_operational_changes(self):
        operational_only = ("app_generator/cli.py", "tests/test_cli.py")
        self.assertTrue(documentation_required(operational_only))
        self.assertFalse(documentation_present(operational_only))

        with_docs = operational_only + ("docs/PDF_TO_APP_QUICKSTART.md",)
        self.assertTrue(documentation_required(with_docs))
        self.assertTrue(documentation_present(with_docs))

        content_only = ("content/chapter-1/section-1-1/package.json",)
        self.assertFalse(documentation_required(content_only))


if __name__ == "__main__":
    unittest.main()

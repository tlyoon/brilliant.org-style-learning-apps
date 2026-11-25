"""Source-free regressions for automatic trusted BOSLA browser runtime selection."""
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from app_generator.runtime import browser_runtime_selection as runtime
from scripts.audit_full_learner_browser import main


class BrowserRuntimeSelectionTests(TestCase):
    def test_existing_selenium_does_not_relaunch(self):
        with patch.object(runtime, "_selenium_usable", return_value=True):
            with patch.object(runtime, "_trusted_interpreters") as discover:
                self.assertIsNone(runtime.recover_existing_browser_runtime(
                    Path.cwd(), Path.cwd() / "script.py", ["--help"]))
        discover.assert_not_called()

    def test_repo_venv_is_used_automatically_before_audit(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "audit.py"
            script.write_text("# synthetic", encoding="utf-8")
            candidate = root / ".venv" / "Scripts" / "python.exe"
            candidate.parent.mkdir(parents=True)
            candidate.write_bytes(b"synthetic")
            with patch.object(runtime, "_selenium_usable", return_value=False), \
                 patch.object(runtime, "_trusted_interpreters",
                              return_value=[candidate]), \
                 patch.object(runtime.subprocess, "run",
                              return_value=SimpleNamespace(returncode=0)), \
                 patch.object(runtime.subprocess, "call", return_value=0) as call, \
                 patch.dict(os.environ, {"BOSLA_BROWSER_RUNTIME_SELECTED": ""}):
                self.assertEqual(0, runtime.recover_existing_browser_runtime(
                    root, script, ["--package", "demo.json"]))
            command = call.call_args.args[0]
            self.assertEqual(str(candidate), command[0])
            self.assertEqual(str(script), command[1])
            self.assertEqual(["--package", "demo.json"], command[2:])
            self.assertEqual("1", call.call_args.kwargs["env"][
                "BOSLA_BROWSER_RUNTIME_SELECTED"])

    def test_linked_worktree_finds_only_owning_git_venv(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "linked"
            root.mkdir()
            checkout = Path(folder) / "owner"
            common = checkout / ".git"
            common.mkdir(parents=True)
            candidate = checkout / ".venv" / "Scripts" / "python.exe"
            candidate.parent.mkdir(parents=True)
            candidate.write_bytes(b"synthetic")
            with patch.object(runtime.subprocess, "run", return_value=(
                SimpleNamespace(returncode=0, stdout=str(common)))):
                selected = runtime._trusted_interpreters(root)
            self.assertEqual([candidate], selected)

    def test_missing_runtime_stops_without_launch_or_install(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "audit.py"
            script.write_text("", encoding="utf-8")
            with patch.object(runtime, "_selenium_usable", return_value=False), \
                 patch.object(runtime, "_trusted_interpreters",
                              return_value=[]), \
                 patch.object(runtime.subprocess, "call") as call:
                with self.assertRaisesRegex(RuntimeError,
                                            "BOSLA_BROWSER_RUNTIME_UNAVAILABLE"):
                    runtime.recover_existing_browser_runtime(root, script, [])
            call.assert_not_called()

    def test_switch_guard_prevents_recursive_dispatch(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "audit.py"
            script.write_text("", encoding="utf-8")
            with patch.object(runtime, "_selenium_usable", return_value=False), \
                 patch.dict(os.environ, {"BOSLA_BROWSER_RUNTIME_SELECTED": "1"}):
                with self.assertRaisesRegex(RuntimeError, "UNAVAILABLE"):
                    runtime.recover_existing_browser_runtime(root, script, [])

    def test_cli_invokes_recovery_before_full_audit(self):
        with patch("scripts.audit_full_learner_browser."
                   "recover_existing_browser_runtime", return_value=7), \
             patch("scripts.audit_full_learner_browser."
                   "audit_existing_candidate") as audit:
            self.assertEqual(7, main(
                ["--package", "nonexistent", "--output-root", "nonexistent"]))
        audit.assert_not_called()

    def test_cli_missing_runtime_reports_sanitized_pre_audit_stop(self):
        with patch("scripts.audit_full_learner_browser."
                   "recover_existing_browser_runtime",
                   side_effect=RuntimeError("BOSLA_BROWSER_RUNTIME_UNAVAILABLE")), \
             patch("scripts.audit_full_learner_browser."
                   "audit_existing_candidate") as audit:
            self.assertEqual(3, main(
                ["--package", "nonexistent", "--output-root", "nonexistent"]))
        audit.assert_not_called()

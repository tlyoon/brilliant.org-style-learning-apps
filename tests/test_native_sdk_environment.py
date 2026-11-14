"""Synthetic no-network tests for the normal V3 native SDK self-repair path."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app_generator.runtime import native_sdk_environment as recovery


class NativeSDKEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir()

    def fake_interpreter(self):
        executable = self.root / ".venv" / (
            "Scripts/python.exe" if os.name == "nt" else "bin/python"
        )
        executable.parent.mkdir(parents=True, exist_ok=True)
        executable.write_text("synthetic not executable", encoding="utf8")
        return executable

    def test_compatible_sdk_does_not_bootstrap_or_delegate(self):
        with patch.object(recovery, "_current_has_retry_guard", return_value=True), \
             patch.object(recovery.subprocess, "run") as run:
            self.assertIsNone(recovery.delegate_to_supported_sdk(
                self.root, ["--execute", "--allow-generated-text-transfer"]))
        run.assert_not_called()

    def test_stale_global_sdk_uses_existing_compatible_venv_once(self):
        executable = self.fake_interpreter()
        with patch.dict(os.environ, {"BOSLA_V3_NATIVE_SDK_REEXEC": "0"}), \
             patch.object(recovery, "_current_has_retry_guard", return_value=False), \
             patch.object(recovery, "_interpreter_has_retry_guard", return_value=True), \
             patch.object(recovery.subprocess, "run",
                          return_value=SimpleNamespace(returncode=7)) as run:
            self.assertEqual(7, recovery.delegate_to_supported_sdk(
                self.root, ["--execute", "--allow-generated-text-transfer"]))
        self.assertEqual(1, run.call_count)
        self.assertEqual(str(executable), run.call_args.args[0][0])
        self.assertEqual("1", run.call_args.kwargs["env"][
            "BOSLA_V3_NATIVE_SDK_REEXEC"])

    def test_missing_venv_bootstraps_pinned_project_once_then_delegates(self):
        with patch.dict(os.environ, {"BOSLA_V3_NATIVE_SDK_REEXEC": "0"}), \
             patch.object(recovery, "_current_has_retry_guard", return_value=False), \
             patch.object(recovery, "_interpreter_has_retry_guard",
                          side_effect=[False, True]), \
             patch.object(recovery.subprocess, "run",
                          return_value=SimpleNamespace(returncode=0)) as run:
            self.assertEqual(0, recovery.delegate_to_supported_sdk(
                self.root, ["--execute", "--allow-generated-text-transfer"]))
        self.assertEqual(3, run.call_count)
        self.assertEqual([os.sys.executable, "-m", "venv"],
                         run.call_args_list[0].args[0][:3])
        install = run.call_args_list[1].args[0]
        self.assertEqual("pip", install[2])
        self.assertIn("--retries", install)
        self.assertIn("0", install)
        self.assertEqual(str(self.root), install[-1])
        self.assertEqual("--execute",run.call_args_list[2].args[0][-2])
        self.assertEqual("--allow-generated-text-transfer",
                         run.call_args_list[2].args[0][-1])

    def test_install_failure_stops_without_any_review_dispatch(self):
        self.fake_interpreter()
        with patch.dict(os.environ, {"BOSLA_V3_NATIVE_SDK_REEXEC": "0"}), \
             patch.object(recovery, "_current_has_retry_guard", return_value=False), \
             patch.object(recovery, "_interpreter_has_retry_guard", return_value=False), \
             patch.object(recovery.subprocess, "run",
                 side_effect=subprocess.CalledProcessError(1, "pip")) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                recovery.delegate_to_supported_sdk(self.root, ["--execute"])
        self.assertEqual(1, run.call_count)
        self.assertIn("pip",run.call_args.args[0])

    def test_child_cannot_recursively_bootstrap_or_replay(self):
        with patch.dict(os.environ, {"BOSLA_V3_NATIVE_SDK_REEXEC": "1"}), \
             patch.object(recovery, "_current_has_retry_guard", return_value=False), \
             patch.object(recovery.subprocess, "run") as run:
            with self.assertRaisesRegex(RuntimeError,
                    "V3_NATIVE_SDK_REEXEC_STILL_INCOMPATIBLE"):
                recovery.delegate_to_supported_sdk(self.root, ["--execute"])
        run.assert_not_called()

    def test_cli_dispatch_invokes_recovery_before_provider_config(self):
        from scripts import run_v3_native_gemini_review as runner
        with patch.object(runner,"plan_v3_course_review",
                          return_value={"dispatchStatus":
                                        "READY_FOR_AUTHORIZED_REVIEW_SESSIONS"}), \
             patch("app_generator.runtime.native_sdk_environment.delegate_to_supported_sdk",
                   return_value=23) as delegate, \
             patch.object(runner,"_load_native_config") as config:
            self.assertEqual(23,runner.main([
                "--execute","--allow-generated-text-transfer"]))
        self.assertEqual(1,delegate.call_count)
        config.assert_not_called()


if __name__ == "__main__":
    unittest.main()

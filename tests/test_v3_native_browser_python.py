"""BSA246: historical Yoga6 global Python missing Selenium, safe automatic venv remedy."""
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app_generator.runtime.v3_native_browser_python import (
    select_source_free_browser_interpreter as choose,
)
from scripts import run_v3_yoga6_recovery_worker as worker


class NativeBrowserPythonTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo=Path(self.tmp.name)/"repo"
        self.repo.mkdir()
        self.venv=self.repo/".venv"/"Scripts"/"python.exe"
        self.venv.parent.mkdir(parents=True)
        self.venv.write_bytes(b"real-interpreter-path-placeholder")
        self.global_python=Path(self.tmp.name)/"global"/"python.exe"

    def test_missing_global_selenium_selects_exact_project_venv(self):
        self.assertEqual(choose(
            repo=self.repo,current=self.global_python,
            windows=True,source_free=True,selenium_available=False,
        ),("REEXEC_PINNED_BROWSER_PYTHON",self.venv))

    def test_installed_selenium_does_not_create_new_process(self):
        self.assertEqual(choose(
            repo=self.repo,current=self.global_python,
            windows=True,source_free=True,selenium_available=True,
        ),("USE_CURRENT_PYTHON",None))

    def test_other_platform_or_authorization_modes_unchanged(self):
        for windows,source_free in ((False,True),(True,False),(False,False)):
            with self.subTest(windows=windows,source_free=source_free):
                self.assertEqual(choose(
                    repo=self.repo,current=self.global_python,
                    windows=windows,source_free=source_free,
                    selenium_available=False,
                ),("USE_CURRENT_PYTHON",None))

    def test_missing_or_symlink_venv_stops_before_browser(self):
        self.venv.unlink()
        self.assertEqual(choose(
            repo=self.repo,current=self.global_python,
            windows=True,source_free=True,selenium_available=False,
        ),("STOP_PINNED_BROWSER_RUNTIME_MISSING",None))
        self.venv.write_bytes(b"fake-not-executed")
        # Fault inject link detection: Windows Yoga6 does not grant the test
        # process the privilege to create actual filesystem symlinks.
        with patch.object(Path,"is_symlink",return_value=True):
            self.assertEqual(choose(
                repo=self.repo,current=self.global_python,
                windows=True,source_free=True,selenium_available=False,
            ),("STOP_PINNED_BROWSER_RUNTIME_MISSING",None))

    def test_invalid_current_venv_without_selenium_stops_no_recursion(self):
        self.assertEqual(choose(
            repo=self.repo,current=self.venv,
            windows=True,source_free=True,selenium_available=False,
        ),("STOP_PINNED_BROWSER_RUNTIME_MISSING",None))

    def test_normal_worker_reexecs_before_main_no_provider_or_install(self):
        calls=[]
        def fake_run(args,**kwargs):
            calls.append((args,kwargs))
            return SimpleNamespace(returncode=0 if len(calls)==1 else 0)
        with (patch.object(worker,"ROOT",self.repo),
              patch.object(worker.sys,"executable",str(self.global_python)),
              patch.object(worker,"main") as main_mock,
              patch("subprocess.run",side_effect=fake_run)):
            self.assertEqual(worker._run_native_browser_entrypoint(
                ["--source-free-advance"],is_windows=True,
                selenium_available=False),0)
            main_mock.assert_not_called()
        self.assertEqual(len(calls),2)
        self.assertEqual(calls[0][0],[str(self.venv),"-c","import selenium"])
        self.assertTrue(calls[0][1]["capture_output"])
        self.assertEqual(calls[1][0][:2],
                         [str(self.venv),str(Path(worker.__file__).resolve())])
        self.assertEqual(calls[1][0][-1],"--source-free-advance")
        self.assertFalse(calls[1][1]["check"])

    def test_failing_probe_does_not_run_browser_or_replay_provider(self):
        with (patch.object(worker,"ROOT",self.repo),
              patch.object(worker.sys,"executable",str(self.global_python)),
              patch.object(worker,"main") as main_mock,
              patch("subprocess.run",
                    return_value=SimpleNamespace(returncode=1)) as sub,
              patch.object(worker,"_print") as report):
            self.assertEqual(worker._run_native_browser_entrypoint(
                ["--source-free-advance"],is_windows=True,
                selenium_available=False),3)
            self.assertEqual(sub.call_count,1)
            main_mock.assert_not_called()
            self.assertEqual(report.call_args.args[0]["status"],
                             "STOP_PINNED_BROWSER_RUNTIME_RELAUNCH_FAILED")

    def test_absent_venv_stops_before_any_stateful_work(self):
        self.venv.unlink()
        with (patch.object(worker,"ROOT",self.repo),
              patch.object(worker,"main") as main_mock,
              patch("subprocess.run") as sub,
              patch.object(worker,"_print") as report):
            self.assertEqual(worker._run_native_browser_entrypoint(
                ["--source-free-advance"],is_windows=True,
                selenium_available=False),3)
            main_mock.assert_not_called()
            sub.assert_not_called()
            self.assertEqual(report.call_args.args[0]["status"],
                             "STOP_PINNED_BROWSER_RUNTIME_MISSING")

    def test_existing_venv_or_other_mode_uses_original_controller(self):
        with patch.object(worker,"main",return_value=0) as main_mock:
            self.assertEqual(worker._run_native_browser_entrypoint(
                ["--source-free-advance"],is_windows=True,
                selenium_available=True),0)
            self.assertEqual(worker._run_native_browser_entrypoint(
                ["--execute"],is_windows=True,
                selenium_available=False),0)
        self.assertEqual(main_mock.call_count,2)

    def test_worker_exposes_actual_integrated_bootstrap(self):
        text=Path(worker.__file__).read_text(encoding="utf8")
        self.assertIn("def _run_native_browser_entrypoint(",text)
        self.assertIn("select_source_free_browser_interpreter(",text)
        self.assertIn("raise SystemExit(_run_native_browser_entrypoint())",text)


if __name__=="__main__":
    unittest.main()

"""BSA254: real OS-wide cross-session single-flight for source-free Bosla.

All tests use temporary Microvid roots and NEVER perform provider calls,
read private source, launch Chrome or publish.
"""
from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime.v3_yoga6_recovery import coordinator_lock
from scripts import run_v3_yoga6_recovery_worker as worker

ROOT = Path(__file__).resolve().parents[1]


class SourceFreeSingleFlightTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.local = Path(t.name)
        self.root = self.local / "Microvid" / "BoslaV3ReviewYoga6"

    def run_worker(self, *extra):
        out = io.StringIO()
        with patch.dict(os.environ, {"LOCALAPPDATA": str(self.local)}), \
             redirect_stdout(out):
            result = worker.main(["--source-free-advance", *extra])
        return result, out.getvalue()

    def test_original_historical_os_lock_blocks_before_any_worker_stage(self):
        with coordinator_lock(self.root), \
             patch.object(worker, "_main_unlocked") as stages:
            code, output = self.run_worker()
        self.assertEqual(code, 3)
        self.assertEqual(json.loads(output), {
            "publicationAuthorized": False,
            "status": "STOP_YOGA6_SOURCE_FREE_ALREADY_RUNNING",
        })
        stages.assert_not_called()

    def test_released_lock_allows_automatic_resume_without_manual_cleanup(self):
        with patch.object(worker, "_main_unlocked", return_value=0) as stages:
            result, _ = self.run_worker()
            self.assertEqual(result, 0)
            second, _ = self.run_worker()
            self.assertEqual(second, 0)
            self.assertEqual(stages.call_count, 2)
            stages.assert_any_call(["--source-free-advance"])

    def test_alternate_private_root_cannot_bypass_global_lock(self):
        other = self.local / "Microvid" / "other-valid-private-root"
        with coordinator_lock(self.root), \
             patch.object(worker, "_main_unlocked") as stages:
            code, output = self.run_worker("--private-root", str(other))
        self.assertEqual(code, 3)
        self.assertIn("STOP_YOGA6_SOURCE_FREE_ALREADY_RUNNING", output)
        stages.assert_not_called()

    def test_invalid_root_is_rejected_before_work_or_provider(self):
        outside = self.local / "outside-private-folder"
        with patch.object(worker, "_main_unlocked") as stages:
            code, output = self.run_worker("--private-root", str(outside))
        self.assertEqual(code, 3)
        self.assertEqual(json.loads(output)["status"],
                         "STOP_YOGA6_SOURCE_FREE_LOCK_ERROR")
        stages.assert_not_called()

    def test_diagnose_and_existing_paid_mode_not_changed(self):
        with patch.object(worker, "_main_unlocked", return_value=42) as stages:
            self.assertEqual(worker.main(["--diagnose-only"]), 42)
            self.assertEqual(worker.main(["--execute"]), 42)
        self.assertEqual(stages.call_count, 2)

    def test_source_free_main_uses_same_lock_when_reentered(self):
        with patch.object(worker, "_main_unlocked", return_value=0) as stages:
            def nested(_args):
                with patch.object(worker, "_main_unlocked", return_value=0):
                    code, report = self.run_worker()
                self.assertEqual(code, 3)
                self.assertIn("ALREADY_RUNNING", report)
                return 0
            stages.side_effect = nested
            code, _ = self.run_worker()
        self.assertEqual(code, 0)

    def test_existing_child_launcher_preserves_native_main_dispatch(self):
        with patch.object(worker, "main", return_value=21) as main:
            self.assertEqual(worker._run_native_browser_entrypoint(
                ["--diagnose-only"], is_windows=False), 21)
            self.assertEqual(worker._run_native_browser_entrypoint(
                ["--source-free-advance"], is_windows=True,
                selenium_available=True), 21)
        self.assertEqual(main.call_count, 2)

    def test_real_second_python_process_lock_is_denied_and_released(self):
        # This exercises the OS lock, rather than testing a mocked boolean.
        holder = (
            "import os,time\n"
            "from pathlib import Path\n"
            "from app_generator.runtime.v3_yoga6_recovery import coordinator_lock\n"
            "p=Path(os.environ['LOCALAPPDATA'])/'Microvid'/'BoslaV3ReviewYoga6'\n"
            "with coordinator_lock(p):\n"
            " print('HELD', flush=True)\n"
            " time.sleep(15)\n"
        )
        env = {**os.environ, "LOCALAPPDATA": str(self.local)}
        process = subprocess.Popen(
            [sys.executable, "-c", holder], cwd=ROOT, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            self.assertEqual(process.stdout.readline().strip(), "HELD")
            with patch.object(worker, "_main_unlocked") as stages:
                result, report = self.run_worker()
            self.assertEqual(result, 3)
            self.assertIn("STOP_YOGA6_SOURCE_FREE_ALREADY_RUNNING", report)
            stages.assert_not_called()
        finally:
            process.terminate()
            try:
                process.communicate(timeout=6)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate(timeout=6)
        # On crash/kill, Windows and Linux kernel locks are automatically
        # released. No process-owned PID file is silently deleted/replayed.
        with patch.object(worker, "_main_unlocked", return_value=0) as stages:
            result, _ = self.run_worker()
        self.assertEqual(result, 0)
        stages.assert_called_once()

    def test_no_malicious_private_text_in_contended_lock_response(self):
        with coordinator_lock(self.root), \
             patch.object(worker, "_main_unlocked") as stages:
            _, report = self.run_worker("--private-root",
                str(self.local / "Microvid" / "SECRET_PRINT_ME"))
        self.assertNotIn("SECRET_PRINT_ME", report)
        self.assertNotIn(str(self.local), report)
        stages.assert_not_called()


if __name__ == "__main__":
    unittest.main()

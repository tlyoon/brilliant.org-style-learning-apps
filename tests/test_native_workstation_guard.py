"""Source-free Bosla Yoga 6 host-ownership gates.

No credential lookup, original source transfer or Google request in these tests.
"""
from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime.native_workstation_guard import require_authorized_native_review_host


class NativeWorkstationGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.file = Path(self.temp.name) / "project.toml"
        self.file.write_text(
            '[project]\nproject_name="BrilliantContentGenerator"\n'
            'native_gemini_review_host="YOGA6"\n',encoding="utf8")

    def test_matches_designated_yoga6_case_insensitively(self):
        with patch("app_generator.runtime.native_workstation_guard.socket.gethostname",
                   return_value="yoga6"):
            self.assertEqual("YOGA6",require_authorized_native_review_host(self.file))

    def test_hp_or_dell_cannot_start_native_gemini_review(self):
        for host in ("hp","DELL-115","YOGA7"):
            with self.subTest(host=host), patch(
                "app_generator.runtime.native_workstation_guard.socket.gethostname",
                return_value=host):
                with self.assertRaisesRegex(PermissionError,
                        "V3_NATIVE_REVIEW_WRONG_WORKSTATION"):
                    require_authorized_native_review_host(self.file)

    def test_unbound_or_corrupt_host_fails_closed(self):
        for item in ("", "Yoga 6", "../YOGA6"):
            with self.subTest(item=item):
                self.file.write_text(
                    f'[project]\nnative_gemini_review_host="{item}"\n',
                    encoding="utf8")
                with self.assertRaisesRegex(ValueError,
                        "V3_NATIVE_REVIEW_HOST_NOT_CONFIGURED"):
                    require_authorized_native_review_host(self.file)

    def test_wrong_host_exits_cli_before_sdk_or_model_checkpoint(self):
        from scripts import run_v3_native_gemini_review as runner
        root = Path(self.temp.name) / "private"
        from unittest.mock import patch as mock
        out = io.StringIO()
        with mock.object(runner, "plan_v3_course_review", return_value={
                "dispatchStatus":"READY_FOR_AUTHORIZED_REVIEW_SESSIONS"}), \
             mock("app_generator.runtime.native_workstation_guard.socket.gethostname",
                  return_value="hp"), \
             mock("app_generator.runtime.native_sdk_environment.delegate_to_supported_sdk") as delegate, \
             mock.object(runner,"_load_native_config") as config, \
             redirect_stdout(out):
            result = runner.main([
                "--execute", "--allow-generated-text-transfer",
                "--private-root",str(root)])
        self.assertEqual(3,result)
        status=json.loads(out.getvalue())
        self.assertEqual("STOP_NATIVE_GEMINI_REVIEW",status["status"])
        self.assertEqual("PermissionError",status["reasonClass"])
        delegate.assert_not_called()
        config.assert_not_called()
        self.assertFalse(root.exists())


if __name__ == "__main__":
    unittest.main()

import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app_generator.cli import DEFAULT_CONFIG, _load, _parser, doctor
from app_generator.coordinator.client import QueueSnapshot


class CliParserTests(unittest.TestCase):
    def test_config_defaults_to_project_local_toml(self):
        args = _parser().parse_args(["run"])

        self.assertEqual(args.config, DEFAULT_CONFIG)
        self.assertEqual(args.config, Path("project.local.toml"))

    def test_explicit_config_overrides_default(self):
        config = Path("configs/custom.toml")

        args = _parser().parse_args(["run", "--config", str(config)])

        self.assertEqual(args.config, config)

    def test_auto_selection_mode_is_exposed(self):
        args = _parser().parse_args(["run", "--selection-mode", "auto"])
        self.assertEqual("auto", args.selection_mode)

    def test_auto_can_accept_explicit_target_subchapter(self):
        args = _parser().parse_args([
            "run",
            "--selection-mode",
            "auto",
            "--pdf-subchapter-path",
            "8.6",
        ])
        self.assertEqual("auto", args.selection_mode)
        self.assertEqual("8.6", args.pdf_subchapter_path)

    def test_targeted_doctor_reports_bounded_failure_diagnostics(self):
        snapshot = QueueSnapshot(
            total=1, queued=0, interrupted=0, leased=0, generated=0,
            review_pending=0, completed=0, failed=1,
            next_job_key="", next_subchapter_id="",
            target_status="failed", target_attempt_count=3,
            target_error_code="LEASE_EXPIRED",
        )
        output = io.StringIO()
        with patch("app_generator.cli.inspect_auto_queue", return_value=snapshot), redirect_stdout(output):
            result = doctor(SimpleNamespace(selection_mode="auto"), auto_target_subchapter_id="9.1")
        self.assertEqual(0, result)
        self.assertIn(
            "Auto target state: status=failed, attempts=3, last_error=LEASE_EXPIRED",
            output.getvalue(),
        )

    def test_failed_job_retry_requires_explicit_target_and_confirmation(self):
        args = _parser().parse_args([
            "coordinator-retry-failed",
            "--pdf-subchapter-path", "9.1",
            "--confirm",
        ])
        self.assertEqual("9.1", args.pdf_subchapter_path)
        self.assertTrue(args.confirm)

    def test_separate_account_arguments_reach_config_loader(self):
        for command in ("doctor", "run", "coordinator-bootstrap", "coordinator-ensure", "coordinator-status"):
            with self.subTest(command=command):
                args = _parser().parse_args([
                    command, "--login-name", "gemini@example.com",
                    "--oauth-login", "oauth@example.com", "--pdf-subchapter-path", "8.6",
                ])
                with patch("app_generator.cli.load_config") as loader:
                    self.assertIs(_load(args), loader.return_value)
                overrides = loader.call_args.kwargs["cli_overrides"]
                self.assertEqual("gemini@example.com", overrides["login_name"])
                self.assertEqual("oauth@example.com", overrides["oauth_login"])
                self.assertEqual("8.6", overrides["pdf_subchapter_path"])

    def test_deployments_command_has_repository_defaults(self):
        args = _parser().parse_args(["deployments"])

        self.assertEqual(Path("."), args.repo_root)
        self.assertEqual(Path("config/deployments.json"), args.registry)


if __name__ == "__main__":
    unittest.main()

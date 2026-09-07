import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app_generator.errors import GitPublishError
from app_generator.publishing.git import GitPublisher


class RecordingPublisher(GitPublisher):
    def __init__(self, config):
        super().__init__(config)
        self.commands = []

    def _run(self, arguments, *, check=True):
        self.commands.append((arguments, check))
        return ""

    def _run_remote(self, arguments, *, check=True, retry=True):
        self.commands.append((arguments, check))
        return ""


class MergePublisher(RecordingPublisher):
    def _run(self, arguments, *, check=True):
        self.commands.append((arguments, check))
        return ""

    def _run_remote(self, arguments, *, check=True, retry=True):
        self.commands.append((arguments, check))
        if arguments[:3] == ["gh", "pr", "view"]:
            return '{"state":"MERGED","mergedAt":"2026-08-29T00:00:00Z"}'
        return ""


class GeneratorPublishingTests(unittest.TestCase):
    def test_sync_is_fast_forward_only_and_job_branch_is_unique(self):
        with tempfile.TemporaryDirectory() as directory:
            config = SimpleNamespace(
                repo_root=Path(directory),
                git_remote="origin",
                git_base_branch="main",
                git_branch_prefix="automation",
            )
            publisher = RecordingPublisher(config)
            publisher.sync_base()
            branch = publisher.prepare_branch(subchapter_id="8.1", job_key="abcdef0123456789")
            commands = [item[0] for item in publisher.commands]
            self.assertIn(["git", "pull", "--ff-only", "origin", "main"], commands)
            self.assertEqual("automation/section-8-1-abcdef0123", branch)
            self.assertIn(
                [
                    "git",
                    "rev-parse",
                    "--verify",
                    "--quiet",
                    "refs/heads/automation/section-8-1-abcdef0123",
                ],
                commands,
            )
            self.assertIn(["git", "switch", "-c", branch], commands)

    def test_transient_remote_failure_is_retried_with_backoff(self):
        with tempfile.TemporaryDirectory() as directory:
            config = SimpleNamespace(repo_root=Path(directory))
            publisher = GitPublisher(config)
            failed = subprocess.CompletedProcess(
                args=["git", "fetch", "origin", "--prune"],
                returncode=128,
                stdout="",
                stderr=(
                    "fatal: unable to access 'https://github.com/example/project/': "
                    "Recv failure: Connection was reset"
                ),
            )
            succeeded = subprocess.CompletedProcess(
                args=["git", "fetch", "origin", "--prune"],
                returncode=0,
                stdout="",
                stderr="",
            )

            with patch("app_generator.publishing.git.subprocess.run", side_effect=[failed, succeeded]) as runner:
                with patch("app_generator.publishing.git.time.sleep") as sleeper:
                    output = publisher._run_remote(["git", "fetch", "origin", "--prune"])

            self.assertEqual("", output)
            self.assertEqual(2, runner.call_count)
            sleeper.assert_called_once_with(2)

    def test_non_transient_remote_failure_fails_without_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            config = SimpleNamespace(repo_root=Path(directory))
            publisher = GitPublisher(config)
            failed = subprocess.CompletedProcess(
                args=["git", "fetch", "origin", "--prune"],
                returncode=128,
                stdout="",
                stderr="fatal: Authentication failed for 'https://github.com/example/project/'",
            )

            with patch("app_generator.publishing.git.subprocess.run", return_value=failed) as runner:
                with patch("app_generator.publishing.git.time.sleep") as sleeper:
                    with self.assertRaisesRegex(GitPublishError, "Authentication failed"):
                        publisher._run_remote(["git", "fetch", "origin", "--prune"])

            self.assertEqual(1, runner.call_count)
            sleeper.assert_not_called()

    def test_transient_remote_failure_stops_after_bounded_attempts(self):
        with tempfile.TemporaryDirectory() as directory:
            config = SimpleNamespace(repo_root=Path(directory))
            publisher = GitPublisher(config)
            failed = subprocess.CompletedProcess(
                args=["git", "fetch", "origin", "--prune"],
                returncode=128,
                stdout="",
                stderr="fatal: Recv failure: Connection was reset",
            )

            with patch("app_generator.publishing.git.subprocess.run", return_value=failed) as runner:
                with patch("app_generator.publishing.git.time.sleep") as sleeper:
                    with self.assertRaisesRegex(GitPublishError, "after 4 transient-network attempt"):
                        publisher._run_remote(["git", "fetch", "origin", "--prune"])

            self.assertEqual(4, runner.call_count)
            self.assertEqual([2, 5, 10], [call.args[0] for call in sleeper.call_args_list])

    def test_missing_local_branch_is_not_treated_as_existing_git_error(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)

            def git(*args: str) -> None:
                subprocess.run(
                    ["git", *args],
                    cwd=repo,
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )

            git("init", "--initial-branch=main")
            git(
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.com",
                "commit",
                "--allow-empty",
                "-m",
                "initial",
            )
            publisher = GitPublisher(SimpleNamespace(repo_root=repo))
            branch = "automation/section-1-2-deadbeef00"

            self.assertFalse(publisher._local_branch_exists(branch))
            git("branch", branch)
            self.assertTrue(publisher._local_branch_exists(branch))

    def test_auto_merge_uses_normal_github_merge_and_verifies_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            config = SimpleNamespace(repo_root=Path(directory))
            publisher = MergePublisher(config)
            pr_url = "https://github.com/example/project/pull/1"
            publisher._merge_pr(pr_url)
            commands = [item[0] for item in publisher.commands]
            self.assertEqual(["gh", "pr", "merge", pr_url, "--merge"], commands[0])
            self.assertEqual(
                ["gh", "pr", "view", pr_url, "--json", "state,mergedAt"],
                commands[1],
            )


if __name__ == "__main__":
    unittest.main()

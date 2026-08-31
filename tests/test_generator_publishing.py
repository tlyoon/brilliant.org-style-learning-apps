import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app_generator.publishing.git import GitPublisher


class RecordingPublisher(GitPublisher):
    def __init__(self, config):
        super().__init__(config)
        self.commands = []

    def _run(self, arguments, *, check=True):
        self.commands.append((arguments, check))
        return ""


class MergePublisher(RecordingPublisher):
    def _run(self, arguments, *, check=True):
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
            # show-ref must emit the matching ref so branch existence can actually be
            # detected; --quiet would always produce an empty output string.
            self.assertIn(
                [
                    "git",
                    "show-ref",
                    "--verify",
                    "refs/heads/automation/section-8-1-abcdef0123",
                ],
                commands,
            )
            self.assertIn(["git", "switch", "-c", branch], commands)

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

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
            self.assertIn(["git", "switch", "-c", branch], commands)


if __name__ == "__main__":
    unittest.main()

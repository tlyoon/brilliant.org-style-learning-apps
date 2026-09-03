import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app_generator.config import load_config
from app_generator.publishing.git import GitPublisher


class AutoConfigurationTests(unittest.TestCase):
    def test_auto_is_valid_as_persistent_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            (repo / "content" / "schema").mkdir(parents=True)
            (repo / "AGENTS.md").write_text("test\n", encoding="utf-8")
            state = root / "state"
            config_path = root / "project.local.toml"
            config_path.write_text(
                f'''project_name = "TestLearningProject"
gem_url = "https://gemini.google.com/gem/test"
gem_name = "test content generator"
login_name = "authorized@example.com"
chrome_profile_dir = "{(state / 'chrome').as_posix()}"
state_dir = "{(state / 'runs').as_posix()}"
repo_root = "{repo.as_posix()}"
sourcepath = "https://drive.google.com/open?id=1234567890A"
pdf_subchapter_path = "1.1"
target_filename = "source.pdf"
target_file = "{{sourcepath}}/**/{{pdf_subchapter_path}}/{{target_filename}}"
source_id_prefix = "test-learning-project"
drive_oauth_client_file = "{(state / 'credentials' / 'drive-oauth-client.json').as_posix()}"
drive_token_file = "{(state / 'credentials' / 'drive-oauth-token.json').as_posix()}"
package_id = "chapter-{{chapter_number}}-section-{{section_slug}}"
chapter = "Chapter {{chapter_number}}"
subchapter = "{{subchapter_id}}"
chapter_dir = "chapter-{{chapter_number}}"
section_dir = "section-{{section_slug}}"
learning_boundary = "Controlled PDF for {{subchapter_id}}"
source_id = "{{source_id_prefix}}-section-{{section_slug}}"
edition = "Test edition"
heading = "{{subchapter_id}}"
page_range = "Complete PDF"
reviewer = "Automated draft"
rights_note = "Controlled source"
selection_mode = "auto"
coordinator_url = "https://script.google.com/macros/s/test/exec"
coordinator_token_env = "TEST_LEARNING_PROJECT_COORDINATOR_TOKEN"
coordinator_timeout_seconds = 30
lease_seconds = 3600
heartbeat_seconds = 300
max_job_attempts = 3
git_publish = true
git_remote = "origin"
git_base_branch = "main"
git_branch_prefix = "automation"
git_create_draft_pr = true
git_run_full_tests = false
git_auto_merge = false
''',
                encoding="utf-8",
            )

            config = load_config(config_path, environ={})

            self.assertEqual("auto", config.selection_mode)
            self.assertTrue(config.git_publish)
            self.assertEqual("https://script.google.com/macros/s/test/exec", config.coordinator_url)


class RecordingPublisher(GitPublisher):
    def __init__(self, *, command_handler):
        config = SimpleNamespace(
            repo_root=Path("/repo"),
            git_remote="origin",
            git_base_branch="main",
            git_branch_prefix="automation",
            git_create_draft_pr=False,
            git_run_full_tests=False,
            git_auto_merge=False,
        )
        super().__init__(config)
        self.command_handler = command_handler
        self.commands = []

    def _run(self, arguments, *, check=True):
        self.commands.append(list(arguments))
        return self.command_handler(list(arguments), check)


class GitHandoffRecoveryTests(unittest.TestCase):
    def test_prepare_branch_deletes_empty_stale_local_branch(self):
        job_key = "abcdef1234567890"
        expected_branch = "automation/section-1-1-abcdef1234"

        def handler(args, check):
            if args[:3] == ["git", "ls-remote", "--heads"]:
                return ""
            if args[:4] == ["git", "rev-parse", "--verify", "--quiet"]:
                return "deadbeef"
            if args[:3] == ["git", "rev-list", "--count"]:
                return "0"
            return ""

        publisher = RecordingPublisher(command_handler=handler)
        branch = publisher.prepare_branch(subchapter_id="1.1", job_key=job_key)

        self.assertEqual(expected_branch, branch)
        self.assertIn(["git", "branch", "-D", expected_branch], publisher.commands)
        self.assertIn(["git", "switch", "-c", expected_branch], publisher.commands)

    def test_remote_handoff_is_recovered_without_regeneration(self):
        job_key = "abcdef1234567890"
        branch = "automation/section-1-1-abcdef1234"
        pr_url = "https://github.com/example/repo/pull/12"
        expected_paths = (
            Path("content/chapter-1/section-1-1/README.md"),
            Path("content/chapter-1/section-1-1/learning-design.md"),
            Path("content/chapter-1/section-1-1/package.json"),
            Path("content/chapter-1/section-1-1/review-record.md"),
            Path("content/source-manifests/chapter-1-section-1-1.json"),
        )
        expected_names = "\n".join(path.as_posix() for path in expected_paths)

        def handler(args, check):
            if args[:3] == ["gh", "pr", "list"]:
                return json.dumps([
                    {
                        "url": pr_url,
                        "state": "OPEN",
                        "mergedAt": None,
                        "headRefOid": "deadbeef",
                    }
                ])
            if args[:3] == ["git", "ls-remote", "--heads"]:
                return f"deadbeef\trefs/heads/{branch}"
            if args[:2] == ["git", "fetch"]:
                return ""
            if args[:3] == ["git", "diff", "--name-only"]:
                return expected_names
            if args[:2] == ["git", "rev-parse"]:
                return "deadbeef"
            return ""

        publisher = RecordingPublisher(command_handler=handler)
        lease_checks = []
        result = publisher.recover_handoff(
            subchapter_id="1.1",
            job_key=job_key,
            expected_paths=expected_paths,
            subchapter="1.1",
            package_id="chapter-1-section-1-1",
            ensure_lease=lambda: lease_checks.append("owned"),
        )

        self.assertIsNotNone(result)
        self.assertEqual(branch, result.branch)
        self.assertEqual("deadbeef", result.commit)
        self.assertEqual(pr_url, result.pr_url)
        self.assertFalse(result.merged)
        self.assertEqual(["owned"], lease_checks)
        self.assertFalse(any(command[:3] == ["git", "switch", "-c"] for command in publisher.commands))


if __name__ == "__main__":
    unittest.main()

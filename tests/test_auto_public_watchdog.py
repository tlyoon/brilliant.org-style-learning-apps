import json
import tempfile
import tomllib
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app_generator.config import load_config
from app_generator.deployments import has_current_public_deployment, load_deployment_registry
from app_generator.errors import AutoJobExecutionError
from app_generator.publishing.public import PublicPagesPublisher
from app_generator.runtime.auto import _base_completed, reconcile_auto_publications
from app_generator.runtime.watchdog import AutoAttemptSupervisor
from app_generator.runtime.state import StateStore


ROOT = Path(__file__).resolve().parents[1]


class AutoPublicConfigurationTests(unittest.TestCase):
    def test_project_public_deploy_config_and_digest_are_valid(self):
        with (ROOT / "config/configure_project.toml").open("rb") as handle:
            automation = tomllib.load(handle)["automation"]
        self.assertTrue(automation["public_deploy"])
        self.assertEqual("tlyoon/section-8-1-learning-app", automation["public_deploy_repository"])
        records = {record.app_id: record for record in load_deployment_registry(ROOT)}
        self.assertEqual(
            "https://tlyoon.github.io/section-8-1-learning-app/section-9-1/",
            records["section-9-1"].public_url,
        )
        self.assertTrue(records["section-9-1"].package_sha256)

    def test_public_deploy_rejects_missing_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            (repo / "content" / "schema").mkdir(parents=True)
            (repo / "AGENTS.md").write_text("test", encoding="utf-8")
            path = root / "project.toml"
            path.write_text(
                f'''project_name = "TestProject"
gem_url = "https://gemini.google.com/gem/test"
login_name = "test@example.com"
oauth_login = "test@example.com"
chrome_profile_dir = "{(root / 'chrome').as_posix()}"
state_dir = "{(root / 'state').as_posix()}"
repo_root = "{repo.as_posix()}"
sourcepath = "https://drive.google.com/open?id=test"
pdf_subchapter_path = "1.1"
target_filename = "source.pdf"
target_file = "{{sourcepath}}/**/{{pdf_subchapter_path}}/{{target_filename}}"
source_id_prefix = "test-project"
drive_oauth_client_file = "{(root / 'client.json').as_posix()}"
drive_token_file = "{(root / 'token.json').as_posix()}"
package_id = "chapter-{{chapter_number}}-section-{{section_slug}}"
chapter = "Chapter {{chapter_number}}"
subchapter = "{{subchapter_id}}"
chapter_dir = "chapter-{{chapter_number}}"
section_dir = "section-{{section_slug}}"
learning_boundary = "test"
source_id = "test-{{section_slug}}"
edition = "test"
heading = "test"
page_range = "test"
reviewer = "test"
rights_note = "test"
git_publish = true
public_deploy = true
public_deploy_base_url = "https://example.github.io/review/"
coordinator_token_env = "TEST_COORDINATOR_TOKEN"
''', encoding="utf-8")
            with self.assertRaisesRegex(Exception, "public_deploy_repository"):
                load_config(path, environ={})

    def test_base_completion_requires_current_public_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "content/chapter-9/section-9-1/package.json"
            package.parent.mkdir(parents=True)
            package.write_text('{"packageId":"chapter-9-section-9-1"}', encoding="utf-8")
            (root / "config").mkdir()
            (root / "config/deployments.json").write_text(json.dumps({"schemaVersion": "1.0", "deployments": []}), encoding="utf-8")
            active = SimpleNamespace(
                package_path=package, chapter_dir="chapter-9", section_dir="section-9-1",
                public_deploy=True, public_deploy_base_url="https://example.github.io/review/",
                public_deploy_repository="example/review",
            )
            config = SimpleNamespace(repo_root=root, public_deploy=True, for_subchapter=lambda _: active)
            source = SimpleNamespace(job_key="job", subchapter_id="9.1")
            self.assertEqual(set(), _base_completed(config, (source,)))
            self.assertFalse(has_current_public_deployment(root, active))


class PublicPublisherTests(unittest.TestCase):
    def test_retry_reuses_deterministic_merged_pr_without_building(self):
        package = ROOT / "content/chapter-9/section-9-1/package.json"
        config = SimpleNamespace(
            repo_root=ROOT,
            public_deploy_repository="example/pages",
            public_deploy_base_url="https://example.github.io/pages/",
            public_deploy_base_branch="main",
            public_deploy_branch_prefix="automation/public-review",
        )

        class Publisher(PublicPagesPublisher):
            def _run(self, arguments, *, cwd=None, check=True):
                if arguments[:3] == ["gh", "pr", "list"]:
                    return '[{"url":"https://github.com/example/pages/pull/7","state":"MERGED","mergedAt":"2026-10-02T00:00:00Z"}]'
                raise AssertionError(arguments)

        result = Publisher(config).publish(
            package_path=package, subchapter_id="9.1", ensure_lease=lambda: None,
        )
        self.assertTrue(result.merged)
        self.assertEqual("automation/public-review/section-9-1-" + result.package_sha256[:12], result.branch)
        self.assertEqual("https://example.github.io/pages/section-9-1/", result.public_url)

    def test_reconciliation_uses_source_main_and_finishes_public_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "content/chapter-9/section-9-1/package.json"
            package.parent.mkdir(parents=True)
            package.write_text('{"packageId":"chapter-9-section-9-1"}', encoding="utf-8")
            active = SimpleNamespace(
                package_path=package, public_deploy=True, pdf_subchapter_path="9.1",
                subchapter="9.1", package_id="chapter-9-section-9-1",
                chapter_dir="chapter-9", section_dir="section-9-1",
            )
            config = SimpleNamespace(
                repo_root=root, public_deploy=True, git_publish=True,
                for_subchapter=lambda _: active,
            )
            source = SimpleNamespace(job_key="job-9-1", subchapter_id="9.1")
            lease = SimpleNamespace()
            calls = []
            publisher = SimpleNamespace(
                sync_base=lambda: calls.append("sync"),
                has_recoverable_handoff=lambda **_: self.fail("source main must not require a source branch"),
            )
            coordinator = SimpleNamespace(
                snapshot_auto=lambda *args, **kwargs: None,
                claim_auto=lambda *args, **kwargs: lease,
                heartbeat=lambda current: current,
                checkpoint_clear=lambda current: calls.append("clear"),
                mark_generated=lambda current, **kwargs: calls.append(("generated", kwargs)),
                mark_failed=lambda *args, **kwargs: self.fail("public recovery should succeed"),
            )
            public = SimpleNamespace(
                branch="automation/public-review/section-9-1-digest",
                pr_url="https://github.com/example/pages/pull/1",
                public_url="https://example.github.io/pages/section-9-1/",
                package_sha256="a" * 64,
                merged=True,
            )
            with patch("app_generator.runtime.auto.GitPublisher", return_value=publisher), \
                 patch("app_generator.runtime.auto.DriveCoordinatorClient", return_value=coordinator), \
                 patch("app_generator.runtime.auto._drive_inventory", return_value=(source,)), \
                 patch("app_generator.runtime.auto._base_completed", return_value=set()), \
                 patch("app_generator.runtime.auto.PublicPagesPublisher") as public_factory:
                public_factory.return_value.publish.return_value = public
                self.assertEqual(1, reconcile_auto_publications(config))
            generated = next(item for item in calls if isinstance(item, tuple) and item[0] == "generated")[1]
            self.assertEqual("source-main", generated["branch"])
            self.assertEqual(public.package_sha256, generated["public_package_sha256"])

    def test_reconciliation_does_not_mark_complete_until_public_pr_merges(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "content/chapter-9/section-9-1/package.json"
            package.parent.mkdir(parents=True)
            package.write_text("{}", encoding="utf-8")
            active = SimpleNamespace(
                package_path=package, public_deploy=True, pdf_subchapter_path="9.1",
                subchapter="9.1", package_id="chapter-9-section-9-1",
                chapter_dir="chapter-9", section_dir="section-9-1",
            )
            config = SimpleNamespace(repo_root=root, public_deploy=True, git_publish=True, for_subchapter=lambda _: active)
            source, lease = SimpleNamespace(job_key="job", subchapter_id="9.1"), SimpleNamespace()
            marked = []
            coordinator = SimpleNamespace(
                snapshot_auto=lambda *args, **kwargs: None, claim_auto=lambda *args, **kwargs: lease,
                heartbeat=lambda current: current, checkpoint_clear=lambda current: None,
                mark_generated=lambda *args, **kwargs: marked.append(True), mark_failed=lambda *args, **kwargs: "interrupted",
            )
            publisher = SimpleNamespace(sync_base=lambda: None, has_recoverable_handoff=lambda **kwargs: False)
            public = SimpleNamespace(merged=False, branch="branch", pr_url="pr", public_url="url", package_sha256="a" * 64)
            with patch("app_generator.runtime.auto.GitPublisher", return_value=publisher), \
                 patch("app_generator.runtime.auto.DriveCoordinatorClient", return_value=coordinator), \
                 patch("app_generator.runtime.auto._drive_inventory", return_value=(source,)), \
                 patch("app_generator.runtime.auto._base_completed", return_value=set()), \
                 patch("app_generator.runtime.auto.PublicPagesPublisher") as public_factory:
                public_factory.return_value.publish.return_value = public
                with self.assertRaises(AutoJobExecutionError):
                    reconcile_auto_publications(config)
            self.assertEqual([], marked)


class WatchdogTests(unittest.TestCase):
    def test_three_stale_checks_terminate_without_touching_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = root / "checkpoint.json"
            checkpoint.write_text('{"mcq-easy": {}}', encoding="utf-8")
            config = SimpleNamespace(
                state_dir=root, stall_check_seconds=1, stall_after_seconds=1,
                stall_max_consecutive_checks=3, stall_terminate_grace_seconds=1,
            )

            class Process:
                def __init__(self): self.terminated = False
                def start(self): pass
                def is_alive(self): return not self.terminated
                def terminate(self): self.terminated = True
                def join(self, *_): pass

            process = Process()
            clock = iter((1, 2, 3, 4, 5, 6))

            class Supervisor(AutoAttemptSupervisor):
                def _activity(self): return ()

            supervisor = Supervisor(
                config, process_factory=lambda *_: process, monotonic=lambda: next(clock), sleeper=lambda _: None,
            )
            with self.assertRaisesRegex(AutoJobExecutionError, "stale checks"):
                supervisor.run()
            self.assertTrue(process.terminated)
            self.assertTrue(checkpoint.is_file())

    def test_preexisting_unrelated_state_writes_do_not_reset_stale_count(self):
        config = SimpleNamespace(
            state_dir=Path("."), stall_check_seconds=1, stall_after_seconds=1,
            stall_max_consecutive_checks=3, stall_terminate_grace_seconds=1,
        )

        class Process:
            def __init__(self): self.terminated = False
            def start(self): pass
            def is_alive(self): return not self.terminated
            def terminate(self): self.terminated = True
            def join(self, *_): pass

        process = Process()
        # The only path existed before the supervised child. Its mtime changes
        # repeatedly, but it must never count as this child's progress.
        activities = iter((
            (("old-run/state/run-state.json", 1),),
            (("old-run/state/run-state.json", 2),),
            (("old-run/state/run-state.json", 3),),
            (("old-run/state/run-state.json", 4),),
        ))
        clock = iter((0, 1, 2, 3, 4, 5))

        class Supervisor(AutoAttemptSupervisor):
            def _activity(self): return next(activities)

        supervisor = Supervisor(
            config, process_factory=lambda *_: process, monotonic=lambda: next(clock), sleeper=lambda _: None,
        )
        with self.assertRaisesRegex(AutoJobExecutionError, "stale checks"):
            supervisor.run()
        self.assertTrue(process.terminated)

    def test_activity_resets_stale_count(self):
        config = SimpleNamespace(
            state_dir=Path("."), stall_check_seconds=1, stall_after_seconds=1,
            stall_max_consecutive_checks=3, stall_terminate_grace_seconds=1,
        )

        class Process:
            def __init__(self): self.calls = 0; self.terminated = False
            def start(self): pass
            def is_alive(self): self.calls += 1; return self.calls <= 4
            def terminate(self): self.terminated = True
            def join(self, *_): pass

        process = Process()
        activities = iter(((), (), (("state", 1),), (("state", 1),), (("state", 1),), (("state", 1),)))
        clock = iter(range(20))

        class Supervisor(AutoAttemptSupervisor):
            def _activity(self): return next(activities)

        supervisor = Supervisor(
            config, process_factory=lambda *_: process, monotonic=lambda: next(clock), sleeper=lambda _: None,
        )
        with self.assertRaisesRegex(AutoJobExecutionError, "without a result"):
            supervisor.run()
        self.assertFalse(process.terminated)


class BackwardCompatibilityTests(unittest.TestCase):
    def test_old_run_state_without_public_fields_loads(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run-state.json"
            path.write_text(json.dumps({
                "run_id": "old", "phase": "GENERATING", "created_at": "x", "updated_at": "x",
            }), encoding="utf-8")
            state = StateStore(path, "old").state
            self.assertIsNone(state.public_deployment_url)
            self.assertFalse(state.public_deployed)


if __name__ == "__main__":
    unittest.main()

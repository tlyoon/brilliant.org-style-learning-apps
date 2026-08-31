import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app_generator.coordinator.client import QueueSnapshot
from app_generator.errors import AutoJobExecutionError, AutoModeBlockedError, NoAvailableJob
from app_generator.runtime.auto import run_continuous_auto
from app_generator.runtime.run_context import RunContext


class RecordingCheckpoint:
    def __init__(self):
        self.saved = []
        self.deleted = []
        self.cleared = 0

    def save(self, name, document):
        self.saved.append((name, document))

    def delete(self, name):
        self.deleted.append(name)

    def clear(self):
        self.cleared += 1


class ContinuousAutoTests(unittest.TestCase):
    def config(self, *, git_publish=True):
        return SimpleNamespace(
            heartbeat_seconds=300,
            git_publish=git_publish,
            worker_id="test-worker",
        )

    def snapshot(self, **overrides):
        values = dict(
            total=3,
            queued=0,
            interrupted=0,
            leased=0,
            generated=3,
            review_pending=0,
            completed=0,
            failed=0,
            next_job_key="",
            next_subchapter_id="",
        )
        values.update(overrides)
        return QueueSnapshot(**values)

    def test_auto_mode_requires_durable_git_publication(self):
        calls = []
        with self.assertRaisesRegex(AutoModeBlockedError, "git_publish=true"):
            run_continuous_auto(
                self.config(git_publish=False),
                run_once=lambda config: calls.append("run"),
                snapshotter=lambda config: self.snapshot(),
                reconciler=lambda config: 0,
                sleeper=lambda seconds: None,
            )
        self.assertEqual([], calls)

    def test_worker_continues_after_recoverable_interruption_then_finishes(self):
        calls = []
        reconciles = []
        completed = object()

        def run_once(config):
            calls.append("run")
            if len(calls) == 1:
                raise AutoJobExecutionError("temporary Gemini failure", status="interrupted", original_code="TEST")
            if len(calls) == 2:
                return completed
            raise NoAvailableJob("none")

        seen = []
        result = run_continuous_auto(
            self.config(),
            run_once=run_once,
            snapshotter=lambda config: self.snapshot(),
            reconciler=lambda config: reconciles.append("reconcile") or 0,
            on_completed=seen.append,
            sleeper=lambda seconds: self.fail("should not sleep"),
        )
        self.assertEqual(0, result)
        self.assertEqual([completed], seen)
        self.assertEqual(3, len(calls))
        self.assertEqual(["reconcile", "reconcile"], reconciles)

    def test_worker_waits_when_only_remaining_work_is_leased(self):
        attempts = {"run": 0, "snapshot": 0}
        sleeps = []

        def run_once(config):
            attempts["run"] += 1
            raise NoAvailableJob("none")

        def snapshotter(config):
            attempts["snapshot"] += 1
            if attempts["snapshot"] == 1:
                return self.snapshot(total=1, generated=0, leased=1)
            return self.snapshot(total=1, generated=1)

        result = run_continuous_auto(
            self.config(),
            run_once=run_once,
            snapshotter=snapshotter,
            reconciler=lambda config: 0,
            sleeper=sleeps.append,
        )
        self.assertEqual(0, result)
        self.assertEqual([30.0], sleeps)
        self.assertEqual(2, attempts["run"])

    def test_terminal_failure_blocks_successful_global_exit(self):
        with self.assertRaises(AutoModeBlockedError):
            run_continuous_auto(
                self.config(),
                run_once=lambda config: (_ for _ in ()).throw(NoAvailableJob("none")),
                snapshotter=lambda config: self.snapshot(total=1, generated=0, failed=1),
                reconciler=lambda config: 0,
                sleeper=lambda seconds: None,
            )

    def test_run_context_shares_only_parsed_stage_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = RecordingCheckpoint()
            context = RunContext.create(Path(directory)).with_checkpoint(checkpoint)
            context.save_raw_response("mcq-easy", "raw Gemini response")
            context.save_stage("mcq-easy", {"activities": [1]})
            self.assertEqual([("mcq-easy", {"activities": [1]})], checkpoint.saved)
            self.assertNotIn("raw Gemini response", repr(checkpoint.saved))
            context.discard_stage("mcq-easy")
            self.assertEqual(["mcq-easy"], checkpoint.deleted)

    def test_checkpoint_restore_populates_local_stage_cache_without_republishing(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = RecordingCheckpoint()
            context = RunContext.create(Path(directory)).with_checkpoint(checkpoint)
            context.restore_stages({"source-analysis": {"sectionTitle": "Recovered"}})
            self.assertEqual({"sectionTitle": "Recovered"}, context.load_stage("source-analysis"))
            self.assertEqual([], checkpoint.saved)


if __name__ == "__main__":
    unittest.main()

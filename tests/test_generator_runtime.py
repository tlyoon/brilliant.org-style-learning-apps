import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app_generator.errors import GeneratorError, NoAvailableJob
from app_generator.filesystem.outputs import Artifact, install_new_artifacts, stage_artifacts
from app_generator.runtime.orchestrator import _log_generation_exception
from app_generator.runtime.state import RunPhase, StateStore


class GeneratorRuntimeTests(unittest.TestCase):
    def test_failed_run_can_resume_but_completed_run_cannot(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            store = StateStore(path, "run-one")
            store.transition(RunPhase.CONFIG_LOADED)
            store.fail(RuntimeError("test"))
            store.resume()
            self.assertEqual(RunPhase.CONFIG_LOADED, store.state.phase)
            history_length = len(store.state.history)
            store.resume()
            self.assertEqual(history_length, len(store.state.history))
            store.transition(RunPhase.COMPLETE)
            with self.assertRaises(GeneratorError):
                store.resume()

    def test_exclusively_locked_interrupted_phase_can_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            store = StateStore(Path(directory) / "state.json", "run-interrupted")
            store.transition(RunPhase.CONFIG_LOADED)
            store.transition(RunPhase.WORKER_LOCK_ACQUIRED)
            store.transition(RunPhase.GENERATING)
            store.resume()
            self.assertEqual(RunPhase.CONFIG_LOADED, store.state.phase)
            self.assertEqual("RESUMED", store.state.history[-1]["to"])

    def test_auto_no_available_job_before_lease_logs_info_without_traceback(self):
        config = SimpleNamespace(selection_mode="auto")
        context = SimpleNamespace(run_id="run-no-job")
        with patch("app_generator.runtime.orchestrator.LOGGER") as logger:
            _log_generation_exception(
                config,
                context,
                NoAvailableJob("No queued source job is currently available"),
                lease=None,
            )

        logger.info.assert_called_once()
        logger.exception.assert_not_called()

    def test_no_available_job_after_lease_still_logs_as_failure(self):
        config = SimpleNamespace(selection_mode="auto")
        context = SimpleNamespace(run_id="run-leased")
        lease = SimpleNamespace(job_key="job-8-5")
        with patch("app_generator.runtime.orchestrator.LOGGER") as logger:
            _log_generation_exception(
                config,
                context,
                NoAvailableJob("unexpected leased-stage no-job"),
                lease=lease,
            )

        logger.exception.assert_called_once()
        logger.info.assert_not_called()

    def test_artifact_install_refuses_overwrite_and_rolls_back_failed_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            candidate = root / "candidate"
            relative = Path("content/chapter-8/section-8-1/package.json")
            stage_artifacts(candidate, [Artifact(relative, '{"draft": true}')])
            with self.assertRaises(Exception):
                install_new_artifacts(repo, candidate, [relative], verify=lambda: (_ for _ in ()).throw(RuntimeError("invalid")))
            self.assertFalse((repo / relative).exists())
            (repo / relative).parent.mkdir(parents=True, exist_ok=True)
            (repo / relative).write_text("reviewed", encoding="utf-8")
            with self.assertRaises(Exception):
                install_new_artifacts(repo, candidate, [relative], verify=lambda: None)
            self.assertEqual("reviewed", (repo / relative).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

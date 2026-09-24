import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app_generator.errors import GeneratorError, NoAvailableJob
from app_generator.filesystem.outputs import Artifact, install_new_artifacts, stage_artifacts
from app_generator.runtime.orchestrator import (
    _log_generation_exception,
    _restart_automation_browser,
    run_generation,
)
from app_generator.runtime.state import RunPhase, StateStore


class GeneratorRuntimeTests(unittest.TestCase):
    def test_transient_restart_reopens_automation_without_manual_sign_in(self):
        events = []

        class Browser:
            def start(self):
                events.append("start")
                return "driver"

            def open_window(self):
                raise AssertionError("transient restart must not open a manual sign-in window")

            def wait_for_manual_sign_in(self):
                raise AssertionError("transient restart must not pause for operator input")

        browser, driver = _restart_automation_browser(
            lambda config: Browser(),
            SimpleNamespace(),
        )

        self.assertIsInstance(browser, Browser)
        self.assertEqual("driver", driver)
        self.assertEqual(["start"], events)

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

    def test_run_generation_uses_api_backend_without_opening_chrome(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            state = root / "state"
            repo.mkdir()
            source_pdf = root / "source.pdf"
            source_pdf.write_bytes(b"%PDF-test")
            package_path = repo / "content" / "chapter-8" / "section-8-4" / "package.json"

            class Config(SimpleNamespace):
                def for_subchapter(self, subchapter_id):
                    self.pdf_subchapter_path = subchapter_id
                    return self

            config = Config(
                state_dir=state, log_level="INFO", gem_url="https://gemini.example/gem",
                selection_mode="manual", git_publish=False, uses_google_drive=False,
                pdf_subchapter_path="8.4", source_files=(source_pdf,), llm_backend="gemini_api",
                package_id="section-8-4", chapter="8", page_range="all",
                existing_source_manifest=None, repo_root=repo, max_repair_attempts=0,
                package_path=package_path, subchapter="8.4", chapter_dir="chapter-8",
                section_dir="section-8-4", manifest_relative_path=Path("content/chapter-8/section-8-4/source-manifest.json"),
            )
            fake_source = SimpleNamespace(
                path=source_pdf, controlled_filename="source.pdf",
                metadata=lambda: {"controlled_filename": "source.pdf"},
            )
            events = []

            class ApiClient:
                actual_model = "test-api-model"
                prompt_sha256 = "prompt-sha"

                def __init__(self, paths):
                    self.paths = paths

                def prepare(self):
                    events.append(("api-prepare", self.paths))

            class Protocol:
                def __init__(self, client, context):
                    events.append(("protocol-client", client))

                def generate(self, **kwargs):
                    return {"activities": []}, {"sectionTitle": "Test"}, []

                def audit_and_repair(self, package):
                    return package, []

            def install(*args, **kwargs):
                package_path.parent.mkdir(parents=True, exist_ok=True)
                package_path.write_text('{"activities": []}\n', encoding="utf-8")
                return [package_path]

            def chrome_factory(_config):
                raise AssertionError("Chrome must not be opened for gemini_api")

            with (
                patch("app_generator.runtime.orchestrator.configure_logging", return_value=None),
                patch("app_generator.runtime.orchestrator.inspect_sources", return_value=(fake_source,)),
                patch("app_generator.runtime.orchestrator.GenerationProtocol", Protocol),
                patch("app_generator.runtime.orchestrator.materialize_source_metadata", side_effect=lambda cfg, analysis: cfg),
                patch("app_generator.runtime.orchestrator.apply_source_metadata", side_effect=lambda package, cfg: package),
                patch("app_generator.runtime.orchestrator.build_manifest", return_value={}),
                patch("app_generator.runtime.orchestrator.validate_manifest", return_value=[]),
                patch("app_generator.runtime.orchestrator._stage_complete_artifacts", return_value=Path("package.json")),
                patch("app_generator.runtime.orchestrator._candidate_errors", return_value=[]),
                patch("app_generator.runtime.orchestrator.install_new_artifacts", side_effect=install),
                patch("app_generator.runtime.orchestrator.run_repository_validator", return_value=None),
            ):
                context = run_generation(
                    config,
                    chrome_factory=chrome_factory,
                    api_client_factory=lambda cfg, paths: ApiClient(paths),
                )

            self.assertEqual(RunPhase.COMPLETE, context.store.state.phase)
            self.assertEqual("gemini_api", context.store.state.llm_backend)
            self.assertEqual("test-api-model", context.store.state.actual_model)
            self.assertEqual("prompt-sha", context.store.state.prompt_sha256)
            self.assertEqual(("api-prepare", (source_pdf,)), events[0])
            self.assertIsInstance(events[1][1], ApiClient)

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

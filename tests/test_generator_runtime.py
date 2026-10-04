import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app_generator.errors import GeneratorError, NoAvailableJob
from app_generator.filesystem.outputs import Artifact, install_new_artifacts, preflight_artifact_install, stage_artifacts
from app_generator.runtime.orchestrator import (
    _log_generation_exception,
    _repair_post_semantic_validation,
    _restart_automation_browser,
    run_generation,
)
from app_generator.runtime.state import RunPhase, StateStore


class GeneratorRuntimeTests(unittest.TestCase):
    def test_post_semantic_validation_repairs_activity_errors_and_rechecks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            validation = root / "validation"
            validation.mkdir()
            context = SimpleNamespace(validation=validation, candidate=root / "candidate")
            config = SimpleNamespace(max_repair_attempts=1)
            protocol = MagicMock()
            protocol.repair_validation_errors.return_value = {"activities": [{"id": "fixed"}]}
            store = MagicMock()
            package = {"activities": [{"id": "original"}]}
            errors = ["content/x/package.json: activity[0].hints[0].zh appears to request calculation"]

            with (
                patch("app_generator.runtime.orchestrator._candidate_errors", side_effect=[errors, []]),
                patch("app_generator.runtime.orchestrator._stage_complete_artifacts"),
            ):
                result = _repair_post_semantic_validation(
                    config, context, package, {}, Path("content/x/package.json"), protocol, store
                )

            self.assertEqual({"activities": [{"id": "fixed"}]}, result)
            protocol.repair_validation_errors.assert_called_once_with(package, errors, 2)
            store.transition.assert_called_once_with(RunPhase.REPAIRING)
            self.assertTrue((validation / "semantic-validation-00.json").is_file())
            self.assertTrue((validation / "semantic-validation-01.json").is_file())

    def test_post_semantic_validation_fails_after_repair_budget_is_exhausted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            validation = root / "validation"
            validation.mkdir()
            context = SimpleNamespace(validation=validation, candidate=root / "candidate")
            config = SimpleNamespace(max_repair_attempts=1)
            protocol = MagicMock()
            protocol.repair_validation_errors.return_value = {"activities": [{"id": "still-bad"}]}
            store = MagicMock()
            package = {"activities": [{"id": "original"}]}
            errors = ["content/x/package.json: activity[0].answerLogic.zh appears to request calculation"]

            with (
                patch("app_generator.runtime.orchestrator._candidate_errors", side_effect=[errors, errors]),
                patch("app_generator.runtime.orchestrator._stage_complete_artifacts"),
            ):
                with self.assertRaisesRegex(Exception, "did not converge"):
                    _repair_post_semantic_validation(
                        config, context, package, {}, Path("content/x/package.json"), protocol, store
                    )

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

    def test_specific_run_fails_before_source_inspection_when_package_already_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            state = root / "state"
            source_pdf = root / "source.pdf"
            source_pdf.write_bytes(b"%PDF-test")
            package_path = repo / "content" / "chapter-8" / "section-8-4" / "package.json"
            package_path.parent.mkdir(parents=True, exist_ok=True)
            package_path.write_text("reviewed", encoding="utf-8")

            class Config(SimpleNamespace):
                def for_subchapter(self, subchapter_id):
                    self.pdf_subchapter_path = subchapter_id
                    return self

            config = Config(
                state_dir=state, log_level="INFO", gem_url="https://gemini.example/gem",
                selection_mode="specific", git_publish=False, uses_google_drive=False,
                pdf_subchapter_path="8.4", source_files=(source_pdf,), llm_backend="gemini_api",
                package_id="section-8-4", repo_root=repo, max_repair_attempts=0,
                package_path=package_path, subchapter="8.4", chapter_dir="chapter-8",
                section_dir="section-8-4",
                manifest_relative_path=Path("content/source-manifests/chapter-8-section-8-4.json"),
                domain_id="university-level-physics",
            )

            with (
                patch("app_generator.runtime.orchestrator.configure_logging", return_value=None),
                patch("app_generator.runtime.orchestrator.resolve_domain", return_value=SimpleNamespace(
                    id="university-level-physics", profile_version="1.0.0"
                )),
                patch("app_generator.runtime.orchestrator.inspect_sources") as inspect_sources_mock,
            ):
                with self.assertRaises(Exception) as failure:
                    run_generation(config)

            self.assertEqual("PACKAGE_ALREADY_EXISTS", failure.exception.code)
            inspect_sources_mock.assert_not_called()

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
                def __init__(self, client, context, *, domain_profile=None):
                    events.append(("protocol-client", client))
                    events.append(("protocol-domain", domain_profile))

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
                patch("app_generator.runtime.orchestrator.resolve_domain", return_value=SimpleNamespace(
                    id="university-level-physics",
                    profile_version="1.0.0",
                    identity=lambda: {
                        "id": "university-level-physics",
                        "profileVersion": "1.0.0",
                        "subject": "physics",
                        "academicLevel": "university",
                    },
                )),
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
            self.assertEqual("university-level-physics", events[2][1].id)

    def test_preflight_fails_fast_for_existing_outputs_unless_regeneration_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            relative = Path("content/chapter-8/section-8-4/package.json")
            target = repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("reviewed", encoding="utf-8")

            with self.assertRaisesRegex(Exception, "--regenerate") as failure:
                preflight_artifact_install(repo, [relative])
            self.assertEqual("PACKAGE_ALREADY_EXISTS", failure.exception.code)
            self.assertEqual([target], preflight_artifact_install(repo, [relative], replace_existing=True))

    def test_regeneration_replaces_only_after_verification_and_restores_on_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            candidate = root / "candidate"
            existing = Path("content/chapter-8/section-8-4/package.json")
            new_file = Path("content/chapter-8/section-8-4/review-record.md")
            (repo / existing).parent.mkdir(parents=True, exist_ok=True)
            (repo / existing).write_text("reviewed-original", encoding="utf-8")
            stage_artifacts(candidate, [
                Artifact(existing, '{"draft": true}'),
                Artifact(new_file, "new review"),
            ])

            with self.assertRaisesRegex(Exception, "repository artifacts were restored"):
                install_new_artifacts(
                    repo, candidate, [existing, new_file],
                    verify=lambda: (_ for _ in ()).throw(RuntimeError("invalid")),
                    replace_existing=True,
                )
            self.assertEqual("reviewed-original", (repo / existing).read_text(encoding="utf-8"))
            self.assertFalse((repo / new_file).exists())

            installed = install_new_artifacts(
                repo, candidate, [existing, new_file],
                verify=lambda: None, replace_existing=True,
            )
            self.assertEqual([repo / existing, repo / new_file], installed)
            self.assertIn('"draft": true', (repo / existing).read_text(encoding="utf-8"))
            self.assertEqual("new review\n", (repo / new_file).read_text(encoding="utf-8"))

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

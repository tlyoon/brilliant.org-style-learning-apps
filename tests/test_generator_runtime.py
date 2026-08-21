import tempfile
import unittest
from pathlib import Path

from app_generator.errors import GeneratorError
from app_generator.filesystem.outputs import Artifact, install_new_artifacts, stage_artifacts
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
            store.transition(RunPhase.COMPLETE)
            with self.assertRaises(GeneratorError):
                store.resume()

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

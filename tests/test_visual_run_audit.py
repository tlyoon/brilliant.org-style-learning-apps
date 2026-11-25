import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_visual_run import audit_run
from tests.test_visual_generation_stage import package, plans, specs

ROOT = Path(__file__).resolve().parents[1]


class OfflineVisualAuditTests(unittest.TestCase):
    def _run(self, root, *, wrong_kind=False, repair=False):
        batches = root / "batches"
        candidate = root / "candidate/content/chapter-9/section-4"
        candidate.mkdir(parents=True)
        batches.mkdir()
        (candidate / "package.json").write_text(json.dumps(package()), encoding="utf-8")
        (batches / "visual-plans.json").write_text(json.dumps(plans()), encoding="utf-8")
        data = copy.deepcopy(specs())
        if wrong_kind:
            data["activities"][0]["visualSpec"]["entities"][0]["kind"] = "invalid-kind"
        if repair:
            (batches / "visual-specs-validated.json").write_text(
                json.dumps({"activities": []}), encoding="utf-8"
            )
            (batches / "visual-specs-repair.response.txt").write_text(
                "BEGIN_JSON\n" + json.dumps(data) + "\nEND_JSON", encoding="utf-8"
            )
        else:
            (batches / "visual-specs.json").write_text(json.dumps(data), encoding="utf-8")

    def test_pass_is_explicitly_offline_only_and_read_only(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            self._run(run)
            before = {str(p): p.read_bytes() for p in run.rglob("*") if p.is_file()}
            result = audit_run(ROOT, run)
            after = {str(p): p.read_bytes() for p in run.rglob("*") if p.is_file()}
            self.assertEqual(before, after)
        self.assertEqual("contract_pass", result["outcome"])
        self.assertEqual(1, result["candidateActivities"])
        self.assertEqual(1, result["visualSpecs"])
        self.assertFalse(result["renderedPixelsVerified"])
        self.assertFalse(result["publicationVerified"])

    def test_complete_run_revalidates_installed_package_without_writes(self):
        from app_generator.visuals.generation import attach_visual_documents
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            self._run(run)
            installed = run / "installed/package.json"
            installed.parent.mkdir()
            attached = attach_visual_documents(ROOT, package(), plans(), specs())
            installed.write_text(json.dumps(attached), encoding="utf-8")
            state = run / "state/run-state.json"
            state.parent.mkdir()
            state.write_text(
                json.dumps({"phase": "COMPLETE", "installed_paths": [str(installed)]}),
                encoding="utf-8",
            )
            before = {str(p): p.read_bytes() for p in run.rglob("*") if p.is_file()}
            result = audit_run(ROOT, run)
            after = {str(p): p.read_bytes() for p in run.rglob("*") if p.is_file()}
            self.assertEqual(before, after)
            self.assertEqual("contract_pass", result["outcome"])
            self.assertEqual("completed_run_installed_package", result["source"])
            self.assertEqual(1, result["visualPlans"])
            self.assertEqual(1, result["visualSpecs"])
            self.assertFalse(result["publicationVerified"])
            broken = copy.deepcopy(attached)
            broken["activities"][0]["visualSpec"]["entities"][0]["kind"] = "body"
            installed.write_text(json.dumps(broken), encoding="utf-8")
            self.assertEqual("incomplete", audit_run(ROOT, run)["outcome"])

    def test_rejects_renderer_mismatch_and_missing_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            self._run(run, wrong_kind=True)
            outcome = audit_run(ROOT, run)
            self.assertEqual("incomplete", outcome["outcome"])
            self.assertIn("cart-collision renderer", outcome["issues"][0])
            (run / "batches/visual-specs.json").unlink()
            missing = audit_run(ROOT, run)
            self.assertEqual("incomplete", missing["outcome"])
            self.assertIn("no saved visual", missing["issues"][0])

    def test_saved_targeted_repair_is_readable_but_still_validated(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            self._run(run, repair=True)
            self.assertEqual("contract_pass", audit_run(ROOT, run)["outcome"])
            response = run / "batches/visual-specs-repair.response.txt"
            response.write_text("not JSON", encoding="utf-8")
            self.assertEqual("incomplete", audit_run(ROOT, run)["outcome"])

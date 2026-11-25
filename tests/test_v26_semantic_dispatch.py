"""BSA253 V26 exact-version normal worker, restart and negative controls."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime import v3_full_semantic_proof_dispatch as dispatch
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs

ROOT = Path(__file__).resolve().parents[1]


class SemanticV26IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = json.loads((ROOT /
            "content/chapter-9/section-9-1/package.json").read_text(
                encoding="utf8"))
        cls.queue = plan_full_semantic_proofs(
            package=cls.package, source_sha256="d"*64)

    def test_actual_eighteen_activity_package_all_semantic_tasks_covered(self):
        q = self.queue
        self.assertEqual(q["activityCount"], 18)
        self.assertGreater(q["taskCounts"]["TRILINGUAL_MEANING_EQUIVALENCE"], 18)
        self.assertGreater(q["taskCounts"]["MCQ_DISTRACTOR_SCIENCE"], 0)
        self.assertGreater(q["taskCounts"]["COMPLETE_SCIENTIFIC_MEANING"], 18)
        self.assertEqual(q["taskCounts"]["RENDERED_DIAGRAM_SCIENCE"],
                         sum(bool(a.get("visualSpec"))
                             for a in self.package["activities"]))
        self.assertEqual(
            q["taskCounts"]["RENDERED_DIAGRAM_SCIENCE"] +
            q["taskCounts"]["VISUAL_COVERAGE_NEEDS_SOURCE"], 18)
        p = dispatch._small_signed_plan(q)
        self.assertEqual(p["totalIndependentProofTasks"], q["taskCount"])
        self.assertEqual(len(p["activityTaskRoster"]), 18)
        self.assertEqual(p["academicProofsIndependentVerified"], 0)
        self.assertFalse(p["publicationAuthorized"])

    def test_compact_real_roster_under_historical_12000_byte_restart_cap(self):
        p = dispatch._small_signed_plan(self.queue)
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp)/dispatch._V26_RESULT
            identity = {"gitHead":"a"*40, "proposalSha256":"b"*64}
            data = {**identity, **p,
                    "status":"FULL_SEMANTIC_PROOFS_QUEUED_NOT_ACCEPTED",
                    "historicAmbiguousGeminiRoleReplayed":False,
                    "oldAcademicClaimsPromoted":False}
            first = _v6_checkpoint(file, data)
            self.assertLess(file.stat().st_size, 12000)
            self.assertEqual(first, _v6_checkpoint(file, data))
            altered = deepcopy(data)
            altered["totalIndependentProofTasks"] += 1
            with self.assertRaisesRegex(ValueError, "CHECKPOINT_CHANGED"):
                _v6_checkpoint(file, altered)

    def test_v26_after_signed_v25_not_optional_in_normal_source_free_worker(self):
        script = (ROOT/"scripts/run_v3_yoga6_recovery_worker.py").read_text(
            encoding="utf8")
        self.assertIn("run_post_v25_full_semantic_queue(", script)
        self.assertIn('result["fullSemanticProofQueue"]', script)
        self.assertIn('result.get("fullSemanticProofQueue",{}).get(', script)
        self.assertIn("V26_FULL_EXPLANATION_DISTRACTOR_DIAGRAM_TRILINGUAL_TASKS_QUEUED", script)

    def test_missing_or_forged_v25_cannot_enter_next_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            v25 = {"integritySha256":"a"*64, "status":dispatch._STATUS26}
            with (patch.object(dispatch, "_preflight", return_value=(
                  folder, None, None, None, None)),
                  patch.object(dispatch, "_signed", return_value=v25),
                  patch.object(dispatch, "_trusted_json",
                               side_effect=AssertionError("unsafe source access"))):
                with self.assertRaisesRegex(ValueError, "SIGNED_V25"):
                    dispatch.run_post_v25_full_semantic_queue(
                        ROOT, folder, {"gitHead":"b"*40}, {}, {}, {}, v25)

    def test_queue_task_ids_change_on_text_or_source_mutation(self):
        p = deepcopy(self.package)
        q1 = self.queue
        p["activities"][0]["prompt"]["ms"] += " altered"
        q2 = plan_full_semantic_proofs(package=p, source_sha256="d"*64)
        self.assertNotEqual(
            dispatch._small_signed_plan(q1)["exactRecomputableTaskRosterSha256"],
            dispatch._small_signed_plan(q2)["exactRecomputableTaskRosterSha256"])
        q3 = plan_full_semantic_proofs(package=self.package, source_sha256="c"*64)
        self.assertNotEqual(
            dispatch._small_signed_plan(q1)["exactRecomputableTaskRosterSha256"],
            dispatch._small_signed_plan(q3)["exactRecomputableTaskRosterSha256"])


if __name__=="__main__":
    unittest.main()

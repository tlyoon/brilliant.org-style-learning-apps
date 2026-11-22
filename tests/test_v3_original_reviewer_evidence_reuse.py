"""BSA245: real V18 chain, exact old claim reuse, hostile drift tests."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime import v3_original_reviewer_evidence_reuse as m


class OriginalReviewerEvidenceReuseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.repo = self.folder / "repo"
        self.repo.mkdir()
        self.private = self.folder / "private"
        self.private.mkdir()
        self.ready = {"gitHead": "a"*40, "proposalSha256": "b"*64}
        identity = dict(self.ready)
        self.source = _v6_checkpoint(
            self.folder / "V18_SELECTED_TEXTBOOK_SCIENCE_RESULT.json",
            {**identity, "state": "ONE_REAL_TEXTBOOK_SOURCE_AUDIT_COMPLETE",
             "audit": {"activityCount": 18, "formalAcademicPassCount": 0,
                       "packageSha256": "c"*64}})
        self.gaps = _v6_checkpoint(
            self.folder / "V18_ACADEMIC_GAP_AUDIT_RESULT.json",
            {**identity, "state": "REAL_SOURCE_BOUND_ACADEMIC_GAP_AUDIT_COMPLETE",
             "result": {"unverifiedGateInstances": 90,
                        "formalAcademicPASS": False}})
        self.v18 = _v6_checkpoint(
            self.folder / m._V18,
            {**identity, "status": m._STATUS,
             "realSingleTextbookPdfOpened": True,
             "nextTaskDispatchActuallyExecuted": True,
             "additionalExternalPdfsRequired": False, "newModelCalls": 0,
             "publicationAuthorized": False,
             "resultSha256": self.source["integritySha256"],
             "academicGapAuditReceiptSha256": self.gaps["integritySha256"]})
        self.original = {
            "oldUncertainIndex": 0, "originalAssessedUnchanged": 1,
            "parentSha256": "c"*64,
            "items": [
                {"index": i, "activityId": "act-%02d" % i,
                 "originalReviewState": "AGGREGATE_EXISTS"}
                for i in range(1, 18)]}
        self.passes = [
            {"originalActivityIndex": i, "activityId": "act-%02d" % i,
             "status": "POTENTIALLY_REUSABLE_NOT_RELEASE_ACCEPTED",
             "sourcePackageSha256": "c"*64,
             "sourceReviewSha256": "%064x" % i,
             "supplementalReviewSliceSha256": "%064x" % (i + 100)}
            for i in range(1, 18)]
        self.preflight = patch.object(
            m, "_preflight", return_value=(self.folder, None, None, None, None))
        self.read_old = patch.object(m, "section91_evidence",
                                     return_value=self.original)
        self.read_pass = patch.object(m, "verified_section91_standing_passes",
                                      return_value=self.passes)
        self.preflight.start()
        self.read_old.start()
        self.read_pass.start()
        self.addCleanup(self.preflight.stop)
        self.addCleanup(self.read_old.stop)
        self.addCleanup(self.read_pass.stop)

    def run_stage(self, v18=None):
        return m.run_post_v18_original_review_reuse(
            self.repo, self.private, self.ready, {}, {}, {},
            self.v18 if v18 is None else v18)

    def test_normal_v18_v19_dispatch_real_reuse_and_idempotent(self):
        first = self.run_stage()
        second = self.run_stage()
        self.assertEqual(first, second)
        self.assertEqual(first["status"], m._STATUS19)
        self.assertEqual(first["reusedIndependentTwoRolePairs"], 17)
        self.assertEqual(first["independentAcademicProofsStillOpen"], 90)
        self.assertFalse(first["independentScientificAcceptanceComplete"])
        self.assertFalse(first["oldUncertainRoleReplayed"])
        self.assertEqual(first["newModelCalls"], 0)
        self.assertTrue((self.folder / m._PRE).is_file())
        self.assertTrue((self.folder / m._RESULT).is_file())
        self.assertTrue((self.folder / m._V19).is_file())

    def test_forged_v18_never_dispatches(self):
        changed = {**self.v18, "newModelCalls": 1}
        with self.assertRaisesRegex(ValueError, "V19_GENUINE"):
            self.run_stage(changed)
        self.assertFalse((self.folder / m._PRE).exists())

    def test_in_memory_mutation_cannot_replace_disk_evidence(self):
        self.source["audit"]["packageSha256"] = "d"*64
        # The signer reads the trusted disk record rather than caller data.
        self.assertEqual(self.run_stage()["status"], m._STATUS19)

    def test_tampered_v18_stored_gap_receipt_blocks_dispatch(self):
        path = self.folder / "V18_ACADEMIC_GAP_AUDIT_RESULT.json"
        raw = path.read_text(encoding="utf8")
        path.write_text(raw.replace('"unverifiedGateInstances": 90',
                                    '"unverifiedGateInstances": 89'),
                        encoding="utf8")
        with self.assertRaises((ValueError, KeyError)):
            self.run_stage()
        self.assertFalse((self.folder / m._PRE).exists())

    def test_original_uncertain_index_cannot_be_replayed(self):
        self.original["oldUncertainIndex"] = 1
        with self.assertRaisesRegex(ValueError, "V19_ORIGINAL"):
            self.run_stage()
        self.assertFalse((self.folder / m._RESULT).exists())

    def test_original_activity_or_review_digest_swap_fails(self):
        self.passes[0]["sourceReviewSha256"] = self.passes[1]["sourceReviewSha256"]
        with self.assertRaisesRegex(ValueError, "V19_ORIGINAL"):
            self.run_stage()
        self.assertFalse((self.folder / m._V19).exists())

    def test_source_package_mismatch_fails(self):
        self.original["parentSha256"] = "e"*64
        with self.assertRaisesRegex(ValueError, "V19_ORIGINAL"):
            self.run_stage()

    def test_unsupported_formal_release_claim_never_generated(self):
        result = self.run_stage()
        self.assertNotIn("academicQA", result)
        self.assertFalse(result["publicationAuthorized"])
        self.assertNotIn("sourceText", str(result))
        self.assertNotIn("apiKey", str(result))

    def test_normal_worker_dispatch_and_exit_guard_required(self):
        worker = (Path(__file__).resolve().parents[1]
                  / "scripts" / "run_v3_yoga6_recovery_worker.py").read_text(
                      encoding="utf8")
        self.assertIn("run_post_v18_original_review_reuse(", worker)
        self.assertIn('result["existingOriginalReviewerEvidenceReuse"]', worker)
        self.assertIn('V19_17_EXISTING_REVIEW_PAIRS_RECONCILED_ACADEMIC_PROOFS_STILL_OPEN',
                      worker)
        self.assertIn('"independentAcademicProofsStillOpen")==90', worker)


if __name__ == "__main__":
    unittest.main()

"""Synthetic negative controls for bounded unseen-PDF generalization evidence.

No real textbook PDF, Gemini call, student record or network access is needed.
These tests do not assert the live generator has passed a held-out campaign.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest

from app_generator.validation.heldout_generalization_gate import (
    STAGES, canonical_sha256, evaluate_campaign, validate_manifest,
)
from scripts.assess_heldout_generalization import main as cli_main


def fixture() -> tuple[dict, dict]:
    manifest = {
        "schemaVersion": 1,
        "campaignId": "heldout-physics-round-one",
        "round": 1,
        "baselineGitSha": "a" * 40,
        "profileId": "university-level-physics",
        "selectionWitnessSha256": "e" * 64,
        "priorCampaign": None,
        "sources": [
            {"caseId": "unseen-mechanics", "sourceSha256": "1" * 64,
             "topicFamily": "mechanics", "declaredUnseen": True,
             "rightsCleared": True},
            {"caseId": "unseen-electricity", "sourceSha256": "2" * 64,
             "topicFamily": "electromagnetism", "declaredUnseen": True,
             "rightsCleared": True},
            {"caseId": "unseen-optics", "sourceSha256": "3" * 64,
             "topicFamily": "waves-optics", "declaredUnseen": True,
             "rightsCleared": True},
        ],
    }
    results = {
        "schemaVersion": 1,
        "campaignId": manifest["campaignId"],
        "manifestSha256": canonical_sha256(manifest),
        "engineGitSha": manifest["baselineGitSha"],
        "cases": [
            {"caseId": source["caseId"],
             "sourceSha256": source["sourceSha256"],
             "engineGitSha": manifest["baselineGitSha"],
             "stages": {name: {"status": "PASS", "evidenceSha256": "9" * 64}
                        for name in STAGES},
             "packageSha256": str(i + 4) * 64,
             "academicQA": "REVIEW_REQUIRED",
             "bespokeCodeChanges": False,
             "publicationAuthorized": False}
            for i, source in enumerate(manifest["sources"])
        ],
    }
    return manifest, results


class HeldoutGeneralizationTests(unittest.TestCase):
    def setUp(self):
        self.manifest, self.results = fixture()

    def check(self):
        return evaluate_campaign(self.manifest, self.results)

    def test_three_distinct_topics_can_reach_provisional_status_only(self):
        report = self.check()
        self.assertEqual(3, report["draftsReportedComplete"])
        self.assertEqual("READY_FOR_TRUSTED_PROVENANCE_AUDIT",
                         report["technicalResult"])
        for gate in ("realPdfExecutionPerformedHere",
                     "selectionAndRightsIndependentlyVerified",
                     "sourceReceiptsIndependentlyVerifiedHere",
                     "technicalAcceptanceGranted",
                     "academicAcceptanceGranted", "publicationAuthorized"):
            self.assertFalse(report[gate])
        self.assertEqual(3, report["academicStatusCounts"]["REVIEW_REQUIRED"])

    def test_pdf_specific_code_edits_are_never_admitted(self):
        self.results["cases"][1]["bespokeCodeChanges"] = True
        with self.assertRaisesRegex(ValueError, "PDF-specific"):
            self.check()

    def test_changed_engine_revision_is_rejected_not_reclassified(self):
        self.results["cases"][1]["engineGitSha"] = "b" * 40
        with self.assertRaisesRegex(ValueError, "frozen baseline"):
            self.check()
        self.results["cases"][1]["engineGitSha"] = "a" * 40
        self.results["engineGitSha"] = "b" * 40
        with self.assertRaisesRegex(ValueError, "candidate code changed"):
            self.check()

    def test_stale_manifest_or_substituted_pdf_rejected(self):
        self.results["manifestSha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "stale"):
            self.check()
        self.results["manifestSha256"] = canonical_sha256(self.manifest)
        self.results["cases"][0]["sourceSha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "substituted"):
            self.check()

    def test_missing_result_or_duplicate_id_cannot_inflate_coverage(self):
        self.results["cases"].pop()
        with self.assertRaisesRegex(ValueError, "all three"):
            self.check()
        _, self.results = fixture()
        self.results["cases"][0]["caseId"] = self.results["cases"][1]["caseId"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.check()

    def test_missing_stage_receipt_cannot_be_reported_as_pass(self):
        self.results["cases"][0]["stages"]["source_ingestion"]["evidenceSha256"] = None
        with self.assertRaisesRegex(ValueError, "stage receipt"):
            self.check()

    def test_fail_does_not_grant_completion_or_publication(self):
        stage = self.results["cases"][0]["stages"]["draft_schema"]
        stage["status"] = "FAIL"
        stage["evidenceSha256"] = None
        report = self.check()
        self.assertEqual("FAILED_LIMITED_CAMPAIGN", report["technicalResult"])
        self.assertEqual(2, report["draftsReportedComplete"])
        self.assertFalse(report["publicationAuthorized"])

    def test_external_block_is_distinct_from_a_defect_and_no_retry(self):
        stage = self.results["cases"][0]["stages"]["trilingual_render"]
        stage["status"] = "BLOCKED_EXTERNAL"
        stage["evidenceSha256"] = None
        report = self.check()
        self.assertEqual("BLOCKED_EXTERNAL", report["technicalResult"])
        self.assertFalse(report["technicalAcceptanceGranted"])
        self.assertEqual("BLOCKED_EXTERNAL",
                         report["caseOutcomes"]["unseen-mechanics"])

    def test_missing_stage_yields_incomplete_not_success(self):
        stage = self.results["cases"][0]["stages"]["source_ingestion"]
        stage["status"] = "NOT_RUN"
        stage["evidenceSha256"] = None
        self.assertEqual("INCOMPLETE", self.check()["technicalResult"])

    def test_failure_must_not_carry_a_passing_receipt(self):
        self.results["cases"][0]["stages"]["source_ingestion"]["status"] = "FAIL"
        with self.assertRaisesRegex(ValueError, "cannot claim a PASS receipt"):
            self.check()

    def test_manifest_rejects_narrow_or_recycled_topic_scope(self):
        self.manifest["sources"][2]["topicFamily"] = "mechanics"
        with self.assertRaisesRegex(ValueError, "repeated source"):
            validate_manifest(self.manifest)
        self.manifest, _ = fixture()
        self.manifest["sources"][2]["sourceSha256"] = "1" * 64
        with self.assertRaisesRegex(ValueError, "repeated source"):
            validate_manifest(self.manifest)
        self.manifest, _ = fixture()
        self.manifest["sources"].pop()
        with self.assertRaisesRegex(ValueError, "exactly three"):
            validate_manifest(self.manifest)

    def test_not_unseen_or_unlicensed_not_a_valid_holdout(self):
        self.manifest["sources"][0]["declaredUnseen"] = False
        with self.assertRaisesRegex(ValueError, "unseen/rights"):
            validate_manifest(self.manifest)
        self.manifest["sources"][0]["declaredUnseen"] = True
        self.manifest["sources"][1]["rightsCleared"] = False
        with self.assertRaisesRegex(ValueError, "unseen/rights"):
            validate_manifest(self.manifest)

    def test_max_two_rounds_and_second_must_use_new_pdfs(self):
        self.manifest["round"] = 3
        with self.assertRaisesRegex(ValueError, "at most one correction"):
            validate_manifest(self.manifest)
        self.manifest["round"] = 2
        self.manifest["priorCampaign"] = {
            "receiptSha256": "a" * 64,
            "genericFixRegressionSha256": "b" * 64,
            "sourceSha256s": ["1" * 64, "f" * 64, "e" * 64],
        }
        with self.assertRaisesRegex(ValueError, "previously used"):
            validate_manifest(self.manifest)
        self.manifest["priorCampaign"]["sourceSha256s"][0] = "d" * 64
        self.results["manifestSha256"] = canonical_sha256(self.manifest)
        self.assertTrue(self.check()["stopAfterThisRoundIfFailed"])

    def test_second_round_requires_generic_repair_proof(self):
        self.manifest["round"] = 2
        with self.assertRaisesRegex(ValueError, "one generic correction"):
            validate_manifest(self.manifest)

    def test_academic_pass_label_does_not_authorize_release(self):
        self.results["cases"][0]["academicQA"] = "PASS"
        report = self.check()
        self.assertEqual(1, report["academicStatusCounts"]["PASS"])
        self.assertFalse(report["academicAcceptanceGranted"])
        self.assertFalse(report["publicationAuthorized"])

    def test_unexpected_source_text_and_secret_fields_rejected(self):
        self.manifest["sources"][0]["rawText"] = "PRIVATE SOURCE"
        with self.assertRaisesRegex(ValueError, "private-safe metadata"):
            validate_manifest(self.manifest)
        self.manifest, self.results = fixture()
        self.results["cases"][0]["apiToken"] = "SECRET"
        with self.assertRaisesRegex(ValueError, "unknown or missing"):
            self.check()

    def test_cli_requires_new_private_receipt_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            m = root / "manifest.json"
            r = root / "receipts.json"
            out = root / "evaluation.json"
            m.write_text(json.dumps(self.manifest), encoding="utf-8")
            r.write_text(json.dumps(self.results), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, cli_main([
                    "--manifest", str(m), "--results", str(r), "--out", str(out)]))
                self.assertEqual(2, cli_main([
                    "--manifest", str(m), "--results", str(r), "--out", str(out)]))
            actual = json.loads(out.read_text(encoding="utf-8"))
            self.assertFalse(actual["publicationAuthorized"])

    def test_cli_fails_closed_on_corrupt_receipts_without_source_leak(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            m = root / "manifest.json"
            r = root / "receipts.json"
            out = root / "evaluation.json"
            m.write_text(json.dumps(self.manifest), encoding="utf-8")
            bad = deepcopy(self.results)
            bad["cases"][0]["sourceSha256"] = "PRIVATE-PDF-TEXT"
            r.write_text(json.dumps(bad), encoding="utf-8")
            stream = io.StringIO()
            with redirect_stdout(stream):
                self.assertEqual(2, cli_main([
                    "--manifest", str(m), "--results", str(r), "--out", str(out)]))
            self.assertFalse(out.exists())
            self.assertNotIn("PRIVATE-PDF-TEXT", stream.getvalue())

    def test_original_manifest_not_mutated_by_evaluation(self):
        original, reports = fixture()
        before = deepcopy(original)
        evaluate_campaign(original, reports)
        self.assertEqual(before, original)


if __name__ == "__main__":
    unittest.main()

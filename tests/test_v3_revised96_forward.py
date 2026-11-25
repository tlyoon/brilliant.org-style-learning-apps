"""BSA208: fake-only post-review forward progress fault injection, no API I/O."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

from app_generator.runtime.v3_revised96_forward import (
    advance_post_revised96_science,
)
from app_generator.runtime.v3_section96_authorized_revised_qa import (
    _EXPECTED_SLICES,
)
from scripts.run_v3_yoga6_recovery_worker import _continue_revised96_source_free


def _review():
    return {
        "status": "REVISED96_AUTHORIZED_BATCH_COMPLETED",
        "maxGeminiReviewerCalls": 4,
        "versionedScopeAdmitted": False,
        "publicationAuthorized": False,
        "outcomes": [
            {"index": row[0], "reviewSliceSha256": row[3],
             "newConsensusPass": True, "newScientificRepairRequired": False,
             "newUncertain": False}
            for row in _EXPECTED_SLICES
        ],
    }


def _forward():
    sha = "a" * 64
    return {
        "section96ScienceIntegrated": True,
        "proposalSha256": sha, "paidGeminiCalls": 0,
        "versionedScopeAdmitted": False, "publicationAuthorized": False,
        "realCandidateBrowserAcceptance": {
            "status": "ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS",
            "proposalSha256": sha, "activitiesInCandidate": 108,
            "all108ActivitiesVisited": True,
            "renderedChecks": 698, "allLocaleViewportPromptChecks": 648,
            "integritySha256": "b" * 64, "publicationAuthorized": False,
        },
    }


class Revised96ContinuationTests(unittest.TestCase):
    def test_two_genuine_passes_advance_one_sourcefree_and_browser_stage(self):
        calls = []
        result = advance_post_revised96_science(
            _review(), lambda: calls.append("sourcefree") or _forward())
        self.assertEqual(calls, ["sourcefree"])
        self.assertEqual(result["status"],
                         "REVISED96_AUTOMATICALLY_ADVANCED_TO_108_BROWSER_PASS")
        self.assertEqual(result["paidGeminiCalls"], 0)
        self.assertFalse(result["publicationAuthorized"])

    def test_scientific_fail_complete_is_not_two_passes(self):
        for bad in ("science_fail", "uncertain", "wrong_sha", "one_item",
                    "wrong_identity", "publication", "admission"):
            review = _review()
            if bad == "science_fail":
                review["outcomes"][1]["newConsensusPass"] = False
                review["outcomes"][1]["newScientificRepairRequired"] = True
            elif bad == "uncertain":
                review["outcomes"][0]["newUncertain"] = True
            elif bad == "wrong_sha":
                review["outcomes"][1]["reviewSliceSha256"] = "0" * 64
            elif bad == "one_item":
                review["outcomes"].pop()
                review["maxGeminiReviewerCalls"] = 2
            elif bad == "wrong_identity":
                review["outcomes"][0]["index"] = 9
            elif bad == "publication":
                review["publicationAuthorized"] = True
            else:
                review["versionedScopeAdmitted"] = True
            with self.subTest(bad=bad):
                output = advance_post_revised96_science(
                    review, lambda: self.fail("MUST NOT dispatch browser"))
                self.assertEqual(output["status"],
                                 "STOP_REVISED96_NOT_TWO_GENUINE_SCIENCE_PASSES")
                self.assertFalse(output["sourceFreeExecuted"])

    def test_uncertain_or_incomplete_batch_does_not_invoke_sourcefree(self):
        for status in ("REVISED96_STOPPED_AT_REVIEW_BOUNDARY",
                       "REVISED96_PROVIDER_UNKNOWN", None):
            review = _review()
            review["status"] = status
            output = advance_post_revised96_science(
                review, lambda: self.fail("Should not run"))
            self.assertEqual(output["status"],
                             "STOP_REVISED96_REVIEW_BOUNDARY_UNRESOLVED")

    def test_browser_or_staging_not_proven_fails_closed(self):
        for bad in ("wrong_proposal", "no_science", "not_full",
                    "no_browser", "paid_calls", "admitted", "wrong_checks"):
            forward = _forward()
            if bad == "wrong_proposal":
                forward["realCandidateBrowserAcceptance"]["proposalSha256"] = "c" * 64
            elif bad == "no_science":
                forward["section96ScienceIntegrated"] = False
            elif bad == "not_full":
                forward["realCandidateBrowserAcceptance"]["activitiesInCandidate"] = 107
            elif bad == "no_browser":
                forward.pop("realCandidateBrowserAcceptance")
            elif bad == "paid_calls":
                forward["paidGeminiCalls"] = 1
            elif bad == "admitted":
                forward["versionedScopeAdmitted"] = True
            else:
                forward["realCandidateBrowserAcceptance"]["renderedChecks"] = 697
            with self.subTest(bad=bad):
                output = advance_post_revised96_science(_review(), lambda: forward)
                self.assertEqual(output["status"],
                                 "STOP_REVISED96_SOURCEFREE_NOT_VERIFIED")

    def test_local_failure_preserves_completed_reviews_for_next_restart(self):
        report = _review()
        def broken():
            raise OSError("synthetic local Chrome failure")
        output = advance_post_revised96_science(report, broken)
        self.assertEqual(output["status"],
                         "STOP_REVISED96_SOURCEFREE_EXECUTION_FAILED")
        self.assertEqual(output["errorClass"], "OSError")
        self.assertFalse(output["publicationAuthorized"])
        self.assertEqual(report, _review())

    def test_reused_bounded_browser_receipt_is_accepted_without_paid_call(self):
        forward = _forward()
        forward["realCandidateBrowserAcceptance"]["reusedVerifiedBrowserReceipt"] = True
        output = advance_post_revised96_science(_review(), lambda: forward)
        self.assertTrue(output["reusedVerifiedBrowserReceipt"])
        self.assertEqual(output["paidGeminiCalls"], 0)

    def test_actual_normal_worker_dispatches_registered_local_stage(self):
        private = Path("synthetic-private")
        forward = _forward()
        with patch("scripts.run_v3_yoga6_recovery_worker."
                   "advance_source_free_until_boundary",
                   return_value={"syntheticStage": True}) as stage, patch(
                   "scripts.run_v3_yoga6_recovery_worker."
                   "_complete_source_free_with_browser",
                   return_value=forward) as browser:
            output = _continue_revised96_source_free(private, _review())
        self.assertEqual(output["status"],
                         "REVISED96_AUTOMATICALLY_ADVANCED_TO_108_BROWSER_PASS")
        stage.assert_called_once()
        browser.assert_called_once_with(private, {"syntheticStage": True})

    def test_worker_skips_local_stage_on_saved_review_uncertainty(self):
        private = Path("synthetic-private")
        review = _review()
        review["outcomes"][0]["newConsensusPass"] = False
        review["outcomes"][0]["newUncertain"] = True
        with patch("scripts.run_v3_yoga6_recovery_worker."
                   "advance_source_free_until_boundary") as stage:
            output = _continue_revised96_source_free(private, review)
            stage.assert_not_called()
        self.assertEqual(output["status"],
                         "STOP_REVISED96_NOT_TWO_GENUINE_SCIENCE_PASSES")


if __name__ == "__main__":
    unittest.main()

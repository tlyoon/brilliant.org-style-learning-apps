"""BSA211: cross-branch normal worker regression for Python import scoping.

Tests make no network, browser or Gemini calls. They reach the actual
main() four-new-activity dispatch through mocks of only the external steps.
"""
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import run_v3_yoga6_recovery_worker as worker


class FourNewWorkerDispatchTests(unittest.TestCase):
    def test_real_normal_cli_branch_invokes_capability_without_local_shadow(self):
        with TemporaryDirectory() as root, ExitStack() as stack:
            private = Path(root)
            baseline = {"section96ScienceIntegrated": True,
                        "paidGeminiCalls": 0,
                        "proposalSha256": "a" * 64,
                        "realCandidateBrowserAcceptance": {
                            "status": "ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS",
                            "proposalSha256": "a" * 64,
                            "renderedChecks": 698,
                            "all108ActivitiesVisited": True,
                        }}
            review = {"status": "NEW4_AUTHORIZED_BATCH_COMPLETED",
                      "outcomes": [], "publicationAuthorized": False}
            post = {"status": "NEW4_AUTOMATICALLY_ADVANCED_108_BROWSER_PASS",
                    "publicationAuthorized": False, "paidGeminiCalls": 0}
            def mock(name, **kwargs):
                return stack.enter_context(patch(name, **kwargs))
            mock("scripts.run_v3_yoga6_recovery_worker.checked_private_root",
                 return_value=private)
            host = mock(
                "scripts.run_v3_yoga6_recovery_worker."
                "require_authorized_native_review_host", return_value=None)
            stage = mock(
                "scripts.run_v3_yoga6_recovery_worker."
                "advance_source_free_until_boundary", return_value={})
            mock("scripts.run_v3_yoga6_recovery_worker."
                 "_complete_source_free_with_browser", return_value=baseline)
            mock("app_generator.runtime.v3_four_new92_review."
                 "exact_four_unreviewed", return_value=[
                     {"index": 14, "sha": "f" * 64}])
            grant = mock("app_generator.runtime.v3_four_new92_review."
                         "authorize_four_new", return_value={})
            delegated = mock(
                "app_generator.runtime.native_sdk_environment."
                "delegate_to_supported_sdk", return_value=None)
            mock("scripts.run_v3_yoga6_recovery_worker._load_native_config",
                 return_value=object())
            capability = mock(
                "scripts.run_v3_yoga6_recovery_worker."
                "diagnose_declared_generation_support",
                return_value={"status": "MODEL_GENERATION_ACTION_DECLARED_QUOTA_UNVERIFIED",
                              "sourceFree": True, "paidModelCalls": 0})
            review_action = mock("app_generator.runtime.v3_four_new92_review."
                                 "advance_four_new", return_value=review)
            continuation = mock("app_generator.runtime.v3_four_new92_review."
                                "continue_four_to_browser", return_value=post)
            printed = []
            mock("scripts.run_v3_yoga6_recovery_worker._print",
                 side_effect=printed.append)
            outcome = worker.main([
                "--advance-new-four", "--execute",
                "--allow-generated-text-transfer",
                "--max-forward-activities", "4",
                "--max-forward-seconds", "900",
            ])
            self.assertEqual(outcome, 0)
            self.assertEqual(printed[0]["postReviewAutomaticContinuation"], post)
            host.assert_called()
            stage.assert_called()
            grant.assert_called_once()
            delegated.assert_called_once()
            capability.assert_called_once()
            review_action.assert_called_once()
            continuation.assert_called_once()

    def test_incompatible_new_four_modes_stop_before_provider(self):
        self.assertEqual(worker.main([
            "--advance-new-four", "--source-free-advance"]), 2)
        self.assertEqual(worker.main([
            "--advance-new-four", "--advance-revised-96"]), 2)


if __name__ == "__main__":
    unittest.main()

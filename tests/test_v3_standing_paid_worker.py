"""BSA217 production normal Yoga6 standing-science dispatch, fake dependencies."""
from contextlib import ExitStack
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import run_v3_yoga6_recovery_worker as worker


class StandingWorkerTests(unittest.TestCase):
    def test_standing_normal_worker_real_dispatch_bounded_and_local_browser(self):
        with TemporaryDirectory() as root, ExitStack() as stack:
            private=Path(root)
            stack.enter_context(patch.dict(os.environ,{"LOCALAPPDATA":root}))
            def mock(name,**kwargs):
                return stack.enter_context(patch(name,**kwargs))
            mock("scripts.run_v3_yoga6_recovery_worker.checked_private_root",
                 return_value=private)
            host=mock("scripts.run_v3_yoga6_recovery_worker."
                      "require_authorized_native_review_host")
            mock("app_generator.runtime.v3_standing_paid_science."
                 "section91_evidence",return_value={
                     "items":[{"index":1,"activityId":"mock-01",
                               "sha":"f"*64,
                               "originalReviewState":"UNREVIEWED_ELIGIBLE"}]})
            grant=mock("app_generator.runtime.v3_standing_paid_science."
                       "authorize_standing",return_value={
                           "standingConsent":True,"maxPaidGeminiCalls":8})
            browser={"status":"ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS",
                     "proposalSha256":"a"*64,"renderedChecks":698,
                     "all108ActivitiesVisited":True,
                     "integritySha256":"b"*64}
            pre={"section96ScienceIntegrated":True,
                 "paidGeminiCalls":0,"proposalSha256":"a"*64,
                 "realCandidateBrowserAcceptance":browser}
            local=mock("scripts.run_v3_yoga6_recovery_worker."
                       "_complete_source_free_with_browser",
                       side_effect=[pre,pre])
            mock("scripts.run_v3_yoga6_recovery_worker."
                 "advance_source_free_until_boundary",return_value={})
            sdk=mock("app_generator.runtime.native_sdk_environment."
                     "delegate_to_supported_sdk",return_value=None)
            mock("scripts.run_v3_yoga6_recovery_worker._load_native_config",
                 return_value={})
            mock("scripts.run_v3_yoga6_recovery_worker."
                 "diagnose_declared_generation_support",return_value={
                     "status":"MODEL_GENERATION_ACTION_DECLARED_QUOTA_UNVERIFIED",
                     "sourceFree":True,"paidModelCalls":0})
            review=mock("app_generator.runtime.v3_standing_paid_science."
                        "advance_standing_science",return_value={
                            "status":"STANDING_BOUNDED_BATCH_COMPLETED",
                            "allNewScientificPass":True,"outcomes":[
                                {"index":1,"newConsensusPass":True}]})
            printed=[]
            mock("scripts.run_v3_yoga6_recovery_worker._print",
                 side_effect=printed.append)
            status=worker.main([
                "--standing-science","--execute",
                "--allow-generated-text-transfer",
                "--max-forward-activities","4",
                "--max-forward-seconds","900"])
            self.assertEqual(status,0)
            host.assert_called_once()
            grant.assert_called_once()
            review.assert_called_once()
            sdk.assert_called_once()
            self.assertEqual(local.call_count,2)
            self.assertEqual(printed[0]["postReviewAutomaticContinuation"]
                             ["status"],
                             "STANDING_AUTOMATICALLY_ADVANCED_BROWSER_PASS")

    def test_missing_transfer_or_conflicting_modes_never_use_provider(self):
        self.assertEqual(worker.main([
            "--standing-science","--source-free-advance"]),2)
        self.assertEqual(worker.main([
            "--standing-science","--advance-new-four"]),2)
        self.assertEqual(worker.main([
            "--standing-science","--execute"]),2)

    def test_old_uncertain_no_browser_acceptance_cannot_be_ignored(self):
        with TemporaryDirectory() as root, ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ,{"LOCALAPPDATA":root}))
            def mock(name,**kwargs):
                return stack.enter_context(patch(name,**kwargs))
            mock("scripts.run_v3_yoga6_recovery_worker.checked_private_root",
                 return_value=Path(root))
            mock("scripts.run_v3_yoga6_recovery_worker."
                 "require_authorized_native_review_host")
            mock("app_generator.runtime.v3_standing_paid_science."
                 "section91_evidence",return_value={"items":[]})
            mock("app_generator.runtime.v3_standing_paid_science."
                 "authorize_standing",return_value={})
            mock("scripts.run_v3_yoga6_recovery_worker."
                 "advance_source_free_until_boundary",return_value={})
            mock("scripts.run_v3_yoga6_recovery_worker."
                 "_complete_source_free_with_browser",return_value={
                     "section96ScienceIntegrated":True,"paidGeminiCalls":0,
                     "proposalSha256":"f"*64,
                     "realCandidateBrowserAcceptance":{
                         "status":"ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS",
                         "proposalSha256":"e"*64,
                         "renderedChecks":697,
                         "all108ActivitiesVisited":True}})
            provider=mock("app_generator.runtime.v3_standing_paid_science."
                          "advance_standing_science")
            self.assertEqual(worker.main([
                "--standing-science","--execute",
                "--allow-generated-text-transfer"]),3)
            provider.assert_not_called()


if __name__=="__main__":
    unittest.main()

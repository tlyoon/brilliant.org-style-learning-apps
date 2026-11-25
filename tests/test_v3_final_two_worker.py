"""BSA218: v7 normal worker dispatch, no fake success or old-role replay."""
from contextlib import ExitStack
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import run_v3_yoga6_recovery_worker as worker


class FinalTwoWorkerTests(unittest.TestCase):
    def arrange(self):
        stack=ExitStack()
        self.addCleanup(stack.close)
        tmp=TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base=Path(tmp.name)
        stack.enter_context(patch.dict(os.environ,{"LOCALAPPDATA":tmp.name}))
        def mock(name,**kwargs):
            return stack.enter_context(patch(name,**kwargs))
        mock("scripts.run_v3_yoga6_recovery_worker.checked_private_root",
             return_value=base)
        mock("scripts.run_v3_yoga6_recovery_worker."
             "require_authorized_native_review_host")
        mock("app_generator.runtime.v3_final_two_science."
             "stage_final_two_new_inputs",return_value=[
                 {"index":0,"section":"section-9-1",
                  "sha":"1"*64,"candidateSha256":"2"*64},
                 {"index":6,"section":"section-9-6",
                  "sha":"3"*64,"candidateSha256":"4"*64}])
        mock("app_generator.runtime.v3_standing_paid_science."
             "authorize_standing",return_value={"standingConsent":True,
                                                 "maxPaidGeminiCalls":4})
        browser={"status":"ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS",
                 "renderedChecks":698,"all108ActivitiesVisited":True,
                 "proposalSha256":"f"*64}
        pre={"section96ScienceIntegrated":True,"paidGeminiCalls":0,
             "proposalSha256":"f"*64,"realCandidateBrowserAcceptance":browser}
        post={**pre,"finalTwoScienceIntegrated":True}
        local=mock("scripts.run_v3_yoga6_recovery_worker."
                   "_complete_source_free_with_browser",side_effect=[pre,post])
        mock("scripts.run_v3_yoga6_recovery_worker."
             "advance_source_free_until_boundary",return_value={})
        mock("app_generator.runtime.native_sdk_environment."
             "delegate_to_supported_sdk",return_value=None)
        mock("scripts.run_v3_yoga6_recovery_worker._load_native_config",
             return_value={})
        mock("scripts.run_v3_yoga6_recovery_worker."
             "diagnose_declared_generation_support",return_value={
                 "status":"MODEL_GENERATION_ACTION_DECLARED_QUOTA_UNVERIFIED",
                 "sourceFree":True,"paidModelCalls":0})
        review=mock("app_generator.runtime.v3_final_two_science."
                    "advance_final_two_new_science",return_value={
                        "status":"FINAL_TWO_STANDING_SCIENCE_COMPLETED",
                        "allNewScientificPass":True,"outcomes":[
                            {"index":0,"newConsensusPass":True},
                            {"index":6,"newConsensusPass":True}]})
        proof=mock("app_generator.runtime.v3_final_two_science."
                   "verified_final_two_science",return_value={
                       "proofs":[{"genuineConsensusPass":True}]*2})
        printed=[]
        mock("scripts.run_v3_yoga6_recovery_worker._print",
             side_effect=printed.append)
        return mock,local,review,proof,printed

    def test_normal_bounded_two_review_to_real_browser_continuation(self):
        mock,local,review,proof,printed=self.arrange()
        status=worker.main(["--final-two-science","--execute",
                            "--allow-generated-text-transfer",
                            "--max-forward-activities","2"])
        self.assertEqual(status,0)
        self.assertEqual(local.call_count,2)
        review.assert_called_once()
        proof.assert_called_once()
        self.assertEqual(printed[-1]["postReviewAutomaticContinuation"]["status"],
                         "FINAL_TWO_AUTOMATICALLY_ADVANCED_BROWSER_PASS")

    def test_scientific_failure_must_not_enter_second_browser(self):
        mock,local,review,proof,printed=self.arrange()
        review.return_value={"status":"FINAL_TWO_STANDING_SCIENCE_COMPLETED",
                             "allNewScientificPass":False,"outcomes":[]}
        status=worker.main(["--final-two-science","--execute",
                            "--allow-generated-text-transfer"])
        self.assertEqual(status,3)
        self.assertEqual(local.call_count,1)
        proof.assert_not_called()

    def test_fake_browser_success_without_source_reuse_refused(self):
        mock,local,review,proof,printed=self.arrange()
        local.side_effect=[{
            "section96ScienceIntegrated":True,"paidGeminiCalls":0,
            "proposalSha256":"f"*64,
            "realCandidateBrowserAcceptance":{
                "status":"ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS",
                "renderedChecks":697,"all108ActivitiesVisited":True,
                "proposalSha256":"f"*64}},{}]
        status=worker.main(["--final-two-science","--execute",
                            "--allow-generated-text-transfer"])
        self.assertEqual(status,3)
        review.assert_not_called()
        proof.assert_not_called()

    def test_reject_conflicting_modes_and_missing_transfer(self):
        for args in (["--final-two-science","--source-free-advance"],
                     ["--final-two-science","--standing-science"],
                     ["--final-two-science","--execute"]):
            with self.subTest(args=args):
                self.assertEqual(worker.main(args),2)

    def test_unpaid_dry_run_exposes_exact_two_new_source_identities(self):
        _,local,review,proof,printed=self.arrange()
        code=worker.main(["--final-two-science"])
        self.assertEqual(code,0)
        self.assertEqual(printed[-1]["status"],
                         "READY_FINAL_TWO_DISTINCT_NEW_SCIENCE_INPUTS")
        self.assertEqual(len(printed[-1]["reviewInputs"]),2)
        local.assert_not_called()
        review.assert_not_called()


if __name__=="__main__":
    unittest.main()

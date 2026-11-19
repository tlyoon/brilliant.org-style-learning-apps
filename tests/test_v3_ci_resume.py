"""BSA224 exact-head hosted CI race: no future manual repeat of sourcefree.

All records, GH statuses and model/browser outputs here are synthetically
injected. Never contact GitHub, Gemini, PDFs or student services in tests.
"""
from contextlib import ExitStack
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app_generator.runtime import v3_ci_resume as ci
from app_generator.runtime import v3_versioned_readiness as actual
from app_generator.runtime import v3_five_stage_completion as five
from scripts import run_v3_yoga6_recovery_worker as worker


class ExactHeadCIBoundedRecoveryTests(unittest.TestCase):
    def setUp(self):
        folder=TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root=Path(folder.name)
        self.head="a"*40
        self.proposal="b"*64
        self.pending={
            "status":ci._WAIT,"gitHead":self.head,
            "proposalSha256":self.proposal,
            "codeWorkingTreeClean":True,
            "exactHeadHostedCiSuccess":False,
            "publicationAuthorized":False,
            "sourceVersionOnly":True,
            "realChromeChecks":698,
            "proposedContentScientificCoverage":108,
        }
        self.success={
            **self.pending,"status":ci._GREEN,
            "exactHeadHostedCiSuccess":True,
            "publicationAuthorized":False,
        }
        self.finished={"headSha":self.head,"status":"completed",
                       "conclusion":"success","databaseId":123}
        self.inflight={"headSha":self.head,"status":"in_progress",
                       "conclusion":"","databaseId":123}

    def run_fake(self,sequence,max_wait=2):
        with ExitStack() as stack:
            stack.enter_context(patch.object(
                actual,"_git_info",return_value=(self.head,"feature/test")))
            stack.enter_context(patch.object(
                actual,"_git_clean",return_value=True))
            gh=stack.enter_context(patch.object(
                actual,"_hosted_runs",side_effect=sequence))
            validate=stack.enter_context(patch.object(
                actual,"evaluate_current_versioned_evidence",
                return_value=self.success))
            rest=stack.enter_context(patch.object(ci.time,"sleep"))
            output=ci.await_exact_ci_and_resume(
                self.root,self.root,self.pending,
                max_wait_seconds=max_wait,poll_interval_seconds=1)
            return output,gh.call_count,validate.call_count,rest.call_count

    def test_running_ci_auto_resumes_to_genuine_revalidation(self):
        output,queries,revalidated,slept=self.run_fake(
            [[self.inflight],[self.finished]])
        self.assertEqual(output["status"],ci._GREEN)
        self.assertEqual(output["ciRecoveryPolls"],2)
        self.assertTrue(output["ciRecoveredInSameInvocation"])
        self.assertEqual(queries,2)
        self.assertEqual(revalidated,1)
        self.assertEqual(slept,1)
        self.assertFalse(output["publicationAuthorized"])

    def test_terminal_failed_hosted_ci_stops_without_retry(self):
        failed={**self.finished,"conclusion":"failure"}
        out,queries,verified,slept=self.run_fake([[failed]])
        self.assertEqual(out["status"],"STOP_HOSTED_CI_COMPLETED_NOT_SUCCESS")
        self.assertEqual(queries,1)
        self.assertEqual(verified,0)
        self.assertEqual(slept,0)
        self.assertFalse(out["publicationAuthorized"])

    def test_wrong_head_green_ci_not_reused(self):
        wrong={**self.finished,"headSha":"f"*40}
        out,queries,verified,slept=self.run_fake(
            [[wrong],[wrong],[wrong]],max_wait=2)
        self.assertEqual(out["status"],"STOP_HOSTED_CI_BOUNDED_WAIT_EXHAUSTED")
        self.assertGreaterEqual(queries,2)
        self.assertEqual(verified,0)
        self.assertFalse(out["publicationAuthorized"])

    def test_missing_hosted_ci_always_finite(self):
        out,queries,verified,slept=self.run_fake(
            [[],[],[]],max_wait=2)
        self.assertEqual(out["status"],"STOP_HOSTED_CI_BOUNDED_WAIT_EXHAUSTED")
        self.assertLessEqual(queries,3)
        self.assertEqual(verified,0)
        self.assertFalse(out["publicationAuthorized"])

    def test_dirty_source_never_touches_hosted_ci(self):
        with patch.object(actual,"_git_info",return_value=(
             self.head,"feature/test")),patch.object(
             actual,"_git_clean",return_value=False),patch.object(
             actual,"_hosted_runs") as gh:
            with self.assertRaisesRegex(ValueError,
                    "GIT_DIRTY_OR_HEAD_MOVED"):
                ci.await_exact_ci_and_resume(
                    self.root,self.root,self.pending)
        gh.assert_not_called()

    def test_exact_head_changes_during_ci_wait_fails_closed(self):
        with patch.object(
                actual,"_git_info",
                side_effect=[(self.head,"feature/test"),("f"*40,"feature/test")]
        ),patch.object(actual,"_git_clean",return_value=True),patch.object(
                actual,"_hosted_runs") as gh:
            with self.assertRaisesRegex(ValueError,
                    "GIT_CHANGED_DURING_WAIT"):
                ci.await_exact_ci_and_resume(
                    self.root,self.root,self.pending)
        gh.assert_not_called()

    def test_bad_wait_window_rejected(self):
        with self.assertRaisesRegex(ValueError,"INVALID_FINITE_BOUNDS"):
            ci.await_exact_ci_and_resume(
                self.root,self.root,self.pending,max_wait_seconds=100000)

    def test_dirty_repo_proof_cannot_wait(self):
        invalid={**self.pending,
                 "status":"VERSIONED_SCIENCE_BROWSER_WAIT_COMMITTED_HEAD",
                 "codeWorkingTreeClean":False}
        with self.assertRaisesRegex(ValueError,"UNSAFE_PENDING_STATUS"):
            ci.await_exact_ci_and_resume(self.root,self.root,invalid)

    def test_green_with_false_ci_flag_refused(self):
        forged={**self.pending,"status":ci._GREEN,
                "exactHeadHostedCiSuccess":False}
        with self.assertRaisesRegex(ValueError,"FORGED_GREEN_STATUS"):
            ci.await_exact_ci_and_resume(self.root,self.root,forged)

    def test_normal_worker_immediately_continues_after_bounded_ci_green(self):
        self._run_worker(when_green=True)

    def test_normal_worker_stops_on_exhausted_ci_without_false_pass(self):
        self._run_worker(when_green=False)

    def _run_worker(self,*,when_green:bool):
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ,{
                "LOCALAPPDATA":str(self.root)}))
            stack.enter_context(patch.object(
                worker,"checked_private_root",return_value=self.root))
            stack.enter_context(patch.object(
                worker,"require_authorized_native_review_host"))
            stack.enter_context(patch.object(
                worker,"advance_source_free_until_boundary",
                return_value={"publicationAuthorized":False}))
            qa={
                "status":"ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS",
                "proposalSha256":self.proposal,"renderedChecks":698,
                "all108ActivitiesVisited":True,
                "allLocaleViewportPromptChecks":648,
            }
            stack.enter_context(patch.object(
                worker,"_complete_source_free_with_browser",
                return_value={
                    "proposalSha256":self.proposal,
                    "finalTwoScienceIntegrated":True,
                    "paidGeminiCalls":0,
                    "publicationAuthorized":False,
                    "realCandidateBrowserAcceptance":qa,
                }))
            original=stack.enter_context(patch.object(
                actual,"evaluate_current_versioned_evidence",
                return_value=self.pending))
            recovered=self.success if when_green else {
                "status":"STOP_HOSTED_CI_BOUNDED_WAIT_EXHAUSTED",
                "publicationAuthorized":False,"paidGeminiCalls":0,
            }
            resumecall=stack.enter_context(patch.object(
                ci,"await_exact_ci_and_resume",return_value=recovered))
            advance=stack.enter_context(patch.object(
                five,"advance_five_stage_on_pinned_browser",
                return_value={
                    "status":"FIVE_STAGE_PRIVATE_TECHNICAL_PATH_COMPLETE_NO_PUBLICATION",
                    "publicationAuthorized":False,
                    "paidGeminiCalls":0,
                    "technicalV3ReleaseAttestationsVerified":True,
                    "privateNativeV3Attestations":6,
                }))
            output=[]
            stack.enter_context(patch.object(
                worker,"_print",side_effect=output.append))
            rc=worker.main(["--source-free-advance"])
        self.assertEqual(rc,0 if when_green else 3)
        self.assertEqual(original.call_count,1)
        self.assertEqual(resumecall.call_count,1)
        self.assertEqual(advance.call_count,1 if when_green else 0)
        self.assertEqual(output[-1]["paidGeminiCalls"],0)
        self.assertFalse(output[-1]["publicationAuthorized"])
        if not when_green:
            self.assertEqual(output[-1]["automaticCiRecoveryBoundary"]["status"],
                "STOP_HOSTED_CI_BOUNDED_WAIT_EXHAUSTED")


if __name__=="__main__":
    unittest.main()

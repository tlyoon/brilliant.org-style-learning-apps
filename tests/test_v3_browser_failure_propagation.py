"""BSA219: ordinary sourcefree browser STOP cannot falsely exit 0.

Tests are offline; success is mocked only for dispatch validation, never science.
"""
from contextlib import ExitStack
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from subprocess import CompletedProcess, TimeoutExpired
import unittest
from unittest.mock import patch

from scripts import run_v3_yoga6_recovery_worker as worker
from scripts.run_v3_yoga6_acceptance import (
    classified_browser_child_failure, _run_bounded_browser_child,
)


class BrowserFailurePropagationTests(unittest.TestCase):
    def fixture(self,result):
        stack=ExitStack()
        self.addCleanup(stack.close)
        temp=TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        stack.enter_context(patch.dict(os.environ,{"LOCALAPPDATA":temp.name}))
        stack.enter_context(patch.object(
            worker,"checked_private_root",return_value=Path(temp.name)))
        stack.enter_context(patch.object(
            worker,"require_authorized_native_review_host"))
        stack.enter_context(patch.object(
            worker,"advance_source_free_until_boundary",return_value={}))
        render=stack.enter_context(patch.object(
            worker,"_complete_source_free_with_browser",return_value=result))
        out=[]
        stack.enter_context(patch.object(worker,"_print",side_effect=out.append))
        return render,out

    def test_genuine_child_browser_stop_returns_nonzero_no_model_calls(self):
        render,out=self.fixture({
            "proposalSha256":"a"*64,
            "paidGeminiCalls":0,"publicationAuthorized":False,
            "realCandidateBrowserAcceptance":{
                "status":"STOP_REAL_CANDIDATE_BROWSER_QA_FAILED",
                "proposalSha256":"a"*64,
                "childStatus":"STOP_ACTUAL_CHAPTER9_BROWSER_QA",
                "childErrorClass":"TimeoutException",
                "childExitCode":3,"publicationAuthorized":False}})
        self.assertEqual(worker.main(["--source-free-advance"]),3)
        self.assertEqual(out[-1]["realCandidateBrowserAcceptance"]
                         ["childErrorClass"],"TimeoutException")
        render.assert_called_once()

    def test_fake_697_not_promoted_to_698_browser_success(self):
        self.fixture({
            "proposalSha256":"a"*64,"paidGeminiCalls":0,
            "publicationAuthorized":False,
            "realCandidateBrowserAcceptance":{
                "status":"ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS",
                "proposalSha256":"a"*64,
                "renderedChecks":697,"all108ActivitiesVisited":True,
                "allLocaleViewportPromptChecks":648}})
        self.assertEqual(worker.main(["--source-free-advance"]),3)

    def test_real_genuine_698_sourcebound_is_only_successful_proposal(self):
        self.fixture({
            "proposalSha256":"a"*64,"paidGeminiCalls":0,
            "publicationAuthorized":False,
            "realCandidateBrowserAcceptance":{
                "status":"ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS",
                "proposalSha256":"a"*64,
                "renderedChecks":698,"all108ActivitiesVisited":True,
                "allLocaleViewportPromptChecks":648}})
        self.assertEqual(worker.main(["--source-free-advance"]),0)

    def test_no_new_proposal_is_not_an_error_after_safe_local_progress(self):
        self.fixture({
            "proposalSha256":None,"paidGeminiCalls":0,
            "publicationAuthorized":False,
            "realCandidateBrowserAcceptance":{
                "status":"NO_NEW_REAL_CANDIDATE_FOR_BROWSER_QA",
                "publicationAuthorized":False}})
        self.assertEqual(worker.main(["--source-free-advance"]),0)

    def test_selenium_transient_child_fails_then_one_genuine_child_pass(self):
        bad=CompletedProcess(["browser"],3,stdout=(
            '{"status":"STOP_ACTUAL_CHAPTER9_BROWSER_QA",'
            '"errorClass":"TimeoutException"}'))
        good=CompletedProcess(["browser"],0,stdout=(
            '{"status":"ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS",'
            '"renderedChecks":698}'))
        with patch("scripts.run_v3_yoga6_acceptance.subprocess.run",
                   side_effect=[bad,good]) as runner:
            result,payload,attempts=_run_bounded_browser_child(
                ["browser"],cwd=Path("."),environment={})
        self.assertEqual(attempts,2)
        self.assertEqual(payload["renderedChecks"],698)
        self.assertEqual(result.returncode,0)
        self.assertEqual(runner.call_count,2)

    def test_content_error_is_not_retried_or_marked_pass(self):
        bad=CompletedProcess(["browser"],3,stdout=(
            '{"status":"STOP_ACTUAL_CHAPTER9_BROWSER_QA",'
            '"errorClass":"ValueError",'
            '"errorCode":"V3_BROWSER_VIEWPORT_OR_PRIVACY_FAILURE"}'))
        with patch("scripts.run_v3_yoga6_acceptance.subprocess.run",
                   return_value=bad) as runner:
            result,payload,attempts=_run_bounded_browser_child(
                ["browser"],cwd=Path("."),environment={})
        self.assertEqual(result.returncode,3)
        self.assertEqual(attempts,1)
        self.assertEqual(payload["errorClass"],"ValueError")
        runner.assert_called_once()

    def test_hung_browser_child_timeout_can_retry_once_but_not_forever(self):
        good=CompletedProcess(["browser"],0,stdout=(
            '{"status":"ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS"}'))
        with patch("scripts.run_v3_yoga6_acceptance.subprocess.run",
                   side_effect=[TimeoutExpired(["browser"],420),good]) as runner:
            _,_,attempts=_run_bounded_browser_child(
                ["browser"],cwd=Path("."),environment={})
        self.assertEqual(attempts,2)
        self.assertEqual(runner.call_count,2)
        with patch("scripts.run_v3_yoga6_acceptance.subprocess.run",
                   side_effect=TimeoutExpired(["browser"],420)) as runner:
            with self.assertRaises(TimeoutExpired):
                _run_bounded_browser_child(
                    ["browser"],cwd=Path("."),environment={})
        self.assertEqual(runner.call_count,2)

    def test_only_safe_error_class_and_named_code_exposed(self):
        result=classified_browser_child_failure("a"*64,{
            "status":"STOP_ACTUAL_CHAPTER9_BROWSER_QA",
            "errorClass":"ValueError",
            "errorCode":"V3_BROWSER_VIEWPORT_OR_PRIVACY_FAILURE",
            "raw":"PRIVATE USER SOURCE MUST NEVER BE RETURNED"},3)
        self.assertEqual(result["childErrorCode"],
                         "V3_BROWSER_VIEWPORT_OR_PRIVACY_FAILURE")
        self.assertEqual(result["childExitCode"],3)
        self.assertNotIn("raw",result)
        self.assertFalse(result["publicationAuthorized"])
        forged=classified_browser_child_failure("a"*64,{
            "errorClass":"TimeoutException",
            "errorCode":"PRIVATE PASSWORD"},3)
        self.assertIsNone(forged["childErrorCode"])


if __name__=="__main__":
    unittest.main()

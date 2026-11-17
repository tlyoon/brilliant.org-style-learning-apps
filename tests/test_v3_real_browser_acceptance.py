"""BOSLA native browser acceptance recovery tests, zero Google/API traffic."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.run_v3_yoga6_acceptance import (
    _read_saved, _write_saved, advance_real_candidate_browser_qa,
)
from scripts import run_v3_yoga6_recovery_worker as worker


class ActualCourseBrowserReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.private=Path(self.temp.name)
        self.target=self.private/"v3-real-chapter9-browser-qa.json"
        self.payload={
            "status":"ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS",
            "proposalSha256":"a"*64,
            "revisionSha":"b"*40,
            "rendererRuntimeSha256":"c"*64,
            "activitiesInCandidate":108,
            "sections":6,"renderedChecks":50,"locales":3,"viewports":2,
            "genuineGeminiReviewsAdded":0,
            "versionedScopeAdmitted":False,"publicationAuthorized":False,
        }

    def test_atomic_browser_receipt_round_trip_and_integrity_check(self):
        first=_write_saved(self.target,self.payload)
        self.assertEqual(first,_read_saved(self.target))
        self.assertEqual(first["status"],
                         "ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS")
        self.assertEqual(first["publicationAuthorized"],False)
        changed=json.loads(self.target.read_text(encoding="utf8"))
        changed["renderedChecks"]=0
        self.target.write_text(json.dumps(changed),encoding="utf8")
        with self.assertRaisesRegex(ValueError,"RECEIPT_INTEGRITY_ERROR"):
            _read_saved(self.target)

    def test_browser_receipt_cannot_authorize_publication_or_model_review(self):
        for field,value in (("publicationAuthorized",True),
                            ("versionedScopeAdmitted",True),
                            ("genuineGeminiReviewsAdded",1)):
            with self.subTest(field=field):
                modified={**self.payload,field:value}
                _write_saved(self.target,modified)
                with self.assertRaisesRegex(ValueError,"INTEGRITY_ERROR"):
                    _read_saved(self.target)

    def test_browser_qa_is_called_from_normal_worker_result(self):
        result={
            "historicalUnrecoverableRoleRecovery":{
                "status":"NEW_VERSIONED_SECTION96_REPAIR_STAGED_QA_NOT_AUTHORIZED",
            },
            "proposalSha256":"a"*64,
            "paidGeminiCalls":0,"publicationAuthorized":False,
        }
        with patch.object(worker,"advance_real_candidate_browser_qa",
                          return_value={**self.payload}) as browser:
            finished=worker._complete_source_free_with_browser(
                self.private,result)
        self.assertEqual(finished["realCandidateBrowserAcceptance"],self.payload)
        browser.assert_called_once_with(worker.ROOT,self.private,result)
        self.assertEqual(finished["paidGeminiCalls"],0)
        self.assertFalse(finished["publicationAuthorized"])

    def test_browser_qa_failure_is_not_reported_as_success(self):
        result={"historicalUnrecoverableRoleRecovery":{
            "status":"NEW_VERSIONED_SECTION96_REPAIR_STAGED_QA_NOT_AUTHORIZED",
        },"proposalSha256":"a"*64,"publicationAuthorized":False}
        with patch.object(worker,"advance_real_candidate_browser_qa",
                          side_effect=RuntimeError("SYNTHETIC_CHROME_FAILURE")):
            finished=worker._complete_source_free_with_browser(self.private,result)
        qa=finished["realCandidateBrowserAcceptance"]
        self.assertEqual(qa["status"],"STOP_NATIVE_REAL_CANDIDATE_BROWSER_QA")
        self.assertEqual(qa["errorClass"],"RuntimeError")
        self.assertFalse(qa["publicationAuthorized"])
        self.assertFalse(finished["publicationAuthorized"])

    def test_no_staged_revised_course_does_not_invoke_browser(self):
        result={"historicalUnrecoverableRoleRecovery":{
            "status":"NO_REGISTERED_HISTORICAL_ROLE_REMEDY"},
            "publicationAuthorized":False}
        with patch("scripts.run_v3_yoga6_acceptance._browser_python",
                   side_effect=AssertionError("NO_BROWSER_START")):
            outcome=advance_real_candidate_browser_qa(
                self.private,self.private,result)
        self.assertEqual(outcome["status"],
                         "NO_NEW_REAL_CANDIDATE_FOR_BROWSER_QA")
        self.assertFalse(outcome["publicationAuthorized"])


if __name__=="__main__":
    unittest.main()

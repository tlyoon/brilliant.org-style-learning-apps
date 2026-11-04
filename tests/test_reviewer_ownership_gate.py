"""Read-only fail-closed reviewer profile ownership checks."""
from __future__ import annotations
from pathlib import Path
import tempfile
import unittest

from app_generator.gemini.reviewer_ownership_gate import reviewer_ownership_preflight


class ReviewerGateTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        self.repo=self.root/"repo"; self.repo.mkdir()
        self.profiles=self.root/"chrome"

    def mkdir_profiles(self):
        for role in ("physics","semantics"):
            (self.profiles/"academic-reviewers"/role/"gemini-browser").mkdir(parents=True)

    def test_unprovisioned_profiles_block_browser_without_checking(self):
        calls=[]
        result=reviewer_ownership_preflight(self.profiles,self.repo,
                                            is_busy=lambda x:calls.append(x))
        self.assertFalse(result["canAttemptIndependentBrowserReview"])
        self.assertEqual([],calls)
        self.assertEqual(["MISSING","MISSING"],[x["status"] for x in result["profiles"]])

    def test_busy_role_never_opens_any_profile(self):
        self.mkdir_profiles()
        calls=[]
        def probe(profile):
            calls.append(profile)
            return "physics" in str(profile)
        report=reviewer_ownership_preflight(self.profiles,self.repo,is_busy=probe)
        self.assertEqual(["BUSY","EXCLUSIVE_CANDIDATE"],
                         [x["status"] for x in report["profiles"]])
        self.assertFalse(report["canAttemptIndependentBrowserReview"])
        self.assertFalse(report["authenticatedVerified"])
        self.assertEqual(2,len(calls))

    def test_free_candidates_do_not_claim_authentication_or_review(self):
        self.mkdir_profiles()
        result=reviewer_ownership_preflight(self.profiles,self.repo,is_busy=lambda _:False)
        self.assertTrue(result["canAttemptIndependentBrowserReview"])
        self.assertFalse(result["authenticatedVerified"])
        self.assertFalse(result["responseCaptured"])
        self.assertFalse(result["fullAcademicPass"])

    def test_unknown_or_malformed_ownership_fails_closed(self):
        self.mkdir_profiles()
        for callback in (lambda _:None,lambda _:1,
                         lambda _:(_ for _ in ()).throw(ValueError("CIM unavailable"))):
            with self.subTest(callback=repr(callback)):
                out=reviewer_ownership_preflight(self.profiles,self.repo,is_busy=callback)
                self.assertFalse(out["canAttemptIndependentBrowserReview"])
                self.assertEqual(["UNKNOWN","UNKNOWN"],
                                 [x["status"] for x in out["profiles"]])

    def test_public_git_profile_disallowed(self):
        with self.assertRaisesRegex(ValueError,"source repository"):
            reviewer_ownership_preflight(self.repo/"profile",self.repo,
                                         is_busy=lambda _:False)


if __name__=="__main__":
    unittest.main()
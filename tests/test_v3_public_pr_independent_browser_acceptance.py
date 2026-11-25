"""BSA235: independent public PR QA fail-closed, restart and dispatch tests."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime import v3_public_pr_independent_browser_acceptance as m

class V14PrIndependentBrowserTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name)
        self.ready={"gitHead":"a"*40,"proposalSha256":"b"*64}
        self.v13={
            "status":m._V13_STATUS,
            "gitHead":self.ready["gitHead"],
            "proposalSha256":self.ready["proposalSha256"],
            "publicDestination":m._REPO,
            "publicBaseMainPinnedSha":m._MAIN,
            "changedSections":list(m._CHANGED),
            "changedFileCount":21,
            "publicPullRequestDraft":True,
            "publicPullRequestOpen":True,
            "remoteBaseRecheckedAfterPr":True,
            "publicMergeExecuted":False,
            "publicDeployExecuted":False,
            "publicationAuthorized":False,
            "scheduledTaskCreated":False,
            "publicReviewBranch":
                "bosla/private-ch9-three-section-"+"c"*12,
            "publicReviewBranchSha":"d"*40,
            "publicReviewTreeSha":"e"*40,
            "privatePatchSha256":"c"*64,
            "publicPullRequestNumber":16,
            "publicPullRequestUrl":
                "https://github.com/"+m._REPO+"/pull/16",
            "sourceV12ReceiptSha256":"1"*64,
            "sourceV11ReceiptSha256":"2"*64,
        }
        self.v13["integritySha256"]=_hash(self.v13)
        (self.folder/m._V13).write_text(json.dumps(self.v13),encoding="utf8")
        self.paths=[f"{s}/{p}" for s in m._CHANGED for p in
           ("app/app.js","app/domain-renderers.js",
            "app/domain-styles.css","app/styles.css",
            "app/visual-renderers.js","content/package.json","index.html")]

    def signed(self):
        return m._verify_v13(self.folder,self.v13,self.ready)

    def pr(self):
        return {"state":"open","draft":True,"merged_at":None,
                "number":16,"html_url":self.v13["publicPullRequestUrl"],
                "head":{"sha":self.v13["publicReviewBranchSha"],
                        "ref":self.v13["publicReviewBranch"],
                        "repo":{"full_name":m._REPO}},
                "base":{"sha":m._MAIN,"ref":"main",
                        "repo":{"full_name":m._REPO}}}

    def test_genuine_signed_v13_prerequisite_accepted(self):
        self.assertEqual(self.signed(),self.v13)

    def test_forged_v13_content_rejected_even_if_in_memory_result_passes(self):
        saved=json.loads((self.folder/m._V13).read_text())
        saved["publicPullRequestDraft"]=False
        (self.folder/m._V13).write_text(json.dumps(saved))
        with self.assertRaisesRegex(ValueError,"GENUINE_SIGNED_V13_REQUIRED"):
            self.signed()

    def test_source_identity_from_other_code_head_refused(self):
        self.ready["gitHead"]="9"*40
        with self.assertRaisesRegex(ValueError,"GENUINE_SIGNED_V13_REQUIRED"):
            self.signed()

    def test_malicious_review_branch_refused(self):
        self.v13["publicReviewBranch"]="main"
        self.v13["integritySha256"]=_hash({
            k:v for k,v in self.v13.items() if k!="integritySha256"})
        (self.folder/m._V13).write_text(json.dumps(self.v13))
        with self.assertRaisesRegex(ValueError,"BRANCH_OR_PR_IDENTITY_INVALID"):
            self.signed()

    def test_current_open_draft_public_pr_matches_exact_source(self):
        out=m._check_pr_snapshot(self.pr(),self.v13)
        self.assertTrue(out["draft"])
        self.assertFalse(out["merged"])

    def test_public_pr_promoted_out_of_draft_is_refused(self):
        pr=self.pr()
        pr["draft"]=False
        with self.assertRaisesRegex(ValueError,"PR_NO_LONGER_SAFE_DRAFT"):
            m._check_pr_snapshot(pr,self.v13)

    def test_public_pr_merge_is_refused(self):
        pr=self.pr()
        pr["merged_at"]="2026-11-20T08:00:00Z"
        with self.assertRaisesRegex(ValueError,"PR_NO_LONGER_SAFE_DRAFT"):
            m._check_pr_snapshot(pr,self.v13)

    def test_public_main_moved_after_pr_is_refused(self):
        pr=self.pr()
        pr["base"]["sha"]="9"*40
        with self.assertRaisesRegex(ValueError,"PR_NO_LONGER_SAFE_DRAFT"):
            m._check_pr_snapshot(pr,self.v13)

    def test_21_precisely_scoped_public_files_accepted(self):
        files=[{"filename":p,"status":"modified"} for p in self.paths]
        self.assertEqual(m._check_pr_diff(files,self.v13),self.paths)

    def test_hidden_additional_9_7_public_file_refused(self):
        files=[{"filename":p,"status":"modified"} for p in self.paths]
        files[-1]["filename"]="section-9-7/app.js"
        with self.assertRaisesRegex(ValueError,"PR_DIFF_SCOPE"):
            m._check_pr_diff(files,self.v13)

    def test_duplicate_file_in_public_pr_diff_refused(self):
        files=[{"filename":p,"status":"modified"} for p in self.paths]
        files[-1]["filename"]=files[0]["filename"]
        with self.assertRaisesRegex(ValueError,"PR_DIFF_SCOPE"):
            m._check_pr_diff(files,self.v13)

    def test_public_pr_file_deletions_not_accepted(self):
        files=[{"filename":p,"status":"modified"} for p in self.paths]
        files[0]["status"]="removed"
        with self.assertRaisesRegex(ValueError,"PR_DIFF_SCOPE"):
            m._check_pr_diff(files,self.v13)

    def test_public_pr_incomplete_diff_refused(self):
        files=[{"filename":p,"status":"modified"} for p in self.paths[:-1]]
        with self.assertRaisesRegex(ValueError,"PR_DIFF_COUNT_CHANGED"):
            m._check_pr_diff(files,self.v13)

    def test_full_route_browser_state_pass(self):
        good={"path":"/section-9-7/","appTextChars":300,"buttons":4,
              "initialPlaceholder":False,"failedLoading":False}
        result=m._check_browser_state(good,"section-9-7",[])
        self.assertTrue(result["realChromeRendered"])

    def test_missing_package_content_prevents_acceptance(self):
        bad={"path":"/section-9-7/","appTextChars":20,"buttons":4,
             "initialPlaceholder":False,"failedLoading":False}
        with self.assertRaisesRegex(ValueError,"CHROME_ROUTE_OR_CONSOLE_FAILED"):
            m._check_browser_state(bad,"section-9-7",[])

    def test_severe_browser_error_rejected(self):
        good={"path":"/section-9-7/","appTextChars":300,"buttons":4,
              "initialPlaceholder":False,"failedLoading":False}
        with self.assertRaisesRegex(ValueError,"CHROME_ROUTE_OR_CONSOLE_FAILED"):
            m._check_browser_state(good,"section-9-7",[
                {"level":"SEVERE","message":"Uncaught Error: code failure"}])

    def test_benign_historical_favicon_handling_reused(self):
        good={"path":"/section-9-9/","appTextChars":300,"buttons":4,
              "initialPlaceholder":False,"failedLoading":False}
        logs=[{"level":"SEVERE","message":
           "http://127.0.0.1:43434/favicon.ico - Failed to load resource: "
           "the server responded with a status of 404 (File not found)"}]
        self.assertTrue(m._check_browser_state(
            good,"section-9-9",logs)["packageLoaded"])

if __name__=="__main__":
    unittest.main()

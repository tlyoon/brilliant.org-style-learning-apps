"""BSA236 V15: observable global checkpoint->next-task dispatch tests."""
from __future__ import annotations
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime import v3_global_post_pr_readonly_roadmap as m


class GlobalReadonlyRoadmapTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.repo=self.root/"repo"
        (self.repo/"docs").mkdir(parents=True)
        self.private=self.root/"private"
        self.private.mkdir()
        self.folder=self.private/"signed"
        self.folder.mkdir()
        self.ready={"gitHead":"a"*40,"proposalSha256":"b"*64}
        self.branch="bosla/private-ch9-three-section-"+"c"*12
        self.head="d"*40
        self.v11={"integritySha256":"1"*64}
        self.v12={"integritySha256":"2"*64}
        self.v13={
            "integritySha256":"3"*64,
            "publicPullRequestNumber":16,
            "publicPullRequestUrl":
                "https://github.com/"+m._REPO+"/pull/16",
            "publicReviewBranch":self.branch,
            "publicReviewBranchSha":self.head,
        }
        self.paths=[f"{s}/{p}" for s in
                    ("section-9-1","section-9-2","section-9-6")
                    for p in ("app/app.js","app/domain-renderers.js",
                    "app/domain-styles.css","app/styles.css",
                    "app/visual-renderers.js","content/package.json",
                    "index.html")]
        self.v14={
            "status":m._V14_STATUS,
            "gitHead":self.ready["gitHead"],
            "proposalSha256":self.ready["proposalSha256"],
            "sourceV13ReceiptSha256":self.v13["integritySha256"],
            "publicBaseMainPinnedSha":m._MAIN,
            "realChromeRoutesPassed":9,
            "changedFileCount":21,
            "actualRemoteGitHubDiffPaths":self.paths,
            "publicPrDraft":True,
            "publicMergeExecuted":False,
            "publicDeployExecuted":False,
            "publicationAuthorized":False,
            "scheduledTaskCreated":False,
        }
        self.v14["integritySha256"]=_hash(self.v14)
        (self.folder/m._V14).write_text(
            json.dumps(self.v14),encoding="utf8")
        self.recurrence={
            "incidents":[
                {"id":"BSA-20261120-235","status":"resolved"},
                {"id":"BSA-20261120-236","status":"active"},
            ]
        }
        (self.repo/"docs"/"recurrence_registry.json").write_text(
            json.dumps(self.recurrence),encoding="utf8")
        (self.repo/"docs"/"CONTINUATION_CHECKPOINT_LATEST.md").write_text(
            "Historical C3 remains FAILED_LIMITED_CAMPAIGN",encoding="utf8")
        self.calls=[]
        self.fail_check_api=False
        self.moved_branch=False

    def gh_fake(self,argv,*,timeout=60):
        self.assertEqual(argv[:4],["gh","api","--method","GET"])
        endpoint=argv[-1]
        self.calls.append(endpoint)
        if endpoint.endswith("/pulls/16"):
            return json.dumps({
                "state":"open","draft":True,"merged_at":None,
                "number":16,"html_url":self.v13["publicPullRequestUrl"],
                "head":{"ref":self.branch,"sha":self.head,
                        "repo":{"full_name":m._REPO}},
                "base":{"ref":"main","sha":m._MAIN,
                        "repo":{"full_name":m._REPO}},
            })
        if endpoint.endswith("/pulls/16/files?per_page=100"):
            return json.dumps([{"filename":p,"status":"modified"}
                               for p in self.paths])
        if endpoint.endswith("/status"):
            return json.dumps({"state":"pending","statuses":[]})
        if endpoint.endswith("/check-runs"):
            if self.fail_check_api:
                raise ValueError("API_TEMPORARILY_UNAVAILABLE")
            return json.dumps({"total_count":0,"check_runs":[]})
        if endpoint.endswith("/reviews?per_page=100"):
            return json.dumps([])
        raise AssertionError("unexpected read-only API "+endpoint)

    def remote_sha(self,branch):
        if branch=="main":
            return m._MAIN
        return "9"*40 if self.moved_branch else self.head

    def invoke(self):
        with (patch.object(m,"_v13_preflight",
                 return_value=(self.folder,self.v11,self.v12,
                               self.branch,self.paths)),
              patch.object(m,"_verify_v13",return_value=self.v13),
              patch.object(m,"_ls_remote",side_effect=self.remote_sha),
              patch.object(m,"_gh",side_effect=self.gh_fake)):
            return m.run_global_readonly_roadmap(
                self.repo,self.private,self.ready,
                {},self.v11,self.v12,self.v13,self.v14)

    def test_real_dispatch_of_all_three_tasks_in_one_call(self):
        result=self.invoke()
        self.assertEqual(result["status"],m._STATUS)
        self.assertEqual(result["taskDispatchCount"],3)
        self.assertEqual(result["taskDispatchOrder"],list(m._TASKS))
        self.assertTrue(result["nextTaskDispatchActuallyExecuted"])
        self.assertEqual(result["quarantinedTaskIds"],[])
        self.assertFalse(result["publicMergeExecuted"])
        self.assertFalse(result["publicDeployExecuted"])
        self.assertFalse(result["crossSessionPersistentSupervisorVerified"])
        self.assertFalse(result["schedulerReinstalled"])
        for n in m._TASKS:
            self.assertTrue((self.folder/
                 ("V15_TASK_"+n+"_PRE_CALL.json")).is_file())
            self.assertTrue((self.folder/
                 ("V15_TASK_"+n+"_RESULT.json")).is_file())
        audit=json.loads((self.folder/
            "V15_TASK_PUBLIC_GITHUB_NATIVE_CHECKS_AND_REVIEWS_RESULT.json"
             ).read_text())
        self.assertEqual(audit["details"]["nativeCheckRunCount"],0)
        self.assertFalse(audit["details"]["nativeChecksPresent"])
        self.assertFalse(audit["details"]["releaseApproved"])

    def test_repeated_restart_reconciles_without_new_remote_write(self):
        first=self.invoke()
        second=self.invoke()
        self.assertEqual(first,second)
        self.assertEqual(first["integritySha256"],_hash({
            k:v for k,v in first.items() if k!="integritySha256"}))
        self.assertEqual(len(self.calls),10) # five GET operations per run

    def test_failed_github_checks_task_quarantined_but_global_scan_runs(self):
        self.fail_check_api=True
        result=self.invoke()
        self.assertEqual(result["quarantinedTaskIds"],
                         ["PUBLIC_GITHUB_NATIVE_CHECKS_AND_REVIEWS"])
        self.assertEqual(result["taskDispatchCount"],3)
        final=json.loads((self.folder/
          "V15_TASK_HISTORICAL_C3_AND_GLOBAL_RECURRENCE_SCAN_RESULT.json"
                        ).read_text())
        self.assertEqual(final["state"],"READONLY_TASK_EXECUTED")
        self.assertEqual(result["status"],
            "POST_PR_GLOBAL_READONLY_TASKS_QUARANTINED_NO_RELEASE")

    def test_moved_branch_prevents_readonly_dispatch(self):
        self.moved_branch=True
        with self.assertRaisesRegex(ValueError,
                                    "PROTECTED_PR_BRANCH_OR_BASE_MOVED"):
            self.invoke()
        self.assertFalse(list(self.folder.glob("*PRE_CALL*")))

    def test_forged_v14_receipt_prevents_dispatch(self):
        doc=json.loads((self.folder/m._V14).read_text())
        doc["publicDeployExecuted"]=True
        (self.folder/m._V14).write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError,
                                    "GENUINE_SIGNED_V14_REQUIRED"):
            self.invoke()
        self.assertFalse(list(self.folder.glob("*PRE_CALL*")))

    def test_changed_historical_c3_evidence_quarantines_only_its_task(self):
        (self.repo/"docs"/"CONTINUATION_CHECKPOINT_LATEST.md").write_text(
            "No historical text",encoding="utf8")
        result=self.invoke()
        self.assertEqual(result["quarantinedTaskIds"],
                         ["HISTORICAL_C3_AND_GLOBAL_RECURRENCE_SCAN"])
        self.assertTrue(any(x.endswith("/pulls/16") for x in self.calls))

    def test_tampered_result_at_restart_refused(self):
        self.invoke()
        path=self.folder/"V15_TASK_ACTUAL_PR_BRANCH_RECONCILIATION_RESULT.json"
        doc=json.loads(path.read_text())
        doc["state"]="FORGED_PASS"
        path.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError,
                                    "CHECKPOINT_CHANGED"):
            self.invoke()

    def test_no_unregistered_task_execution_allowed(self):
        with self.assertRaisesRegex(ValueError,
                                    "UNREGISTERED_TASK_DISPATCH_REFUSED"):
            m._dispatch_task(self.folder,self.ready,self.v14,
                "UNTRUSTED_EXTERNAL_ACTION",
                lambda a,b,c:{},self.v13,self.repo)

    def test_bad_active_incident_id_cannot_be_reported_as_valid(self):
        self.recurrence["incidents"].append(
            {"id":"not-a-registered-incident","status":"active"})
        (self.repo/"docs"/"recurrence_registry.json").write_text(
            json.dumps(self.recurrence),encoding="utf8")
        self.assertRaisesRegex(
            ValueError,"BAD_ACTIVE_ID",
            m._task_global_recurrence,self.v13,self.v14,self.repo)

if __name__=="__main__":
    unittest.main()

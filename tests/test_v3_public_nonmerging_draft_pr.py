"""V13 public draft PR recovery: historical safe Git creator + no duplicate writes."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase,main
from unittest.mock import patch

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime import v3_public_nonmerging_draft_pr as m

class V13SafeDraftPrTests(TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir=Path(self.tmp.name)
        self.folder=self.dir/"private-full";self.folder.mkdir()
        self.repo=self.dir/"repo";self.repo.mkdir()
        self.private=self.dir/"private-short";self.private.mkdir()
        self.paths=[f"{s}/{p}" for s in m._ALLOWED_ROUTES for p in (
            "app/app.js","app/domain-renderers.js","app/domain-styles.css",
            "app/styles.css","app/visual-renderers.js",
            "content/package.json","index.html")]
        self.branch="bosla/private-ch9-three-section-"+"a"*12
        self.head="c"*40
        self.proposal="e"*64
        self.tree="d"*40
        self.public_sha="f"*40
        self.remote_main=m._MAIN
        self.remote_branch=None
        self.pr=None
        self.rejected_write=False
        self.push_uncertain=False
        self.pr_uncertain=False
        self.calls=[]
        self.v9={"integritySha256":"b"*64}
        self.v11={
            "integritySha256":"0"*64,
            "sourceV9ReceiptSha256":self.v9["integritySha256"],
            "privatePatchSha256":"a"*64,
        }
        self.ready={"gitHead":self.head,"proposalSha256":self.proposal}
        draft=b"# PRIVATE PROPOSAL - NOT CREATED\n"
        (self.folder/m._DRAFT).write_bytes(draft)
        v12={
            "contract":"BOSLA_V12_PRIVATE_NONMERGING_PR_READINESS_V1",
            "status":m._V12_STATUS,
            "sourceV11ReceiptSha256":self.v11["integritySha256"],
            "publicDestination":m._REPO,
            "publicMainPinnedSha":m._MAIN,
            "gitHead":self.head,
            "proposalSha256":self.proposal,
            "changedSections":list(m._ALLOWED_ROUTES),
            "changedFileCount":21,
            "privatePatchSha256":self.v11["privatePatchSha256"],
            "remoteMainStillPinned":True,
            "proposedBranchNotCreated":self.branch,
            "proposedPullRequestTitle":"Scope-limited draft review",
            "privateDraftSha256":sha256(draft).hexdigest(),
            "publicPRCreated":False,"publicPushExecuted":False,
            "publicMergeExecuted":False,"publicDeployExecuted":False,
            "publicationAuthorized":False,"scheduledTaskCreated":False,
        }
        v12["integritySha256"]=_hash(v12)
        self.v12=v12
        (self.folder/m._V12).write_text(json.dumps(v12),encoding="utf8")

    def pr_obj(self,draft=True,head=None):
        return {
            "number":18,
            "html_url":"https://github.com/"+m._REPO+"/pull/18",
            "state":"open",
            "draft":draft,
            "merged_at":None,
            "head":{"ref":self.branch,"sha":head or self.public_sha,
                    "repo":{"full_name":m._REPO}},
            "base":{"ref":"main","repo":{"full_name":m._REPO}},
        }

    def fake_git(self,argv,*,cwd=None,timeout=120):
        self.calls.append(("git",argv[1]))
        op=argv[1]
        if op=="ls-remote":
            if argv[-1]=="refs/heads/main":
                return self.remote_main+"\trefs/heads/main"
            return (self.remote_branch+"\trefs/heads/"+self.branch
                    if self.remote_branch else "")
        if op=="clone":
            Path(argv[-1]).mkdir(parents=True)
            return ""
        if op=="rev-parse":
            if argv[-1]=="HEAD":
                return m._MAIN
            if argv[-1] in ("HEAD^{tree}","FETCH_HEAD^{tree}"):
                return self.tree
            if argv[-1]=="FETCH_HEAD":
                return self.remote_branch
            raise AssertionError("unexpected ref "+argv[-1])
        if op=="diff" and "--name-only" in argv:
            return "\n".join(self.paths)
        if op=="push":
            self.remote_branch=self.public_sha
            if self.push_uncertain:
                raise ValueError("V13_GIT_PUSH_FAILED")
        return ""

    def fake_gh(self,argv,*,timeout=60):
        self.calls.append(("gh",argv[1]+(" "+argv[2] if len(argv)>2 else "")))
        if argv[1]=="api":
            return json.dumps([self.pr] if self.pr else [])
        if argv[1]=="pr" and argv[2]=="create":
            self.assertIn("--draft",argv)
            self.assertIn("--head",argv)
            self.assertEqual(argv[argv.index("--head")+1],self.branch)
            self.pr=self.pr_obj()
            if self.pr_uncertain:
                raise ValueError("V13_GH_COMMAND_FAILED")
            return self.pr["html_url"]
        raise AssertionError("Unexpected remote method "+repr(argv))

    def run_stage(self):
        with (patch.object(m,"_v9_preflight",return_value=(
                self.folder,self.folder,self.v9)),
              patch.object(m,"_signed_v11",return_value=self.v11),
              patch.object(m,"_verify_patch_and_exact_scope",
                           return_value=self.paths),
              patch.object(m,"_git",side_effect=self.fake_git),
              patch.object(m,"_gh",side_effect=self.fake_gh)):
            return m.dispatch_scoped_nonmerging_public_pr(
                self.repo,self.private,self.ready,
                self.v9,self.v11,self.v12)

    def test_real_safe_draft_pr_created_and_not_merged_or_deployed(self):
        r=self.run_stage()
        self.assertEqual(r["status"],m._STATUS)
        self.assertEqual(r["publicPullRequestNumber"],18)
        self.assertTrue(r["publicPullRequestDraft"])
        self.assertEqual(r["changedFileCount"],21)
        self.assertFalse(r["publicMergeExecuted"])
        self.assertFalse(r["publicDeployExecuted"])
        self.assertFalse(r["publicationAuthorized"])
        self.assertFalse(r["scheduledTaskCreated"])
        self.assertEqual(sum(x==("git","push") for x in self.calls),1)
        self.assertEqual(sum(x==("gh","pr create") for x in self.calls),1)
        self.assertTrue((self.folder/m._PREPARE).exists())
        self.assertEqual(r["integritySha256"],_hash({
            k:v for k,v in r.items() if k!="integritySha256"}))

    def test_restart_reconciles_remote_branch_and_pr_without_duplicate_write(self):
        first=self.run_stage()
        second=self.run_stage()
        self.assertEqual(first,second)
        self.assertEqual(sum(x==("git","push") for x in self.calls),1)
        self.assertEqual(sum(x==("gh","pr create") for x in self.calls),1)

    def test_uncertain_push_is_reconciled_not_replayed(self):
        self.push_uncertain=True
        self.run_stage()
        self.assertEqual(sum(x==("git","push") for x in self.calls),1)
        self.assertIsNotNone(self.remote_branch)

    def test_uncertain_pr_create_is_reconciled_not_replayed(self):
        self.pr_uncertain=True
        self.run_stage()
        self.assertEqual(sum(x==("gh","pr create") for x in self.calls),1)

    def test_altered_public_main_prevents_any_write(self):
        self.remote_main="9"*40
        with self.assertRaisesRegex(ValueError,"PUBLIC_MAIN_CHANGED"):
            self.run_stage()
        self.assertFalse(any(x in (("git","push"),("gh","pr create"))
                             for x in self.calls))

    def test_existing_branch_wrong_tree_is_refused_without_pr(self):
        self.remote_branch=self.public_sha
        with patch.object(m,"_git",side_effect=lambda argv,**kw:
                "9"*40 if argv[-1]=="FETCH_HEAD^{tree}" else
                self.fake_git(argv,**kw)),patch.object(
                    m,"_gh",side_effect=self.fake_gh),patch.object(
                    m,"_v9_preflight",return_value=(
                        self.folder,self.folder,self.v9)),patch.object(
                    m,"_signed_v11",return_value=self.v11),patch.object(
                    m,"_verify_patch_and_exact_scope",return_value=self.paths):
            with self.assertRaisesRegex(ValueError,"REMOTE_TREE_MISMATCH"):
                m.dispatch_scoped_nonmerging_public_pr(
                    self.repo,self.private,self.ready,
                    self.v9,self.v11,self.v12)
        self.assertIsNone(self.pr)

    def test_existing_nondraft_pr_cannot_be_accepted(self):
        self.remote_branch=self.public_sha
        self.pr=self.pr_obj(draft=False)
        with self.assertRaisesRegex(ValueError,"EXISTING_PUBLIC_PR_UNSAFE"):
            self.run_stage()

    def test_duplicate_pr_list_cannot_be_treated_as_success(self):
        self.remote_branch=self.public_sha
        with (patch.object(m,"_gh",side_effect=lambda argv,**kw:
                json.dumps([self.pr_obj(),self.pr_obj()]) if argv[1]=="api"
                else self.fake_gh(argv,**kw)),patch.object(
                    m,"_git",side_effect=self.fake_git),patch.object(
                    m,"_v9_preflight",return_value=(self.folder,self.folder,self.v9)),
                patch.object(m,"_signed_v11",return_value=self.v11),
                patch.object(m,"_verify_patch_and_exact_scope",return_value=self.paths)):
            with self.assertRaisesRegex(ValueError,"DUPLICATE_PR_HISTORY"):
                m.dispatch_scoped_nonmerging_public_pr(
                    self.repo,self.private,self.ready,
                    self.v9,self.v11,self.v12)

    def test_forged_v12_receipt_refused_before_public_write(self):
        data=json.loads((self.folder/m._V12).read_text())
        data["publicPRCreated"]=True
        (self.folder/m._V12).write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,"SIGNED_V12_RELEASE_SCOPE_INVALID"):
            self.run_stage()
        self.assertFalse(self.calls)

    def test_draft_body_can_never_claim_automerge(self):
        body=m._make_body(self.v12,self.v11)
        self.assertIn("NOT merged or deployed",body)
        self.assertIn("Please keep this PR unmerged",body)
        self.assertNotIn("auto-merge this PR",body)

    def test_no_unscoped_git_or_gh_command_permitted(self):
        with self.assertRaisesRegex(ValueError,"UNAUTHORIZED_GIT_COMMAND"):
            m._git(["git","push","--force","origin","main"])
        with self.assertRaisesRegex(ValueError,"UNAUTHORIZED_GH_COMMAND"):
            m._gh(["gh","pr","merge","18"])

if __name__=="__main__":
    main()

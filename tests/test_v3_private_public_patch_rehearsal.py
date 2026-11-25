"""BSA232 V11 private patch scope, fake-Git fault injection and restart.

These synthetic controls complement real authenticated owner Yoga6 read-only
Git clone / git apply --check validation.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import shutil
import unittest

from app_generator.runtime import v3_private_public_patch_rehearsal as m
from app_generator.runtime.v3_five_stage_completion import _hash


class PrivatePublicPatchV11Tests(unittest.TestCase):
    def setUp(self):
        t=TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.tmp=Path(t.name)
        self.private=self.tmp/"private";self.private.mkdir()
        self.folder=self.private/"candidate";self.folder.mkdir()
        self.repo=self.tmp/"repo";self.repo.mkdir()
        self.source=self.folder/"stage";self.source.mkdir()
        self.seed=self.tmp/"seed";self.seed.mkdir()
        for route in m._CHAPTER_ROUTES:
            old=self.seed/route
            new=self.source/route
            for p in (old,new):
                (p/"app").mkdir(parents=True)
                (p/"content").mkdir()
                (p/"index.html").write_text("<html>stage version</html>")
                (p/"app"/"app.js").write_text("old local javascript")
                (p/"app"/"styles.css").write_text("styles")
                (p/"content"/"package.json").write_text('{"activities":[]}')
                (p/".nojekyll").write_text("")
            for file in ("app/domain-renderers.js","app/domain-styles.css",
                         "app/visual-renderers.js"):
                (new/file).write_text("new validated production renderer")
        self.v9={"status":"THREE_ROUTE_PRIVATE_PINNED_RELEASE_PROPOSAL_READY_NO_PUBLIC_WRITE",
                 "integritySha256":"c"*64,"publicMainPinnedSha":m._MAIN,
                 "publicDestination":m._DEST}
        self.v10={"status":m._V10_STATUS,
                  "realHeadlessChromeRoutesPassed":3,
                  "privateProductionBundleFilesVerified":24,
                  "sourceV9ReceiptSha256":"c"*64,
                  "publicMainPinnedSha":m._MAIN,
                  "publicDeployExecuted":False,
                  "publicationAuthorized":False}
        self.v10["integritySha256"]=_hash(self.v10)
        (self.folder/m._V10).write_text(json.dumps(self.v10))
        self.ready={"gitHead":"a"*40,"proposalSha256":"b"*64}
        self.operations=[]
        self.fail_remote=False
        self.wrong_scope=False

    def fake_git(self,argv,*,cwd=None,timeout=120):
        op=argv[1]
        self.operations.append(op)
        self.assertIn(op,m._ALLOW_GIT)
        if op=="clone":
            shutil.copytree(self.seed,Path(argv[-1]))
            return b""
        if op=="rev-parse":
            return m._MAIN.encode()
        if op=="ls-remote":
            sha=("d"*40) if self.fail_remote else m._MAIN
            return (sha+"\trefs/heads/main\n").encode()
        if op=="diff" and "--name-only" in argv:
            paths=[f"{s}/{p}" for s in m._CHAPTER_ROUTES for p in (
                "app/app.js","app/styles.css","app/domain-renderers.js",
                "app/domain-styles.css","app/visual-renderers.js",
                "content/package.json","index.html")]
            if self.wrong_scope:
                paths[0]="section-9-7/content/package.json"
            return ("\n".join(paths)+"\n").encode()
        if op=="diff" and "--binary" in argv:
            return b"diff --git a/section-9-1 b/section-9-1\n"+b"x"*2400
        return b""

    def call(self):
        with patch.object(m,"_v10_preflight",return_value=(
                self.folder,self.source,self.v9)),patch.object(
                m,"_git",side_effect=self.fake_git):
            return m.stage_exact_private_public_patch(
                self.repo,self.private,self.ready,self.v9,self.v10)

    def test_three_route_private_patch_and_no_public_action(self):
        r=self.call()
        self.assertEqual(r["changedFileCount"],21)
        self.assertEqual(r["changedSections"],list(m._CHAPTER_ROUTES))
        self.assertTrue(r["gitApplyCheckAgainstIndependentCleanPinnedMain"])
        self.assertFalse(r["publicPRCreated"])
        self.assertFalse(r["publicPushExecuted"])
        self.assertFalse(r["publicMergeExecuted"])
        self.assertFalse(r["publicDeployExecuted"])
        self.assertEqual(self.operations.count("clone"),2)
        self.assertIn("apply",self.operations)
        self.assertEqual(r["privatePatchSha256"],m.sha256(
            (self.folder/m._PATCH).read_bytes()).hexdigest())

    def test_idempotent_restart_with_identical_patch_and_receipt(self):
        first=self.call()
        second=self.call()
        self.assertEqual(first,second)
        self.assertEqual(self.operations.count("clone"),4)

    def test_existing_private_patch_tamper_fails(self):
        self.call()
        (self.folder/m._PATCH).write_bytes(b"corrupted private patch")
        with self.assertRaisesRegex(ValueError,"EXISTING_PRIVATE_PATCH_CHANGED"):
            self.call()

    def test_public_remote_revision_drift_fails_closed(self):
        self.fail_remote=True
        with self.assertRaisesRegex(ValueError,"PUBLIC_MAIN_CHANGED_DURING_REHEARSAL"):
            self.call()
        self.assertFalse((self.folder/m._V11).exists())

    def test_extra_section_97_in_diff_is_refused(self):
        self.wrong_scope=True
        with self.assertRaisesRegex(ValueError,"CHANGED_PATH_SCOPE_NOT_EXACT"):
            self.call()
        self.assertFalse((self.folder/m._PATCH).exists())

    def test_missing_public_route_refused(self):
        shutil.rmtree(self.seed/"section-9-6")
        with self.assertRaisesRegex(ValueError,"UNSAFE_EXISTING_PUBLIC_ROUTE"):
            self.call()

    def test_forged_v10_receipt_is_refused_before_remote_git(self):
        data=json.loads((self.folder/m._V10).read_text())
        data["realHeadlessChromeRoutesPassed"]=2
        (self.folder/m._V10).write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,"SIGNED_V10_PROOF_CHANGED"):
            self.call()
        self.assertFalse(self.operations)

    def test_unrecognized_remote_git_action_not_permitted(self):
        with self.assertRaisesRegex(ValueError,"UNAUTHORIZED_GIT_ACTION"):
            m._git(["git","push","origin","main"])

if __name__=="__main__":
    unittest.main()

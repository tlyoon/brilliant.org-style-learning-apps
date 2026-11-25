"""BSA233: V11-to-V12 private PR draft and ordinary-worker continuity tests."""
from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase,main
from unittest.mock import patch

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime import v3_private_nonmerging_pr_readiness as stage


class V12NonmergingPrTests(TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir=Path(self.tmp.name)
        self.folder=self.dir/"verified"
        self.folder.mkdir()
        self.repo=self.dir/"checkout"
        self.repo.mkdir()
        self.private=self.dir/"private"
        self.private.mkdir()
        paths=[f"{section}/{path}" for section in stage._ALLOWED for path in (
            "app/app.js","app/domain-renderers.js",
            "app/domain-styles.css","app/styles.css",
            "app/visual-renderers.js","content/package.json","index.html")]
        self.paths=paths
        data=b"".join(
            b"diff --git a/"+p.encode()+b" b/"+p.encode()+b"\n"+
            b"index 234..567 100644\n" for p in paths)
        (self.folder/stage._PATCH).write_bytes(data)
        self.v9={"integritySha256":"e"*64}
        self.v11={
            "status":stage._V11_STATUS,
            "changedFileCount":21,
            "changedSections":list(stage._ALLOWED),
            "publicMainPinnedSha":stage._MAIN,
            "publicDestination":stage._DEST,
            "gitApplyCheckAgainstIndependentCleanPinnedMain":True,
            "publicPRCreated":False,
            "publicPushExecuted":False,
            "publicMergeExecuted":False,
            "publicDeployExecuted":False,
            "publicationAuthorized":False,
            "gitHead":"a"*40,
            "proposalSha256":"b"*64,
            "sourceV9ReceiptSha256":self.v9["integritySha256"],
            "privatePatchBytes":len(data),
            "privatePatchSha256":sha256(data).hexdigest(),
            "changedFilePaths":paths,
        }
        self.v11["integritySha256"]=_hash(self.v11)
        (self.folder/stage._V11).write_text(
            json.dumps(self.v11),encoding="utf8")
        self.ready={"gitHead":"a"*40,"proposalSha256":"b"*64}
        self.remote_head=stage._MAIN
        self.ops=[]

    def fake_git(self,argv,*,cwd=None,timeout=120):
        self.ops.append(argv)
        self.assertEqual(argv[1],"ls-remote")
        return (self.remote_head+"\trefs/heads/main\n").encode()

    def call(self):
        with (patch.object(stage,"_v9_preflight",
                          return_value=(self.folder,self.folder,self.v9)),
              patch.object(stage,"_git",side_effect=self.fake_git)):
            return stage.stage_private_nonmerging_pr_draft(
                self.repo,self.private,self.ready,self.v9,self.v11)

    def test_real_signed_patch_generates_only_private_draft(self):
        receipt=self.call()
        self.assertEqual(receipt["status"],stage._STATUS)
        self.assertEqual(receipt["changedFileCount"],21)
        self.assertEqual(receipt["privatePatchSha256"],
                         self.v11["privatePatchSha256"])
        self.assertTrue(receipt["remoteMainStillPinned"])
        self.assertFalse(receipt["publicPRCreated"])
        self.assertFalse(receipt["publicPushExecuted"])
        self.assertFalse(receipt["publicMergeExecuted"])
        self.assertFalse(receipt["publicDeployExecuted"])
        self.assertFalse(receipt["publicationAuthorized"])
        self.assertFalse(receipt["scheduledTaskCreated"])
        self.assertEqual(len(self.ops),1)
        self.assertTrue((self.folder/stage._DRAFT).exists())
        text=(self.folder/stage._DRAFT).read_text(encoding="utf8")
        self.assertIn("NOT A CREATED GITHUB PULL REQUEST",text)
        self.assertIn("section-9-6",text)
        self.assertNotIn("git push",text.lower())

    def test_restart_does_not_mutate_private_draft(self):
        first=self.call()
        original=(self.folder/stage._DRAFT).read_bytes()
        second=self.call()
        self.assertEqual(first,second)
        self.assertEqual(original,(self.folder/stage._DRAFT).read_bytes())

    def test_tampered_private_draft_refused(self):
        self.call()
        (self.folder/stage._DRAFT).write_text("injected private PR text")
        with self.assertRaisesRegex(ValueError,
                                    "V12_EXISTING_DRAFT_CHANGED_ON_RESTART"):
            self.call()

    def test_changed_public_revision_fails_closed(self):
        self.remote_head="d"*40
        with self.assertRaisesRegex(ValueError,"V12_PUBLIC_BASE_CHANGED"):
            self.call()
        self.assertFalse((self.folder/stage._V12).exists())

    def test_tampered_v11_signed_receipt_blocks_even_if_result_claims_pass(self):
        data=json.loads((self.folder/stage._V11).read_text())
        data["changedFileCount"]=30
        (self.folder/stage._V11).write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,"V12_SIGNED_V11_PROOF_INVALID"):
            self.call()
        self.assertFalse(self.ops)

    def test_9_7_path_in_patch_fails_scope(self):
        bytes_before=(self.folder/stage._PATCH).read_bytes()
        replaced=bytes_before.replace(b"section-9-1/app/app.js",
                                      b"section-9-7/app/app.js")
        (self.folder/stage._PATCH).write_bytes(replaced)
        self.v11["privatePatchBytes"]=len(replaced)
        self.v11["privatePatchSha256"]=sha256(replaced).hexdigest()
        self.v11["integritySha256"]=_hash({k:v for k,v in self.v11.items()
                                            if k!="integritySha256"})
        (self.folder/stage._V11).write_text(json.dumps(self.v11))
        with self.assertRaisesRegex(ValueError,
                                    "V12_PATCH_OUT_OF_SCOPE"):
            self.call()
        self.assertFalse(self.ops)

    def test_mismatched_diff_paths_fails_even_with_updated_sha(self):
        data=(self.folder/stage._PATCH).read_bytes().replace(
            b" b/section-9-1/app/app.js",b" b/section-9-2/app/app.js")
        (self.folder/stage._PATCH).write_bytes(data)
        self.v11["privatePatchBytes"]=len(data)
        self.v11["privatePatchSha256"]=sha256(data).hexdigest()
        self.v11["integritySha256"]=_hash({k:v for k,v in self.v11.items()
                                            if k!="integritySha256"})
        (self.folder/stage._V11).write_text(json.dumps(self.v11))
        with self.assertRaisesRegex(ValueError,
                                    "V12_PATCH_HEADER_UNSAFE_OR_MISMATCHED"):
            self.call()

    def test_missing_or_replaced_patch_is_refused(self):
        (self.folder/stage._PATCH).unlink()
        with self.assertRaisesRegex(ValueError,
                                    "V12_PRIVATE_PATCH_MISSING_OR_UNSAFE"):
            self.call()

    def test_staged_identity_not_stolen_from_another_head(self):
        self.ready["gitHead"]="d"*40
        with self.assertRaisesRegex(ValueError,
                                    "V12_PROPOSAL_SOURCE_IDENTITY_CHANGED"):
            self.call()

if __name__=="__main__":
    main()

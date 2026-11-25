"""BSA227 offline public destination audit: fake-only fixtures and failures.

No public repository is read, no account permissions inferred, no push or
deployment. The separate real Yoga6 source-free worker proves live V8.
"""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import shutil
import unittest

from app_generator.runtime import v3_public_deployment_scope as s
from app_generator.runtime.v3_five_stage_completion import _BASE, _hash
from app_generator.runtime import v3_versioned_readiness as source

def sha(b):
    return sha256(b).hexdigest()

class PublicV8ScopeTests(unittest.TestCase):
    def setUp(self):
        tmp=TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp=Path(tmp.name)
        self.repo=self.tmp/"repo"
        self.repo.mkdir()
        self.private=self.tmp/"private"
        self.private.mkdir()
        self.site=self.tmp/"site"
        self.site.mkdir()
        self.head="a"*40
        self.proposal="b"*64
        self.folder=self.private/_BASE/self.head/self.proposal
        self.folder.mkdir(parents=True)
        self.source=self.folder/"private-preview"
        self.baseline={}
        self.expected={}
        self.records=[]
        for n,changes in enumerate((1,1,0,0,0,3),1):
            name=f"section-9-{n}"
            base={"schemaVersion":1,"packageId":f"fake-{name}",
                  "status":"draft","activities":[
                {"id":f"activity-{i}","prompt":f"fake-{i}"} for i in range(18)]}
            fixed=deepcopy(base)
            for i in range(changes):
                fixed["activities"][i]["prompt"]=f"new-fake-{i}"
            first=json.dumps(base,sort_keys=True).encode()
            second=json.dumps(fixed,sort_keys=True).encode()
            current=self.site/name/"content"/"package.json"
            staged=self.source/"content"/"chapter-9"/name/"package.json"
            current.parent.mkdir(parents=True)
            staged.parent.mkdir(parents=True)
            current.write_bytes(first)
            staged.write_bytes(second)
            self.baseline[name]=sha(first)
            self.expected[name]=changes
            self.records.append({"section":name,"packageSha256":sha(second),
                                 "bundleFileCount":8})
        for n in (7,8,9):
            path=self.site/f"section-9-{n}"/"content"/"package.json"
            path.parent.mkdir(parents=True)
            path.write_text('{"activities":[]}')
        self.v7={
            "status":"SIX_REAL_PUBLIC_BUNDLE_BUILDS_VERIFIED_PRIVATE_NO_DEPLOY",
            "realOriginalPublicBuilderInvocations":6,
            "gitHead":self.head,"proposalSha256":self.proposal,
            "publicationAuthorized":False,"publicDeployExecuted":False,
            "releases":self.records,
        }
        self.v7["integritySha256"]=_hash(self.v7)
        (self.folder/s._V7).write_text(json.dumps(self.v7))
        self.ready={
            "status":"VERSIONED_SCIENCE_BROWSER_AND_CI_VERIFIED_UNADMITTED",
            "exactHeadHostedCiSuccess":True,"codeWorkingTreeClean":True,
            "publicationAuthorized":False,"gitHead":self.head,
            "proposalSha256":self.proposal,
        }

    def compare(self):
        return s._compare_public(self.site,self.source,self.v7,
                                 baseline=self.baseline,
                                 expected_changes=self.expected)

    def test_exact_six_scope_is_three_changed_five_activities(self):
        rows=self.compare()
        self.assertEqual(len(rows),6)
        self.assertEqual(sum(x["changedActivities"] for x in rows),5)
        self.assertEqual(sum(x["wouldReplacePublicBytes"] for x in rows),3)

    def test_changed_unrelated_public_baseline_blocks(self):
        name="section-9-1"
        path=self.site/name/"content"/"package.json"
        path.write_bytes(path.read_bytes()+b" ")
        with self.assertRaisesRegex(ValueError,"UNEXPECTED_PUBLIC_OR_PRIVATE_BYTES"):
            self.compare()

    def test_changes_in_unexpected_activity_block(self):
        name="section-9-3"
        path=self.source/"content"/"chapter-9"/name/"package.json"
        doc=json.loads(path.read_text())
        doc["activities"][0]["prompt"]="unexpected"
        updated=json.dumps(doc,sort_keys=True).encode()
        path.write_bytes(updated)
        self.records[2]["packageSha256"]=sha(updated)
        with self.assertRaisesRegex(ValueError,"UNEXPECTED_CONTENT_CHANGE_COUNT"):
            self.compare()

    def test_activity_id_rewrite_refused(self):
        name="section-9-6"
        path=self.source/"content"/"chapter-9"/name/"package.json"
        doc=json.loads(path.read_text())
        doc["activities"][0]["id"]="replacement-id"
        updated=json.dumps(doc,sort_keys=True).encode()
        path.write_bytes(updated)
        self.records[5]["packageSha256"]=sha(updated)
        with self.assertRaisesRegex(ValueError,"UNEXPECTED_ACTIVITY_ROSTER"):
            self.compare()

    def test_wrong_package_identity_refused(self):
        name="section-9-1"
        path=self.source/"content"/"chapter-9"/name/"package.json"
        doc=json.loads(path.read_text())
        doc["packageId"]="different"
        updated=json.dumps(doc,sort_keys=True).encode()
        path.write_bytes(updated)
        self.records[0]["packageSha256"]=sha(updated)
        with self.assertRaisesRegex(ValueError,"PACKAGE_IDENTITY_OR_SIZE_CHANGED"):
            self.compare()

    def test_section_nine_unrelated_routes_must_remain(self):
        (self.site/"section-9-8"/"content"/"package.json").unlink()
        with self.assertRaisesRegex(ValueError,"OTHER_CHAPTER9_ROUTES_MISSING"):
            self.compare()

    def test_v7_roster_must_not_be_relabelled(self):
        self.records[0]["section"]="section-9-9"
        with self.assertRaisesRegex(ValueError,"INVALID_V7_ROSTER"):
            self.compare()

    def test_unsafe_symlink_public_package_fails(self):
        name="section-9-2"
        target=self.site/name/"content"/"package.json"
        real=target.with_suffix(".backup")
        target.rename(real)
        try:
            target.symlink_to(real)
        except OSError:
            self.skipTest("Windows nonadmin symlink unavailable")
        with self.assertRaisesRegex(ValueError,"UNSAFE_PACKAGE"):
            self.compare()

    def test_config_destination_mismatch_fails_closed(self):
        config=self.repo/"config"/"configure_project.toml"
        config.parent.mkdir()
        config.write_text('[automation]\npublic_deploy_repository="wrong/site"\n'
                          'public_deploy_base_url="https://wrong/"\n'
                          'public_deploy_base_branch="main"\n')
        with self.assertRaisesRegex(ValueError,"WRONG_DESTINATION_CONFIG"):
            s._config(self.repo)

    def test_no_public_write_commands_accepted(self):
        with self.assertRaisesRegex(ValueError,"WRITING_COMMAND_FORBIDDEN"):
            s._proc(["git","push","origin","main"])
        with self.assertRaisesRegex(ValueError,"WRITING_COMMAND_FORBIDDEN"):
            s._proc(["gh","pr","merge","123"])

    def test_finite_synthetic_full_v8_proof_and_restart(self):
        def safe_remote(argv,*,cwd=None,timeout=120):
            if argv[:2]==["git","clone"]:
                shutil.copytree(self.site,Path(argv[-1]))
                return ""
            if argv[:2]==["git","rev-parse"]:
                return s._MAIN
            if argv[:2]==["git","ls-remote"]:
                return s._MAIN+" refs/heads/main"
            raise AssertionError("non-read command")
        with patch.object(s,"_PUBLIC_BASE",self.baseline),patch.object(
                s,"_git_info",return_value=(self.head,"feature/fake")),patch.object(
                s,"_git_clean",return_value=True),patch.object(
                s,"_hosted_runs",return_value=[]),patch.object(
                s,"_exact_ci_success",return_value=True),patch.object(
                source,"_read_previous",return_value=self.ready),patch.object(
                s,"_config",return_value={}),patch.object(
                s,"_permissions",return_value={
                    "authenticatedPushPermissionVerified":True,
                    "authenticatedAdminPermissionVerified":True,
                    "pagesBaseUrlMatches":True}),patch.object(
                s,"_proc",side_effect=safe_remote):
            first=s.verify_public_deployment_scope(
                self.repo,self.private,self.ready,self.v7)
            second=s.verify_public_deployment_scope(
                self.repo,self.private,self.ready,self.v7)
        self.assertEqual(first,second)
        self.assertEqual(first["status"],s._STATUS)
        self.assertEqual(first["packagesRequiringUpdates"],3)
        self.assertEqual(first["individualChangedActivities"],5)
        self.assertFalse(first["publicPushExecuted"])
        self.assertFalse(first["publicationAuthorized"])
        self.assertTrue((self.folder/s._V8).is_file())

    def test_altered_v7_receipt_rejected_without_remote_io(self):
        doc=json.loads((self.folder/s._V7).read_text())
        doc["publicDeployExecuted"]=True
        (self.folder/s._V7).write_text(json.dumps(doc))
        with patch.object(s,"_git_info",return_value=(self.head,"feature/fake")),patch.object(
                s,"_git_clean",return_value=True),patch.object(
                s,"_hosted_runs",return_value=[]),patch.object(
                s,"_exact_ci_success",return_value=True),patch.object(
                source,"_read_previous",return_value=self.ready),patch.object(
                s,"_permissions") as permissions:
            with self.assertRaisesRegex(ValueError,"V7_RECEIPT_MISMATCH"):
                s.verify_public_deployment_scope(self.repo,self.private,self.ready,self.v7)
        permissions.assert_not_called()

    def test_authenticated_github_push_denied_fails_closed(self):
        fake={"full_name":s._DEST,"default_branch":"main",
              "private":False,"push":False,"admin":True,
              "homepage":s._URL}
        with patch.object(s,"_proc",return_value=json.dumps(fake)):
            with self.assertRaisesRegex(ValueError,
                                        "PERMISSION_OR_HOME_MISMATCH"):
                s._permissions()

    def test_public_head_moves_during_read_only_audit(self):
        def changed_remote(argv,*,cwd=None,timeout=120):
            if argv[:2]==["git","clone"]:
                shutil.copytree(self.site,Path(argv[-1]))
                return ""
            if argv[:2]==["git","rev-parse"]:
                return s._MAIN
            if argv[:2]==["git","ls-remote"]:
                return ("f"*40)+" refs/heads/main"
            raise AssertionError("unexpected write/network action")
        with patch.object(s,"_PUBLIC_BASE",self.baseline),patch.object(
                s,"_git_info",return_value=(self.head,"feature/fake")),patch.object(
                s,"_git_clean",return_value=True),patch.object(
                s,"_hosted_runs",return_value=[]),patch.object(
                s,"_exact_ci_success",return_value=True),patch.object(
                source,"_read_previous",return_value=self.ready),patch.object(
                s,"_config",return_value={}),patch.object(
                s,"_permissions",return_value={
                    "authenticatedPushPermissionVerified":True,
                    "authenticatedAdminPermissionVerified":True,
                    "pagesBaseUrlMatches":True}),patch.object(
                s,"_proc",side_effect=changed_remote):
            with self.assertRaisesRegex(ValueError,
                                        "REMOTE_CHANGED_DURING_AUDIT"):
                s.verify_public_deployment_scope(
                    self.repo,self.private,self.ready,self.v7)

if __name__=="__main__":
    unittest.main()

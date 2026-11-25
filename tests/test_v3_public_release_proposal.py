"""BSA229 fake-only fault-injection tests; live Yoga6 run is separate."""
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import shutil
import unittest

from app_generator.runtime import v3_pinned_public_release_proposal as p
from app_generator.runtime.v3_five_stage_completion import _BASE, _hash
from app_generator.runtime import v3_versioned_readiness as version


class PrivatePinnedProposalTests(unittest.TestCase):
    def setUp(self):
        t=TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        self.repo=self.root/"repo";self.repo.mkdir()
        for name in ("app","domains"):
            f=self.repo/name;f.mkdir()
            (f/"placeholder.txt").write_text("fake")
        self.private=self.root/"private";self.private.mkdir()
        self.head="a"*40;self.proposal="b"*64
        self.folder=self.private/_BASE/self.head/self.proposal
        self.folder.mkdir(parents=True)
        self.source=self.folder/"private-preview"
        self.site=self.root/"fake-public"
        self.site.mkdir()
        self.v7={"status":"SIX_REAL_PUBLIC_BUNDLE_BUILDS_VERIFIED_PRIVATE_NO_DEPLOY",
                 "gitHead":self.head,"proposalSha256":self.proposal,
                 "releases":[]}
        original_v6=[]
        for number in range(1,10):
            name=f"section-9-{number}"
            sitefile=self.site/name/"content"/"package.json"
            sitefile.parent.mkdir(parents=True)
            sitefile.write_text('{"publicFake":true}')
            if number>6:
                continue
            raw=json.dumps({"packageId":name,"activities":[{
                "id":f"fake-{j}","type":"mcq"} for j in range(18)]}).encode()
            item=self.source/"content"/"chapter-9"/name/"package.json"
            item.parent.mkdir(parents=True)
            item.write_bytes(raw)
            att=self.folder/"native-v3-exact-attestations"/name/"autonomous-v3-release-receipt.json"
            att.parent.mkdir(parents=True)
            att.write_bytes(b"fake-native-receipt-"+str(number).encode())
            sha=sha256(raw).hexdigest()
            self.v7["releases"].append({"section":name,"packageSha256":sha})
            original_v6.append({
                "section":name,
                "privateAttestationSha256":sha256(att.read_bytes()).hexdigest()})
        self.v7["integritySha256"]=_hash(self.v7)
        (self.folder/"V7_ACTUAL_PUBLIC_BUNDLE_BUILDER_HANDOFF.json").write_text(
            json.dumps(self.v7))
        (self.folder/"V6_GENUINE_NATIVE_V3_RELEASE_ATTESTATION.json").write_text(
            json.dumps({"packages":original_v6}))
        self.v8={"status":p.scope._STATUS,"gitHead":self.head,
                 "proposalSha256":self.proposal,"packagesChecked":6,
                 "packagesRequiringUpdates":3,"individualChangedActivities":5,
                 "publicDestinationMainCommit":p.scope._MAIN,
                 "publicDestinationRepository":p.scope._DEST,
                 "sourceV7ReceiptSha256":self.v7["integritySha256"],
                 "publicDeployExecuted":False,"publicPushExecuted":False,
                 "publicationAuthorized":False}
        self.v8["integritySha256"]=_hash(self.v8)
        (self.folder/p.scope._V8).write_text(json.dumps(self.v8))
        self.ready={"status":"VERSIONED_SCIENCE_BROWSER_AND_CI_VERIFIED_UNADMITTED",
                    "exactHeadHostedCiSuccess":True,
                    "codeWorkingTreeClean":True,
                    "publicationAuthorized":False,"gitHead":self.head,
                    "proposalSha256":self.proposal}
        self.remote_drift=False
        self.clones=[]

    def fakeproc(self,argv,*,cwd=None,timeout=120):
        assert argv[:2] in (["git","clone"],["git","rev-parse"],["git","ls-remote"])
        if argv[:2]==["git","clone"]:
            shutil.copytree(self.site,Path(argv[-1]))
            self.clones.append(argv[-1])
            return ""
        if argv[:2]==["git","rev-parse"]:
            return p.scope._MAIN
        return (("f"*40) if self.remote_drift else p.scope._MAIN)+" refs/heads/main"

    def fake_build(self,output,package,**kwargs):
        output.mkdir()
        (output/"app").mkdir()
        (output/"content").mkdir()
        (output/"content"/"package.json").write_bytes(package.read_bytes())
        (output/"index.html").write_text("<html>published build</html>")
        (output/".nojekyll").write_bytes(b"")
        for i in range(5):
            (output/"app"/f"file{i}.js").write_text("fake public")

    def call(self):
        with patch.object(p,"_git_info",return_value=(self.head,"fake")),patch.object(
                p,"_git_clean",return_value=True),patch.object(
                p,"_hosted_runs",return_value=[]),patch.object(
                p,"_exact_ci_success",return_value=True),patch.object(
                p,"_read_previous",return_value=self.ready),patch.object(
                p.scope,"_config",return_value={}),patch.object(
                p.scope,"_proc",side_effect=self.fakeproc),patch.object(
                p.scope,"_compare_public",return_value=[
                    {"section":f"section-9-{i}",
                     "wouldReplacePublicBytes":i in (1,2,6)} for i in range(1,7)]),patch.object(
                p,"enforce_academic_release_gate",side_effect=lambda _,source,__:{
                    "artifactSha256":sha256(source.read_bytes()).hexdigest()}),patch.object(
                p,"build",side_effect=self.fake_build) as build:
            outcome=p.stage_pinned_private_public_proposal(
                self.repo,self.private,self.ready,self.v8)
            return outcome,build.call_count

    def test_six_source_packages_only_three_staged_production_bundles(self):
        out,calls=self.call()
        self.assertEqual(out["status"],p._STATUS)
        self.assertEqual(calls,3)
        self.assertEqual(out["releaseFileCount"],24)
        self.assertEqual(out["changedPublicRoutes"],
                         ["section-9-1","section-9-2","section-9-6"])
        self.assertFalse(out["publicPushExecuted"])
        self.assertFalse(out["publicPRCreated"])
        self.assertFalse(out["publicationAuthorized"])
        release=self.folder/p._FOLDER
        self.assertFalse((release/"section-9-3").exists())
        self.assertTrue((release/"section-9-6"/"content"/"package.json").is_file())

    def test_restart_is_immutable_and_does_not_duplicate_external_actions(self):
        before,first_count=self.call()
        after,second_count=self.call()
        self.assertEqual(before,after)
        self.assertEqual((first_count,second_count),(3,3))
        self.assertFalse(any("push" in " ".join(c) for c in self.clones))

    def test_tampered_v8_receipt_refused_before_public_read(self):
        doc=json.loads((self.folder/p.scope._V8).read_text())
        doc["packagesRequiringUpdates"]=4
        (self.folder/p.scope._V8).write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError,"SIGNED_PUBLIC_SCOPE_OR_V7_TAMPER"):
            self.call()
        self.assertFalse(self.clones)

    def test_wrong_candidate_sha_rejected(self):
        target=self.source/"content"/"chapter-9"/"section-9-1"/"package.json"
        target.write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError,"EXACT_PACKAGE_OR_ATTESTATION_CHANGED"):
            self.call()

    def test_unexpected_remote_head_movement_fails_closed(self):
        self.remote_drift=True
        with self.assertRaisesRegex(ValueError,"PUBLIC_MAIN_DRIFT_BEFORE_PROPOSAL"):
            self.call()
        self.assertFalse((self.folder/p._FOLDER).exists())

    def test_private_staged_package_corruption_blocks_restart(self):
        self.call()
        staged=self.folder/p._FOLDER/"section-9-1"/"content"/"package.json"
        staged.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError,"PRIVATE_PROPOSAL_CHANGED_ON_RESTART"):
            self.call()

    def test_readiness_and_exact_ci_cannot_be_bypassed(self):
        self.ready["exactHeadHostedCiSuccess"]=False
        with self.assertRaisesRegex(ValueError,"SOURCE_BOUND_V8_PREREQUISITE_MISSING"):
            self.call()
        self.assertFalse(self.clones)


if __name__=="__main__":
    unittest.main()

"""BSA225 synthetic/fault-injection tests. These are NOT real Gemini evidence.

The separate Yoga6 normal worker test executes the actual original release
builder on six genuinely attested packages, without publication.
"""
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app_generator.runtime import v3_public_bundle_handoff as h
from app_generator.runtime.v3_five_stage_completion import _BASE, _hash


class V7PublicBundleHandoffTests(unittest.TestCase):
    def setUp(self):
        temp=TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base=Path(temp.name)
        self.repo=self.base/"repo"
        (self.repo/"app").mkdir(parents=True)
        (self.repo/"domains").mkdir()
        (self.repo/"app"/"index.html").write_text("<html></html>")
        (self.repo/"domains"/"registry.json").write_text("{}")
        self.private=self.base/"private"
        self.private.mkdir()
        self.head="a"*40
        self.proposal="b"*64
        self.folder=self.private/_BASE/self.head/self.proposal
        self.folder.mkdir(parents=True)
        self.ready={
            "status":"VERSIONED_SCIENCE_BROWSER_AND_CI_VERIFIED_UNADMITTED",
            "exactHeadHostedCiSuccess":True,
            "codeWorkingTreeClean":True,
            "proposedContentScientificCoverage":108,
            "publicationAuthorized":False,
            "gitHead":self.head,
            "proposalSha256":self.proposal,
        }
        self.stage={
            "status":"FIVE_STAGE_PRIVATE_TECHNICAL_PATH_COMPLETE_NO_PUBLICATION",
            "technicalV3ReleaseAttestationsVerified":True,
            "privateNativeV3Attestations":6,
            "publicationAuthorized":False,
            "gitHead":self.head,
            "proposalSha256":self.proposal,
        }
        self.raw=b'{"activities":[]}'
        self.digest=sha256(self.raw).hexdigest()
        self.records=[]
        for i in range(1,7):
            name=f"section-9-{i}"
            source=(self.folder/"private-preview"/"content"/"chapter-9"/
                    name/"package.json")
            source.parent.mkdir(parents=True)
            source.write_bytes(self.raw)
            att=(self.folder/"native-v3-exact-attestations"/name/
                 "autonomous-v3-release-receipt.json")
            att.parent.mkdir(parents=True)
            att.write_bytes(b"fake-synthetic-attestation")
            self.records.append({
                "section":name,"packageSha256":self.digest,
                "nativeV3TechnicalGatePassed":True,
                "privateAttestationSha256":sha256(att.read_bytes()).hexdigest(),
            })
        v6={
            "status":"SIX_PRIVATE_NATIVE_V3_RELEASE_ATTESTATIONS_VERIFIED_NO_PUBLIC_DEPLOY",
            "gitHead":self.head,"proposalSha256":self.proposal,
            "nativeV3TechnicalReleaseChecksPassed":6,
            "sourceGenuineTwoReviewerPositions":108,
            "publicationAuthorized":False,"publicDeployExecuted":False,
            "packages":self.records,
        }
        v6["integritySha256"]=_hash(v6)
        self.v6=v6
        (self.folder/h._V6).write_text(json.dumps(v6))
        self.stage["nativeV3TechnicalReleaseEvidence"]={
            "integritySha256":v6["integritySha256"]}
        self.patches=[
            patch.object(h,"_read_previous",return_value=self.ready),
            patch.object(h,"_git_info",return_value=(self.head,"fake")),
            patch.object(h,"_git_clean",return_value=True),
            patch.object(h,"_hosted_runs",return_value=[]),
            patch.object(h,"_exact_ci_success",return_value=True),
            patch.object(h,"enforce_academic_release_gate",
                         return_value={"artifactSha256":self.digest,
                                       "automatedTechnicalEligible":True}),
            patch.object(h,"build",side_effect=self.fake_build),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    @staticmethod
    def fake_build(output,package,**kwargs):
        output.mkdir()
        (output/"content").mkdir()
        (output/"app").mkdir()
        (output/"content"/"package.json").write_bytes(package.read_bytes())
        (output/"index.html").write_text("<html>release</html>")
        for i in range(5):
            (output/"app"/f"file-{i}.js").write_text("fake")

    def run_stage(self):
        return h.dispatch_private_public_bundle_build(
            self.repo,self.private,self.ready,self.stage)

    def test_six_actual_release_builder_dispatches_and_durable_receipt(self):
        got=self.run_stage()
        self.assertEqual(got["status"],h._STATUS)
        self.assertEqual(got["realOriginalPublicBuilderInvocations"],6)
        self.assertEqual(h.build.call_count,6)
        self.assertFalse(got["publicDeployExecuted"])
        self.assertFalse(got["publicationAuthorized"])
        self.assertEqual(len(got["releases"]),6)
        self.assertTrue((self.folder/h._V7).is_file())

    def test_repeat_verifies_existing_checkpoint_no_publisher(self):
        first=self.run_stage()
        second=self.run_stage()
        self.assertEqual(first,second)
        self.assertEqual(h.build.call_count,12)

    def test_modified_source_package_is_rejected(self):
        p=self.folder/"private-preview"/"content"/"chapter-9"/"section-9-3"/"package.json"
        p.write_bytes(b'{"changed":true}')
        with self.assertRaisesRegex(ValueError,"PACKAGE_OR_ATTESTATION_CHANGED"):
            self.run_stage()

    def test_tampered_private_v3_attestation_rejected(self):
        p=self.folder/"native-v3-exact-attestations"/"section-9-3"/"autonomous-v3-release-receipt.json"
        p.write_bytes(b"forged-synthetic")
        with self.assertRaisesRegex(ValueError,"PACKAGE_OR_ATTESTATION_CHANGED"):
            self.run_stage()

    def test_v6_integrity_tamper_rejected(self):
        p=self.folder/h._V6
        doc=json.loads(p.read_text())
        doc["nativeV3TechnicalReleaseChecksPassed"]=5
        p.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError,"V6_INTEGRITY_OR_STATUS_CHANGED"):
            self.run_stage()

    def test_no_five_stage_science_cannot_build(self):
        self.stage["privateNativeV3Attestations"]=5
        with self.assertRaisesRegex(ValueError,"GENUINE_V6_PREREQUISITE_MISSING"):
            self.run_stage()
        self.assertEqual(h.build.call_count,0)

    def test_wrong_head_or_dirty_source_cannot_build(self):
        with patch.object(h,"_git_clean",return_value=False):
            with self.assertRaisesRegex(ValueError,"EXACT_HEAD_CI_OR_CLEAN_MISSING"):
                self.run_stage()
        self.assertEqual(h.build.call_count,0)

    def test_missing_hosted_ci_cannot_build(self):
        with patch.object(h,"_exact_ci_success",return_value=False):
            with self.assertRaisesRegex(ValueError,"EXACT_HEAD_CI_OR_CLEAN_MISSING"):
                self.run_stage()
        self.assertEqual(h.build.call_count,0)

    def test_builder_changed_bytes_fails_closed(self):
        def corrupt(output,package,**kwargs):
            self.fake_build(output,package,**kwargs)
            (output/"content"/"package.json").write_bytes(b"wrong")
        with patch.object(h,"build",side_effect=corrupt):
            with self.assertRaisesRegex(ValueError,"PRODUCTION_BUNDLE_BYTES_CHANGED"):
                self.run_stage()

    def test_old_signed_v7_receipt_must_not_be_replaced(self):
        self.run_stage()
        p=self.folder/h._V7
        doc=json.loads(p.read_text())
        doc["publicDeployExecuted"]=True
        p.write_text(json.dumps(doc))
        with self.assertRaises(ValueError):
            self.run_stage()


if __name__=="__main__":
    unittest.main()

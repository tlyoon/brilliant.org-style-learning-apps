"""BSA218: exact SHA browser source selection for two new independently reviewed items.

Mocked Gemini verdicts are test-only; NEVER source of true science acceptance.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app_generator.runtime.v3_frozen_original_tail import _bytes
from app_generator.runtime.v3_versioned_acceptance_scope import _encoded
from app_generator.validation.autonomous_completion import package_identity
from scripts import check_v3_real_chapter9_browser as browser


COURSE=Path(__file__).resolve().parents[1]/"content"/"chapter-9"


class FinalTwoBrowserTests(unittest.TestCase):
    def setUp(self):
        temp=TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)/"repo"
        self.private=Path(temp.name)/"private"
        self.private.mkdir()
        rows=[]
        self.sources={}
        for n in range(1,7):
            label=f"section-9-{n}"
            raw=(COURSE/label/"package.json").read_bytes()
            package=json.loads(raw.decode("utf8"))
            orig,_=package_identity(raw)
            target=orig
            if n in (1,6):
                package=deepcopy(package)
                changes=[0] if n==1 else [5,6,9]
                for k in changes:
                    package["activities"][k]["prompt"]["en"]+=(
                        " TEST-ONLY changed source content.")
                newraw=_bytes(package)
                target,_=package_identity(newraw)
                directory=self.private/"final-two-science-candidates"/label/target
                directory.mkdir(parents=True)
                (directory/"package.json").write_bytes(newraw)
            else:
                directory=self.root/"content"/"chapter-9"/label
                directory.mkdir(parents=True)
                (directory/"package.json").write_bytes(raw)
                newraw=raw
            self.sources[label]=target
            rows.append({"section":label,"activities":18,
                         "originalPackageSha256":orig,
                         "proposedPackageSha256":target})
        self.proofs=[{"section":"section-9-1","genuineConsensusPass":True},
                     {"section":"section-9-6","genuineConsensusPass":True}]
        self.final={
            "reviewedNewSourceOnly":True,
            "originalSection91Index0UnknownPreserved":True,
            "originalSection96Index6UnknownPreserved":True,
            "publicationAuthorized":False,
            "versionedScopeAdmitted":False,
            "proofs":self.proofs,
        }
        self.doc={
            "sections":rows,
            "publicationAuthorized":False,"versionedScopeAdmitted":False,
            "section96UnrecoverableRoleReplacement":{},
            "section96ScientificFailureReplacement":{
                "changedActivityIndices":[5,9],
                "originalIndex9ScientificFailurePreserved":True,
                "originalIndex6ProviderUnknownPreserved":True,
                "independentNewVersionGeminiEvidence":[
                    {"genuineConsensusPass":True}]*2,
            },
            "finalTwoNewVersionGenuineScience":self.final,
        }
        self.fake_verifier={
            "proofs":self.proofs,
            "section91":{"candidatePackageSha256":self.sources["section-9-1"]},
            "section96":{"candidatePackageSha256":self.sources["section-9-6"]},
        }

    def snapshot(self):
        payload={k:v for k,v in self.doc.items() if k!="integritySha256"}
        digest=sha256(_encoded(payload)).hexdigest()
        folder=self.private/"versioned-course-proposals"/digest
        folder.mkdir(parents=True,exist_ok=True)
        (folder/"scope-proposal.json").write_text(
            json.dumps({**payload,"integritySha256":digest}),encoding="utf8")
        return digest

    def test_exact_new_two_science_provenance_selects_all_six_packages(self):
        digest=self.snapshot()
        with patch.object(browser,"ROOT",self.root),patch.object(
             browser,"read_source_free_checkpoint",return_value={
                 "publicationAuthorized":False,"proposalSha256":digest}),patch(
             "app_generator.runtime.v3_final_two_science.verified_final_two_science",
             return_value=self.fake_verifier):
            observed,packages=browser._source_bound_packages(self.private)
        self.assertEqual(observed,digest)
        self.assertEqual(len(packages),6)
        self.assertEqual(sum(len(items) for _,_,items in packages),108)
        self.assertEqual(package_identity(packages[0][1])[0],
                         self.sources["section-9-1"])
        self.assertEqual(package_identity(packages[-1][1])[0],
                         self.sources["section-9-6"])

    def test_no_genuine_saved_role_evidence_rejects_forged_proposal(self):
        digest=self.snapshot()
        with patch.object(browser,"ROOT",self.root),patch.object(
             browser,"read_source_free_checkpoint",return_value={
                 "publicationAuthorized":False,"proposalSha256":digest}),patch(
             "app_generator.runtime.v3_final_two_science.verified_final_two_science",
             return_value=None):
            with self.assertRaisesRegex(ValueError,"NEEDS_GENUINE_NEW_ROLE_PROOF"):
                browser._source_bound_packages(self.private)

    def test_mismatched_new_section96_sha_is_fatal_not_browser_pass(self):
        self.fake_verifier["section96"]["candidatePackageSha256"]="f"*64
        digest=self.snapshot()
        with patch.object(browser,"ROOT",self.root),patch.object(
             browser,"read_source_free_checkpoint",return_value={
                 "publicationAuthorized":False,"proposalSha256":digest}),patch(
             "app_generator.runtime.v3_final_two_science.verified_final_two_science",
             return_value=self.fake_verifier):
            with self.assertRaisesRegex(ValueError,"PROPOSED_SHA_MISMATCH"):
                browser._source_bound_packages(self.private)

    def test_content_mutation_does_not_reuse_sha_bound_browser_receipt(self):
        digest=self.snapshot()
        path=(self.private/"final-two-science-candidates"/"section-9-1"/
              self.sources["section-9-1"]/"package.json")
        path.write_bytes(path.read_bytes()+b" ")
        with patch.object(browser,"ROOT",self.root),patch.object(
             browser,"read_source_free_checkpoint",return_value={
                 "publicationAuthorized":False,"proposalSha256":digest}),patch(
             "app_generator.runtime.v3_final_two_science.verified_final_two_science",
             return_value=self.fake_verifier):
            with self.assertRaisesRegex(ValueError,"SOURCE_SHA_NOT_PROPOSED_VERSION"):
                browser._source_bound_packages(self.private)


if __name__=="__main__":
    unittest.main()

"""Source-free adversarial tests for immutable v2-to-v3 academic handoff."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app_generator.validation.impulse_v3 import (
    V3_LABEL, V3_ANSWER_LOGIC, ITEM_ID, review_candidate_v3, canonical_digest,
)
from app_generator.validation.impulse_v3_audit import audit_v3
from scripts.make_impulse_v3_candidate import export_v3
from tests import test_impulse_semantics as fixture_source

ROOT=Path(__file__).resolve().parents[1]


class ImpulseV3Tests(unittest.TestCase):
    def fixture(self,folder):
        root=Path(folder)
        pdf=root/"source.pdf"
        pdf.write_bytes(b"%PDF-1.4 synthetic")
        sha=hashlib.sha256(pdf.read_bytes()).hexdigest()
        v2=fixture_source.TrilingualDistractorTests()._fictional_candidate()
        activity=v2["activities"][0]
        activity["type"]="interactive"
        activity["visualPlan"]={"learningObjective":"unchanged"}
        activity["objective"]="unchanged"
        for i in range(17):
            v2["activities"].append({"id":f"filler-{i}","type":"mcq",
                                      "prompt":{"en":"unchanged"}})
        v2_path=root/"parent-v2.json"
        v2_path.write_bytes((json.dumps(v2,ensure_ascii=False)+"\n").encode("utf-8"))
        parent_sha=hashlib.sha256(v2_path.read_bytes()).hexdigest()
        receipt=root/"parent-review.json"
        receipt.write_text(json.dumps({
            "candidatePackageFileSha256":parent_sha,
            "controlledSourceSha256":sha,
            "reviewOnly":True,"publicationAuthorized":False
        }),encoding="utf-8")
        return v2_path,receipt,pdf,sha,parent_sha

    def test_exact_v3_candidate_and_review_gate(self):
        with tempfile.TemporaryDirectory() as t:
            v2,review,pdf,sha,parent_sha=self.fixture(t)
            out=Path(t)/"review-v3"
            with patch("app_generator.validation.impulse_v3.EXPECTED_V2_SHA256",parent_sha):
              with patch("app_generator.validation.impulse_v3.SOURCE_SHA256",sha):
                result=export_v3(v2,review,pdf,out)
                candidate=json.loads((out/"package.json").read_text(encoding="utf-8"))
                target=candidate["activities"][0]
                previous=json.loads(v2.read_text(encoding="utf-8"))
                self.assertEqual(V3_LABEL,target["interaction"]["items"][0]["label"])
                self.assertEqual(V3_ANSWER_LOGIC,target["answerLogic"])
                self.assertEqual(17,result["untouchedActivities"])
                self.assertEqual(previous["activities"][1:],candidate["activities"][1:])
                self.assertEqual(previous["activities"][0]["visualPlan"],target["visualPlan"])
                self.assertEqual(previous["activities"][0]["interaction"]["correctSelections"],
                                 target["interaction"]["correctSelections"])
                self.assertEqual("REVIEW_REQUIRED",result["academicQA"])
                self.assertFalse(result["publicationAuthorized"])
                file_sha=result["candidateFileSha256"]
                canonical=canonical_digest(candidate)
                with patch("app_generator.validation.impulse_v3_audit.EXPECTED_V3_FILE_SHA256",file_sha):
                  with patch("app_generator.validation.impulse_v3_audit.EXPECTED_V3_CANONICAL_SHA256",canonical):
                    qa=audit_v3(out/"package.json",out/"review.json",v2,review,pdf)
                    self.assertEqual(5,qa["boundedOptionsVerified"])
                    self.assertEqual(21,qa["multilingualNarrative"]["boundedConceptsPresent"])
                    self.assertFalse(qa["fullSemanticEquivalenceVerified"])
                    self.assertFalse(qa["publicationAuthorized"])
                with self.assertRaisesRegex(ValueError,"already exists"):
                    export_v3(v2,review,pdf,out)

    def test_source_and_parent_tampering_block(self):
        with tempfile.TemporaryDirectory() as t:
            v2,review,pdf,sha,parent_sha=self.fixture(t)
            original=v2.read_bytes()
            with patch("app_generator.validation.impulse_v3.EXPECTED_V2_SHA256",parent_sha):
              with patch("app_generator.validation.impulse_v3.SOURCE_SHA256",sha):
                changed=copy.deepcopy(json.loads(original.decode("utf-8")))
                changed["activities"][0]["interaction"]["correctSelections"].pop()
                v2.write_bytes(json.dumps(changed).encode("utf-8"))
                with self.assertRaisesRegex(ValueError,"checksum"):
                    review_candidate_v3(v2,review,pdf)
                v2.write_bytes(original)
                pdf.write_bytes(b"%PDF-1.4 altered")
                with self.assertRaisesRegex(ValueError,"PDF"):
                    review_candidate_v3(v2,review,pdf)

    def test_bad_selection_key_rejected_even_with_resigned_parent(self):
        with tempfile.TemporaryDirectory() as t:
            v2,review,pdf,sha,parent_sha=self.fixture(t)
            package=json.loads(v2.read_text(encoding="utf-8"))
            package["activities"][0]["interaction"]["correctSelections"].pop()
            v2.write_bytes(json.dumps(package,ensure_ascii=False).encode("utf-8"))
            new_sha=hashlib.sha256(v2.read_bytes()).hexdigest()
            body=json.loads(review.read_text())
            body["candidatePackageFileSha256"]=new_sha
            review.write_text(json.dumps(body))
            with patch("app_generator.validation.impulse_v3.EXPECTED_V2_SHA256",new_sha):
              with patch("app_generator.validation.impulse_v3.SOURCE_SHA256",sha):
                with self.assertRaisesRegex(ValueError,"answer structure"):
                    review_candidate_v3(v2,review,pdf)

    def test_multilingual_condition_distinguishes_net_from_individual_force(self):
        checks={
            "en":("net external impulse","negligible","does not require each external force"),
            "ms":("impuls luar bersih","boleh diabaikan","tidak mensyaratkan setiap daya luar"),
            "zh":("\u51c0\u5916\u529b\u51b2\u91cf","\u53ef\u5ffd\u7565",
                  "\u4e0d\u8981\u6c42\u6bcf\u4e00\u4e2a\u5916\u529b"),
        }
        for l,terms in checks.items():
            for term in terms:
                self.assertIn(term,V3_LABEL[l])
        self.assertNotIn("vastly greater than any external",V3_LABEL["en"].casefold())

    def test_unicode_integrity_and_current_checkout_cli(self):
        self.assertTrue(any("\u4e00"<=c<="\u9fff" for c in V3_LABEL["zh"]))
        self.assertNotIn("\ufffd",V3_LABEL["zh"])
        for name in ("make_impulse_v3_candidate.py","audit_impulse_v3.py"):
            p=ROOT/"scripts"/name
            r=subprocess.run([sys.executable,"-I",str(p),"--help"],
                             capture_output=True,text=True,timeout=20,cwd=ROOT)
            self.assertEqual(0,r.returncode,(name,r.stderr))

    def test_fail_closed_private_output_path(self):
        with tempfile.TemporaryDirectory() as t:
            v2,review,pdf,sha,parent_sha=self.fixture(t)
            with self.assertRaisesRegex(ValueError,"public Git repository"):
                export_v3(v2,review,pdf,ROOT/"candidate-must-not-be-written")


if __name__=="__main__":
    unittest.main()

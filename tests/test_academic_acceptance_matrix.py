"""Full activity QA matrix: scientific claims never passed from schema alone."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app_generator.validation.academic_qa import Finding
from app_generator.validation.academic_acceptance_matrix import audit_activity_matrix

def lang(s):
    return {"en":s+" english","ms":s+" bahasa","zh":"?????????"}

def sample():
    return {"activities":[
        {"id":"mcq-one","type":"mcq","prompt":lang("Momentum"),
         "feedback":lang("Feedback"),
         "answerKey":{"correct":"a","options":[
            {"id":"a","label":lang("Conserved momentum")},
            {"id":"b","label":lang("Not conserved")},
         ]}},
        {"id":"int-two","type":"interactive","interactionMode":"selection",
         "prompt":lang("Impulses"),"feedback":lang("Feedback"),
         "interaction":{"items":[{"id":"x","label":lang("Zero impulse")},
                                 {"id":"y","label":lang("Small impulse")}],
                        "correctSelections":["x"]}},
    ]}

class MatrixTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
        self.pdf=self.root/"source.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 controlled synthetic source")
        self.sha=hashlib.sha256(self.pdf.read_bytes()).hexdigest()
        self.pkg=self.root/"package.json"
        self.save(sample())
        self.repo=Path(__file__).resolve().parents[1]
    def save(self,obj):
        self.pkg.write_bytes(json.dumps(obj,ensure_ascii=False).encode("utf-8"))
    def audit(self,**kw):
        return audit_activity_matrix(
            repo_root=self.repo,package_path=self.pkg,source_pdf=self.pdf,
            source_sha256=self.sha,expected_count=2,**kw)
    def test_all_activities_tracked_without_fabricated_academic_pass(self):
        r=self.audit()
        self.assertEqual(2,r["activityCount"])
        self.assertEqual(0,r["counts"]["PASS"])
        self.assertEqual(2,r["counts"]["REVIEW_REQUIRED"])
        self.assertFalse(r["publicationAuthorized"])
        self.assertFalse(r["humanAcademicApprovalRequired"])
        self.assertTrue(all(a["nextAction"]=="AUTO_SOURCE_CHECK" for a in r["activities"]))
        self.assertTrue(all(not a["sourceLocationVerified"] for a in r["activities"]))
    def test_structural_answer_key_and_translation_defects_are_real_fails(self):
        p=sample()
        p["activities"][0]["answerKey"]["correct"]="missing"
        p["activities"][1]["interaction"]["items"][0]["label"].pop("ms")
        self.save(p)
        r=self.audit()
        self.assertEqual(2,r["counts"]["FAIL"])
        self.assertTrue(all(a["nextAction"]=="AUTO_REPAIR" for a in r["activities"]))
    def test_reject_controlled_source_mismatch_or_ambiguous_package(self):
        self.pdf.write_bytes(b"wrong original")
        with self.assertRaisesRegex(ValueError,"controlled PDF"):
            self.audit()
        self.pdf.write_bytes(b"%PDF-1.4 controlled synthetic source")
        p=sample()
        p["activities"][1]["id"]="mcq-one"
        self.save(p)
        with self.assertRaisesRegex(ValueError,"duplicate activity"):
            self.audit()
    def test_stale_or_forged_source_packets_are_not_evidence(self):
        packets={"packageSha256":"0"*64,"sourceSha256":self.sha,"packets":{}}
        r=self.audit(source_packets=packets)
        self.assertEqual(0,sum(x["sourceLocationVerified"] for x in r["activities"]))
        packets["packageSha256"]=hashlib.sha256(self.pkg.read_bytes()).hexdigest()
        packets["packets"]={"mcq-one":{"activityId":"mcq-one",
            "sourceSha256":self.sha,"sourceAnchors":[{"activityId":"mcq-one",
                  "pageIndex":1,"quotedText":"falsely invented original excerpt"}],
            "sourceEvidence":"invented"}}
        r=self.audit(source_packets=packets)
        self.assertFalse(r["activities"][0]["sourceLocationVerified"])
    def test_malformed_nested_generated_json_does_not_abort_other_activity_reviews(self):
        def null_mcq_key(p):
            p["activities"][0]["answerKey"]=None
        def unhashable_mcq_option_id(p):
            p["activities"][0]["answerKey"]["options"][0]["id"]=["a"]
        def malformed_mcq_options(p):
            p["activities"][0]["answerKey"]["options"]=None
        def unhashable_interactive_selection(p):
            p["activities"][1]["interaction"]["correctSelections"]=[["x"]]
        def unhashable_classification_placement(p):
            a=p["activities"][1]
            a["interactionMode"]="classification"
            a["interaction"]["targets"]=[{"id":"t","label":lang("Target")}]
            a["interaction"]["placements"]=[
                {"itemId":["x"],"targetId":"t"},
                {"itemId":"y","targetId":"t"}]
        for label, change, affected in (
            ("null-mcq-key",null_mcq_key,0),
            ("unhashable-mcq-option-id",unhashable_mcq_option_id,0),
            ("missing-mcq-options-list",malformed_mcq_options,0),
            ("unhashable-selection",unhashable_interactive_selection,1),
            ("unhashable-classification-placement",unhashable_classification_placement,1),
        ):
            with self.subTest(case=label):
                p=sample()
                change(p)
                self.save(p)
                result=self.audit()
                self.assertEqual(2,result["activityCount"])
                self.assertEqual("FAIL",result["activities"][affected]["academicQA"])
                self.assertEqual("AUTO_REPAIR",result["activities"][affected]["nextAction"])
                self.assertEqual("REVIEW_REQUIRED",
                                 result["activities"][1-affected]["academicQA"])
                self.assertFalse(result["publicationAuthorized"])
                self.assertEqual("FAIL",result["academicQA"])

    def test_malformed_failure_diagnostics_never_echo_private_answer_text(self):
        p=sample()
        p["activities"][0]["answerKey"]["options"][0]["id"]=["private textbook text"]
        self.save(p)
        result=self.audit()
        details=json.dumps(result,ensure_ascii=False)
        self.assertNotIn("private textbook text",details)
        self.assertIn("invalid answer structure (TypeError)",details)

    def test_ai_only_unsupported_pass_cannot_be_injected_as_json(self):
        with self.assertRaisesRegex(ValueError,"executable trusted"):
            self.audit(trusted_verifiers={"source_fidelity":"SUPPORTED"})
        def lie(a,ctx):
            return Finding("source_fidelity","PASS","source_verified",
                           "model-agreement","AI agrees",True)
        with self.assertRaisesRegex(ValueError,"independently verified"):
            self.audit(trusted_verifiers={"source_fidelity":lie})
    def test_valid_location_does_not_prove_scientific_meaning(self):
        p=sample()
        source={"sourceSha256":self.sha,"verifiedPages":[1],
                "sourceEvidence":"A controlled PDF passage with sufficient explanatory text.",
                "passageSha256":["a"*64]}
        anchor={"activityId":"mcq-one","sourceSha256":self.sha,
                "sourceAnchors":[{"activityId":"mcq-one","pageIndex":1,
                                  "quotedText":"A sufficiently long controlled scientific passage in PDF."}],
                "sourceEvidence":source["sourceEvidence"]}
        meta={"packageSha256":hashlib.sha256(self.pkg.read_bytes()).hexdigest(),
              "sourceSha256":self.sha,"packets":{"mcq-one":anchor}}
        with patch("app_generator.validation.academic_acceptance_matrix.verified_source_packet",
                   return_value=source):
            r=self.audit(source_packets=meta)
        self.assertTrue(r["activities"][0]["sourceLocationVerified"])
        self.assertEqual("REVIEW_REQUIRED",r["activities"][0]["academicQA"])
        self.assertEqual("AUTO_RETRY",r["activities"][0]["nextAction"])

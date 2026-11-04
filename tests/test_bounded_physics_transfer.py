"""Adversarial cross-version bounded-model transfer without real source files."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from app_generator.validation.bounded_physics_transfer import reverify_bounded_physics,digest

class PhysicsTransferTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        r=Path(self.tmp.name)
        self.old={"activities":[
            {"id":"mcq-a","type":"mcq","prompt":{"en":"Momentum"}},
            {"id":"int-b","type":"interactive","prompt":{"en":"Impulse","ms":"Impuls","zh":"??"}},
        ]}
        self.new=copy.deepcopy(self.old)
        self.new["activities"][1]["prompt"]["en"]="Net external impulse"
        self.old_file=r/"old.json"
        self.new_file=r/"new.json"
        self.old_file.write_text(json.dumps(self.old),encoding="utf-8")
        self.new_file.write_text(json.dumps(self.new),encoding="utf-8")
        self.pdf=r/"source.pdf";self.pdf.write_bytes(b"%PDF-1.4 controlled synthetic")
        self.sha=hashlib.sha256(self.pdf.read_bytes()).hexdigest()
        self.mfile=r/"mcq.json";self.ifile=r/"interactions.json"
        for p in (self.mfile,self.ifile):p.write_text("{}")
        self.v2=r/"v2.json";self.v2review=r/"v2-review.json";self.v3review=r/"v3-review.json"
        for p in (self.v2,self.v2review,self.v3review):p.write_text("{}")
        self.results=self.report()
    def report(self):
        return {
          "mcq":{
            "sourceSha256":self.sha,"packageCanonicalSha256":digest(self.old),
            "proofs":[{"activityId":"mcq-a","status":"BOUNDED_PROPOSITION_VERIFIED"}]},
          "interactive":{
            "sourceSha256":self.sha,"packageCanonicalSha256":digest(self.old),
            "results":[{"activityId":"int-b","status":"QUALIFIER_REVIEW_REQUIRED"}]},
          "v3":{
            "sourceSha256":self.sha,"candidateFileSha256":hashlib.sha256(self.new_file.read_bytes()).hexdigest(),
            "activityId":"int-b","boundedOptionsVerified":5,
            "optionReviewsRequired":0,"fullAcademicActivitiesPassed":0,
            "publicationAuthorized":False,
          }}
    def audit(self):
        return reverify_bounded_physics(
            prior_package=self.old_file,revised_package=self.new_file,
            source_pdf=self.pdf,source_sha256=self.sha,
            mcq_receipts=self.mfile,interaction_receipts=self.ifile,
            parent_v2_package=self.v2,parent_v2_review=self.v2review,
            revised_v3_review=self.v3review,
            mcq_auditor=lambda *a:self.results["mcq"],
            interaction_auditor=lambda *a:self.results["interactive"],
            revision_auditor=lambda *a:self.results["v3"])
    def test_unchanged_math_plus_fresh_corrected_item_no_full_pass(self):
        x=self.audit()
        self.assertEqual(2,x["boundedPropositionsVerified"])
        self.assertEqual(1,x["unchangedBoundedVerified"])
        self.assertEqual(1,x["revisedBoundedVerified"])
        self.assertEqual(["int-b"],x["changedActivityIds"])
        self.assertEqual(0,x["fullyAcademicallyApproved"])
        self.assertFalse(x["publicationAuthorized"])
        self.assertEqual("REVIEW_REQUIRED",x["academicQA"])
        self.assertTrue(all(not item["fullAcademicPass"] for item in x["activities"]))
    def test_second_unreviewed_content_edit_blocked(self):
        self.new["activities"][0]["prompt"]["en"]="Replaced unreviewed answer"
        self.new_file.write_text(json.dumps(self.new))
        self.results["v3"]["candidateFileSha256"]=hashlib.sha256(self.new_file.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError,"not exact independently reviewed correction"):
            self.audit()
    def test_source_pdf_or_receipt_mismatch_refused(self):
        self.pdf.write_bytes(b"%PDF-1.4 different")
        with self.assertRaisesRegex(ValueError,"textbook PDF"):
            self.audit()
        self.pdf.write_bytes(b"%PDF-1.4 controlled synthetic")
        self.results["mcq"]["packageCanonicalSha256"]="a"*64
        with self.assertRaisesRegex(ValueError,"identity mismatch"):
            self.audit()
    def test_original_unverified_model_rejected(self):
        self.results["mcq"]["proofs"][0]["status"]="REVIEW_REQUIRED"
        with self.assertRaisesRegex(ValueError,"unresolved original physics witness"):
            self.audit()
    def test_revised_counterexamples_missing_rejected(self):
        self.results["v3"]["boundedOptionsVerified"]=4
        with self.assertRaisesRegex(ValueError,"verification incomplete"):
            self.audit()
    def test_duplicate_or_missing_original_proof_refused(self):
        self.results["interactive"]["results"]=[]
        with self.assertRaisesRegex(ValueError,"coverage incomplete"):
            self.audit()

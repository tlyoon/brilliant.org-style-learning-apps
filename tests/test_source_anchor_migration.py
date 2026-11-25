"""Adversarial tests: source-location migration is not academic approval."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from app_generator.validation.source_anchor_migration import migrate_anchor_packets,digest

Q1="For an isolated collision, linear momentum is conserved in the absence of external impulse."
Q2="An ideal elastic collision also conserves total kinetic energy for both objects in the system."

class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.pdf=self.root/"source.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 synthetic controlled fixture")
        self.sha=hashlib.sha256(self.pdf.read_bytes()).hexdigest()
        self.prior={"activities":[
            {"id":"a","type":"mcq","prompt":{"en":"Original one"}},
            {"id":"b","type":"interactive","prompt":{"en":"Original two"}},
        ]}
        self.target=copy.deepcopy(self.prior)
        self.target["activities"][1]["prompt"]["en"]="Revised concept two"
        self.old=self.root/"prior.json"
        self.new=self.root/"target.json"
        self.old.write_text(json.dumps(self.prior))
        self.new.write_text(json.dumps(self.target))
        self.anchors=[{"activityId":"a","pageIndex":1,"quotedText":Q1},
                      {"activityId":"b","pageIndex":2,"quotedText":Q2}]
        self.r1=self.root/"receipt1.json"
        self.r2=self.root/"receipt2.json"
        self.write_receipts()
    def write_receipts(self):
        for p,anchor in ((self.r1,self.anchors[0]),(self.r2,self.anchors[1])):
            p.write_text(json.dumps({
                "sourceSha256":self.sha,
                "packageCanonicalSha256":digest(self.prior),
                "proofs":[{"activityId":anchor["activityId"],"anchor":anchor}],
            }))
    def run_migration(self,receipts=None,pages=None):
        return migrate_anchor_packets(
            pdf=self.pdf,source_sha256=self.sha,prior_package=self.old,
            target_package=self.new,
            prior_receipts=[self.r1,self.r2] if receipts is None else receipts,
            extractor=lambda _:(Q1,Q2) if pages is None else pages,
        )
    def test_exact_source_and_version_with_individual_changed_flag(self):
        x=self.run_migration()
        self.assertEqual(2,x["verifiedSourceLocations"])
        self.assertEqual(["b"],x["changedActivityIds"])
        self.assertFalse(x["sourceInterpretationVerified"])
        self.assertFalse(x["publicationAuthorized"])
        self.assertEqual("REVIEW_REQUIRED",x["academicQA"])
        self.assertEqual(["a","b"],sorted(x["packets"]))
        self.assertFalse(x["packets"]["a"]["activityContentChangedSincePrior"])
        self.assertTrue(x["packets"]["b"]["activityContentChangedSincePrior"])
        self.assertFalse(x["packets"]["b"]["sourceInterpretationVerified"])
    def test_stale_parent_canonical_and_source_refused(self):
        r=json.loads(self.r1.read_text())
        r["packageCanonicalSha256"]="a"*64
        self.r1.write_text(json.dumps(r))
        with self.assertRaisesRegex(ValueError,"prior proof"):
            self.run_migration()
        self.write_receipts()
        self.pdf.write_bytes(b"%PDF-1.4 modified")
        with self.assertRaisesRegex(ValueError,"PDF SHA256"):
            self.run_migration()
    def test_wrong_page_or_missing_source_text_rejected(self):
        with self.assertRaisesRegex(ValueError,"source passage"):
            self.run_migration(pages=(Q2,Q1))
        with self.assertRaisesRegex(ValueError,"source passage"):
            self.run_migration(pages=("no matching passage",Q2))
    def test_duplicate_or_missing_anchor_fails(self):
        with self.assertRaisesRegex(ValueError,"duplicate"):
            self.run_migration(receipts=[self.r1,self.r1,self.r2])
        with self.assertRaisesRegex(ValueError,"not all"):
            self.run_migration(receipts=[self.r1])
    def test_target_activity_set_mismatch_blocked(self):
        self.target["activities"].append({"id":"c","type":"mcq"})
        self.new.write_text(json.dumps(self.target))
        with self.assertRaisesRegex(ValueError,"activity set mismatch"):
            self.run_migration()
    def test_no_unsupported_ai_or_human_pass(self):
        x=self.run_migration()
        self.assertFalse(x["humanReviewRequired"])
        self.assertNotIn("AIReviewed",x)
        self.assertTrue(all(k["sourceLocationOnly"] for k in x["packets"].values()))

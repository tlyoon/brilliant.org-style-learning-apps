"""No-source synthetic tests for source-bound claim reconciliation."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.validation.autonomous_ai_review import canonical_digest
from app_generator.validation.source_bound_claim_audit import audit_source_bound_claim_run


class SourceBoundClaimTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.pdf=root/"original.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 synthetic no-source test")
        self.package=root/"package.json"
        self.activity={"id":"synthetic-a","prompt":{"en":"Synthetic no-source activity"}}
        self.package.write_text(json.dumps({"activities":[self.activity]}),encoding="utf-8")
        self.source_sha=sha256(self.pdf.read_bytes()).hexdigest()
        self.package_sha=sha256(self.package.read_bytes()).hexdigest()
        self.context={"activityId":"synthetic-a","sourceSha256":self.source_sha,
                      "verifiedPages":[2],"sourceEvidence":"synthetic source-only context",
                      "passageSha256":["b"*64]}
        self.packet=root/"packets.json"
        self.anchors=[{"activityId":"synthetic-a","pageIndex":2,"quotedText":"synthetic"}]
        self.packet.write_text(json.dumps({
            "packageSha256":self.package_sha,"sourceSha256":self.source_sha,
            "packets":{"synthetic-a":{"sourceAnchors":self.anchors,
                                     "sourceEvidence":self.context["sourceEvidence"],
                                     "passageSha256":self.context["passageSha256"],
                                     "verifiedPages":[2]}}
        }),encoding="utf-8")
        self.claims=root/"claims"
        self.claims.mkdir()
        self.args=dict(package_file=self.package,pdf_file=self.pdf,
                       packets_file=self.packet,claims_dir=self.claims,
                       activity_id="synthetic-a",claim_prefix="fresh-synthetic")
        self.stage={"activityId":"synthetic-a",
                    "activityHash":canonical_digest(self.activity),
                    "packageHash":self.package_sha,"sourceHash":self.source_sha,
                    "sourceContextHash":canonical_digest(self.context),
                    "roleIndex":0,"gate":"source_fidelity",
                    "promptHash":"a"*64,"state":"IN_FLIGHT"}

    def review(self):
        with patch("app_generator.validation.source_bound_claim_audit.verified_source_packet",
                   return_value=self.context) as verification:
            result=audit_source_bound_claim_run(**self.args)
        verification.assert_called_once()
        return result

    def test_exact_source_package_packet_and_claim_receipt_without_pass(self):
        (self.claims/"fresh-synthetic-source-fidelity-0.json").write_text(
            json.dumps(self.stage),encoding="utf-8")
        result=self.review()
        self.assertEqual(1,result["stateCounts"]["IN_FLIGHT"])
        self.assertEqual(9,result["stateCounts"]["MISSING"])
        self.assertEqual(1,result["sourcePacketRosterCount"])
        self.assertEqual(1,result["sourcePacketReverifiedCount"])
        self.assertTrue(result["originalSourcePassageReverified"])
        self.assertFalse(result["formalAcademicPASS"])
        self.assertFalse(result["publicationAuthorized"])

    def test_changed_package_fails_before_claim_reconciliation(self):
        self.package.write_text(json.dumps({"activities":[self.activity],"extra":1}),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"SHA mismatch"):
            self.review()

    def test_changed_original_pdf_fails_closed(self):
        self.pdf.write_bytes(b"%PDF-1.4 synthetic changed")
        with self.assertRaisesRegex(ValueError,"SHA mismatch"):
            self.review()

    def test_false_source_page_identity_fails_closed(self):
        doc=json.loads(self.packet.read_text(encoding="utf-8"))
        doc["packets"]["synthetic-a"]["verifiedPages"]=[3]
        self.packet.write_text(json.dumps(doc),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"independently re-extracted"):
            self.review()

    def test_changed_immutable_claim_identity_fails_closed(self):
        mismatch={**self.stage,"sourceContextHash":"c"*64}
        (self.claims/"fresh-synthetic-source-fidelity-0.json").write_text(
            json.dumps(mismatch),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"mismatched immutable claim"):
            self.review()


if __name__=="__main__":
    unittest.main()

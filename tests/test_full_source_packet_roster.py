"""No-source exact roster provenance integrity tests."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster


class FullRosterTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root=Path(tmp.name)
        self.pdf=root/"source.pdf"
        self.pdf.write_bytes(b"%PDF-1.7 synthetic")
        self.pkg=root/"package.json"
        self.pkg.write_text(json.dumps({"activities":[{"id":"safe-a"},{"id":"safe-b"}]}),encoding="utf-8")
        self.mft=root/"packets.json"
        self.source_sha=sha256(self.pdf.read_bytes()).hexdigest()
        self.package_sha=sha256(self.pkg.read_bytes()).hexdigest()
        self.verified={}
        for aid in ("safe-a","safe-b"):
            self.verified[aid]={"activityId":aid,"sourceEvidence":"SYNTHETIC SOURCE TEXT",
                                "sourceAnchors":[{"activityId":aid,"quotedText":"synthetic","pageIndex":1}],
                                "passageSha256":["a"*64],"verifiedPages":[1],
                                "passageCount":1,"sourceSha256":self.source_sha}
        self.manifest={"sourceSha256":self.source_sha,"packageSha256":self.package_sha,
                       "packets":json.loads(json.dumps(self.verified))}
        self.write()
        self.args=dict(package_file=self.pkg,source_pdf=self.pdf,
                       packets_file=self.mft,expected_count=2)

    def write(self):
        self.mft.write_text(json.dumps(self.manifest),encoding="utf-8")

    def verify(self):
        with patch("app_generator.validation.full_source_packet_roster.source_packets_for_activities",
                   return_value=self.verified) as factory:
            result=verify_full_source_packet_roster(**self.args)
            factory.assert_called_once()
        return result

    def test_full_roster_all_records_reverified_without_semantic_pass(self):
        result=self.verify()
        self.assertEqual(2,result["newlyReverifiedSourceActivities"])
        self.assertEqual(2,result["newlyReverifiedSourcePassages"])
        self.assertFalse(result["sourceInterpretationVerified"])
        self.assertFalse(result["formalAcademicPASS"])
        self.assertFalse(result["publicationAuthorized"])
        self.assertNotIn("SYNTHETIC SOURCE TEXT",json.dumps(result))

    def test_missing_or_extra_activity_packet_fails_closed(self):
        del self.manifest["packets"]["safe-b"]
        self.write()
        with self.assertRaisesRegex(ValueError,"roster"):
            self.verify()

    def test_fake_pdf_or_changed_package_hash_fails_before_extraction(self):
        self.pdf.write_bytes(b"BAD synthetic")
        with self.assertRaisesRegex(ValueError,"hash"):
            self.verify()
        self.pdf.write_bytes(b"%PDF-1.7 synthetic")
        self.pkg.write_text('{"activities":[{"id":"safe-a"}]}',encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"hash"):
            self.verify()

    def test_stale_verified_page_or_quoted_passage_rejected(self):
        self.manifest["packets"]["safe-a"]={**self.verified["safe-a"],"verifiedPages":[4]}
        self.write()
        with self.assertRaisesRegex(ValueError,"passage/physical page"):
            self.verify()
        self.manifest["packets"]["safe-a"]={**self.verified["safe-a"],
                                           "sourceEvidence":"altered private material"}
        self.write()
        with self.assertRaisesRegex(ValueError,"passage/physical page"):
            self.verify()

    def test_invalid_activity_count_fails_before_extraction(self):
        with self.assertRaisesRegex(ValueError,"bounded"):
            verify_full_source_packet_roster(**{**self.args,"expected_count":True})
        with self.assertRaisesRegex(ValueError,"count"):
            verify_full_source_packet_roster(**{**self.args,"expected_count":3})


if __name__=="__main__":
    unittest.main()

"""Source-free academic claim coverage matrix tests."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.validation.full_academic_claim_coverage import audit_academic_claim_coverage


class ClaimCoverageTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root=Path(tmp.name)
        self.pkg=root/"package.json"
        self.pkg.write_text('{"activities":[{"id":"a"},{"id":"b"}]}',encoding="utf-8")
        self.pdf=root/"source.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 SYNTHETIC ONLY")
        self.packets=root/"packets.json"
        self.packets.write_text("{}",encoding="utf-8")
        self.runs=root/"runs.json"
        self.source={"packageSha256":sha256(self.pkg.read_bytes()).hexdigest(),
                     "sourceSha256":sha256(self.pdf.read_bytes()).hexdigest(),
                     "newlyReverifiedSourceActivities":2,
                     "newlyReverifiedSourcePassages":2,
                     "activityEvidence":[{"activityId":"a"},{"activityId":"b"}]}
        self.args=dict(package_file=self.pkg,source_pdf=self.pdf,packets_file=self.packets,
                       reviewer_runs_file=self.runs,expected_count=2)
        self.write([])

    def write(self,entries):
        self.runs.write_text(json.dumps({
            "packageSha256":self.source["packageSha256"],
            "sourceSha256":self.source["sourceSha256"],"runs":entries}),encoding="utf-8")

    def call(self,result=None):
        with patch("app_generator.validation.full_academic_claim_coverage.verify_full_source_packet_roster",
                   return_value=self.source):
            with patch("app_generator.validation.full_academic_claim_coverage.audit_source_bound_claim_run",
                       return_value=result) as reviewer:
                output=audit_academic_claim_coverage(**self.args)
        return output,reviewer

    def test_fully_unsubmitted_source_verified_is_not_academic_pass(self):
        result,reviewer=self.call()
        self.assertEqual(20,result["claimStates"]["NOT_SUBMITTED"])
        self.assertEqual(0,result["reviewedRunCount"])
        self.assertEqual(0,result["formalAcademicPASSCount"])
        self.assertFalse(result["publicationAuthorized"])
        reviewer.assert_not_called()

    def test_one_real_review_five_complete_three_ambiguous_two_skipped(self):
        self.write([{"activityId":"a","claimsDir":"/private/test","claimPrefix":"v5-a"}])
        record={"sourcePacketReverifiedCount":1,"publicationAuthorized":False,
                "stateCounts":{"COMPLETE":5,"AMBIGUOUS":3,"SKIPPED_UNSENT":2}}
        result,reviewer=self.call(record)
        self.assertEqual(1,reviewer.call_count)
        self.assertEqual(20,result["claimRoleSlots"])
        self.assertEqual(10,result["claimStates"]["NOT_SUBMITTED"])
        self.assertEqual(5,result["claimStates"]["COMPLETE"])
        self.assertEqual(3,result["claimStates"]["AMBIGUOUS"])
        self.assertEqual(2,result["claimStates"]["SKIPPED_UNSENT"])
        self.assertEqual(0,result["formalAcademicPASSCount"])

    def test_duplicate_run_rejected_before_remote_request(self):
        row={"activityId":"a","claimsDir":"/private/test","claimPrefix":"v5-a"}
        self.write([row,row])
        with self.assertRaisesRegex(ValueError,"unique"):
            self.call()

    def test_manifest_does_not_match_exact_package(self):
        self.write([])
        doc=json.loads(self.runs.read_text(encoding="utf-8"))
        doc["packageSha256"]="b"*64
        self.runs.write_text(json.dumps(doc),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"not bound"):
            self.call()

    def test_bogus_approval_in_source_bound_receipt_rejected(self):
        self.write([{"activityId":"a","claimsDir":"/private/test","claimPrefix":"v5-a"}])
        with self.assertRaisesRegex(ValueError,"not bound"):
            self.call({"sourcePacketReverifiedCount":1,"publicationAuthorized":True,
                       "stateCounts":{"COMPLETE":10}})


if __name__=="__main__":
    unittest.main()

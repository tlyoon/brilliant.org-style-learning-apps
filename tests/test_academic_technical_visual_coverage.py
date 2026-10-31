"""Synthetic tests: screenshot integrity cannot become scientific PASS."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.validation.academic_technical_visual_coverage import audit_source_bound_visual_readiness


class VisualCoverageTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        root=Path(t.name)
        self.pkg=root/"package.json"
        self.pkg.write_text(json.dumps({"activities":[{"id":"one","visualSpec":{"type":"vector"}},
                                                       {"id":"two"}]}),encoding="utf-8")
        self.pdf=root/"source.pdf"
        self.pdf.write_bytes(b"%PDF-1.7 source-free test")
        self.psha=sha256(self.pkg.read_bytes()).hexdigest()
        self.ssha=sha256(self.pdf.read_bytes()).hexdigest()
        self.args=dict(package_file=self.pkg,source_pdf=self.pdf,
                       browser_evidence_dir=root,
                       academic_queue={
                           "status":"SOURCE_BOUND_AUTONOMOUS_ACADEMIC_REVIEW_QUEUE",
                           "sourceSha256":self.ssha,"packageSha256":self.psha,
                           "activityCount":2,"publicationAuthorized":False,
                           "activities":[
                               {"activityId":"one","priority":"INDEPENDENT_MULTILINGUAL_SEMANTIC_REVIEW",
                                "publicationAuthorized":False},
                               {"activityId":"two","priority":"SUBMIT_FRESH_INDEPENDENT_REVIEW_WHEN_AUTHORIZED",
                                "publicationAuthorized":False},
                           ]})
        self.visual_receipt={
            "packageSha256":self.psha,"sourceSha256":self.ssha,
            "pixelQualityReviewed":False,"academicAccuracyReviewed":False,
            "publicationAuthorized":False,"technicalPixelIntegrityChecked":True,
            "sourceIdentityStatus":"SOURCE_BOUND_BROWSER_VISUAL_CAPTURE_VERIFIED",
            "checks":[{"activityId":"one","locale":lang,"viewportWidth":w}
                      for lang in ("en","ms","zh") for w in (390,1280)]}

    def check(self):
        with patch("app_generator.validation.academic_technical_visual_coverage.audit_private_visual_pixel_integrity",
                   return_value=self.visual_receipt):
            return audit_source_bound_visual_readiness(**self.args)

    def test_complete_png_capture_does_not_grant_visual_scientific_pass(self):
        report=self.check()
        self.assertEqual(6,report["screenshotCapturesVerified"])
        self.assertEqual(1,report["visualActivities"])
        self.assertFalse(report["scientificVisualSemanticsVerified"])
        self.assertFalse(report["publicationAuthorized"])
        self.assertEqual(0,report["formalAcademicPASSCount"])
        self.assertFalse(report["activities"][1]["visualSpecPresent"])

    def test_missing_chinese_mobile_screenshot_fail_closed(self):
        self.visual_receipt["checks"].pop()
        with self.assertRaisesRegex(ValueError,"full locale"):
            self.check()

    def test_duplicate_screenshot_fail_closed(self):
        self.visual_receipt["checks"][-1]=self.visual_receipt["checks"][0]
        with self.assertRaisesRegex(ValueError,"full locale"):
            self.check()

    def test_falsely_approved_screenshot_receipt_rejected(self):
        self.visual_receipt["academicAccuracyReviewed"]=True
        with self.assertRaisesRegex(ValueError,"scientific approval"):
            self.check()

    def test_changed_original_source_package_and_queue_rejected(self):
        self.pdf.write_bytes(b"%PDF-1.7 MODIFIED")
        with self.assertRaisesRegex(ValueError,"controlled"):
            self.check()
        self.pdf.write_bytes(b"%PDF-1.7 source-free test")
        self.args["academic_queue"]["activities"][1]["activityId"]="one"
        with self.assertRaisesRegex(ValueError,"identities"):
            self.check()


if __name__=="__main__":
    unittest.main()

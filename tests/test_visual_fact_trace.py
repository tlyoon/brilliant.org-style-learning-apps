"""Synthetic visual fact/provenance adversarial tests; no private source."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.validation.visual_fact_trace import FACTS,audit_source_visual_fact_trace
from tests.test_bounded_diagram_physics import cart,spring


class VisualFactTraceTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        p=Path(t.name)
        self.pkg=p/"package.json"
        self.source=p/"original.pdf"
        self.source.write_bytes(b"%PDF-1.4 synthetic")
        self.packets=p/"packets.json"
        self.packets.write_text("{}")
        self.pix=p/"pixel.json"
        self.activities=[]
        for aid,(_,facts) in FACTS.items():
            act=spring() if aid=="mcq-spring-collision-intermediate" else cart(aid)
            act["visualSpec"]["grounding"]=[
                {"factId":fid,"origin":origin,"appliesTo":list(references)}
                for fid,origin,references in facts]
            self.activities.append(act)
        self.activities.extend({"id":"other-"+str(i)} for i in range(13))
        self.save()

    def save(self):
        self.pkg.write_text(json.dumps({"activities":self.activities}),encoding="utf-8")
        self.pixel={
            "packageSha256":sha256(self.pkg.read_bytes()).hexdigest(),
            "sourceSha256":sha256(self.source.read_bytes()).hexdigest(),
            "publicationAuthorized":False,
            "technicalPixelIntegrityChecked":True,
            "academicAccuracyReviewed":False,
            "pixelQualityReviewed":False,"screenCapturesChecked":30,
            "checks":[{"activityId":aid,"locale":loc,"viewportWidth":width,
                       "distinctSampleColors":40,"nonwhitePixelPercent":30,
                       "width":420,"height":200}
                      for aid in FACTS for loc in ("en","ms","zh") for width in (390,1280)],
        }
        self.pix.write_text(json.dumps(self.pixel),encoding="utf-8")
        self.receipt={
            "newlyReverifiedSourceActivities":18,
            "packageSha256":sha256(self.pkg.read_bytes()).hexdigest(),
            "sourceSha256":sha256(self.source.read_bytes()).hexdigest(),
            "publicationAuthorized":False,
            "activityEvidence":[{"activityId":a["id"],
                "verifiedPhysicalPdfPages":[FACTS[a["id"]][0]]
                if a["id"] in FACTS else [1]} for a in self.activities]
        }

    def audit(self):
        with patch(
            "app_generator.validation.visual_fact_trace.verify_full_source_packet_roster",
            return_value=self.receipt,
        ) as verifier:
            result=audit_source_visual_fact_trace(
                package_file=self.pkg,source_pdf=self.source,
                packets_file=self.packets,historical_pixel_receipt=self.pix)
            verifier.assert_called_once()
        return result

    def test_complete_five_diagram_fact_and_capture_roster(self):
        q=self.audit()
        self.assertEqual(18,q["allOriginalSourceActivitiesReverified"])
        self.assertEqual(5,q["boundedVisualPhysicsModelsRechecked"])
        self.assertEqual(11,q["declaredFactIdentifiersCrossChecked"])
        self.assertEqual(1,q["declaredPedagogicalSimplifications"])
        self.assertEqual(30,q["historicalTechnicalScreenshotReceiptsCrossChecked"])
        self.assertFalse(q["historicalScreenshotPixelsRehashedInThisRun"])
        self.assertFalse(q["sourcePassageSemanticsApproved"])
        self.assertFalse(q["figurePixelScientificMeaningApproved"])
        self.assertEqual(0,q["formalAcademicPASS"])
        self.assertFalse(q["publicationAuthorized"])

    def test_wrong_source_fact_origin_cannot_pass(self):
        a=self.activities[0]
        a["visualSpec"]["grounding"][0]["origin"]="pedagogical_simplification"
        self.save()
        with self.assertRaisesRegex(ValueError,"provenance changed"):self.audit()

    def test_undeclared_figure_fact_reference_cannot_pass(self):
        self.activities[0]["visualSpec"]["grounding"][0]["appliesTo"]=["other-item"]
        self.save()
        with self.assertRaises(ValueError):self.audit()

    def test_source_page_drift_blocked(self):
        self.receipt["activityEvidence"][0]["verifiedPhysicalPdfPages"]=[8]
        with self.assertRaisesRegex(ValueError,"source page"):self.audit()

    def test_diagram_direction_mismatch_fails_bounded_physics(self):
        v=self.activities[0]["visualSpec"]["vectors"]
        v[0]["direction"]="left"
        self.save()
        with self.assertRaisesRegex(ValueError,"arrows"):self.audit()

    def test_historical_locale_or_size_duplicate_fails(self):
        self.pixel["checks"][1]["locale"]="en"
        self.pixel["checks"][1]["viewportWidth"]=390
        self.pix.write_text(json.dumps(self.pixel),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"duplicate historical"):self.audit()

    def test_stale_screenshot_package_or_inappropriate_pass_rejected(self):
        self.pixel["packageSha256"]="f"*64
        self.pix.write_text(json.dumps(self.pixel),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"identity/limitations"):self.audit()
        self.pixel["packageSha256"]=self.receipt["packageSha256"]
        self.pixel["academicAccuracyReviewed"]=True
        self.pix.write_text(json.dumps(self.pixel),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"identity/limitations"):self.audit()


if __name__=="__main__":
    unittest.main()

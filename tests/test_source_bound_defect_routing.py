"""Synthetic adversarial tests; no private textbook or provider requests."""
from __future__ import annotations
import copy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from app_generator.validation.bounded_physics_transfer import digest
from app_generator.validation.impulse_qualifier_repair import ACTIVITY_ID
from app_generator.validation.impulse_v3 import V3_LABEL
from app_generator.validation.impulse_v3_audit import ITEM_ID
from app_generator.validation.source_bound_defect_routing import route_source_bound_defect


class DefectRoutingTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        root=Path(t.name)
        self.package=root/"package.json"
        self.pdf=root/"source.pdf"
        self.dossier=root/"dossier.json"
        self.pdf.write_bytes(b"%PDF-1.4 synthetic source")
        self.activity={"id":ACTIVITY_ID,"type":"interactive",
            "interactionMode":"selection","interaction":{"items":[
                {"id":ITEM_ID,"label":copy.deepcopy(V3_LABEL)},
                {"id":"other","label":{"en":"X","ms":"Y","zh":"Z"}}],
                "correctSelections":[ITEM_ID]}}
        self.save()

    def save(self):
        self.package.write_text(json.dumps({"activities":[self.activity]},ensure_ascii=False),encoding="utf-8")
        self.package_sha=sha256(self.package.read_bytes()).hexdigest()
        self.pdf_sha=sha256(self.pdf.read_bytes()).hexdigest()
        self.data={"packageSha256":self.package_sha,"sourceSha256":self.pdf_sha,
            "activityId":ACTIVITY_ID,"activitySha256":digest(self.activity),
            "sourceLocationVerifiedInMatrix":True,
            "boundedPhysicsReceiptMatched":True,"publicationAuthorized":False,
            "fullAcademicPass":False,"academicQA":"REVIEW_REQUIRED"}
        self.dossier.write_text(json.dumps(self.data))

    def route(self):
        return route_source_bound_defect(package_file=self.package,
            source_pdf=self.pdf,dossier_file=self.dossier,
            expected_package_sha256=self.package_sha,
            expected_source_sha256=self.pdf_sha)

    def test_correct_original_has_only_independent_review_next(self):
        x=self.route()
        self.assertEqual("AUTO_INDEPENDENT_SEMANTIC_VISUAL_REVIEW",x["nextAction"])
        self.assertEqual([],x["objections"])
        self.assertFalse(x["publicationAuthorized"])
        self.assertFalse(x["fullSemanticEquivalenceVerified"])

    def test_detect_contradiction_as_auto_repair_without_unsafe_pass(self):
        additions={
            "en":" Nevertheless, each external force must be small.",
            "ms":" Walau bagaimanapun, setiap daya luar mesti kecil.",
            "zh":"\u4f46\u662f\u6bcf\u4e00\u4e2a\u5916\u529b\u90fd\u5fc5\u987b\u5f88\u5c0f\u3002",
        }
        for lang,text in additions.items():
            with self.subTest(lang=lang):
                self.activity["interaction"]["items"][0]["label"][lang]+=text
                self.save()
                report=self.route()
                self.assertEqual("AUTO_REPAIR",report["nextAction"])
                self.assertIn(lang,[x["language"] for x in report["objections"]])
                self.assertFalse(report["publicationAuthorized"])
                self.assertFalse(report["fullSemanticEquivalenceVerified"])
                self.activity["interaction"]["items"][0]["label"]=copy.deepcopy(V3_LABEL)

    def test_missing_marker_is_source_check_not_unearned_repair(self):
        self.activity["interaction"]["items"][0]["label"]["en"]="Short unsupported statement"
        self.save()
        report=self.route()
        self.assertEqual("AUTO_SOURCE_CHECK",report["nextAction"])
        self.assertEqual(["en"],report["unresolvedLanguages"])

    def test_tampering_with_receipts_source_or_package_blocks(self):
        self.data["activitySha256"]="0"*64
        self.dossier.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError,"dossier"):
            self.route()
        self.save()
        self.pdf.write_bytes(b"%PDF-1.4 altered")
        with self.assertRaisesRegex(ValueError,"differs"):
            self.route()
        self.pdf.write_bytes(b"%PDF-1.4 synthetic source")
        self.activity["interaction"]["correctSelections"]=[]
        self.package.write_text(json.dumps({"activities":[self.activity]}),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"differs"):
            self.route()

    def test_previously_approved_or_missing_source_evidence_rejected(self):
        for change in (
            {"fullAcademicPass":True},
            {"publicationAuthorized":True},
            {"sourceLocationVerifiedInMatrix":False},
            {"boundedPhysicsReceiptMatched":False},
            {"academicQA":"PASS"},
        ):
            self.save()
            self.data.update(change)
            self.dossier.write_text(json.dumps(self.data))
            with self.assertRaises(ValueError):
                self.route()


if __name__ == "__main__":
    unittest.main()
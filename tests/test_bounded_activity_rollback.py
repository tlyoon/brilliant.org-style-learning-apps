"""Bounded synthetic scientific-defect -> rollback -> recheck, no AI model."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from app_generator.validation.bounded_physics_transfer import digest
from app_generator.validation.impulse_qualifier_repair import ACTIVITY_ID
from app_generator.validation.impulse_v3 import V3_LABEL
from app_generator.validation.impulse_v3_audit import ITEM_ID
from app_generator.validation.bounded_activity_rollback import restore_known_bounded_version


class BoundedRollbackTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.r=Path(t.name)
        self.base=self.r/"base.json"
        self.candidate=self.r/"changed.json"
        self.pdf=self.r/"source.pdf"
        self.dossier=self.r/"dossier.json"
        self.out=self.r/"restored"
        self.pdf.write_bytes(b"%PDF-1.4 synthetic")
        self.source_sha=sha256(self.pdf.read_bytes()).hexdigest()
        self.pkg={"activities":[{"id":ACTIVITY_ID,"type":"interactive",
            "interactionMode":"selection","interaction":{
                "items":[{"id":ITEM_ID,"label":deepcopy(V3_LABEL)},
                         {"id":"other","label":{"en":"x","ms":"y","zh":"z"}}],
                "correctSelections":[ITEM_ID]}}]}
        self.base.write_text(json.dumps(self.pkg,ensure_ascii=False),encoding="utf-8")
        self.baseline_sha=sha256(self.base.read_bytes()).hexdigest()
        a=self.pkg["activities"][0]
        self.dossier.write_text(json.dumps({
            "packageSha256":self.baseline_sha,
            "sourceSha256":self.source_sha,
            "activityId":ACTIVITY_ID,
            "activitySha256":digest(a),
            "sourceLocationVerifiedInMatrix":True,
            "boundedPhysicsReceiptMatched":True,
            "publicationAuthorized":False,
            "fullAcademicPass":False,
            "academicQA":"REVIEW_REQUIRED",
        }),encoding="utf-8")
        self.mutated=deepcopy(self.pkg)
        self.mutated["activities"][0]["interaction"]["items"][0]["label"]["en"]+=(
            " Nevertheless, each external force must be small.")
        self.save_mutated()

    def save_mutated(self):
        self.candidate.write_text(json.dumps(self.mutated,ensure_ascii=False),
                                  encoding="utf-8")

    def rollback(self):
        return restore_known_bounded_version(
            candidate_file=self.candidate,baseline_file=self.base,
            source_pdf=self.pdf,baseline_dossier_file=self.dossier,
            expected_baseline_sha256=self.baseline_sha,
            expected_source_sha256=self.source_sha,
            private_output_dir=self.out,
        )

    def test_scientific_contradiction_restored_to_exact_bounded_version(self):
        report=self.rollback()
        self.assertEqual("EXACT_KNOWN_BOUNDED_BASELINE",report["restoration"])
        self.assertEqual("AUTO_INDEPENDENT_SEMANTIC_VISUAL_REVIEW",report["nextAction"])
        self.assertEqual(self.base.read_bytes(),(self.out/"restored-package.json").read_bytes())
        self.assertEqual(self.baseline_sha,report["restoredPackageSha256"])
        self.assertEqual("en",report["detectedContradictions"][0]["language"])
        self.assertFalse(report["fullAcademicPass"])
        self.assertFalse(report["publicationAuthorized"])
        with self.assertRaises(ValueError):
            self.rollback()

    def test_unrelated_edits_refused(self):
        for mutation in (
            lambda p:p["activities"][0]["interaction"]["correctSelections"].clear(),
            lambda p:p["activities"].append({"id":"another","type":"mcq"}),
            lambda p:p["activities"][0]["interaction"]["items"][1].update(id="changed"),
        ):
            self.mutated=deepcopy(self.pkg)
            self.mutated["activities"][0]["interaction"]["items"][0]["label"]["en"]+=(
                " Nevertheless, each external force must be small.")
            mutation(self.mutated)
            self.save_mutated()
            with self.assertRaisesRegex(ValueError,"unrelated"):
                self.rollback()

    def test_rephrasing_and_missing_contradiction_not_automatically_fixed(self):
        for changed in ("Different unsupported claim",V3_LABEL["en"]+" Unknown extra notes"):
            self.mutated=deepcopy(self.pkg)
            self.mutated["activities"][0]["interaction"]["items"][0]["label"]["en"]=changed
            self.save_mutated()
            with self.assertRaises(ValueError):
                self.rollback()

    def test_stale_source_baseline_dossier_rejected_without_writing(self):
        self.dossier.write_text(json.dumps({"activityId":ACTIVITY_ID}),encoding="utf-8")
        with self.assertRaises(ValueError):
            self.rollback()
        self.assertFalse(self.out.exists())

    def test_multiple_languages_append_only_restored(self):
        self.mutated["activities"][0]["interaction"]["items"][0]["label"]["ms"]+=(
            " Walau bagaimanapun, setiap daya luar mesti kecil.")
        self.mutated["activities"][0]["interaction"]["items"][0]["label"]["zh"]+=(
            "\u4f46\u662f\u6bcf\u4e00\u4e2a\u5916\u529b\u90fd\u5fc5\u987b\u5f88\u5c0f\u3002")
        self.save_mutated()
        result=self.rollback()
        self.assertEqual({"en","ms","zh"},
            {entry["language"] for entry in result["detectedContradictions"]})


if __name__=="__main__":
    unittest.main()
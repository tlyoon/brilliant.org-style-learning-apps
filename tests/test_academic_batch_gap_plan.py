"""Synthetic batch review planning with exact activity/source/physics bindings."""
from __future__ import annotations
import copy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from app_generator.validation.academic_batch_gap_plan import plan_exact_academic_batch
from app_generator.validation.bounded_physics_transfer import digest
from app_generator.validation.academic_qa import REQUIRED
from app_generator.validation.impulse_qualifier_repair import ACTIVITY_ID


class BatchPlanTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        r=Path(t.name)
        self.pkg=r/"private-package.json"
        self.pdf=r/"private-source.pdf"
        self.m=r/"matrix.json"
        self.p=r/"physics.json"
        self.pdf.write_bytes(b"%PDF-1.4 synthetic")
        self.source_sha=sha256(self.pdf.read_bytes()).hexdigest()
        self.activities=[
            {"id":"mcq-first","type":"mcq","prompt":{"en":"a"}},
            {"id":ACTIVITY_ID,"type":"interactive","prompt":{"en":"b"}},
        ]
        self.save()

    def save(self):
        pack={"activities":self.activities}
        self.pkg.write_text(json.dumps(pack,ensure_ascii=False),encoding="utf-8")
        sha=sha256(self.pkg.read_bytes()).hexdigest()
        self.matrix={
            "packageSha256":sha,"sourceSha256":self.source_sha,
            "activityCount":len(self.activities),
            "publicationAuthorized":False,
            "counts":{"PASS":0,"FAIL":0,"REVIEW_REQUIRED":len(self.activities)},
            "activities":[{
                "activityId":a["id"],"activitySha256":digest(a),
                "academicQA":"REVIEW_REQUIRED",
                "gates":{gate:"REVIEW_REQUIRED" for gate in REQUIRED},
                "sourceLocationVerified":True,"sourcePages":[3],
                "publicationAuthorized":False,
            } for a in self.activities],
        }
        self.physics={
            "revisedPackageSha256":sha,
            "revisedPackageCanonicalSha256":digest(pack),
            "sourceSha256":self.source_sha,
            "activityCount":len(self.activities),
            "boundedPropositionsVerified":len(self.activities),
            "publicationAuthorized":False,"fullyAcademicallyApproved":0,
            "activities":[{
                "activityId":a["id"],"currentActivitySha256":digest(a),
                "status":"REVISED_BOUNDED_PHYSICS_VERIFIED",
                "fullAcademicPass":False,"publicationAuthorized":False,
            } for a in self.activities],
        }
        self.flush()

    def flush(self):
        self.m.write_text(json.dumps(self.matrix),encoding="utf-8")
        self.p.write_text(json.dumps(self.physics),encoding="utf-8")

    def plan(self):
        return plan_exact_academic_batch(
            package_file=self.pkg,source_pdf=self.pdf,
            matrix_file=self.m,physics_file=self.p,
            expected_count=2,
        )

    def test_all_activities_reconciled_with_pilot_first(self):
        out=self.plan()
        self.assertEqual(2,out["verifiedSourceLocationReceipts"])
        self.assertEqual(2,out["matchedBoundedPhysicsReceipts"])
        self.assertEqual(ACTIVITY_ID,out["prioritizedActivities"][0]["activityId"])
        self.assertEqual(0,out["fullAcademicPassCount"])
        self.assertEqual(2,out["academicCounts"]["REVIEW_REQUIRED"])
        self.assertEqual(2,out["nextActionCounts"]["AUTO_INDEPENDENT_SEMANTIC_VISUAL_REVIEW"])
        self.assertFalse(out["publicationAuthorized"])
        self.assertFalse(out["completeTrilingualSemanticsVerified"])

    def test_second_activity_tampered_is_blocked(self):
        self.matrix["activities"][0]["activitySha256"]="f"*64
        self.flush()
        with self.assertRaisesRegex(ValueError,"digest"):
            self.plan()

    def test_missing_source_receipt_fails_for_whole_batch(self):
        self.matrix["activities"].pop()
        self.flush()
        with self.assertRaises(ValueError):
            self.plan()

    def test_forged_full_pass_never_unlocked(self):
        self.matrix["activities"][1]["academicQA"]="PASS"
        self.matrix["counts"]={"PASS":1,"FAIL":0,"REVIEW_REQUIRED":1}
        self.flush()
        with self.assertRaises(ValueError):
            self.plan()

    def test_expected_count_and_duplicate_id_enforced(self):
        with self.assertRaisesRegex(ValueError,"count"):
            plan_exact_academic_batch(
                package_file=self.pkg,source_pdf=self.pdf,
                matrix_file=self.m,physics_file=self.p,expected_count=18)
        self.activities[0]["id"]=ACTIVITY_ID
        self.save()
        with self.assertRaisesRegex(ValueError,"duplicate"):
            self.plan()


if __name__=="__main__":
    unittest.main()
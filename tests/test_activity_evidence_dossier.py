"""Untrusted/private evidence must not be silently promoted into academic approval."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from app_generator.validation.activity_evidence_dossier import reconcile_activity_evidence
from app_generator.validation.bounded_physics_transfer import digest
from app_generator.validation.academic_qa import REQUIRED


class EvidenceDossierTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.pkg = root/"package.json"
        self.pdf = root/"source.pdf"
        self.matrix = root/"matrix.json"
        self.physics = root/"physics.json"
        self.pdf.write_bytes(b"%PDF-1.4 synthetic")
        self.activities = [
            {"id":"a","type":"interactive","interaction":{"items":[{"id":"x"}]}},
            {"id":"b","type":"mcq","answerKey":{"correct":"y"}},
        ]
        self.write_evidence()

    def write_evidence(self, *, source_present=True):
        package = {"activities":self.activities}
        self.pkg.write_text(json.dumps(package),encoding="utf-8")
        sha=hashlib.sha256(self.pkg.read_bytes()).hexdigest()
        pdf_sha=hashlib.sha256(self.pdf.read_bytes()).hexdigest()
        self.m = {"packageSha256":sha,"sourceSha256":pdf_sha,"activityCount":2,
            "counts":{"PASS":0,"FAIL":0,"REVIEW_REQUIRED":2},
            "publicationAuthorized":False,"activities":[{
                "activityId":x["id"],"activitySha256":digest(x),
                "academicQA":"REVIEW_REQUIRED",
                "gates":{g:"REVIEW_REQUIRED" for g in REQUIRED},
                "sourceLocationVerified":source_present,
                "sourcePages":[2] if source_present else [],
                "answerStructureErrors":[],"visualContractErrorCount":0,
                "publicationAuthorized":False,
            } for x in self.activities]}
        self.p = {"revisedPackageSha256":sha,
            "revisedPackageCanonicalSha256":digest(package),
            "sourceSha256":pdf_sha,"activityCount":2,"boundedPropositionsVerified":2,
            "fullyAcademicallyApproved":0,"publicationAuthorized":False,
            "activities":[{
                "activityId":x["id"],"currentActivitySha256":digest(x),
                "status":"REVISED_BOUNDED_PHYSICS_VERIFIED" if x["id"]=="a"
                         else "UNCHANGED_BOUNDED_PHYSICS_REVERIFIED",
                "fullAcademicPass":False,"publicationAuthorized":False,
            } for x in self.activities]}
        self.flush()

    def flush(self):
        self.matrix.write_text(json.dumps(self.m),encoding="utf-8")
        self.physics.write_text(json.dumps(self.p),encoding="utf-8")

    def run_dossier(self,aid="a"):
        return reconcile_activity_evidence(package_file=self.pkg,
            source_pdf=self.pdf,matrix_file=self.matrix,
            physics_file=self.physics,activity_id=aid)

    def test_exact_version_reconciles_without_full_pass(self):
        result=self.run_dossier()
        self.assertTrue(result["sourceLocationVerifiedInMatrix"])
        self.assertTrue(result["boundedPhysicsReceiptMatched"])
        self.assertEqual("AUTO_INDEPENDENT_SEMANTIC_VISUAL_REVIEW",result["nextAction"])
        self.assertFalse(result["fullAcademicPass"])
        self.assertFalse(result["publicationAuthorized"])
        self.assertFalse(result["meaningVerified"])
        self.assertNotIn("synthetic",json.dumps(result))

    def test_all_activities_covered_and_version_bound(self):
        for mutation in (
            lambda:self.m["activities"].pop(),
            lambda:self.p["activities"].append(copy.deepcopy(self.p["activities"][0])),
            lambda:self.p["activities"][0].update(currentActivitySha256="0"*64),
            lambda:self.m.update(packageSha256="0"*64),
            lambda:self.p.update(revisedPackageCanonicalSha256="0"*64),
            lambda:self.p.update(sourceSha256="0"*64),
        ):
            self.write_evidence()
            mutation()
            self.flush()
            with self.assertRaises(ValueError):
                self.run_dossier()

    def test_changed_package_or_pdf_rejected(self):
        self.activities[0]["interaction"]["items"][0]["id"]="changed"
        self.pkg.write_text(json.dumps({"activities":self.activities}),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"mismatch"):
            self.run_dossier()
        self.write_evidence()
        self.pdf.write_bytes(b"%PDF-1.4 changed source")
        with self.assertRaisesRegex(ValueError,"mismatch"):
            self.run_dossier()

    def test_reject_fake_academic_pass_or_publication(self):
        for mutation in (
            lambda:self.m["activities"][0].update(academicQA="PASS"),
            lambda:self.p["activities"][0].update(fullAcademicPass=True),
            lambda:self.p.update(publicationAuthorized=True),
            lambda:self.m["activities"][0].update(publicationAuthorized=True),
            lambda:self.m["activities"][0].update(sourcePages=[]),
        ):
            self.write_evidence()
            mutation()
            self.flush()
            with self.assertRaises(ValueError):
                self.run_dossier()

    def test_missing_source_or_failing_gate_auto_routes(self):
        self.write_evidence(source_present=False)
        self.assertEqual("AUTO_SOURCE_CHECK",self.run_dossier()["nextAction"])
        self.write_evidence()
        self.m["activities"][0]["academicQA"]="FAIL"
        self.m["activities"][0]["gates"]["answer_correctness"]="FAIL"
        self.m["counts"]={"PASS":0,"FAIL":1,"REVIEW_REQUIRED":1}
        self.flush()
        self.assertEqual("AUTO_REPAIR",self.run_dossier()["nextAction"])


if __name__=="__main__":
    unittest.main()
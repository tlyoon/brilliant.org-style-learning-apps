import copy
import json
import tempfile
import unittest
from pathlib import Path
from scripts.audit_academic_qa import academic_triage
from tests.test_visual_contracts import activity

ROOT=Path(__file__).resolve().parents[1]
class AcademicReportTests(unittest.TestCase):
    def test_saved_package_review_not_false_pass(self):
        source=ROOT/"content/chapter-9/section-9-4/package.json"
        result=academic_triage(ROOT, source)
        self.assertEqual("REVIEW_REQUIRED",result["academicQA"])
        self.assertFalse(result["publicationAuthorized"])
        self.assertFalse(result["humanReviewed"])
        self.assertEqual(18,result["activityCount"])
        self.assertEqual("REVIEW_REQUIRED",result["gates"]["source_fidelity"])

    def test_bounded_evidence_does_not_override_full_academic_qa(self):
        from unittest.mock import patch
        source=ROOT / "content/chapter-9/section-9-4/package.json"
        evidence={"boundedPropositionsVerified":6,"failedWitnesses":0,"academicActivitiesPassed":0}
        with patch("scripts.audit_academic_qa.audit_proofs",return_value=evidence):
            result=academic_triage(ROOT,source,ROOT / "tests/test_academic_qa_report.py",physics_receipts={})
        self.assertEqual(6,result["boundedPhysicsEvidence"]["boundedPropositionsVerified"])
        self.assertNotEqual("PASS",result["academicQA"])
        self.assertFalse(result["publicationAuthorized"])
    def test_interaction_model_evidence_does_not_fabricate_academic_pass(self):
        from unittest.mock import patch
        source=ROOT/"content/chapter-9/section-9-4/package.json"
        with patch("scripts.audit_academic_qa.audit_interaction_models",return_value={
            "boundedModelsVerified":8,"qualifierReviewRequired":1,
            "modelDiscrepancies":0,"fullAcademicActivitiesPassed":0,
            "academicQA":"REVIEW_REQUIRED",
        }):
            report=academic_triage(ROOT,source,ROOT/"tests/test_academic_qa_report.py",
                                   interaction_receipts={"private":"fixture"})
        self.assertEqual(8,report["interactivePhysicsEvidence"]["boundedModelsVerified"])
        self.assertEqual(1,report["interactivePhysicsEvidence"]["qualifierReviewRequired"])
        self.assertNotEqual("PASS",report["academicQA"])
        self.assertFalse(report["publicationAuthorized"])

    def test_confirmed_interaction_model_disagreement_fails_academic_qa(self):
        from unittest.mock import patch
        source=ROOT/"content/chapter-9/section-9-4/package.json"
        with patch("scripts.audit_academic_qa.audit_interaction_models",return_value={
            "boundedModelsVerified":7,"qualifierReviewRequired":1,
            "modelDiscrepancies":1,"fullAcademicActivitiesPassed":0,
        }):
            report=academic_triage(ROOT,source,ROOT/"tests/test_academic_qa_report.py",
                                   interaction_receipts={"private":"fixture"})
        self.assertEqual("FAIL",report["academicQA"])
        self.assertFalse(report["publicationAuthorized"])

    def test_impulse_semantic_evidence_keeps_full_academic_qa_unresolved(self):
        from unittest.mock import patch
        source=ROOT/"content/chapter-9/section-9-4/package.json"
        with patch("scripts.audit_academic_qa.audit_impulse_candidate",return_value={
            "boundedOptionModelsVerified":4,
            "optionQualifiersReviewRequired":1,
            "completeMultilingualSemanticAgreement":False,
            "academicQA":"REVIEW_REQUIRED",
            "publicationAuthorized":False,
        }):
            report=academic_triage(
                ROOT,source,ROOT/"tests/test_academic_qa_report.py",
                impulse_review_path=ROOT/"tests/test_academic_qa_report.py",
            )
        self.assertEqual(4,report["trilingualDistractorEvidence"]["boundedOptionModelsVerified"])
        self.assertEqual(1,report["trilingualDistractorEvidence"]["optionQualifiersReviewRequired"])
        self.assertNotEqual("PASS",report["academicQA"])
        self.assertFalse(report["publicationAuthorized"])

    def test_bad_mcq_fails_without_touching_files(self):
        source=ROOT/"content/chapter-9/section-9-4/package.json"
        with tempfile.TemporaryDirectory() as d:
            pkg=json.loads(source.read_text(encoding="utf-8"))
            item=next(a for a in pkg["activities"] if a["type"]=="mcq")
            item["answerKey"]["correct"]="does-not-exist"
            file=Path(d)/"candidate.json"
            file.write_text(json.dumps(pkg),encoding="utf-8")
            before=file.read_bytes()
            result=academic_triage(ROOT,file)
            self.assertEqual("FAIL",result["academicQA"])
            self.assertEqual(before,file.read_bytes())

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

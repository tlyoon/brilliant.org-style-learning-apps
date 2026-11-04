"""Academic QA should FAIL known invalid uniqueness, not invent scientific PASS."""
import json
from pathlib import Path
import tempfile
import unittest
from hashlib import sha256
from app_generator.validation.multiball_qualification import (
    ACTIVITY,explicit_multiball_uniqueness_defects,
)
from app_generator.validation.academic_acceptance_matrix import audit_activity_matrix
from tests.test_academic_acceptance_matrix import sample


class MultiballQAGuardTests(unittest.TestCase):
    def setUp(self):
        self.activity={
            "id":ACTIVITY,
            "explanation":{
              "en":"The only configuration that satisfies both conservation laws is one outgoing ball.",
              "ms":"Satu-satunya konfigurasi yang memenuhi kedua-dua hukum ialah satu bola.",
              "zh":"\u552f\u4e00\u80fd\u540c\u65f6\u6ee1\u8db3\u4e24\u4e2a\u5b88\u6052\u5b9a\u5f8b\u7684\u662f\u4e00\u4e2a\u7403\u3002",
            },
        }

    def test_all_three_legacy_overclaims_fail_individually(self):
        errors=explicit_multiball_uniqueness_defects(self.activity)
        self.assertEqual(3,len(errors))
        for lang in ("en","ms","zh"):
            self.assertTrue(any(e.endswith("in "+lang) for e in errors))
        self.assertNotIn("The only configuration",json.dumps(errors))

    def test_corrected_caveat_not_scientific_pass(self):
        a=self.activity.copy()
        a["explanation"]={
          "en":"Conservation laws alone are necessary but insufficient. Contact and direction assumptions matter.",
          "ms":"Hukum pemuliharaan sahaja tidak cukup tanpa syarat arah dan sentuhan.",
          "zh":"\u4e24\u4e2a\u5b88\u6052\u5b9a\u5f8b\u4e0d\u8db3\u4ee5\u552f\u4e00\u786e\u5b9a\u7ed3\u679c\u3002",
        }
        self.assertEqual([],explicit_multiball_uniqueness_defects(a))
        a["id"]="different-activity-with-same-wording"
        self.assertEqual([],explicit_multiball_uniqueness_defects(a))

    def test_missing_language_is_rejected(self):
        del self.activity["explanation"]["ms"]
        self.assertIn("missing Newton cradle explanation for ms",
                      explicit_multiball_uniqueness_defects(self.activity))

    def test_integrated_matrix_fail_v6_but_no_false_pass_v7(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            pdf=root/"source.pdf"
            pdf.write_bytes(b"%PDF-1.4 synthetic original")
            source_hash=sha256(pdf.read_bytes()).hexdigest()
            pkg=root/"package.json"
            a=sample()
            a["activities"][0]["id"]=ACTIVITY
            a["activities"][0]["explanation"]=self.activity["explanation"].copy()
            def check():
                pkg.write_text(json.dumps(a,ensure_ascii=False),encoding="utf-8")
                return audit_activity_matrix(
                    repo_root=Path(__file__).resolve().parents[1],
                    package_path=pkg,source_pdf=pdf,
                    source_sha256=source_hash,expected_count=2)
            old=check()
            self.assertEqual("FAIL",old["activities"][0]["academicQA"])
            self.assertEqual("FAIL",old["activities"][0]["gates"]["physics_consistency"])
            self.assertEqual("AUTO_REPAIR",old["activities"][0]["nextAction"])
            self.assertFalse(old["publicationAuthorized"])
            a["activities"][0]["explanation"]={
                "en":"Two conservation laws alone cannot select every multiball final state.",
                "ms":"Dua hukum pemuliharaan tidak mencukupi untuk semua gerakan bola.",
                "zh":"\u4e24\u4e2a\u5b88\u6052\u5b9a\u5f8b\u672c\u8eab\u65e0\u6cd5\u552f\u4e00\u786e\u5b9a\u6240\u6709\u4e09\u7403\u8fd0\u52a8\u3002"}
            new=check()
            self.assertEqual("REVIEW_REQUIRED",new["activities"][0]["gates"]["physics_consistency"])
            self.assertEqual(0,new["counts"]["PASS"])
            self.assertFalse(new["publicationAuthorized"])


if __name__=="__main__":
    unittest.main()

"""Adversarial regression for future incorrect inelastic-rebound physics claims."""
import json
import tempfile
from pathlib import Path
from hashlib import sha256
import unittest

from app_generator.validation.inelastic_separation_claim import (
    ACTIVITY, unqualified_inelastic_rebound_defects,
)
from app_generator.validation.academic_acceptance_matrix import audit_activity_matrix
from tests.test_academic_acceptance_matrix import sample


class InelasticReboundQAGuardTests(unittest.TestCase):
    def setUp(self):
        self.old={"id":ACTIVITY,"explanation":{
            "en":"In an inelastic collision, the objects rebound separately.",
            "ms":"Dalam perlanggaran tak kenyal, objek melantun secara berasingan.",
            "zh":"\u5728\u975e\u5f39\u6027\u78b0\u649e\u4e2d\uff0c\u7269\u4f53\u5206\u522b\u53cd\u5f39\u3002",
        }}
        self.new={"id":ACTIVITY,"explanation":{
            "en":"In a non-sticking inelastic collision the objects separate, but may both continue forward.",
            "ms":"Dalam perlanggaran tak kenyal tanpa melekat, objek berpisah dan boleh terus bergerak ke depan.",
            "zh":"\u4e0d\u7c98\u8fde\u7684\u975e\u5f39\u6027\u78b0\u649e\u540e\uff0c\u7269\u4f53\u5206\u5f00\u4f46\u53ef\u540c\u65f6\u5411\u524d\u79fb\u52a8\u3002",
        }}

    def test_old_three_locales_are_physics_fails(self):
        issues=unqualified_inelastic_rebound_defects(self.old)
        self.assertEqual(3,len(issues))
        for loc in ("en","ms","zh"):
            self.assertTrue(any(x.endswith("in "+loc) for x in issues))
        self.assertNotIn("the objects rebound separately",json.dumps(issues))

    def test_corrected_words_do_not_constitute_academic_pass(self):
        self.assertEqual([],unqualified_inelastic_rebound_defects(self.new))

    def test_unrelated_activity_ignored_and_missing_locale_rejected(self):
        fake=dict(self.old,id="unrelated")
        self.assertEqual([],unqualified_inelastic_rebound_defects(fake))
        del self.old["explanation"]["ms"]
        self.assertTrue(any(x.endswith("in ms") for x in
                            unqualified_inelastic_rebound_defects(self.old)))

    def test_academic_matrix_changes_from_fail_to_review_required(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            source=root/"original.pdf"
            source.write_bytes(b"%PDF-1.4 synthetic")
            pkg=root/"package.json"
            example=sample()
            example["activities"][0]["id"]=ACTIVITY
            example["activities"][0]["explanation"]=self.old["explanation"].copy()
            def run():
                pkg.write_text(json.dumps(example,ensure_ascii=False),"utf-8")
                return audit_activity_matrix(repo_root=Path(__file__).resolve().parents[1],
                    package_path=pkg,source_pdf=source,
                    source_sha256=sha256(source.read_bytes()).hexdigest(),
                    expected_count=2)
            before=run()
            self.assertEqual("FAIL",before["activities"][0]["gates"]["physics_consistency"])
            self.assertFalse(before["publicationAuthorized"])
            example["activities"][0]["explanation"]=self.new["explanation"].copy()
            after=run()
            self.assertEqual("REVIEW_REQUIRED",after["activities"][0]["gates"]["physics_consistency"])
            self.assertEqual(0,after["counts"]["PASS"])
            self.assertFalse(after["publicationAuthorized"])


if __name__=="__main__":unittest.main()

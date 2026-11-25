"""Guard against strict ballistic impact momentum claims under negligible impulse."""
import json
import unittest
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from app_generator.validation.ballistic_impulse_scope import (
    ACTIVITY, invalid_ballistic_impact_exactness_defects,
)
from app_generator.validation.academic_acceptance_matrix import audit_activity_matrix
from tests.test_academic_acceptance_matrix import sample


class BallisticImpulseQAGuardTests(unittest.TestCase):
    def setUp(self):
        self.old={"id":ACTIVITY,"answerLogic":{
          "en":"External gravity is negligible, so momentum is conserved. The velocity is determined strictly by momentum conservation.",
          "ms":"Daya luar boleh diabaikan, maka momentum dikekalkan. Halaju ditentukan secara ketat oleh pemuliharaan momentum.",
          "zh":"\u5916\u90e8\u51b2\u91cf\u53ef\u5ffd\u7565\uff0c\u52a8\u91cf\u4e25\u683c\u5b88\u6052\u3002\u901f\u5ea6\u5b8c\u5168\u7531\u52a8\u91cf\u5b88\u6052\u51b3\u5b9a\u3002",
        }}
        self.new={"id":ACTIVITY,"answerLogic":{
          "en":"Net external horizontal impulse is assumed negligible, so momentum is approximately conserved; exact conservation needs zero net external impulse.",
          "ms":"Impuls luar bersih boleh diabaikan, maka momentum mengufuk hampir dikekalkan; tepat jika impuls luar sifar.",
          "zh":"\u51c0\u5916\u90e8\u6c34\u5e73\u51b2\u91cf\u53ef\u5ffd\u7565\uff0c\u56e0\u6b64\u52a8\u91cf\u8fd1\u4f3c\u5b88\u6052\uff1b\u51c0\u5916\u51b2\u91cf\u4e3a\u96f6\u65f6\u624d\u7cbe\u786e\u5b88\u6052\u3002",
        }}

    def test_old_exactness_claims_fail_all_three_languages(self):
        issues=invalid_ballistic_impact_exactness_defects(self.old)
        self.assertEqual(3,len(issues))
        for lang in ("en","ms","zh"):
            self.assertTrue(any(x.endswith("in "+lang) for x in issues))
        self.assertNotIn("External gravity",json.dumps(issues))

    def test_revised_approximate_claim_does_not_auto_pass_academic_review(self):
        self.assertEqual([],invalid_ballistic_impact_exactness_defects(self.new))

    def test_other_activities_ignored_and_missing_locale_flagged(self):
        self.assertEqual([],invalid_ballistic_impact_exactness_defects(
           dict(self.old,id="another-physics-activity")))
        del self.old["answerLogic"]["ms"]
        self.assertTrue(any(x.endswith("in ms") for x in
            invalid_ballistic_impact_exactness_defects(self.old)))

    def test_actual_academic_matrix_fail_to_review_required(self):
        with TemporaryDirectory() as t:
            root=Path(t)
            pdf=root/"synthetic.pdf"
            pdf.write_bytes(b"%PDF-1.4 synthetic")
            pkg=root/"package.json"
            item=sample()
            item["activities"][0]["id"]=ACTIVITY
            item["activities"][0]["answerLogic"]=self.old["answerLogic"].copy()
            def evaluate():
                pkg.write_text(json.dumps(item,ensure_ascii=True),encoding="utf-8")
                return audit_activity_matrix(
                  repo_root=Path(__file__).resolve().parents[1],
                  package_path=pkg,source_pdf=pdf,
                  source_sha256=sha256(pdf.read_bytes()).hexdigest(),
                  expected_count=2)
            before=evaluate()
            self.assertEqual("FAIL",before["activities"][0]["gates"]["physics_consistency"])
            self.assertFalse(before["publicationAuthorized"])
            item["activities"][0]["answerLogic"]=self.new["answerLogic"].copy()
            after=evaluate()
            self.assertEqual("REVIEW_REQUIRED",after["activities"][0]["gates"]["physics_consistency"])
            self.assertEqual(0,after["counts"]["PASS"])
            self.assertFalse(after["publicationAuthorized"])


if __name__=="__main__":unittest.main()

"""Exact rational conservation and private source-scoped correction tests."""
from fractions import Fraction as F
from hashlib import sha256
import copy
import unittest

from app_generator.validation.multiball_qualification import (
    rational_conservation_witness,apply_private_clarification,ACTIVITY,FIELD,
)


class MultiballQualificationTests(unittest.TestCase):
    def setUp(self):
        self.package={"activities":[{"id":"other-"+str(i),"type":"interactive"}
                                    for i in range(17)]+[
                      {"id":ACTIVITY,"type":"mcq","answerKey":{
                         "correct":"option-A","options":[{"id":"option-A"}]},
                       FIELD:{
                         "en":"Conservation checks. The only configuration that satisfies both conservation laws is one departing ball.",
                         "ms":"Pemuliharaan diperiksa. Satu-satunya konfigurasi yang memenuhi kedua-dua hukum ialah satu bola.",
                         "zh":"\u52a8\u91cf\u5b88\u6052\u3002\u552f\u4e00\u80fd\u540c\u65f6\u6ee1\u8db3\u4e24\u4e2a\u5b88\u6052\u5b9a\u5f8b\u7684\u662f\u4e00\u4e2a\u7403\u3002",
                       }}]}
        new={
          "en":"Conservation is necessary, not enough for a unique multibody solution. Extra constraints on contact and direction determine the textbook outcome.",
          "ms":"Pemuliharaan ialah syarat perlu, tetapi tidak mencukupi bagi penyelesaian banyak bola yang unik. Andaian arah dan sentuhan tambahan diperlukan.",
          "zh":"\u5b88\u6052\u5b9a\u5f8b\u662f\u5fc5\u8981\u6761\u4ef6\uff0c\u4f46\u4e0d\u8db3\u4ee5\u552f\u4e00\u786e\u5b9a\u591a\u7403\u8fd0\u52a8\u3002\u8fd8\u9700\u8981\u63a5\u89e6\u52a8\u529b\u5b66\u548c\u8fd0\u52a8\u65b9\u5411\u7684\u6761\u4ef6\u3002",
        }
        new["zh"] += ("\u4e24\u4e2a\u4fdd\u5b88\u5b9a\u5f8b\u4e0d\u80fd\u4ee3\u66ff"
                      "\u63a5\u89e6\u8fc7\u7a0b\u4e0e\u8fd0\u52a8\u65b9\u5411\u7684\u7269\u7406\u7ea6\u675f\u3002")
        self.rules={"activityId":ACTIVITY,"field":FIELD,"replacements":{
            l:{"oldFieldSha256":sha256(self.package["activities"][-1][FIELD][l].encode()).hexdigest(),
               "newText":new[l]} for l in ("en","ms","zh")}}

    def test_counterexample_preserves_both_exact_invariants(self):
        x=rational_conservation_witness()
        self.assertEqual(["-1/3","2/3","2/3"],x["alternateThreeBallVelocityUnits"])
        self.assertEqual("1",x["alternateMomentumUnits"])
        self.assertEqual("1",x["alternateDoubledKineticEnergyUnits"])
        self.assertEqual("1/2",x["twoHalfSpeedProposalDoubledKineticEnergyUnits"])
        self.assertFalse(x["conservationAloneUniquelyDeterminesMultibodyOutcome"])
        self.assertFalse(x["alternateTrajectoryEstablishedPhysically"])
        self.assertTrue(x["restrictedForwardOnlyOneNonzeroVelocity"])

    def test_exact_three_locale_repair_and_all_other_fields_preserved(self):
        unchanged=copy.deepcopy(self.package)
        new,result=apply_private_clarification(self.package,self.rules)
        self.assertEqual(unchanged,self.package)
        self.assertEqual(1,result["changedActivities"])
        self.assertEqual(3,result["changedFields"])
        self.assertEqual(0,result["formalAcademicPASS"])
        self.assertFalse(result["publicationAuthorized"])
        for i in range(17):self.assertEqual(unchanged["activities"][i],new["activities"][i])
        self.assertEqual(unchanged["activities"][-1]["answerKey"],
                         new["activities"][-1]["answerKey"])
        self.assertNotEqual(unchanged["activities"][-1][FIELD],
                            new["activities"][-1][FIELD])

    def test_tampered_old_explanation_hash_fails_closed(self):
        self.package["activities"][-1][FIELD]["ms"]+=" tampered"
        with self.assertRaisesRegex(ValueError,"field hash"):
            apply_private_clarification(self.package,self.rules)

    def test_unqualified_uniqueness_remains_rejected(self):
        self.rules["replacements"]["en"]["newText"]=self.package["activities"][-1][FIELD]["en"]+" and more text."
        with self.assertRaisesRegex(ValueError,"uniqueness"):
            apply_private_clarification(self.package,self.rules)

    def test_missing_locale_or_modified_activity_roster_fails_closed(self):
        del self.rules["replacements"]["zh"]
        with self.assertRaisesRegex(ValueError,"three locale"):
            apply_private_clarification(self.package,self.rules)
        self.rules["replacements"]["zh"]={"oldFieldSha256":"0"*64,"newText":"x"*100}
        self.package["activities"].pop()
        with self.assertRaisesRegex(ValueError,"eighteen-activity"):
            apply_private_clarification(self.package,self.rules)


if __name__=="__main__":
    unittest.main()

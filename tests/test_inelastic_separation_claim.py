"""Exact non-reversing inelastic collision and scoped source revision QA."""
from copy import deepcopy
import json
from fractions import Fraction as F
from hashlib import sha256
import unittest

from app_generator.validation.inelastic_separation_claim import (
    ACTIVITY, nonreversing_inelastic_witness, scoped_private_correction,
)
from app_generator.validation.mcq_statement_physics import (
    _approved_v9_malay_lexicon_reconciliation,
    APPROVED_INELASTIC_QUALIFICATION_V10_SHA,
)



class InelasticSeparationClaimTests(unittest.TestCase):
    def setUp(self):
        self.data={"activities":[{"id":"other-"+str(i)} for i in range(17)]+[
            {"id":ACTIVITY,"type":"interactive",
             "interaction":{"items":[{"id":"a"}]},
             "explanation":{
                 "en":"In an inelastic collision, the objects rebound separately while dissipating some kinetic energy.",
                 "ms":"Dalam perlanggaran tak kenyal, objek melantun secara berasingan sambil melesapkan tenaga kinetik.",
                 "zh":"\u5728\u975e\u5f39\u6027\u78b0\u649e\u4e2d\uff0c\u7269\u4f53\u5206\u522b\u53cd\u5f39\u3002",
             }}]}
        self.rules={"activityId":ACTIVITY,"field":"explanation","replacements":{}}
        endings={
            "en":" In fact, a non-sticking collision can leave both objects moving forward.",
            "ms":" Kedua-dua objek boleh terus bergerak ke hadapan selepas bersentuhan.",
            "zh":"\u4e24\u7269\u4f53\u5728\u63a5\u89e6\u540e\u53ef\u4ee5\u7ee7\u7eed\u5411\u524d\u8fd0\u52a8\u3002"
        }
        for loc,old in self.data["activities"][-1]["explanation"].items():
            new=old
            forbidden={
                "en":"the objects rebound separately",
                "ms":"objek melantun secara berasingan",
                "zh":"\u7269\u4f53\u5206\u522b\u53cd\u5f39",
            }
            new=new.replace(forbidden[loc],"the objects separate" if loc=="en" else
                "objek berpisah" if loc=="ms" else
                "\u7269\u4f53\u5206\u5f00")
            new+=endings[loc]
            if loc=="zh":
                new+=("\u5728\u6b64\u4f8b\u4e2d\uff0c\u4e24\u4e2a\u76f8\u540c\u8d28\u91cf\u7684\u7269\u4f53\u4ee5\u4e0d\u540c\u7684\u5411\u524d\u901f\u5ea6\u5206\u5f00\u3002")*7
            self.rules["replacements"][loc]={
                "oldFieldSha256":sha256(old.encode("utf-8")).hexdigest(),
                "newText":new}

    def test_exact_restitution_collision_proves_no_reversal_is_required(self):
        result=nonreversing_inelastic_witness()
        self.assertEqual(["1/4","3/4"],result["finalVelocityUnits"])
        self.assertEqual("1/2",result["coefficientOfRestitution"])
        self.assertEqual("5/8",result["kineticEnergyFinalToInitial"])
        self.assertTrue(result["momentumConserved"])
        self.assertTrue(result["bothObjectsContinueForward"])
        self.assertFalse(result["nonStickingInelasticReversalRequired"])

    def test_three_language_scoped_copy_on_write_and_answers_unchanged(self):
        original=deepcopy(self.data)
        new,receipt=scoped_private_correction(self.data,self.rules)
        self.assertEqual(original,self.data)
        self.assertEqual(original["activities"][:17],new["activities"][:17])
        self.assertEqual(original["activities"][-1]["interaction"],
                         new["activities"][-1]["interaction"])
        self.assertEqual(receipt["changedLocalizedExplanationFields"],3)
        self.assertFalse(receipt["publicationAuthorized"])

    def test_new_revision_can_reuse_exact_protected_option_labels_only(self):
        old={"en":"Momentum conserved","ms":"Keabadian momentum",
             "zh":"动量守恒"}
        new=dict(old,ms="Pemuliharaan momentum")
        digest=sha256(json.dumps(old,sort_keys=True,ensure_ascii=False,
                    separators=(",",":")).encode("utf-8")).hexdigest()
        self.assertTrue(_approved_v9_malay_lexicon_reconciliation(
            new,digest,APPROVED_INELASTIC_QUALIFICATION_V10_SHA))
        self.assertFalse(_approved_v9_malay_lexicon_reconciliation(
            dict(new,zh="changed"),digest,APPROVED_INELASTIC_QUALIFICATION_V10_SHA))
        self.assertFalse(_approved_v9_malay_lexicon_reconciliation(
            new,digest,"a"*64))

    def test_stale_field_hash_fails_closed(self):
        self.data["activities"][-1]["explanation"]["ms"]+=" modified"
        with self.assertRaisesRegex(ValueError,"unverified"):
            scoped_private_correction(self.data,self.rules)

    def test_old_rebound_claim_remaining_is_rejected(self):
        old=self.data["activities"][-1]["explanation"]["en"]
        self.rules["replacements"]["en"]["newText"]=old+" Additional generic text to meet the length."
        with self.assertRaisesRegex(ValueError,"reversal"):
            scoped_private_correction(self.data,self.rules)

    def test_locale_missing_or_unrelated_field_rejected(self):
        del self.rules["replacements"]["zh"]
        with self.assertRaisesRegex(ValueError,"three localized"):
            scoped_private_correction(self.data,self.rules)
        self.rules["field"]="feedback"
        with self.assertRaisesRegex(ValueError,"unexpected activity"):
            scoped_private_correction(self.data,self.rules)


if __name__=="__main__":unittest.main()

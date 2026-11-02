"""Exact horizontal impulse physics and narrow private trilingual correction tests."""
import json
from copy import deepcopy
from hashlib import sha256
from fractions import Fraction as F
import unittest

from app_generator.validation.ballistic_impulse_scope import (
    ACTIVITY, small_external_impulse_witness, copy_private_qualification,
)
from app_generator.validation.mcq_statement_physics import (
    APPROVED_BALLISTIC_IMPULSE_V11_SHA, _approved_v9_malay_lexicon_reconciliation,
)


class BallisticImpulseScopeTests(unittest.TestCase):
    def setUp(self):
        self.source={"activities":[{"id":"other-"+str(i)} for i in range(17)]+[
          {"id":ACTIVITY,"interactionMode":"ordering",
           "interaction":{"correctOrder":["a","b","c"]},
           "answerLogic":{
             "en":"Before the impact the projectile is moving. During the impact we approximate momentum conservation by the impulse approximation. After contact, the combined objects move as one.",
             "ms":"Sebelum hentaman projektil bergerak. Sepanjang hentaman, momentum mengufuk hampir dikekalkan menggunakan penghampiran impuls. Selepas sentuhan, kedua-duanya bergerak bersama.",
             "zh":"\u78b0\u649e\u524d\u5f39\u4e38\u6b63\u5728\u8fd0\u52a8\u3002\u78b0\u649e\u671f\u95f4\u6c34\u5e73\u52a8\u91cf\u8fd1\u4f3c\u5b88\u6052\uff0c\u800c\u5916\u90e8\u51b2\u91cf\u5e76\u975e\u4e25\u683c\u4e3a\u96f6\u3002"
           }}]}
        self.rules={"activityId":ACTIVITY,"field":"answerLogic","replacements":{}}
        for loc,old in self.source["activities"][-1]["answerLogic"].items():
            new=old+" "+("Horizontal momentum is approximately conserved when the net external impulse is negligible. The net impulse must be exactly zero for exact conservation."
                              if loc=="en" else
                           "Impuls luar bersih mesti sifar untuk pemuliharaan tepat."
                              if loc=="ms" else
                           "\u53ea\u6709\u5916\u529b\u51b2\u91cf\u4e3a\u96f6\u65f6\u624d\u80fd\u7cbe\u786e\u5b88\u6052\u52a8\u91cf\u3002"*9)
            self.rules["replacements"][loc]={
                 "oldFieldSha256":sha256(old.encode("utf-8")).hexdigest(),
                 "newText":new}

    def test_exact_small_nonzero_external_impulse_does_not_conserve_momentum(self):
        result=small_external_impulse_witness()
        self.assertEqual("1/1000",result["externalHorizontalImpulse"])
        self.assertEqual("1001/1000",result["finalHorizontalMomentum"])
        self.assertEqual("1/5000",result["velocityDifference"])
        self.assertEqual(F(1,5000),F(result["velocityDifference"]))
        self.assertFalse(result["exactMomentumConservation"])
        self.assertTrue(result["approximateMomentumConservation"])

    def test_copy_on_write_and_full_answer_model_stability(self):
        old=deepcopy(self.source)
        revised,receipt=copy_private_qualification(self.source,self.rules)
        self.assertEqual(self.source,old)
        self.assertEqual(old["activities"][:17],revised["activities"][:17])
        self.assertEqual(old["activities"][-1]["interaction"],revised["activities"][-1]["interaction"])
        self.assertEqual(3,receipt["changedLocalizedAnswerLogicFields"])
        self.assertFalse(receipt["publicationAuthorized"])

    def test_stale_hash_and_scope_rejected(self):
        self.source["activities"][-1]["answerLogic"]["en"]+=" altered"
        with self.assertRaisesRegex(ValueError,"stale hash"):
            copy_private_qualification(self.source,self.rules)
        self.rules["activityId"]="wrong"
        with self.assertRaisesRegex(ValueError,"scope"):
            copy_private_qualification(self.source,self.rules)

    def test_missing_language_and_strict_chinese_claim_rejected(self):
        self.rules["replacements"].pop("ms")
        with self.assertRaisesRegex(ValueError,"three translated"):
            copy_private_qualification(self.source,self.rules)
        original=self.source["activities"][-1]["answerLogic"]["ms"]
        self.rules["replacements"]["ms"]={
            "oldFieldSha256":sha256(original.encode("utf-8")).hexdigest(),
            "newText":original+" Impuls luar bersih boleh diabaikan; momentum hampir dikekalkan."}
        self.rules["replacements"]["zh"]["newText"]+="\u52a8\u91cf\u4e25\u683c\u5b88\u6052"
        with self.assertRaisesRegex(ValueError,"strict impact momentum"):
            copy_private_qualification(self.source,self.rules)

    def test_new_sha_cannot_bypass_original_option_digest(self):
        old={"en":"Momentum conserved","ms":"Keabadian momentum",
             "zh":"\u52a8\u91cf\u5b88\u6052"}
        new=dict(old,ms="Pemuliharaan momentum")
        expected=sha256(json.dumps(old,sort_keys=True,ensure_ascii=False,
                      separators=(",",":")).encode("utf-8")).hexdigest()
        self.assertTrue(_approved_v9_malay_lexicon_reconciliation(
            new,expected,APPROVED_BALLISTIC_IMPULSE_V11_SHA))
        self.assertFalse(_approved_v9_malay_lexicon_reconciliation(
            dict(new,en="Different answer"),expected,APPROVED_BALLISTIC_IMPULSE_V11_SHA))
        self.assertFalse(_approved_v9_malay_lexicon_reconciliation(
            new,expected,"0"*64))


if __name__=="__main__":unittest.main()

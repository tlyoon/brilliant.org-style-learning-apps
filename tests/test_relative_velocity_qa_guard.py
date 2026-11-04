"""Ensure known invalid derivations cause academic FAIL, not a false PASS."""
import unittest
from app_generator.validation.relative_velocity_derivation import incorrect_derivation_premise_defects

class DerivationQAGuardTests(unittest.TestCase):
    def setUp(self):
        self.item={"id":"mcq-relative-velocity-scope","answerLogic":{
            "en":"If kinetic energy is lost, this division is invalid.",
            "ms":"Jika tenaga hilang, pembahagian ini tidak sah.",
            "zh":"\u8fd9\u4e00\u9664\u6cd5\u4fbf\u4e0d\u6210\u7acb"}}
    def test_three_locales_flagged(self):
        result=incorrect_derivation_premise_defects(self.item)
        self.assertEqual(3,len(result))
        self.assertTrue(all(any(x.endswith("in "+l) for x in result) for l in ("en","ms","zh")))
    def test_corrected_explanation_not_automatically_passed(self):
        self.item["answerLogic"]={"en":"The kinetic-energy conservation premise fails.",
                                 "ms":"Persamaan tenaga kinetik tidak terpelihara.",
                                 "zh":"\u52a8\u80fd\u5b88\u6052\u7b49\u5f0f\u4e0d\u6210\u7acb"}
        self.assertEqual([],incorrect_derivation_premise_defects(self.item))
    def test_other_activity_not_targeted(self):
        self.item["id"]="another-activity"
        self.assertEqual([],incorrect_derivation_premise_defects(self.item))
    def test_missing_locale_is_concrete_defect(self):
        self.item["answerLogic"].pop("ms")
        self.assertTrue(any(x.endswith("in ms") for x in incorrect_derivation_premise_defects(self.item)))
if __name__=="__main__":unittest.main()

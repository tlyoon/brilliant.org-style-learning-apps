import copy
import unittest
from app_generator.validation.language_qa import check_multilingual_surface, scientific_malay_eternal_terms
from tests.test_visual_contracts import activity

class MultilingualQATests(unittest.TestCase):
    def test_present_text_still_needs_semantic_crosscheck(self):
        self.assertEqual("REVIEW_REQUIRED",check_multilingual_surface(activity()).result)

    def test_missing_translation_fails(self):
        v=copy.deepcopy(activity())
        v["prompt"]["zh"]=""
        self.assertEqual("FAIL",check_multilingual_surface(v).result)

    def test_physics_conservative_mistranslation_hard_fails_academic_qa(self):
        v=copy.deepcopy(activity())
        v["feedback"]={
          "en":"During a conservative swing, total mechanical energy is conserved.",
          "ms":"Dalam ayunan abadi, tenaga mekanikal dipelihara.",
          "zh":"\\u6446\\u52a8\\u4e2d\\u673a\\u68b0\\u80fd\\u5b88\\u6052",
        }
        finding=check_multilingual_surface(v)
        self.assertEqual("FAIL",finding.result)
        self.assertIn("feedback/ms",finding.detail)
        self.assertTrue(finding.independently_verified)
        self.assertNotIn("Dalam ayunan abadi",finding.detail)

    def test_nested_physics_mistranslation_and_nonphysics_eternal_distinct(self):
        x={"prerequisites":[{"description":{
             "en":"A conservative spring force",
             "ms":"Daya spring abadi","zh":"\\u4fdd\\u5b88\\u529b"}}]}
        self.assertEqual(["/prerequisites/0/description/ms"],
                         scientific_malay_eternal_terms(x))
        self.assertEqual([],scientific_malay_eternal_terms({
            "feedback":{"en":"Nature of eternal life",
                        "ms":"Kehidupan abadi","zh":"\\u751f\\u547d"}}))
        self.assertEqual([],scientific_malay_eternal_terms({
            "feedback":{"en":"Momentum is conserved",
                        "ms":"Momentum diabadikan","zh":"\\u52a8\\u91cf\\u5b88\\u6052"}}))

    def test_corrected_conservative_terms_do_not_grant_translation_pass(self):
        v=copy.deepcopy(activity())
        v["feedback"]={"en":"conservative spring force",
                       "ms":"daya spring konservatif",
                       "zh":"\\u4fdd\\u5b88\\u529b"}
        result=check_multilingual_surface(v)
        self.assertEqual("REVIEW_REQUIRED",result.result)
        self.assertFalse(result.result=="PASS")

    def test_exact_english_copy_triggers_review(self):
        v=copy.deepcopy(activity())
        v["feedback"]["en"]="This is an unusually long English explanation of collisions and momentum."
        v["feedback"]["zh"]=v["feedback"]["en"]
        result=check_multilingual_surface(v)
        self.assertEqual("REVIEW_REQUIRED",result.result)
        self.assertIn("identical",result.detail)

import copy
import unittest
from app_generator.validation.language_qa import check_multilingual_surface, scientific_malay_eternal_terms
from tests.test_visual_contracts import activity

class MultilingualQATests(unittest.TestCase):

    def test_missing_answer_explanation_locale_is_a_real_fail(self):
        for field, missing in (("answerLogic","ms"), ("explanation","zh"),
                               ("accessibilityText","en")):
            with self.subTest(field=field):
                a=copy.deepcopy(activity())
                a[field]={"en":"Conservation of momentum",
                          "ms":"Pemuliharaan momentum","zh":"动量守恒"}
                a[field][missing]=""
                result=check_multilingual_surface(a)
                self.assertEqual("FAIL",result.result)
                self.assertIn(field,result.detail)
                self.assertNotIn("Conservation of momentum",result.detail)

    def test_prerequisite_recovery_prompt_also_checked(self):
        a=copy.deepcopy(activity())
        a["prerequisiteRecovery"]={"prerequisiteId":"before-collision",
                                   "prompt":{"en":"Review the impulse principle",
                                             "ms":"Semak prinsip impuls","zh":""}}
        result=check_multilingual_surface(a)
        self.assertEqual("FAIL",result.result)
        self.assertIn("prerequisiteRecovery/prompt",result.detail)

    def test_interactive_item_and_target_translation_failures(self):
        a=copy.deepcopy(activity())
        a["type"]="interactive"
        a.pop("answerKey")
        a["interactionMode"]="matching"
        a["interaction"]={
            "items":[{"id":"ball-a","label":{
                "en":"Ball A","ms":"Bola A","zh":"球A"}}],
            "targets":[{"id":"conserve","label":{
                "en":"Conserved","ms":"","zh":"守恒"}}]}
        self.assertEqual("FAIL",check_multilingual_surface(a).result)
        self.assertIn("interaction/targets/0/label",check_multilingual_surface(a).detail)
        a["interaction"]["targets"][0]["label"]["ms"]="Dikekalkan"
        a["interaction"]["items"][0]["label"]["zh"]=""
        self.assertIn("interaction/items/0/label",check_multilingual_surface(a).detail)

    def test_visual_entity_and_accessibility_locales_not_omitted(self):
        a=copy.deepcopy(activity())
        a["visualSpec"]={
            "entities":[{"id":"cart","label":{
                "en":"Cart","ms":"Troli","zh":""}}],
            "accessibility":{"description":{
                "en":"Two carts collide","ms":"Dua troli berlanggar","zh":"两车碰撞"}}}
        result=check_multilingual_surface(a)
        self.assertEqual("FAIL",result.result)
        self.assertIn("visualSpec/entities/0/label",result.detail)
        a["visualSpec"]["entities"][0]["label"]["zh"]="小车"
        a["visualSpec"]["accessibility"]["description"]["ms"]=""
        self.assertIn("visualSpec/accessibility/description",
                      check_multilingual_surface(a).detail)

    def test_empty_hints_are_not_mistaken_for_complete_translations(self):
        a=copy.deepcopy(activity())
        a["hints"]=[]
        result=check_multilingual_surface(a)
        self.assertEqual("FAIL",result.result)
        self.assertIn("hints",result.detail)

    def test_complete_new_fields_remain_review_required_not_semantics_pass(self):
        a=copy.deepcopy(activity())
        complete={"en":"Conservation of momentum in collisions",
                  "ms":"Pemuliharaan momentum dalam perlanggaran",
                  "zh":"碰撞中的动量守恒"}
        a["answerLogic"]=dict(complete)
        a["explanation"]=dict(complete)
        a["accessibilityText"]=dict(complete)
        result=check_multilingual_surface(a)
        self.assertEqual("REVIEW_REQUIRED",result.result)
        self.assertTrue(result.independently_verified)

    def test_untranslated_long_explanation_does_not_pass(self):
        a=copy.deepcopy(activity())
        text="Kinetic energy is not necessarily conserved in this inelastic collision."
        a["explanation"]={"en":text,"ms":"Tenaga kinetik berkurang","zh":text}
        finding=check_multilingual_surface(a)
        self.assertEqual("REVIEW_REQUIRED",finding.result)
        self.assertIn("explanation",finding.detail)
        self.assertNotIn(text,finding.detail)

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

    def test_eternity_derived_lexicon_in_mechanics_fails(self):
        for malay in ("Keabadian momentum linear",
                      "Sistem mengabadikan tenaga kinetik",
                      "Momentum sentiasa diabadikan"):
            v=copy.deepcopy(activity())
            v["prompt"]["en"]="A collision conserves kinetic energy?"
            v["feedback"]["ms"]=malay
            result=check_multilingual_surface(v)
            self.assertEqual("FAIL",result.result)
            self.assertIn("eternity/immortalization",result.detail)
            self.assertNotIn(malay,result.detail)

    def test_literature_eternity_does_not_trigger_science_gate(self):
        v=copy.deepcopy(activity())
        v["prompt"]["en"]="What does eternity symbolize in this story?"
        v["feedback"]["ms"]="Keabadian ialah tema utama karya sastera."
        result=check_multilingual_surface(v)
        self.assertEqual("REVIEW_REQUIRED",result.result)

    def test_repaired_scientific_word_is_not_automatic_academic_pass(self):
        v=copy.deepcopy(activity())
        v["prompt"]["en"]="Does a collision conserve momentum?"
        v["feedback"]["ms"]="Pemuliharaan momentum linear dalam sistem terpencil."
        self.assertEqual("REVIEW_REQUIRED",check_multilingual_surface(v).result)

    def test_exact_english_copy_triggers_review(self):
        v=copy.deepcopy(activity())
        v["feedback"]["en"]="This is an unusually long English explanation of collisions and momentum."
        v["feedback"]["zh"]=v["feedback"]["en"]
        result=check_multilingual_surface(v)
        self.assertEqual("REVIEW_REQUIRED",result.result)
        self.assertIn("identical",result.detail)

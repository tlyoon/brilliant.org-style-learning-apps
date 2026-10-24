import copy
import unittest
from app_generator.validation.language_qa import check_multilingual_surface
from tests.test_visual_contracts import activity

class MultilingualQATests(unittest.TestCase):
    def test_present_text_still_needs_semantic_crosscheck(self):
        self.assertEqual("REVIEW_REQUIRED",check_multilingual_surface(activity()).result)

    def test_missing_translation_fails(self):
        v=copy.deepcopy(activity())
        v["prompt"]["zh"]=""
        self.assertEqual("FAIL",check_multilingual_surface(v).result)

    def test_exact_english_copy_triggers_review(self):
        v=copy.deepcopy(activity())
        v["feedback"]["en"]="This is an unusually long English explanation of collisions and momentum."
        v["feedback"]["zh"]=v["feedback"]["en"]
        result=check_multilingual_surface(v)
        self.assertEqual("REVIEW_REQUIRED",result.result)
        self.assertIn("identical",result.detail)

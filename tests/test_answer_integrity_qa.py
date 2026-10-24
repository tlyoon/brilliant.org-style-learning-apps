import copy
import unittest
from app_generator.validation.answer_integrity import check_answer_integrity
from tests.test_visual_contracts import activity

class AnswerIntegrityTests(unittest.TestCase):
    def test_well_formed_mcq_is_not_scientific_pass(self):
        self.assertEqual("REVIEW_REQUIRED",check_answer_integrity(activity()).result)

    def test_duplicate_translated_answers_or_key_fail(self):
        item=activity()
        broken=copy.deepcopy(item)
        broken["answerKey"]["options"][1]["label"]["ms"]=broken["answerKey"]["options"][0]["label"]["ms"]
        self.assertEqual("FAIL",check_answer_integrity(broken).result)
        broken=copy.deepcopy(item)
        broken["answerKey"]["correct"]="ghost"
        self.assertEqual("FAIL",check_answer_integrity(broken).result)
        broken=copy.deepcopy(item)
        broken["answerKey"]["options"][1]["id"]=broken["answerKey"]["options"][0]["id"]
        self.assertEqual("FAIL",check_answer_integrity(broken).result)

    def test_other_interaction_needs_a_different_checker(self):
        self.assertEqual("REVIEW_REQUIRED",check_answer_integrity({"id":"x","type":"interactive"}).result)

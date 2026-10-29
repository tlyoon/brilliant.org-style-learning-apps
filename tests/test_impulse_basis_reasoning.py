"""Regression for explicit answer-key/rationale mismatch in trilingual MCQ."""
from __future__ import annotations
import copy
import unittest

from app_generator.validation.impulse_basis_reasoning import (
    explicit_impulse_basis_rationale_defects,
)
from app_generator.validation.academic_acceptance_matrix import _answer_shape_defects

WRONG = {
    "en": "Option D confuses horizontal normal forces with external forces.",
    "ms": "Pilihan D mengelirukan daya normal mendatar dengan daya luar.",
    "zh": "\u9009\u9879 D \u6df7\u6dc6\u4e86\u6c34\u5e73\u652f\u6301\u529b\u4e0e\u5916\u529b\u6982\u5ff5\u3002",
}
RIGHT = {
    "en": "Option D does not require equal masses or opposite velocities.",
    "ms": "Pilihan D tidak memerlukan jisim sama atau halaju bertentangan.",
    "zh": "\u9009\u9879 D \u4e0d\u8981\u6c42\u8d28\u91cf\u76f8\u540c\u6216\u901f\u5ea6\u76f8\u53cd\u3002",
}
OPTION_D = {
    "en": "Equal masses and opposite velocities are prerequisites.",
    "ms": "Jisim sama dan halaju bertentangan ialah syarat.",
    "zh": "\u8d28\u91cf\u76f8\u540c\u548c\u901f\u5ea6\u76f8\u53cd\u662f\u5fc5\u8981\u6761\u4ef6\u3002",
}


def activity(logic: dict[str, str]) -> dict:
    return {
        "id":"mcq-impulse-approximation-basis","type":"mcq",
        "answerKey":{
            "correct":"opt-internal-forces-dominate",
            "options":[
                {"id":"opt-internal-forces-dominate","label":{"en":"A","ms":"A","zh":"A"}},
                {"id":"opt-external-forces-vanish","label":{"en":"B","ms":"B","zh":"B"}},
                {"id":"opt-inelastic-breaks-momentum","label":{"en":"C","ms":"C","zh":"C"}},
                {"id":"opt-equal-masses-required","label":OPTION_D},
            ],
        },
        "answerLogic":logic,
    }


class ImpulseBasisReasoningTests(unittest.TestCase):
    def test_detects_all_three_explicit_known_mismatches(self):
        sample=activity(WRONG)
        defects=explicit_impulse_basis_rationale_defects(sample)
        self.assertEqual(3,len(defects))
        self.assertTrue(all("option D rationale" in x for x in defects))
        self.assertEqual(3,len(_answer_shape_defects(sample)))

    def test_fixed_distractor_rationale_clears_concrete_error_but_not_academic_pass(self):
        sample=activity(RIGHT)
        self.assertEqual([],explicit_impulse_basis_rationale_defects(sample))
        self.assertEqual([],_answer_shape_defects(sample))

    def test_not_invent_a_failure_for_unknown_activity_or_changed_option(self):
        sample=activity(WRONG)
        sample["id"]="mcq-unrelated-topic"
        self.assertEqual([],explicit_impulse_basis_rationale_defects(sample))
        sample=activity(WRONG)
        sample["answerKey"]["options"][-1]["id"]="new-distractor"
        self.assertEqual([],explicit_impulse_basis_rationale_defects(sample))
        sample=activity(WRONG)
        sample["answerKey"]["correct"]="other-choice"
        self.assertEqual([],explicit_impulse_basis_rationale_defects(sample))

    def test_unrelated_explanation_without_explicit_wrong_normal_force_is_not_contradiction(self):
        sample=activity({key:{"en":"Option D is wrong.","ms":"Pilihan D salah.",
                              "zh":"\u9009\u9879 D \u9519\u8bef\u3002"}[key] for key in RIGHT})
        self.assertEqual([],explicit_impulse_basis_rationale_defects(sample))

    def test_bounded_detector_requires_actual_distractor_concepts(self):
        sample=copy.deepcopy(activity(WRONG))
        sample["answerKey"]["options"][-1]["label"]={
            "en":"Unrelated wording","ms":"Lain","zh":"\u5176\u4ed6"
        }
        self.assertEqual([],explicit_impulse_basis_rationale_defects(sample))


if __name__=="__main__":
    unittest.main()

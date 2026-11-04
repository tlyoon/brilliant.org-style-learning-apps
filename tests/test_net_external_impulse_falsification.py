"""Contradictory physics propositions must fail despite matching keyword signatures."""
from __future__ import annotations

import copy
import unittest

from app_generator.validation.impulse_v3_audit import (
    check_first_option, net_impulse_scope_conflicts,
)
from app_generator.validation.impulse_v3 import V3_LABEL


class NetExternalImpulseFalsificationTests(unittest.TestCase):
    def test_actual_corrected_trilingual_option_has_no_explicit_conflicts(self):
        report=check_first_option({"label":V3_LABEL})
        self.assertEqual(set(report),{"en","ms","zh"})
        for lang in ("en","ms","zh"):
            with self.subTest(lang=lang):
                self.assertEqual("BOUNDED_CONCEPT_PRESENT",report[lang]["status"])
                self.assertEqual([],report[lang]["explicitContradictionCodes"])

    def test_extra_contradictory_sentences_rejected_despite_all_positive_markers(self):
        bad={
            "en":" Nevertheless, each external force must be small.",
            "ms":" Walau bagaimanapun, setiap daya luar mesti kecil.",
            "zh":"但是每一个外力都必须很小。",
        }
        for lang,sentence in bad.items():
            with self.subTest(lang=lang):
                corrupted={"label":copy.deepcopy(V3_LABEL)}
                corrupted["label"][lang]+=sentence
                report=check_first_option(corrupted)
                self.assertEqual("REVIEW_REQUIRED",report[lang]["status"])
                self.assertIn("individual-forces-must-be-small",
                              report[lang]["explicitContradictionCodes"])
                self.assertNotIn(sentence.strip(),report[lang]["reason"])

    def test_negated_net_impulse_assertions_are_detected_in_three_languages(self):
        bad={
            "en":" The net external impulse is not negligible.",
            "ms":" Impuls luar bersih tidak boleh diabaikan.",
            "zh":"净外力冲量不可忽略。",
        }
        for lang,sentence in bad.items():
            with self.subTest(lang=lang):
                corrupted={"label":copy.deepcopy(V3_LABEL)}
                corrupted["label"][lang]+=sentence
                report=check_first_option(corrupted)
                self.assertEqual("REVIEW_REQUIRED",report[lang]["status"])
                self.assertIn("net-external-impulse-not-negligible",
                              report[lang]["explicitContradictionCodes"])

    def test_negation_scope_is_not_treated_as_a_contradiction(self):
        valid={
            "en":"does not require each external force individually to be small",
            "ms":"tidak mensyaratkan setiap daya luar secara individu adalah kecil",
            "zh":"不要求每一个外力都很小",
        }
        for lang,clause in valid.items():
            with self.subTest(lang=lang):
                self.assertFalse(net_impulse_scope_conflicts(clause,lang))

    def test_reject_unknown_language_or_non_text(self):
        with self.assertRaises(ValueError):
            net_impulse_scope_conflicts("any text","unknown")
        with self.assertRaises(ValueError):
            net_impulse_scope_conflicts(None,"en")


if __name__=="__main__":
    unittest.main()

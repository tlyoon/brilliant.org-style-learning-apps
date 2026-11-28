"""BSA265 V37: real historic equation/prose boundary regression tests.

A parser must not equate a false law with a true one, nor claim full
English/Malay/Chinese meaning because the math substrings match.
"""
from __future__ import annotations
import json
from pathlib import Path
from unittest import TestCase

from app_generator.validation import typed_scientific_semantic_alignment as qa

ROOT=Path(__file__).resolve().parents[1]

class EquationBoundaryRepair(TestCase):
    def test_english_is_and_for_are_prose_not_math(self):
        self.assertEqual(qa._eqs("p = m*v is fundamentally a vector"),["p=mv"])
        self.assertEqual(qa._eqs("p = m v is a vector"),["p=mv"])
        self.assertEqual(qa._eqs("F = m a for each particle"),["f=ma"])

    def test_malay_dan_and_ialah_are_prose_not_math(self):
        self.assertEqual(qa._eqs("K = 0.5 m v^2 dan magnitud momentum"),["k=0.5mv^2"])
        self.assertEqual(qa._eqs("p = m v ialah vektor"),["p=mv"])

    def test_exact_square_root_notation_in_three_languages(self):
        english=qa._eqs("p = sqrt(2mK). For equal kinetic energy")
        malay=qa._eqs("p = punca kuasa dua (2mK). Bagi tenaga sama")
        chinese=qa._eqs("p = \u6839\u53f7(2mK)\u3002")
        self.assertEqual(english,["p=sqrt(2mk)"])
        self.assertEqual(english,malay)
        self.assertEqual(english,chinese)
        self.assertNotEqual(qa._eqs("p = sqrt(2mK^2)"),english)

    def test_short_english_at_stays_outside_internal_force_equation(self):
        self.assertEqual(
            qa._eqs("F_12 + F_21 = 0 at every instant"),
            ["f_12+f_21=0"])

    def test_v_squared_is_not_lost_to_prose_boundary(self):
        self.assertEqual(qa._eqs("p = m v^2 is not linear momentum"),["p=mv^2"])
        self.assertTrue(qa._unmistakable_wrong_law("p = m v^2"))

    def test_false_force_equals_momentum_remains_detected(self):
        self.assertEqual(qa._eqs("F = p"),["f=p"])
        self.assertTrue(qa._unmistakable_wrong_law("F = p"))

    def test_legacy_dot_sentence_split_remains(self):
        self.assertEqual(qa._eqs("p = m v. As a vector"),["p=mv"])
        self.assertEqual(qa._eqs("p = m v. Kerana jisim"),["p=mv"])

    def test_genuine_18_activity_three_locale_semantic_QA_not_false_pass(self):
        data=json.loads((ROOT/"content/chapter-9/section-9-1/package.json").read_text(
            encoding="utf8"))["activities"]
        proof=qa.audit_reusable_scientific_alignment(data)
        self.assertEqual(proof["activitiesChecked"],18)
        self.assertEqual(proof["surfacesChecked"],222)
        self.assertEqual(proof["mathematicalDriftIssues"],0)
        self.assertFalse(proof["allScientificStatementsProven"])
        self.assertFalse(proof["trilingualSemanticEquivalenceProven"])
        self.assertFalse(proof["publicationAuthorized"])

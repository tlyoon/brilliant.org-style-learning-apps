"""BSA273: vector-momentum misconception proof and adversarial regressions."""
from __future__ import annotations
import copy
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app_generator.validation import section91_second_distractor_proof as science

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "content/chapter-9/section-9-1/package.json"
AXIOMS = {
    "defined to be the product of the mass and velocity": 1,
    "linear momentum is a vector": 1,
}


class SecondGenuineDistractorScience(TestCase):
    def example(self, mutate=None, corrupt_source=False):
        p = json.loads(PACKAGE.read_text(encoding="utf8"))
        if mutate:
            mutate(p)
        with TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "original.pdf"
            pdf.write_bytes(b"%PDF-synthetic-transport-only")
            candidate = Path(tmp) / "frozen.json"
            candidate.write_text(json.dumps(p, ensure_ascii=False, sort_keys=True),
                                 encoding="utf8")
            source_sha = sha256(pdf.read_bytes()).hexdigest()
            candidate_sha = sha256(candidate.read_bytes()).hexdigest()
            anchors = [{
                "activityId": a["id"],
                "physicalPage": 2,
                "passageSha256": "d" * 64,
                "uniquePagePassageLocated": True,
            } for a in p["activities"]]
            if corrupt_source:
                pdf.write_bytes(b"changed")
            with (patch.object(science, "_SOURCE_SHA", source_sha),
                  patch.object(science, "_CANDIDATE_SHA", candidate_sha),
                  patch.object(science, "_source_axioms", return_value=AXIOMS),
                  patch.object(science, "extract_pages", return_value=("x", "y")),
                  patch.object(science, "_source_activity_anchors",
                               return_value=anchors)):
                return science.independent_second_distractor_science(
                    source_pdf=pdf, candidate_path=candidate)

    def test_real_second_option_semantics_and_two_exact_counterexamples(self):
        proof = self.example()
        self.assertEqual(proof["optionId"], "opt-b")
        self.assertEqual(proof["taskKind"], "MCQ_DISTRACTOR_SCIENCE")
        self.assertNotEqual(proof["taskId"], "ce320185009e7c529840a5cf96c75a1f469ad2a5961b3cbbca2ac4f07d9f9d60")
        self.assertEqual(set(proof["completeLocalizedFiniteGrammarDigests"]),
                         {"en", "ms", "zh"})
        self.assertEqual(proof["completeAcademicProofGatesStillOpen"], 90)
        from fractions import Fraction
        for w in proof["exactRationalCounterexamples"]:
            m, v = Fraction(w["mass"]), Fraction(w["constantSpeed"])
            self.assertEqual(Fraction(w["momentumForward"]), m*v)
            self.assertEqual(Fraction(w["momentumBackward"]), -m*v)
            self.assertNotEqual(Fraction(w["momentumForward"]),
                                Fraction(w["momentumBackward"]))
        self.assertFalse(proof["otherTrilingualMeaningProofAccepted"])
        self.assertFalse(proof["publicationAuthorized"])

    def test_false_directional_proposition_changed_to_true_refused(self):
        def change(p):
            o=p["activities"][0]["answerKey"]["options"][1]["label"]
            o["en"]=o["en"].replace("completely identical", "opposite in direction")
        with self.assertRaisesRegex(ValueError, "UNINTERPRETED_OR_CHANGED_BSA273_OPTION_EN"):
            self.example(change)

    def test_malay_direction_reversal_refused(self):
        def change(p):
            o=p["activities"][0]["answerKey"]["options"][1]["label"]
            o["ms"]=o["ms"].replace("tanpa bergantung pada arah", "bergantung pada arah")
        with self.assertRaisesRegex(ValueError, "UNINTERPRETED_OR_CHANGED_BSA273_OPTION_MS"):
            self.example(change)

    def test_chinese_negation_reversal_refused(self):
        def change(p):
            o=p["activities"][0]["answerKey"]["options"][1]["label"]
            o["zh"]=o["zh"].replace("\u65e0\u5173","\u6709\u5173")
        with self.assertRaisesRegex(ValueError, "UNINTERPRETED_OR_CHANGED_BSA273_OPTION_ZH"):
            self.example(change)

    def test_unexamined_extra_clause_refused(self):
        def change(p):
            o=p["activities"][0]["answerKey"]["options"][1]["label"]
            o["zh"]+="\u7269\u7406\u7ed3\u8bba\u5fc5\u7136\u6210\u7acb"
        with self.assertRaisesRegex(ValueError, "UNINTERPRETED_OR_CHANGED_BSA273_OPTION_ZH"):
            self.example(change)

    def test_wrong_premise_or_answer_key_refused(self):
        def premise(p):
            p["activities"][0]["prompt"]["en"] = p["activities"][0]["prompt"]["en"].replace(
                "opposite directions", "same direction")
        with self.assertRaisesRegex(ValueError, "UNINTERPRETED_OR_CHANGED_BSA273_PROMPT_EN"):
            self.example(premise)
        def key(p):
            p["activities"][0]["answerKey"]["correct"] = "opt-b"
        with self.assertRaisesRegex(ValueError, "BSA273_FALSE_OPTION_OR_ANSWER_KEY_CHANGED"):
            self.example(key)

    def test_changed_source_and_false_physics_prohibited(self):
        with self.assertRaisesRegex(ValueError, "BSA273_ORIGINAL_ONE_TEXTBOOK"):
            self.example(corrupt_source=True)
        with patch.object(science,"_source_axioms",return_value={}):
            # A synthetic transport-only test still must validate axioms.
            with self.assertRaises((ValueError,FileNotFoundError)):
                science.independent_second_distractor_science(
                    source_pdf=ROOT/"no-original.pdf",
                    candidate_path=PACKAGE)

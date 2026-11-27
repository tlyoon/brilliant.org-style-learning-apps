"""BSA292 explanation science, authentic-source gate and falsification."""
from copy import deepcopy
from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app_generator.validation import section91_vector_explanation_proof as p
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs

_REAL_SOURCE_SHA = p._SOURCE_SHA
_PACKAGE = Path("content/chapter-9/section-9-1/package.json")


class VectorExplanationScience(TestCase):
    def test_exact_models_and_negative_mass_falsification(self):
        for row in p._models():
            self.assertEqual(F(row["momentumA"]), -F(row["momentumB"]))
            self.assertEqual(F(row["momentumSum"]), 0)
            self.assertGreater(F(row["momentumA"]), 0)
        for mass, speed in ((F(0), F(2)), (F(-1), F(2)), (F(2), F(0))):
            with self.assertRaises(ValueError):
                p._model(mass, speed)

    def test_original_gate_and_restart_recomputation(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "source.pdf"
            candidate = Path(folder) / "candidate.json"
            source.write_bytes(b"%PDF-synthetic")
            candidate.write_bytes(_PACKAGE.read_bytes())
            anchors = [{"activityId": p._ACTIVITY,
                        "uniquePagePassageLocated": True,
                        "physicalPage": 1, "passageSha256": "a" * 64}]
            with patch.object(p, "extract_pages", side_effect=AssertionError("source must be pinned")):
                with self.assertRaisesRegex(ValueError, "AUTHENTIC_ONE_SERWAY"):
                    p.independently_prove_vector_explanation(source_pdf=source, candidate_path=candidate)
            with (patch.object(p, "_SOURCE_SHA", sha256(source.read_bytes()).hexdigest()),
                  patch.object(p, "_CANDIDATE_SHA", sha256(candidate.read_bytes()).hexdigest()),
                  patch.object(p, "_source_axioms", return_value={
                      "linear momentum is a vector": 1,
                      "defined to be the product of the mass and velocity": 1}),
                  patch.object(p, "extract_pages", return_value=["synthetic"]),
                  patch.object(p, "_source_activity_anchors", return_value=anchors),
                  patch.object(p, "plan_full_semantic_proofs", side_effect=lambda **kw:
                      plan_full_semantic_proofs(package=kw["package"], source_sha256=_REAL_SOURCE_SHA))):
                proof = p.independently_prove_vector_explanation(source_pdf=source, candidate_path=candidate)
                p.independently_check_vector_explanation_witness(proof)
                for field in ("momentumA", "momentumSum", "equalMagnitude"):
                    forged = deepcopy(proof)
                    forged["models"][0][field] = "1" if field != "equalMagnitude" else False
                    forged["witnessSha256"] = p._digest({k:v for k,v in forged.items() if k != "witnessSha256"})
                    with self.subTest(field=field), self.assertRaises(ValueError):
                        p.independently_check_vector_explanation_witness(forged)
                false_pass = {**proof, "academicTaskAccepted": True}
                false_pass["witnessSha256"] = p._digest({k:v for k,v in false_pass.items() if k != "witnessSha256"})
                with self.assertRaises(ValueError):
                    p.independently_check_vector_explanation_witness(false_pass)
                source.write_bytes(b"%PDF-mutated")
                with self.assertRaisesRegex(ValueError, "AUTHENTIC_ONE_SERWAY"):
                    p.independently_prove_vector_explanation(source_pdf=source, candidate_path=candidate)

    def test_frozen_complete_language_surfaces(self):
        activity = json.loads(_PACKAGE.read_text(encoding="utf8"))["activities"][0]
        self.assertEqual(p._locale_hashes(activity["prompt"], p._PROMPT), p._PROMPT)
        self.assertEqual(p._locale_hashes(activity["explanation"], p._EXPLANATION), p._EXPLANATION)
        changed = dict(activity["explanation"])
        changed["zh"] += "!"
        with self.assertRaises(ValueError):
            p._locale_hashes(changed, p._EXPLANATION)

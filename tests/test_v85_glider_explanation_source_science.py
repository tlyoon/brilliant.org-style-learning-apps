"""MCQ04 explanation: exact vector and scalar energy science and fail-closed original-source gate."""
from copy import deepcopy
from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app_generator.validation import section91_glider_explanation_proof as p
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs

_PACKAGE = Path("content/chapter-9/section-9-1/package.json")
_REAL_SOURCE_SHA = p._SOURCE_SHA


class GliderExplanationScience(TestCase):
    def test_exact_vector_scalar_contrast_and_falsification(self):
        for row in p._models():
            self.assertEqual(F(row["systemMomentum"]), 0)
            self.assertGreater(F(row["systemKineticEnergy"]), 0)
            self.assertEqual(F(row["systemKineticEnergy"]), 2 * F(row["kineticEnergyEach"]))
        for values in ((F(0), F(1)), (F(1), F(0)), (F(1), F(-1))):
            with self.assertRaises(ValueError):
                p._model(*values)

    def test_source_candidate_restart_and_forged_witness(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "source.pdf"
            candidate = Path(folder) / "candidate.json"
            source.write_bytes(b"%PDF-synthetic")
            candidate.write_bytes(_PACKAGE.read_bytes())
            anchors = [{}, {}, {}, {"activityId": p._ACTIVITY,
                                "uniquePagePassageLocated": True,
                                "physicalPage": 3, "passageSha256": "a" * 64}]
            with patch.object(p, "extract_pages", side_effect=AssertionError("unpinned source extracted")):
                with self.assertRaisesRegex(ValueError, "AUTHENTIC_SERWAY"):
                    p.independently_prove_glider_explanation(source_pdf=source, candidate_path=candidate)
            with (patch.object(p, "_SOURCE_SHA", sha256(source.read_bytes()).hexdigest()),
                  patch.object(p, "_CANDIDATE_SHA", sha256(candidate.read_bytes()).hexdigest()),
                  patch.object(p, "_source_axioms", return_value={"linear momentum is a vector": 1, "defined to be the product of the mass and velocity": 1, "kinetic energy can transform": 1}),
                  patch.object(p, "extract_pages", return_value=["synthetic"]),
                  patch.object(p, "_source_activity_anchors", return_value=anchors),
                  patch.object(p, "plan_full_semantic_proofs", side_effect=lambda **kw:
                      plan_full_semantic_proofs(package=kw["package"], source_sha256=_REAL_SOURCE_SHA))):
                proof = p.independently_prove_glider_explanation(source_pdf=source, candidate_path=candidate)
                self.assertEqual(proof, p.independently_prove_glider_explanation(source_pdf=source, candidate_path=candidate))
                for key, value in (("systemMomentum", "1"), ("systemKineticEnergy", "0"),
                                   ("scalarKineticEnergyAdds", False)):
                    forged = deepcopy(proof)
                    forged["models"][0][key] = value
                    forged["witnessSha256"] = p._digest({k: v for k, v in forged.items() if k != "witnessSha256"})
                    with self.subTest(key=key), self.assertRaises(ValueError):
                        p.independently_check_glider_explanation_witness(forged)
                candidate.write_bytes(candidate.read_bytes() + b" ")
                with self.assertRaisesRegex(ValueError, "AUTHENTIC_SERWAY"):
                    p.independently_prove_glider_explanation(source_pdf=source, candidate_path=candidate)

    def test_source_change_during_extraction_is_rejected(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "source.pdf"
            candidate = Path(folder) / "candidate.json"
            source.write_bytes(b"%PDF-synthetic")
            candidate.write_bytes(_PACKAGE.read_bytes())
            def mutate_source(_):
                source.write_bytes(b"%PDF-mutated")
                return ["synthetic"]
            with (patch.object(p, "_SOURCE_SHA", sha256(source.read_bytes()).hexdigest()),
                  patch.object(p, "_CANDIDATE_SHA", sha256(candidate.read_bytes()).hexdigest()),
                  patch.object(p, "_source_axioms", return_value={
                      "linear momentum is a vector": 1,
                      "defined to be the product of the mass and velocity": 1,
                      "kinetic energy can transform": 1}),
                  patch.object(p, "extract_pages", side_effect=mutate_source),
                  patch.object(p, "_source_activity_anchors", return_value=[])):
                with self.assertRaisesRegex(ValueError, "SOURCE_CHANGED_DURING_EXTRACTION"):
                    p.independently_prove_glider_explanation(source_pdf=source, candidate_path=candidate)

    def test_complete_frozen_language_surface(self):
        activity = json.loads(_PACKAGE.read_text(encoding="utf8"))["activities"][3]
        self.assertEqual(p._locale_hashes(activity["prompt"], p._PROMPT), p._PROMPT)
        self.assertEqual(p._locale_hashes(activity["explanation"], p._EXPLANATION), p._EXPLANATION)
        altered = dict(activity["explanation"])
        altered["ms"] += " bukan"
        with self.assertRaises(ValueError):
            p._locale_hashes(altered, p._EXPLANATION)

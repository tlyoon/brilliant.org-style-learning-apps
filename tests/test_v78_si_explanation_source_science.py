"""MCQ02 exact dimension and vector science with source gate falsification."""
from copy import deepcopy
from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app_generator.validation import section91_si_explanation_proof as p
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs

_REAL_SOURCE_SHA = p._SOURCE_SHA
_PACKAGE = Path("content/chapter-9/section-9-1/package.json")


class SiExplanationScience(TestCase):
    def test_exact_models_and_adversarial_inputs(self):
        for row in p._models():
            self.assertEqual(row["momentumDimension"], [1, 1, -1])
            self.assertEqual(F(row["momentumKilogramMetersPerSecond"][0]),
                             F(row["massKg"]) * F(row["velocityMetersPerSecond"][0]))
        for values in ((F(0),F(1),F(0)), (F(-1),F(1),F(0)), (F(1),F(0),F(0))):
            with self.assertRaises(ValueError):
                p._model(*values)

    def test_original_gate_restart_and_fault_injection(self):
        with TemporaryDirectory() as folder:
            source = Path(folder)/"source.pdf"
            candidate = Path(folder)/"candidate.json"
            source.write_bytes(b"%PDF-synthetic")
            candidate.write_bytes(_PACKAGE.read_bytes())
            anchors = [{}, {"activityId":p._ACTIVITY,"uniquePagePassageLocated":True,
                            "physicalPage":2,"passageSha256":"a"*64}]
            with patch.object(p,"extract_pages",side_effect=AssertionError("unpinned source extracted")):
                with self.assertRaisesRegex(ValueError,"AUTHENTIC_ONE_SERWAY"):
                    p.independently_prove_si_explanation(source_pdf=source,candidate_path=candidate)
            with (patch.object(p,"_SOURCE_SHA",sha256(source.read_bytes()).hexdigest()),
                  patch.object(p,"_CANDIDATE_SHA",sha256(candidate.read_bytes()).hexdigest()),
                  patch.object(p,"_source_axioms",return_value={
                      "linear momentum is a vector":1,
                      "defined to be the product of the mass and velocity":1,
                      "dimensions ml/t":1}),
                  patch.object(p,"extract_pages",return_value=["synthetic"]),
                  patch.object(p,"_source_activity_anchors",return_value=anchors),
                  patch.object(p,"plan_full_semantic_proofs",side_effect=lambda **kw:
                      plan_full_semantic_proofs(package=kw["package"],source_sha256=_REAL_SOURCE_SHA))):
                proof=p.independently_prove_si_explanation(source_pdf=source,candidate_path=candidate)
                p.independently_check_si_explanation_witness(proof)
                self.assertEqual(proof,p.independently_prove_si_explanation(source_pdf=source,candidate_path=candidate))
                for field,value in (("momentumDimension",[1,2,-1]),
                                    ("momentumIsVector",False),
                                    ("momentumKilogramMetersPerSecond",["0","0"])):
                    forged=deepcopy(proof)
                    forged["models"][0][field]=value
                    forged["witnessSha256"]=p._digest({k:v for k,v in forged.items() if k!="witnessSha256"})
                    with self.subTest(field=field),self.assertRaises(ValueError):
                        p.independently_check_si_explanation_witness(forged)
                candidate.write_bytes(candidate.read_bytes()+b" ")
                with self.assertRaisesRegex(ValueError,"AUTHENTIC_ONE_SERWAY"):
                    p.independently_prove_si_explanation(source_pdf=source,candidate_path=candidate)

    def test_frozen_three_language_explanation(self):
        activity=json.loads(_PACKAGE.read_text(encoding="utf8"))["activities"][1]
        self.assertEqual(p._locale_hashes(activity["explanation"],p._EXPLANATION),p._EXPLANATION)
        changed=dict(activity["explanation"])
        changed["ms"] += " bukan"
        with self.assertRaises(ValueError):
            p._locale_hashes(changed,p._EXPLANATION)

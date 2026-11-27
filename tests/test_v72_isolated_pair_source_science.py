"""BSA290: MCQ07 independent source and exact-energy falsification controls."""
from copy import deepcopy
from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app_generator.validation import section91_isolated_pair_false_options_proof as p
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs

_REAL_SOURCE_SHA=p._SOURCE_SHA
_PACKAGE=Path("content/chapter-9/section-9-1/package.json")


class IsolatedPairScience(TestCase):
    def test_exact_pair_countermodels_and_falsification(self):
        self.assertEqual(len(set(p._TASKS.values())),3)
        for row in p._models():
            self.assertEqual(F(row["nadiaMomentum"])+F(row["leoMomentum"]),0)
            self.assertNotEqual(F(row["nadiaMomentum"]),0)
            self.assertEqual(F(row["nadiaForce"]),-F(row["leoForce"]))
            self.assertEqual(F(row["nadiaForce"]),F(row["nadiaMomentum"])/F(row["duration"]))
        for args in ((F(0),F(3),F(4),F(2)),(F(2),F(3),F(0),F(2)),
                     (F(2),F(3),F(4),F(0))):
            with self.subTest(args=args),self.assertRaises(ValueError):
                p._model(*args)

    def test_original_gate_queue_and_restart_recomputation(self):
        with TemporaryDirectory() as folder:
            source=Path(folder)/"source.pdf"
            candidate=Path(folder)/"candidate.json"
            source.write_bytes(b"%PDF-synthetic")
            candidate.write_bytes(_PACKAGE.read_bytes())
            anchors=[{} for _ in range(18)]
            anchors[7]={"activityId":p._ACTIVITY,"uniquePagePassageLocated":True,
                        "physicalPage":2,"passageSha256":"a"*64}
            with patch.object(p,"extract_pages",side_effect=AssertionError("source must be pinned")):
                with self.assertRaisesRegex(ValueError,"AUTHENTIC_ONE_SERWAY"):
                    p.independently_prove_isolated_pair_false_option(
                        source_pdf=source,candidate_path=candidate,option_id="opt-single-particle-conserved")
            with (patch.object(p,"_SOURCE_SHA",sha256(source.read_bytes()).hexdigest()),
                  patch.object(p,"_CANDIDATE_SHA",sha256(candidate.read_bytes()).hexdigest()),
                  patch.object(p,"_source_axioms",return_value={
                      "isolated system":3, "third law":1,
                      "time rate of change of the linear momentum":1,
                      "defined to be the product of the mass and velocity":1}),
                  patch.object(p,"extract_pages",return_value=["synthetic"]),
                  patch.object(p,"_source_activity_anchors",return_value=anchors),
                  patch.object(p,"plan_full_semantic_proofs",side_effect=lambda **kw:
                      plan_full_semantic_proofs(package=kw["package"],source_sha256=_REAL_SOURCE_SHA))):
                for option in p._TASKS:
                    proof=p.independently_prove_isolated_pair_false_option(
                        source_pdf=source,candidate_path=candidate,option_id=option)
                    p.independently_check_isolated_pair_witness(proof)
                    self.assertFalse(proof["academicTaskAccepted"])
                    for changed in ("nadiaMomentum","nadiaForce","leoMass"):
                        forged=deepcopy(proof)
                        forged["models"][0][changed]="0"
                        forged["witnessSha256"]=p._digest({k:v for k,v in forged.items() if k!="witnessSha256"})
                        with self.subTest(option=option,changed=changed),self.assertRaises(ValueError):
                            p.independently_check_isolated_pair_witness(forged)
                    falsely_admitted=deepcopy(proof)
                    falsely_admitted["academicTaskAccepted"]=True
                    falsely_admitted["witnessSha256"]=p._digest({
                        k:v for k,v in falsely_admitted.items() if k!="witnessSha256"})
                    with self.assertRaisesRegex(ValueError,"UNTRUSTED_ISOLATED_PAIR"):
                        p.independently_check_isolated_pair_witness(falsely_admitted)
                source.write_bytes(b"%PDF-mutated")
                with self.assertRaisesRegex(ValueError,"AUTHENTIC_ONE_SERWAY"):
                    p.independently_prove_isolated_pair_false_option(
                        source_pdf=source,candidate_path=candidate,option_id="opt-single-particle-conserved")

    def test_all_localized_sentences_are_pinned(self):
        activity=json.loads(_PACKAGE.read_text(encoding="utf8"))["activities"][7]
        self.assertEqual(p._locales(activity["prompt"],p._PROMPT),p._PROMPT)
        for option in activity["answerKey"]["options"][1:]:
            self.assertEqual(p._locales(option["label"],p._OPTIONS[option["id"]]),
                             p._OPTIONS[option["id"]])
            changed=dict(option["label"])
            changed["zh"]+="!"
            with self.assertRaises(ValueError):
                p._locales(changed,p._OPTIONS[option["id"]])

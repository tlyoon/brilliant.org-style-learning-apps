"""BSA291 spring and rail impulse proof falsification and source controls."""
from copy import deepcopy
from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app_generator.validation import section91_spring_buffer_false_options_proof as p
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs

_REAL_SOURCE_SHA=p._SOURCE_SHA
_PACKAGE=Path("content/chapter-9/section-9-1/package.json")


class SpringBufferScience(TestCase):
    def test_exact_countermodels_and_falsification(self):
        self.assertEqual(len(set(p._OPTIONS_ORDER)),3)
        for row in p._models():
            self.assertEqual(F(row["initialKineticEnergy"]),F(row["springPotentialEnergy"]))
            self.assertEqual(F(row["initialMomentum"]),F(row["railImpulse"]))
            self.assertEqual(F(row["thermalEnergy"]),0)
            self.assertNotEqual(row["momentumDimension"],row["energyDimension"])
        for args in ((F(0),F(2),F(2)),(F(3),F(0),F(2)),(F(3),F(2),F(0))):
            with self.subTest(args=args),self.assertRaises(ValueError):
                p._model(*args)

    def test_original_gate_queue_and_restart_recomputation(self):
        with TemporaryDirectory() as folder:
            source=Path(folder)/"source.pdf"
            candidate=Path(folder)/"candidate.json"
            source.write_bytes(b"%PDF-synthetic")
            candidate.write_bytes(_PACKAGE.read_bytes())
            anchors=[{} for _ in range(18)]
            anchors[8]={"activityId":p._ACTIVITY,"uniquePagePassageLocated":True,
                        "physicalPage":3,"passageSha256":"a"*64}
            with patch.object(p,"extract_pages",side_effect=AssertionError("source must be pinned")):
                with self.assertRaisesRegex(ValueError,"AUTHENTIC_ONE_SERWAY"):
                    p.independently_prove_spring_buffer_false_option(
                        source_pdf=source,candidate_path=candidate,
                        option_id="opt-potential-momentum-stored")
            with (patch.object(p,"_SOURCE_SHA",sha256(source.read_bytes()).hexdigest()),
                  patch.object(p,"_CANDIDATE_SHA",sha256(candidate.read_bytes()).hexdigest()),
                  patch.object(p,"_source_axioms",return_value={
                      "kinetic energy can transform":1,
                      "only one type of linear momentum":1,
                      "isolated system":3,
                      "defined to be the product of the mass and velocity":1}),
                  patch.object(p,"extract_pages",return_value=["synthetic"]),
                  patch.object(p,"_source_activity_anchors",return_value=anchors),
                  patch.object(p,"plan_full_semantic_proofs",side_effect=lambda **kw:
                      plan_full_semantic_proofs(package=kw["package"],source_sha256=_REAL_SOURCE_SHA))):
                for option in p._OPTIONS_ORDER:
                    proof=p.independently_prove_spring_buffer_false_option(
                        source_pdf=source,candidate_path=candidate,option_id=option)
                    p.independently_check_spring_buffer_witness(proof)
                    for changed in ("initialMomentum","springPotentialEnergy","railImpulse"):
                        forged=deepcopy(proof)
                        forged["models"][0][changed]="0"
                        forged["witnessSha256"]=p._digest({k:v for k,v in forged.items() if k!="witnessSha256"})
                        with self.subTest(option=option,changed=changed),self.assertRaises(ValueError):
                            p.independently_check_spring_buffer_witness(forged)
                    false_pass={**proof,"academicTaskAccepted":True}
                    false_pass["witnessSha256"]=p._digest({k:v for k,v in false_pass.items() if k!="witnessSha256"})
                    with self.assertRaisesRegex(ValueError,"UNTRUSTED_SPRING_BUFFER"):
                        p.independently_check_spring_buffer_witness(false_pass)
                source.write_bytes(b"%PDF-mutated")
                with self.assertRaisesRegex(ValueError,"AUTHENTIC_ONE_SERWAY"):
                    p.independently_prove_spring_buffer_false_option(
                        source_pdf=source,candidate_path=candidate,option_id="opt-both-turn-to-heat")

    def test_all_localized_sentences_are_pinned(self):
        activity=json.loads(_PACKAGE.read_text(encoding="utf8"))["activities"][8]
        self.assertEqual(p._locales(activity["prompt"],p._PROMPT),p._PROMPT)
        for option in activity["answerKey"]["options"][1:]:
            self.assertEqual(p._locales(option["label"],p._OPTIONS[option["id"]]),p._OPTIONS[option["id"]])
            changed=dict(option["label"])
            changed["ms"]+="!"
            with self.assertRaises(ValueError):
                p._locales(changed,p._OPTIONS[option["id"]])

    def test_sample_ids_are_not_owner_task_pins(self):
        sample=json.loads(_PACKAGE.read_text(encoding="utf8"))
        queue=plan_full_semantic_proofs(package=sample,source_sha256=_REAL_SOURCE_SHA)
        ids=[t["taskId"] for t in queue["tasks"] if
             t["activityId"]==p._ACTIVITY and t["kind"]=="MCQ_DISTRACTOR_SCIENCE"]
        self.assertEqual(len(set(ids)),3)
        self.assertFalse(hasattr(p,"_TASKS"))
        revised=deepcopy(sample)
        revised["activities"][0]["id"]+="-private-revision"
        changed=plan_full_semantic_proofs(package=revised,source_sha256=_REAL_SOURCE_SHA)
        changed_ids=[t["taskId"] for t in changed["tasks"] if
                     t["activityId"]==p._ACTIVITY and t["kind"]=="MCQ_DISTRACTOR_SCIENCE"]
        self.assertNotEqual(ids,changed_ids)
        self.assertEqual(sample["activities"][8],revised["activities"][8])

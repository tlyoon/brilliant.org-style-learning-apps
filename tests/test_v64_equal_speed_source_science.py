"""BSA284 MCQ06 exact-rational source gate and adversarial witnesses."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app_generator.validation import section91_equal_speed_false_options_proof as p
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs

_REAL_SOURCE_SHA = p._SOURCE_SHA


def witness(option: str) -> dict:
    body = {"taskId": p._TASKS[option], "optionId": option, "falseClaim": p._CLAIMS[option],
            "sourceSha256": p._SOURCE_SHA, "candidateSha256": p._CANDIDATE_SHA,
            "promptLocaleSha256": p._PROMPT, "optionLocaleSha256": p._OPTIONS[option],
            "models": p._models(), "academicTaskAccepted": False,
            "completeAcademicProofGatesStillOpen": 90, "newProviderCalls": 0,
            "publicationAuthorized": False}
    return {**body, "witnessSha256": p._digest(body)}


class EqualSpeedScience(TestCase):
    def test_three_new_tasks_and_two_distinct_exact_vector_models(self):
        self.assertEqual(len(set(p._TASKS.values())), 3)
        self.assertEqual(len(set(p._CLAIMS.values())), 3)
        for option in p._TASKS:
            p.independently_check_equal_speed_witness(witness(option))
        for row in p._models():
            t, c, v = F(row["truckMass"]), F(row["carMass"]), F(row["commonSpeed"])
            self.assertGreater(t, c)
            self.assertGreater(c, 0)
            self.assertGreater(v, 0)
            self.assertEqual(tuple(map(F, row["truckMomentumEastNorth"])), (0, t*v))
            self.assertEqual(tuple(map(F, row["carMomentumEastNorth"])), (c*v, 0))
            self.assertGreater(t*v, c*v)

    def test_rehashed_science_and_status_tampering_is_rejected(self):
        changes = (("models", lambda x: x["models"][0].update(truckMagnitude="0")),
                   ("models", lambda x: x["models"][0].update(dotProduct="1")),
                   ("models", lambda x: x["models"][1].update(carMass="8")),
                   ("sourceSha256", lambda x: x.update(sourceSha256="0"*64)),
                   ("academicTaskAccepted", lambda x: x.update(academicTaskAccepted=True)),
                   ("completeAcademicProofGatesStillOpen", lambda x: x.update(completeAcademicProofGatesStillOpen=89)),
                   ("optionLocaleSha256", lambda x: x["optionLocaleSha256"].update(zh="0"*64)))
        for name, change in changes:
            proof = deepcopy(witness("opt-b"))
            change(proof)
            proof["witnessSha256"] = p._digest({k: v for k, v in proof.items() if k != "witnessSha256"})
            with self.subTest(name=name), self.assertRaises(ValueError):
                p.independently_check_equal_speed_witness(proof)

    def test_complete_frozen_three_language_clauses_reject_edits(self):
        activity = json.loads(Path("content/chapter-9/section-9-1/package.json").read_text(encoding="utf8"))["activities"][5]
        self.assertEqual(p._locale_digests(activity["prompt"], p._PROMPT), p._PROMPT)
        for option in activity["answerKey"]["options"][1:]:
            expected = p._OPTIONS[option["id"]]
            self.assertEqual(p._locale_digests(option["label"], expected), expected)
            for lang in expected:
                changed = dict(option["label"])
                changed[lang] += " not"
                with self.subTest(option=option["id"], lang=lang), self.assertRaises(ValueError):
                    p._locale_digests(changed, expected)
        with self.assertRaises(ValueError):
            p._locale_digests({"en": "a", "ms": "b"}, p._PROMPT)

    def test_degenerate_models_rejected(self):
        for args in ((F(1), F(1), F(2)), (F(1), F(2), F(2)),
                     (F(2), F(1), F(0)), (F(-2), F(1), F(1))):
            with self.subTest(args=args), self.assertRaises(ValueError):
                p._model(*args)

    def test_producer_requires_exact_source_and_candidate_before_extraction(self):
        with TemporaryDirectory() as folder:
            source = Path(folder)/"source.pdf"
            candidate = Path(folder)/"candidate.json"
            source.write_bytes(b"%PDF-synthetic")
            candidate.write_bytes(Path("content/chapter-9/section-9-1/package.json").read_bytes())
            with patch.object(p, "extract_pages", side_effect=AssertionError("must not extract")):
                with self.assertRaisesRegex(ValueError, "AUTHENTIC_ONE_SERWAY"):
                    p.independently_prove_equal_speed_false_option(
                        source_pdf=source, candidate_path=candidate, option_id="opt-b")

    def test_source_bound_producer_exercises_original_check_and_task_derivation(self):
        # The owner PDF is absent here. A synthetic source tests the exact
        # digest/anchor/queue control flow; it cannot grant owner acceptance.
        with TemporaryDirectory() as folder:
            source = Path(folder)/"source.pdf"
            candidate = Path(folder)/"candidate.json"
            source.write_bytes(b"%PDF-synthetic")
            candidate.write_bytes(Path("content/chapter-9/section-9-1/package.json").read_bytes())
            anchors = [{} for _ in range(18)]
            anchors[5] = {"activityId": p._ACTIVITY, "uniquePagePassageLocated": True,
                          "physicalPage": 1, "passageSha256": "a"*64}
            with (patch.object(p, "_SOURCE_SHA", sha256(source.read_bytes()).hexdigest()),
                  patch.object(p, "_CANDIDATE_SHA", sha256(candidate.read_bytes()).hexdigest()),
                  patch.object(p, "_source_axioms", return_value={
                      "linear momentum is a vector": 1,
                      "defined to be the product of the mass and velocity": 1}),
                  patch.object(p, "extract_pages", return_value=["synthetic"]),
                  patch.object(p, "_source_activity_anchors", return_value=anchors),
                  patch.object(p, "plan_full_semantic_proofs", side_effect=lambda **kw:
                      plan_full_semantic_proofs(package=kw["package"], source_sha256=_REAL_SOURCE_SHA))):
                for option in p._TASKS:
                    proof = p.independently_prove_equal_speed_false_option(
                        source_pdf=source, candidate_path=candidate, option_id=option)
                    p.independently_check_equal_speed_witness(proof)
                    self.assertFalse(proof["academicTaskAccepted"])
                source.write_bytes(b"%PDF-changed")
                with self.assertRaisesRegex(ValueError, "AUTHENTIC_ONE_SERWAY"):
                    p.independently_prove_equal_speed_false_option(
                        source_pdf=source, candidate_path=candidate, option_id="opt-b")

"""BSA292 explanation science, authentic-source gate and falsification."""
from copy import deepcopy
from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless
from unittest.mock import patch
import os

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

    def test_whole_candidate_revision_rederives_explanation_id(self):
        package = json.loads(_PACKAGE.read_text(encoding="utf8"))
        original = plan_full_semantic_proofs(package=package, source_sha256=_REAL_SOURCE_SHA)
        package["activities"][-1]["id"] += "-revised"
        revised = plan_full_semantic_proofs(package=package, source_sha256=_REAL_SOURCE_SHA)
        def explanation_id(queue):
            return next(row["taskId"] for row in queue["tasks"] if
                        row["activityId"] == p._ACTIVITY and
                        row["kind"] == "COMPLETE_SCIENTIFIC_MEANING" and
                        row["surfacePath"] == "explanation")
        self.assertNotEqual(explanation_id(original), explanation_id(revised))
        with TemporaryDirectory() as folder:
            source = Path(folder) / "source.pdf"
            candidate = Path(folder) / "candidate.json"
            source.write_bytes(b"%PDF-synthetic")
            candidate.write_text(json.dumps(package, ensure_ascii=False), encoding="utf8")
            anchors = [{"activityId": p._ACTIVITY, "uniquePagePassageLocated": True,
                        "physicalPage": 1, "passageSha256": "a" * 64}]
            with (patch.object(p, "_SOURCE_SHA", sha256(source.read_bytes()).hexdigest()),
                  patch.object(p, "_CANDIDATE_SHA", sha256(candidate.read_bytes()).hexdigest()),
                  patch.object(p, "_source_axioms", return_value={
                      "linear momentum is a vector": 1,
                      "defined to be the product of the mass and velocity": 1}),
                  patch.object(p, "extract_pages", return_value=["synthetic"]),
                  patch.object(p, "_source_activity_anchors", return_value=anchors)):
                proof = p.independently_prove_vector_explanation(
                    source_pdf=source, candidate_path=candidate)
                source_bound = plan_full_semantic_proofs(
                    package=package, source_sha256=sha256(source.read_bytes()).hexdigest())
                self.assertEqual(proof["taskId"], explanation_id(source_bound))
                candidate.write_bytes(candidate.read_bytes() + b" ")
                with self.assertRaisesRegex(ValueError, "AUTHENTIC_ONE_SERWAY"):
                    p.independently_prove_vector_explanation(
                        source_pdf=source, candidate_path=candidate)


def _owner_source_available():
    if os.name != "nt" or os.environ.get("COMPUTERNAME", "").upper() != "YOGA6":
        return False
    binding = (Path(os.environ.get("LOCALAPPDATA", "")) / "Microvid" /
               "BoslaV3ReviewYoga6" / "bosla-selected-textbook-source-binding.json")
    try:
        return Path(json.loads(binding.read_text(encoding="utf8"))["sourcePdf"]).is_file()
    except (OSError, ValueError, KeyError, TypeError):
        return False


@skipUnless(_owner_source_available(),
            "Private original Serway source exists only on owner Yoga6")
class OwnerVectorExplanationCanonicalTask(TestCase):
    def test_real_source_signed_first_partition_and_negative_candidate(self):
        from app_generator.runtime.v3_first_academic_proof_admission import _bound_inputs
        from app_generator.runtime.v3_long_horizon_development import read_long_horizon_development
        from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
        private = Path(os.environ["LOCALAPPDATA"]) / "Microvid" / "BoslaV3ReviewYoga6"
        state = read_long_horizon_development(private)
        ready = {"gitHead": state["gitHead"], "proposalSha256": state["proposalSha256"]}
        _, _, _, source, candidate = _bound_inputs(private, ready, allow_historical=False)
        folder = private / "owner-five-stage-completion" / ready["gitHead"] / ready["proposalSha256"]
        partition = _signed(folder, "V36_PARTITION_01.json", ready)
        proof = p.independently_prove_vector_explanation(source_pdf=source, candidate_path=candidate)
        queue = plan_full_semantic_proofs(package=json.loads(candidate.read_bytes()),
                                          source_sha256=p._SOURCE_SHA)
        rows = [row for row in queue["tasks"] if row["activityId"] == p._ACTIVITY and
                row["kind"] == "COMPLETE_SCIENTIFIC_MEANING" and row["surfacePath"] == "explanation"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(proof["taskId"], rows[0]["taskId"])
        signed = [row for row in partition["activity"]["evidenceRows"] if
                  row.get("taskId") == proof["taskId"]]
        self.assertEqual(len(signed), 1)
        self.assertEqual(signed[0]["surfaceSha256"], proof["surfaceSha256"])
        self.assertNotIn("surfacePath", signed[0])
        from app_generator.runtime.v3_vector_explanation_academic_admission import _original_proof
        _, checked_partition, checked_proof = _original_proof(
            private=private, ready=ready, historical=False)
        self.assertEqual(checked_partition, partition)
        self.assertEqual(checked_proof, proof)
        with TemporaryDirectory() as folder:
            altered = Path(folder) / "candidate.json"
            altered.write_bytes(candidate.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "AUTHENTIC_ONE_SERWAY"):
                p.independently_prove_vector_explanation(source_pdf=source, candidate_path=altered)

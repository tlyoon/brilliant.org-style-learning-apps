"""MCQ02 exact dimension and vector science with source gate falsification."""
from copy import deepcopy
from fractions import Fraction as F
from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless
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

    def test_whole_candidate_revision_rederives_si_explanation_id(self):
        package = json.loads(_PACKAGE.read_text(encoding="utf8"))
        def task_id(candidate):
            rows = plan_full_semantic_proofs(package=candidate, source_sha256=_REAL_SOURCE_SHA)["tasks"]
            return next(row["taskId"] for row in rows if row["activityId"] == p._ACTIVITY
                        and row["kind"] == "COMPLETE_SCIENTIFIC_MEANING"
                        and row["surfacePath"] == "explanation")
        original = task_id(package)
        package["activities"][-1]["id"] += "-other-activity-revised"
        self.assertNotEqual(original, task_id(package))
        with TemporaryDirectory() as folder:
            source, candidate = Path(folder)/"source.pdf", Path(folder)/"candidate.json"
            source.write_bytes(b"%PDF-synthetic")
            candidate.write_text(json.dumps(package, ensure_ascii=False), encoding="utf8")
            anchors = [{}, {"activityId":p._ACTIVITY,"uniquePagePassageLocated":True,
                            "physicalPage":2,"passageSha256":"a"*64}]
            with (patch.object(p,"_SOURCE_SHA",sha256(source.read_bytes()).hexdigest()),
                  patch.object(p,"_CANDIDATE_SHA",sha256(candidate.read_bytes()).hexdigest()),
                  patch.object(p,"_source_axioms",return_value={
                      "linear momentum is a vector":1,
                      "defined to be the product of the mass and velocity":1,
                      "dimensions ml/t":1}),
                  patch.object(p,"extract_pages",return_value=["synthetic"]),
                  patch.object(p,"_source_activity_anchors",return_value=anchors)):
                source_bound = plan_full_semantic_proofs(
                    package=package, source_sha256=sha256(source.read_bytes()).hexdigest())
                expected = next(row["taskId"] for row in source_bound["tasks"] if
                                row["activityId"] == p._ACTIVITY and
                                row["kind"] == "COMPLETE_SCIENTIFIC_MEANING" and
                                row["surfacePath"] == "explanation")
                proof = p.independently_prove_si_explanation(source_pdf=source,candidate_path=candidate)
                self.assertEqual(proof["taskId"], expected)
                candidate.write_bytes(candidate.read_bytes()+b" ")
                with self.assertRaisesRegex(ValueError,"AUTHENTIC_ONE_SERWAY"):
                    p.independently_prove_si_explanation(source_pdf=source,candidate_path=candidate)


def _owner_source_available():
    if os.name != "nt" or os.environ.get("COMPUTERNAME", "").upper() != "YOGA6":
        return False
    binding = (Path(os.environ.get("LOCALAPPDATA", "")) / "Microvid" /
               "BoslaV3ReviewYoga6" / "bosla-selected-textbook-source-binding.json")
    try:
        return Path(json.loads(binding.read_text(encoding="utf8"))["sourcePdf"]).is_file()
    except (OSError, ValueError, KeyError, TypeError):
        return False


@skipUnless(_owner_source_available(), "Private original Serway source exists only on owner Yoga6")
class OwnerSiExplanationCanonicalTask(TestCase):
    def test_real_source_signed_second_partition_and_negative_candidate(self):
        from app_generator.runtime.v3_first_academic_proof_admission import _bound_inputs
        from app_generator.runtime.v3_long_horizon_development import read_long_horizon_development
        from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
        from app_generator.runtime.v3_si_explanation_academic_admission import _original_proof
        private = Path(os.environ["LOCALAPPDATA"]) / "Microvid" / "BoslaV3ReviewYoga6"
        state = read_long_horizon_development(private)
        ready = {"gitHead":state["gitHead"],"proposalSha256":state["proposalSha256"]}
        _, _, _, source, candidate = _bound_inputs(private, ready, allow_historical=False)
        folder = private / "owner-five-stage-completion" / ready["gitHead"] / ready["proposalSha256"]
        partition = _signed(folder,"V36_PARTITION_02.json",ready)
        proof = p.independently_prove_si_explanation(source_pdf=source,candidate_path=candidate)
        queue = plan_full_semantic_proofs(package=json.loads(candidate.read_bytes()),source_sha256=p._SOURCE_SHA)
        rows = [row for row in queue["tasks"] if row["activityId"] == p._ACTIVITY and
                row["kind"] == "COMPLETE_SCIENTIFIC_MEANING" and row["surfacePath"] == "explanation"]
        self.assertEqual(len(rows),1)
        self.assertEqual(proof["taskId"],rows[0]["taskId"])
        signed = [row for row in partition["activity"]["evidenceRows"] if row.get("taskId") == proof["taskId"]]
        self.assertEqual(len(signed),1)
        self.assertEqual(signed[0]["surfaceSha256"],proof["surfaceSha256"])
        self.assertNotIn("surfacePath",signed[0])
        _, checked_partition, checked_proof = _original_proof(private=private,ready=ready,historical=False)
        self.assertEqual(checked_partition,partition)
        self.assertEqual(checked_proof,proof)
        with TemporaryDirectory() as folder:
            altered = Path(folder)/"candidate.json"
            altered.write_bytes(candidate.read_bytes()+b" ")
            with self.assertRaisesRegex(ValueError,"AUTHENTIC_ONE_SERWAY"):
                p.independently_prove_si_explanation(source_pdf=source,candidate_path=altered)

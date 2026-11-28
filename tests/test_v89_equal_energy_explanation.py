"""Falsification and restart controls for the unadmitted MCQ07 explanation."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless
from unittest.mock import patch
import sys
import types

# This snapshot can lack the declared runtime jsonschema dependency. Admission
# imports its visual gate transitively; these tests never execute that gate.
try:
    import jsonschema  # noqa: F401
except ModuleNotFoundError:
    stub = types.ModuleType("jsonschema")
    stub.Draft202012Validator = type("ImportOnlyValidator", (), {})
    stub.FormatChecker = type("ImportOnlyFormatChecker", (), {})
    sys.modules["jsonschema"] = stub

from app_generator.validation import section91_equal_energy_explanation_proof as p
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs
from app_generator.runtime import v3_equal_energy_explanation_academic_admission as a

_PACKAGE = Path("content/chapter-9/section-9-1/package.json")
_PIN = p._SOURCE_SHA


class EqualEnergyExplanation(TestCase):
    def test_exact_equal_energy_momentum_magnitude_models(self):
        rows = p._models()
        self.assertEqual(len(rows), 2)
        for row in rows:
            p._check_model(row)
            self.assertGreater(p.F(row["heavyMomentumMagnitude"]), p.F(row["lightMomentumMagnitude"]))
            self.assertEqual(row["heavyKineticEnergy"], row["lightKineticEnergy"])
        with self.assertRaises(ValueError):
            p._model(p.F(1), p.F(2), p.F(3), p.F(4))
        for heavy, light, energy in ((p.F(11, 7), p.F(2, 3), p.F(1, 13)),
                                     (p.F(500), p.F(1, 1000), p.F(7, 2))):
            self.assertTrue(p._equal_energy_order_theorem(heavy, light, energy))
        with self.assertRaisesRegex(ValueError, "THEOREM_DOMAIN"):
            p._equal_energy_order_theorem(p.F(1), p.F(2), p.F(1))

    def test_frozen_three_language_explanation_and_source_restart(self):
        activity = json.loads(_PACKAGE.read_text(encoding="utf8"))["activities"][6]
        self.assertEqual(p._locale_hashes(activity["explanation"], p._EXPLANATION), p._EXPLANATION)
        changed = dict(activity["explanation"])
        changed["zh"] += "。"
        with self.assertRaises(ValueError):
            p._locale_hashes(changed, p._EXPLANATION)
        with TemporaryDirectory() as folder:
            source = Path(folder)/"source.pdf"
            candidate = Path(folder)/"candidate.json"
            source.write_bytes(b"%PDF-synthetic")
            candidate.write_bytes(_PACKAGE.read_bytes())
            with patch.object(p, "extract_pages", side_effect=AssertionError("unverified extraction")):
                with self.assertRaisesRegex(ValueError, "AUTHENTIC_ONE_SERWAY"):
                    p.independently_prove_equal_energy_explanation(source_pdf=source, candidate_path=candidate)
            anchors = [{} for _ in range(7)]
            anchors[6] = {"activityId":p._ACTIVITY,"uniquePagePassageLocated":True,
                          "physicalPage":1,"passageSha256":"a"*64}
            with (patch.object(p,"_SOURCE_SHA",sha256(source.read_bytes()).hexdigest()),
                  patch.object(p,"_CANDIDATE_SHA",sha256(candidate.read_bytes()).hexdigest()),
                  patch.object(p,"_source_axioms",return_value={"linear momentum is a vector":1,
                      "defined to be the product of the mass and velocity":1,"kinetic energy can transform":1}),
                  patch.object(p,"extract_pages",return_value=["synthetic vector page"]),
                  patch.object(p,"_source_activity_anchors",return_value=anchors),
                  patch.object(p,"plan_full_semantic_proofs",side_effect=lambda **kw:
                      plan_full_semantic_proofs(package=kw["package"],source_sha256=_PIN))):
                proof=p.independently_prove_equal_energy_explanation(source_pdf=source,candidate_path=candidate)
                self.assertEqual(proof,p.independently_prove_equal_energy_explanation(source_pdf=source,candidate_path=candidate))
                forged=deepcopy(proof)
                forged["models"][0]["heavyKineticEnergy"]="0"
                forged["witnessSha256"]=p._digest({k:v for k,v in forged.items() if k!="witnessSha256"})
                with self.assertRaises(ValueError):
                    p.independently_check_equal_energy_explanation_witness(forged)
                def changing_extraction(_):
                    source.write_bytes(source.read_bytes()+b"changed during extraction")
                    return ["synthetic vector page"]
                with patch.object(p,"extract_pages",side_effect=changing_extraction):
                    with self.assertRaisesRegex(ValueError,"SOURCE_CHANGED_DURING_EXTRACTION"):
                        p.independently_prove_equal_energy_explanation(source_pdf=source,candidate_path=candidate)
                source.write_bytes(b"%PDF-synthetic")
                source.write_bytes(source.read_bytes()+b"altered")
                with self.assertRaisesRegex(ValueError,"AUTHENTIC_ONE_SERWAY"):
                    p.independently_prove_equal_energy_explanation(source_pdf=source,candidate_path=candidate)

    def test_signed_partition_requires_exact_row(self):
        ready={"gitHead":"a"*40,"proposalSha256":"b"*64}
        proof={"taskId":"t"*64,"surfaceSha256":"s"*64,"newProviderCalls":0,"publicationAuthorized":False}
        part={"integritySha256":"signed","sourceSha256":a._SOURCE_SHA,
              "candidateSha256":a._CANDIDATE_SHA,"academicPASS":0,"publicationAuthorized":False,
              "activity":{"activityId":p._ACTIVITY,"evidenceRows":[
                  {"taskId":proof["taskId"],"kind":"COMPLETE_SCIENTIFIC_MEANING",
                   "status":"BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED","surfaceSha256":proof["surfaceSha256"]}]}}
        v36={"signedPartitionHashes":[{} for _ in range(18)],"semanticTasksAutomaticallyDispatched":429,
             "fullAcademicProofTasksAccepted":0,"completeAcademicProofGatesStillOpen":90,
             "sourceSha256":a._SOURCE_SHA,"publicationAuthorized":False}
        v36["signedPartitionHashes"][6]={"activityId":p._ACTIVITY,"signedEvidenceSha256":"signed"}
        def run(partition):
            with (patch.object(a,"_bound_inputs",return_value=(None,v36,None,Path("source.pdf"),Path("candidate.json"))),
                  patch.object(a,"_signed",return_value=partition),
                  patch.object(a,"independently_prove_equal_energy_explanation",return_value=proof),
                  patch.object(a,"independently_check_equal_energy_explanation_witness")):
                return a._original_proof(private=Path("."),ready=ready,historical=False)
        self.assertEqual(run(part)[2],proof)
        for field in ("taskId","kind","status","surfaceSha256"):
            altered=deepcopy(part)
            altered["activity"]["evidenceRows"][0][field]="forged"
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,"SCIENCE_NOT_REPROVEN"):
                run(altered)
        duplicate=deepcopy(part)
        duplicate["activity"]["evidenceRows"].append(deepcopy(duplicate["activity"]["evidenceRows"][0]))
        with self.assertRaisesRegex(ValueError,"SCIENCE_NOT_REPROVEN"):
            run(duplicate)

    def test_prior_chain_and_cross_head_restart(self):
        prior={"independentlyAcceptedAcademicTasks":33,"fullAcademicTasksStillOpen":396,
               "acceptedAcademicTaskIds":[str(i) for i in range(33)],
               "completeAcademicProofGatesStillOpen":90,"fullAcademicActivityPASS":0,
               "publicationAuthorized":False,"equalSpeedExplanationReceiptSha256":"prior"}
        with patch.object(a,"verify_equal_speed_explanation_across_git_heads",return_value=prior):
            self.assertEqual(a._prior(Path(".")),prior)
        with patch.object(a,"verify_equal_speed_explanation_across_git_heads",return_value={**prior,"acceptedAcademicTaskIds":prior["acceptedAcademicTaskIds"][:-1]}):
            with self.assertRaisesRegex(ValueError,"A1_A33_CHAIN"):
                a._prior(Path("."))
        proof={"taskId":"t"*64,"models":p._models()}
        frontier={"gitHead":"a"*40,"proposalSha256":"b"*64,"status":a._FRONTIER_STATUS,
                  "sourceSha256":a._SOURCE_SHA,"candidateSha256":a._CANDIDATE_SHA,
                  "cumulativeAcademicTasksAccepted":34,"fullAcademicTasksStillOpen":395,
                  "completeAcademicProofGatesStillOpen":90,"fullAcademicActivityPASS":0,
                  "publicationAuthorized":False,"newScientificReceiptSha256":"signed",
                  "previousAcademicTaskIds":prior["acceptedAcademicTaskIds"],"newAcceptedTaskId":"t"*64}
        now={"gitHead":"c"*40,"proposalSha256":"d"*64,"sourceSha256":a._SOURCE_SHA,"candidateSha256":a._CANDIDATE_SHA}
        receipt={"integritySha256":"signed","previousEqualSpeedExplanationReceiptSha256":"prior"}
        def check(fresh):
            with (patch.object(a,"_read_signed",return_value=frontier),
                  patch.object(a,"read_long_horizon_development",return_value=now),
                  patch.object(a,"_verify_receipt",return_value=(receipt,proof)),
                  patch.object(a,"_original_proof",return_value=({}, {}, fresh)),
                  patch.object(a,"_prior",return_value=prior)):
                return a.verify_equal_energy_explanation_across_git_heads(private=Path("."))
        self.assertTrue(check(proof)["carriedAcrossGitHead"])
        with self.assertRaisesRegex(ValueError,"SCIENCE_CHANGED_ACROSS_CODE_HEADS"):
            check({**proof,"models":[]})


@skipUnless(os.name == "nt" and os.environ.get("BOSLA_OWNER_ACADEMIC_TESTS") == "1",
            "Explicit owner source-bound test run required; sandbox snapshot cannot read private Serway")
class OwnerEqualEnergyExplanation(TestCase):
    def test_original_serway_explanation_and_signed_partition(self):
        from app_generator.runtime.v3_long_horizon_development import read_long_horizon_development
        private = Path(os.environ["LOCALAPPDATA"]) / "Microvid" / "BoslaV3ReviewYoga6"
        ready_state = read_long_horizon_development(private)
        ready = {"gitHead": ready_state["gitHead"], "proposalSha256": ready_state["proposalSha256"]}
        _, _, proof = a._original_proof(private=private, ready=ready, historical=False)
        self.assertEqual(proof["sourceSha256"], p._SOURCE_SHA)
        self.assertEqual(proof["candidateSha256"], p._CANDIDATE_SHA)
        self.assertEqual(proof["explanationLocaleSha256"], p._EXPLANATION)
        self.assertFalse(proof["academicTaskAccepted"])

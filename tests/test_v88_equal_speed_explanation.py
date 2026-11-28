"""Falsification and restart controls for the unadmitted MCQ06 explanation."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
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

from app_generator.validation import section91_equal_speed_explanation_proof as p
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs
from app_generator.runtime import v3_equal_speed_explanation_academic_admission as a

_PACKAGE = Path("content/chapter-9/section-9-1/package.json")
_PIN = p._SOURCE_SHA


class EqualSpeedExplanation(TestCase):
    def test_exact_vector_and_scalar_models(self):
        rows = p._models()
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(row, p._model(p.F(row["heavyMass"]), p.F(row["lightMass"]), p.F(row["commonSpeed"])))
            self.assertGreater(p.F(row["truckMomentumMagnitude"]), p.F(row["carMomentumMagnitude"]))
            self.assertNotEqual(row["truckEastNorthMomentum"], row["carEastNorthMomentum"])
        with self.assertRaises(ValueError):
            p._model(p.F(1), p.F(2), p.F(3))

    def test_frozen_three_language_explanation_and_source_restart(self):
        activity = json.loads(_PACKAGE.read_text(encoding="utf8"))["activities"][5]
        self.assertEqual(p._locale_digests(activity["explanation"], p._EXPLANATION), p._EXPLANATION)
        changed = dict(activity["explanation"])
        changed["zh"] += "。"
        with self.assertRaises(ValueError):
            p._locale_digests(changed, p._EXPLANATION)
        with TemporaryDirectory() as folder:
            source = Path(folder)/"source.pdf"
            candidate = Path(folder)/"candidate.json"
            source.write_bytes(b"%PDF-synthetic")
            candidate.write_bytes(_PACKAGE.read_bytes())
            with patch.object(p, "extract_pages", side_effect=AssertionError("unverified extraction")):
                with self.assertRaisesRegex(ValueError, "AUTHENTIC_ONE_SERWAY"):
                    p.independently_prove_equal_speed_explanation(source_pdf=source, candidate_path=candidate)
            anchors = [{} for _ in range(6)]
            anchors[5] = {"activityId":p._ACTIVITY,"uniquePagePassageLocated":True,
                          "physicalPage":1,"passageSha256":"a"*64}
            with (patch.object(p,"_SOURCE_SHA",sha256(source.read_bytes()).hexdigest()),
                  patch.object(p,"_CANDIDATE_SHA",sha256(candidate.read_bytes()).hexdigest()),
                  patch.object(p,"_source_axioms",return_value={"linear momentum is a vector":1,
                      "defined to be the product of the mass and velocity":1}),
                  patch.object(p,"extract_pages",return_value=["synthetic vector page"]),
                  patch.object(p,"_source_activity_anchors",return_value=anchors),
                  patch.object(p,"plan_full_semantic_proofs",side_effect=lambda **kw:
                      plan_full_semantic_proofs(package=kw["package"],source_sha256=_PIN))):
                proof=p.independently_prove_equal_speed_explanation(source_pdf=source,candidate_path=candidate)
                self.assertEqual(proof,p.independently_prove_equal_speed_explanation(source_pdf=source,candidate_path=candidate))
                forged=deepcopy(proof)
                forged["models"][0]["truckKineticEnergy"]="0"
                forged["witnessSha256"]=p._digest({k:v for k,v in forged.items() if k!="witnessSha256"})
                with self.assertRaises(ValueError):
                    p.independently_check_equal_speed_explanation_witness(forged)
                def changing_extraction(_):
                    source.write_bytes(source.read_bytes()+b"changed during extraction")
                    return ["synthetic vector page"]
                with patch.object(p,"extract_pages",side_effect=changing_extraction):
                    with self.assertRaisesRegex(ValueError,"SOURCE_CHANGED_DURING_EXTRACTION"):
                        p.independently_prove_equal_speed_explanation(source_pdf=source,candidate_path=candidate)
                source.write_bytes(b"%PDF-synthetic")
                source.write_bytes(source.read_bytes()+b"altered")
                with self.assertRaisesRegex(ValueError,"AUTHENTIC_ONE_SERWAY"):
                    p.independently_prove_equal_speed_explanation(source_pdf=source,candidate_path=candidate)

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
        v36["signedPartitionHashes"][5]={"activityId":p._ACTIVITY,"signedEvidenceSha256":"signed"}
        def run(partition):
            with (patch.object(a,"_bound_inputs",return_value=(None,v36,None,Path("source.pdf"),Path("candidate.json"))),
                  patch.object(a,"_signed",return_value=partition),
                  patch.object(a,"independently_prove_equal_speed_explanation",return_value=proof),
                  patch.object(a,"independently_check_equal_speed_explanation_witness")):
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
        prior={"independentlyAcceptedAcademicTasks":32,"fullAcademicTasksStillOpen":397,
               "acceptedAcademicTaskIds":[str(i) for i in range(32)],
               "completeAcademicProofGatesStillOpen":90,"fullAcademicActivityPASS":0,
               "publicationAuthorized":False,"thirdLawExplanationReceiptSha256":"prior"}
        with patch.object(a,"verify_third_law_explanation_across_git_heads",return_value=prior):
            self.assertEqual(a._prior(Path(".")),prior)
        with patch.object(a,"verify_third_law_explanation_across_git_heads",return_value={**prior,"acceptedAcademicTaskIds":prior["acceptedAcademicTaskIds"][:-1]}):
            with self.assertRaisesRegex(ValueError,"A1_A32_CHAIN"):
                a._prior(Path("."))
        proof={"taskId":"t"*64,"models":p._models()}
        frontier={"gitHead":"a"*40,"proposalSha256":"b"*64,"status":a._FRONTIER_STATUS,
                  "sourceSha256":a._SOURCE_SHA,"candidateSha256":a._CANDIDATE_SHA,
                  "cumulativeAcademicTasksAccepted":33,"fullAcademicTasksStillOpen":396,
                  "completeAcademicProofGatesStillOpen":90,"fullAcademicActivityPASS":0,
                  "publicationAuthorized":False,"newScientificReceiptSha256":"signed",
                  "previousAcademicTaskIds":prior["acceptedAcademicTaskIds"],"newAcceptedTaskId":"t"*64}
        now={"gitHead":"c"*40,"proposalSha256":"d"*64,"sourceSha256":a._SOURCE_SHA,"candidateSha256":a._CANDIDATE_SHA}
        receipt={"integritySha256":"signed","previousThirdLawExplanationReceiptSha256":"prior"}
        def check(fresh):
            with (patch.object(a,"_read_signed",return_value=frontier),
                  patch.object(a,"read_long_horizon_development",return_value=now),
                  patch.object(a,"_verify_receipt",return_value=(receipt,proof)),
                  patch.object(a,"_original_proof",return_value=({}, {}, fresh)),
                  patch.object(a,"_prior",return_value=prior)):
                return a.verify_equal_speed_explanation_across_git_heads(private=Path("."))
        self.assertTrue(check(proof)["carriedAcrossGitHead"])
        with self.assertRaisesRegex(ValueError,"SCIENCE_CHANGED_ACROSS_CODE_HEADS"):
            check({**proof,"models":[]})

"""MCQ09 complete explanation requires exact physics and owner source binding."""
from copy import deepcopy
from fractions import Fraction as F
from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless
from unittest.mock import patch
import sys
import types

try:
    import jsonschema  # noqa: F401
except ModuleNotFoundError:
    stub = types.ModuleType("jsonschema")
    stub.Draft202012Validator = type("ImportOnlyValidator", (), {})
    stub.FormatChecker = type("ImportOnlyFormatChecker", (), {})
    sys.modules["jsonschema"] = stub

from app_generator.validation import section91_spring_buffer_explanation_proof as p
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs
from app_generator.runtime import v3_spring_buffer_explanation_academic_admission as a

_PACKAGE = Path("content/chapter-9/section-9-1/package.json")
_REAL_SOURCE_SHA = p._SOURCE_SHA


class SpringBufferExplanation(TestCase):
    def test_exact_conversion_and_falsification(self):
        rows = p._cases()
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(F(row["initialKineticEnergy"]),
                             F(row["springPotentialEnergy"]) + F(row["thermalEnergy"]))
            self.assertEqual(F(row["podImpulse"]) + F(row["railImpulse"]), 0)
            self.assertEqual(F(row["initialMomentum"]) + F(row["podImpulse"]), 0)
        self.assertNotEqual(rows[0]["springFraction"], rows[1]["springFraction"])
        for bad in ((F(0), F(2), F(1), F(1)), (F(1), F(0), F(1), F(1)),
                    (F(1), F(1), F(0), F(1)), (F(1), F(1), F(1), F(3, 2))):
            with self.assertRaisesRegex(ValueError, "DOMAIN_REQUIRED"):
                p._check_conversion(*bad)
        proof = {"taskId": "a"*64, "sourceSha256": p._SOURCE_SHA,
                 "candidateSha256": p._CANDIDATE_SHA, "promptLocaleSha256": p._PROMPT,
                 "explanationLocaleSha256": p._EXPLANATION, "models": p._cases(),
                 "generalLaw": p._LAW, "sourcePageIndex": 1,
                 "surfaceSha256": "b"*64, "sourcePassageSha256": "c"*64,
                 "sourcePhysicsPremisesSha256": "d"*64, "academicTaskAccepted": False,
                 "completeAcademicProofGatesStillOpen": 90, "newProviderCalls": 0,
                 "publicationAuthorized": False}
        proof["witnessSha256"] = p._digest(proof)
        p.independently_check_spring_buffer_explanation_witness(proof)
        forged = deepcopy(proof)
        forged["models"][0]["railImpulse"] = "0"
        forged["witnessSha256"] = p._digest({k:v for k,v in forged.items() if k!="witnessSha256"})
        with self.assertRaises(ValueError):
            p.independently_check_spring_buffer_explanation_witness(forged)
        forged = deepcopy(proof)
        forged["academicTaskAccepted"] = True
        forged["witnessSha256"] = p._digest({k:v for k,v in forged.items() if k!="witnessSha256"})
        with self.assertRaises(ValueError):
            p.independently_check_spring_buffer_explanation_witness(forged)

    def test_frozen_trilingual_source_and_restart(self):
        activity = json.loads(_PACKAGE.read_text(encoding="utf8"))["activities"][8]
        self.assertEqual(p._locales(activity["prompt"], p._PROMPT), p._PROMPT)
        self.assertEqual(p._locales(activity["explanation"], p._EXPLANATION), p._EXPLANATION)
        altered = dict(activity["explanation"])
        altered["zh"] += "!"
        with self.assertRaises(ValueError):
            p._locales(altered, p._EXPLANATION)
        with TemporaryDirectory() as folder:
            source = Path(folder)/"source.pdf"
            candidate = Path(folder)/"candidate.json"
            source.write_bytes(b"%PDF-synthetic")
            candidate.write_bytes(_PACKAGE.read_bytes())
            with patch.object(p, "extract_pages", side_effect=AssertionError("untrusted PDF")):
                with self.assertRaisesRegex(ValueError, "AUTHENTIC_ONE_SERWAY"):
                    p.independently_prove_spring_buffer_explanation(source_pdf=source, candidate_path=candidate)
            anchors = [{} for _ in range(9)]
            anchors[8] = {"activityId": p._ACTIVITY, "uniquePagePassageLocated": True,
                          "physicalPage": 1, "passageSha256": "a"*64}
            axioms = {"kinetic energy can transform": 1, "only one type of linear momentum": 1,
                      "third law": 1, "time rate of change of the linear momentum": 1,
                      "defined to be the product of the mass and velocity": 1}
            with (patch.object(p, "_SOURCE_SHA", sha256(source.read_bytes()).hexdigest()),
                  patch.object(p, "_CANDIDATE_SHA", sha256(candidate.read_bytes()).hexdigest()),
                  patch.object(p, "_source_axioms", return_value=axioms),
                  patch.object(p, "extract_pages", return_value=["synthetic page"]),
                  patch.object(p, "_source_activity_anchors", return_value=anchors),
                  patch.object(p, "plan_full_semantic_proofs", side_effect=lambda **kw:
                      plan_full_semantic_proofs(package=kw["package"], source_sha256=_REAL_SOURCE_SHA))):
                proof = p.independently_prove_spring_buffer_explanation(source_pdf=source, candidate_path=candidate)
                self.assertEqual(proof, p.independently_prove_spring_buffer_explanation(
                    source_pdf=source, candidate_path=candidate))
                old_extract = p.extract_pages
                def change_source(path):
                    path.write_bytes(b"%PDF-changed")
                    return old_extract(path)
                with patch.object(p, "extract_pages", side_effect=change_source):
                    with self.assertRaisesRegex(ValueError, "SOURCE_CHANGED_DURING_EXTRACTION"):
                        p.independently_prove_spring_buffer_explanation(source_pdf=source, candidate_path=candidate)
                source.write_bytes(b"%PDF-synthetic")
                candidate.write_bytes(candidate.read_bytes()+b" ")
                with self.assertRaisesRegex(ValueError, "AUTHENTIC_ONE_SERWAY"):
                    p.independently_prove_spring_buffer_explanation(source_pdf=source, candidate_path=candidate)

    def test_signed_ninth_partition_and_cross_head_restart(self):
        ready = {"gitHead":"a"*40, "proposalSha256":"b"*64}
        proof = {"taskId":"t"*64, "surfaceSha256":"s"*64,
                 "newProviderCalls":0, "publicationAuthorized":False}
        row = {"taskId":proof["taskId"], "kind":"COMPLETE_SCIENTIFIC_MEANING",
               "status":"BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED", "surfaceSha256":proof["surfaceSha256"]}
        part = {"integritySha256":"signed", "sourceSha256":a._SOURCE_SHA,
                "candidateSha256":a._CANDIDATE_SHA, "academicPASS":0,
                "publicationAuthorized":False,
                "activity":{"activityId":p._ACTIVITY,"evidenceRows":[row]}}
        v36 = {"signedPartitionHashes":[{} for _ in range(18)],
               "semanticTasksAutomaticallyDispatched":429,"fullAcademicProofTasksAccepted":0,
               "completeAcademicProofGatesStillOpen":90,"sourceSha256":a._SOURCE_SHA,
               "publicationAuthorized":False}
        v36["signedPartitionHashes"][8] = {"activityId":p._ACTIVITY,"signedEvidenceSha256":"signed"}
        def check_partition(partition):
            with (patch.object(a,"_bound_inputs",return_value=(None,v36,None,Path("source.pdf"),Path("candidate.json"))),
                  patch.object(a,"_signed",return_value=partition),
                  patch.object(a,"independently_prove_spring_buffer_explanation",return_value=proof),
                  patch.object(a,"independently_check_spring_buffer_explanation_witness")):
                return a._original_proof(private=Path("."),ready=ready,historical=False)
        self.assertEqual(check_partition(part)[2], proof)
        bad = deepcopy(part)
        bad["activity"]["evidenceRows"][0]["surfaceSha256"] = "forged"
        with self.assertRaisesRegex(ValueError,"SCIENCE_NOT_REPROVEN"):
            check_partition(bad)
        prior={"independentlyAcceptedAcademicTasks":35,"fullAcademicTasksStillOpen":394,
               "acceptedAcademicTaskIds":[str(i) for i in range(35)],
               "completeAcademicProofGatesStillOpen":90,"fullAcademicActivityPASS":0,
               "publicationAuthorized":False,"isolatedPairExplanationReceiptSha256":"prior"}
        with patch.object(a,"verify_isolated_pair_explanation_across_git_heads",return_value=prior):
            self.assertEqual(a._prior(Path(".")),prior)
        with patch.object(a,"verify_isolated_pair_explanation_across_git_heads",
                          return_value={**prior,"fullAcademicTasksStillOpen":393}):
            with self.assertRaisesRegex(ValueError,"A1_A35_CHAIN"):
                a._prior(Path("."))
        frontier={"gitHead":"a"*40,"proposalSha256":"b"*64,"status":a._FRONTIER_STATUS,
                  "sourceSha256":a._SOURCE_SHA,"candidateSha256":a._CANDIDATE_SHA,
                  "cumulativeAcademicTasksAccepted":36,"fullAcademicTasksStillOpen":393,
                  "completeAcademicProofGatesStillOpen":90,"fullAcademicActivityPASS":0,
                  "publicationAuthorized":False,"newScientificReceiptSha256":"signed",
                  "previousAcademicTaskIds":prior["acceptedAcademicTaskIds"],"newAcceptedTaskId":"t"*64}
        now={"gitHead":"c"*40,"proposalSha256":"d"*64,
             "sourceSha256":a._SOURCE_SHA,"candidateSha256":a._CANDIDATE_SHA}
        receipt={"integritySha256":"signed","previousIsolatedPairExplanationReceiptSha256":"prior"}
        def check_restart(fresh):
            with (patch.object(a,"_read_signed",return_value=frontier),
                  patch.object(a,"read_long_horizon_development",return_value=now),
                  patch.object(a,"_verify_receipt",return_value=(receipt,proof)),
                  patch.object(a,"_original_proof",return_value=({}, {}, fresh)),
                  patch.object(a,"_prior",return_value=prior)):
                return a.verify_spring_buffer_explanation_across_git_heads(private=Path("."))
        self.assertTrue(check_restart(proof)["carriedAcrossGitHead"])
        with self.assertRaisesRegex(ValueError,"SCIENCE_CHANGED_ACROSS_CODE_HEADS"):
            check_restart({**proof,"models":[]})


@skipUnless(os.name == "nt" and os.environ.get("BOSLA_OWNER_ACADEMIC_TESTS") == "1",
            "Explicit owner source-bound run required")
class OwnerSpringBufferExplanation(TestCase):
    def test_original_serway_explanation_and_signed_partition(self):
        from app_generator.runtime.v3_long_horizon_development import read_long_horizon_development
        private=Path(os.environ["LOCALAPPDATA"])/"Microvid"/"BoslaV3ReviewYoga6"
        state=read_long_horizon_development(private)
        ready={"gitHead":state["gitHead"],"proposalSha256":state["proposalSha256"]}
        _,_,proof=a._original_proof(private=private,ready=ready,historical=False)
        self.assertEqual(proof["sourceSha256"],p._SOURCE_SHA)
        self.assertEqual(proof["explanationLocaleSha256"],p._EXPLANATION)
        self.assertFalse(proof["academicTaskAccepted"])

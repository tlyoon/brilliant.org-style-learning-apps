"""MCQ08 complete explanation: exact models, source binding and signed A35 row."""
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

# The disposable snapshot may lack this declared dependency. The tests only
# import admission code; they never run its visual schema gate.
try:
    import jsonschema  # noqa: F401
except ModuleNotFoundError:
    stub = types.ModuleType("jsonschema")
    stub.Draft202012Validator = type("ImportOnlyValidator", (), {})
    stub.FormatChecker = type("ImportOnlyFormatChecker", (), {})
    sys.modules["jsonschema"] = stub

from app_generator.validation import section91_isolated_pair_explanation_proof as p
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs
from app_generator.runtime import v3_isolated_pair_explanation_academic_admission as a

_PACKAGE = Path("content/chapter-9/section-9-1/package.json")
_REAL_SOURCE_SHA = p._SOURCE_SHA


class IsolatedPairExplanation(TestCase):
    def test_exact_pair_law_and_adversarial_models(self):
        for row in p._models():
            p._check_model(row)
            self.assertEqual(F(row["nadiaMomentum"]) + F(row["leoMomentum"]), 0)
            self.assertNotEqual(F(row["nadiaMomentum"]), 0)
        for bad in ((F(0), F(3), F(4), F(2)), (F(2), F(3), F(0), F(2)),
                    (F(2), F(3), F(4), F(0))):
            with self.assertRaises(ValueError):
                p._check_pair_law(*bad)
        changed = deepcopy(p._models()[0])
        changed["nadiaMomentum"] = "0"
        with self.assertRaisesRegex(ValueError, "MODEL_TAMPERED"):
            p._check_model(changed)

    def test_frozen_trilingual_surface_and_source_restart(self):
        activity = json.loads(_PACKAGE.read_text(encoding="utf8"))["activities"][7]
        self.assertEqual(p._locales(activity["prompt"], p._PROMPT), p._PROMPT)
        self.assertEqual(p._locales(activity["explanation"], p._EXPLANATION), p._EXPLANATION)
        altered = dict(activity["explanation"])
        altered["ms"] += "!"
        with self.assertRaises(ValueError):
            p._locales(altered, p._EXPLANATION)
        with TemporaryDirectory() as folder:
            source = Path(folder)/"source.pdf"
            candidate = Path(folder)/"candidate.json"
            source.write_bytes(b"%PDF-synthetic")
            candidate.write_bytes(_PACKAGE.read_bytes())
            with patch.object(p, "extract_pages", side_effect=AssertionError("untrusted source reached")):
                with self.assertRaisesRegex(ValueError, "AUTHENTIC_ONE_SERWAY"):
                    p.independently_prove_isolated_pair_explanation(source_pdf=source, candidate_path=candidate)
            anchors = [{} for _ in range(8)]
            anchors[7] = {"activityId": p._ACTIVITY, "uniquePagePassageLocated": True,
                          "physicalPage": 1, "passageSha256": "a"*64}
            with (patch.object(p, "_SOURCE_SHA", sha256(source.read_bytes()).hexdigest()),
                  patch.object(p, "_CANDIDATE_SHA", sha256(candidate.read_bytes()).hexdigest()),
                  patch.object(p, "_source_axioms", return_value={"isolated system": 3,
                      "third law": 1, "time rate of change of the linear momentum": 1,
                      "defined to be the product of the mass and velocity": 1}),
                  patch.object(p, "extract_pages", return_value=["synthetic page"]),
                  patch.object(p, "_source_activity_anchors", return_value=anchors),
                  patch.object(p, "plan_full_semantic_proofs", side_effect=lambda **kw:
                      plan_full_semantic_proofs(package=kw["package"], source_sha256=_REAL_SOURCE_SHA))):
                proof = p.independently_prove_isolated_pair_explanation(source_pdf=source, candidate_path=candidate)
                self.assertEqual(proof, p.independently_prove_isolated_pair_explanation(
                    source_pdf=source, candidate_path=candidate))
                forged = deepcopy(proof)
                forged["models"][0]["nadiaMomentum"] = "0"
                forged["witnessSha256"] = p._digest({k:v for k,v in forged.items() if k!="witnessSha256"})
                with self.assertRaises(ValueError):
                    p.independently_check_isolated_pair_explanation_witness(forged)
                original_extract = p.extract_pages
                def changed_during_extraction(path):
                    path.write_bytes(b"%PDF-modified")
                    return original_extract(path)
                with patch.object(p, "extract_pages", side_effect=changed_during_extraction):
                    with self.assertRaisesRegex(ValueError, "SOURCE_CHANGED_DURING_EXTRACTION"):
                        p.independently_prove_isolated_pair_explanation(source_pdf=source, candidate_path=candidate)
                source.write_bytes(b"%PDF-synthetic")
                candidate.write_bytes(candidate.read_bytes()+b" ")
                with self.assertRaisesRegex(ValueError, "AUTHENTIC_ONE_SERWAY"):
                    p.independently_prove_isolated_pair_explanation(source_pdf=source, candidate_path=candidate)

    def test_signed_eighth_partition_requires_exact_row(self):
        ready = {"gitHead": "a"*40, "proposalSha256": "b"*64}
        proof = {"taskId": "t"*64, "surfaceSha256": "s"*64,
                 "newProviderCalls": 0, "publicationAuthorized": False}
        row = {"taskId": proof["taskId"], "kind": "COMPLETE_SCIENTIFIC_MEANING",
               "status": "BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED",
               "surfaceSha256": proof["surfaceSha256"]}
        part = {"integritySha256": "signed", "sourceSha256": a._SOURCE_SHA,
                "candidateSha256": a._CANDIDATE_SHA, "academicPASS": 0,
                "publicationAuthorized": False,
                "activity": {"activityId": p._ACTIVITY, "evidenceRows": [row]}}
        v36 = {"signedPartitionHashes": [{} for _ in range(18)],
               "semanticTasksAutomaticallyDispatched": 429, "fullAcademicProofTasksAccepted": 0,
               "completeAcademicProofGatesStillOpen": 90, "sourceSha256": a._SOURCE_SHA,
               "publicationAuthorized": False}
        v36["signedPartitionHashes"][7] = {"activityId": p._ACTIVITY,
                                             "signedEvidenceSha256": "signed"}
        def check(partition):
            with (patch.object(a, "_bound_inputs", return_value=(None,v36,None,Path("source.pdf"),Path("candidate.json"))),
                  patch.object(a, "_signed", return_value=partition),
                  patch.object(a, "independently_prove_isolated_pair_explanation", return_value=proof),
                  patch.object(a, "independently_check_isolated_pair_explanation_witness")):
                return a._original_proof(private=Path("."), ready=ready, historical=False)
        self.assertEqual(check(part)[2], proof)
        for field in row:
            altered = deepcopy(part)
            altered["activity"]["evidenceRows"][0][field] = "forged"
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "SCIENCE_NOT_REPROVEN"):
                check(altered)
        duplicate = deepcopy(part)
        duplicate["activity"]["evidenceRows"].append(dict(row))
        with self.assertRaisesRegex(ValueError, "SCIENCE_NOT_REPROVEN"):
            check(duplicate)

    def test_prior_chain_and_cross_head_restart(self):
        prior = {"independentlyAcceptedAcademicTasks":34, "fullAcademicTasksStillOpen":395,
                 "acceptedAcademicTaskIds":[str(i) for i in range(34)],
                 "completeAcademicProofGatesStillOpen":90, "fullAcademicActivityPASS":0,
                 "publicationAuthorized":False, "equalEnergyExplanationReceiptSha256":"prior"}
        with patch.object(a, "verify_equal_energy_explanation_across_git_heads", return_value=prior):
            self.assertEqual(a._prior(Path(".")), prior)
        with patch.object(a, "verify_equal_energy_explanation_across_git_heads",
                          return_value={**prior, "fullAcademicTasksStillOpen":394}):
            with self.assertRaisesRegex(ValueError, "A1_A34_CHAIN"):
                a._prior(Path("."))
        proof = {"taskId":"t"*64, "models":p._models()}
        frontier = {"gitHead":"a"*40, "proposalSha256":"b"*64,
                    "status":a._FRONTIER_STATUS, "sourceSha256":a._SOURCE_SHA,
                    "candidateSha256":a._CANDIDATE_SHA,
                    "cumulativeAcademicTasksAccepted":35, "fullAcademicTasksStillOpen":394,
                    "completeAcademicProofGatesStillOpen":90, "fullAcademicActivityPASS":0,
                    "publicationAuthorized":False, "newScientificReceiptSha256":"signed",
                    "previousAcademicTaskIds":prior["acceptedAcademicTaskIds"],
                    "newAcceptedTaskId":"t"*64}
        now = {"gitHead":"c"*40, "proposalSha256":"d"*64,
               "sourceSha256":a._SOURCE_SHA, "candidateSha256":a._CANDIDATE_SHA}
        receipt = {"integritySha256":"signed", "previousEqualEnergyExplanationReceiptSha256":"prior"}
        def check(fresh):
            with (patch.object(a, "_read_signed", return_value=frontier),
                  patch.object(a, "read_long_horizon_development", return_value=now),
                  patch.object(a, "_verify_receipt", return_value=(receipt,proof)),
                  patch.object(a, "_original_proof", return_value=({}, {}, fresh)),
                  patch.object(a, "_prior", return_value=prior)):
                return a.verify_isolated_pair_explanation_across_git_heads(private=Path("."))
        self.assertTrue(check(proof)["carriedAcrossGitHead"])
        with self.assertRaisesRegex(ValueError, "SCIENCE_CHANGED_ACROSS_CODE_HEADS"):
            check({**proof,"models":[]})


@skipUnless(os.name == "nt" and os.environ.get("BOSLA_OWNER_ACADEMIC_TESTS") == "1",
            "Explicit owner source-bound run required; snapshot lacks private Serway")
class OwnerIsolatedPairExplanation(TestCase):
    def test_original_serway_explanation_and_signed_partition(self):
        from app_generator.runtime.v3_long_horizon_development import read_long_horizon_development
        private = Path(os.environ["LOCALAPPDATA"]) / "Microvid" / "BoslaV3ReviewYoga6"
        state = read_long_horizon_development(private)
        ready = {"gitHead": state["gitHead"], "proposalSha256": state["proposalSha256"]}
        _, _, proof = a._original_proof(private=private, ready=ready, historical=False)
        self.assertEqual(proof["sourceSha256"], p._SOURCE_SHA)
        self.assertEqual(proof["candidateSha256"], p._CANDIDATE_SHA)
        self.assertEqual(proof["explanationLocaleSha256"], p._EXPLANATION)
        self.assertFalse(proof["academicTaskAccepted"])

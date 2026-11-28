"""BSA321 exact source-proof explanation identity vs signed V36 row schema.

A30/A31 source-bound producers already rederive explanation surfacePath from
the candidate. V36 evidence rows intentionally omit that non-signed metadata.
Synthetic tests here never issue academic PASS or read the original textbook.
"""
from copy import deepcopy
from pathlib import Path
import inspect
from unittest import TestCase
from unittest.mock import patch

from app_generator.runtime import (
    v3_newton_explanation_academic_admission as newton,
    v3_glider_explanation_academic_admission as glider,
)
from app_generator.validation import (
    section91_newton_explanation_proof as newton_proof,
    section91_glider_explanation_proof as glider_proof,
)


class V36ExplanationRowCompatibility(TestCase):
    CASES = (
        (newton, newton_proof, 2, "act-mcq-03-net-force-definition",
         "independently_prove_newton_explanation",
         "independently_check_newton_explanation_witness"),
        (glider, glider_proof, 3, "act-mcq-04-two-particle-opposite-momentum",
         "independently_prove_glider_explanation",
         "independently_check_glider_explanation_witness"),
    )

    def _run(self, spec, *, mutation=None, extra=None):
        module, producer, index, activity, prove, witness = spec
        ready = {"gitHead": "a" * 40, "proposalSha256": "b" * 64}
        proof = {"taskId": "c" * 64, "surfaceSha256": "d" * 64,
                 "newProviderCalls": 0, "publicationAuthorized": False}
        signed_row = {"taskId": proof["taskId"],
                      "kind": "COMPLETE_SCIENTIFIC_MEANING",
                      "status": "BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED",
                      "surfaceSha256": proof["surfaceSha256"]}
        if mutation is not None:
            signed_row.update(mutation)
        part = {
            "integritySha256": "partition-hash",
            "sourceSha256": module._SOURCE_SHA,
            "candidateSha256": module._CANDIDATE_SHA,
            "academicPASS": 0, "publicationAuthorized": False,
            "activity": {"activityId": activity, "evidenceRows": [signed_row]},
        }
        if extra is not None:
            part["activity"]["evidenceRows"].append(dict(signed_row))
        v36 = {"signedPartitionHashes": [{} for _ in range(18)],
               "semanticTasksAutomaticallyDispatched": 429,
               "fullAcademicProofTasksAccepted": 0,
               "completeAcademicProofGatesStillOpen": 90,
               "sourceSha256": module._SOURCE_SHA,
               "publicationAuthorized": False}
        v36["signedPartitionHashes"][index] = {
            "activityId": activity, "signedEvidenceSha256": "partition-hash"}
        with (patch.object(module, "_bound_inputs",
                           return_value=(None, v36, None,
                                         Path("private-source-not-opened.pdf"),
                                         Path("private-candidate-not-opened.json"))),
              patch.object(module, "_signed", return_value=part),
              patch.object(module, prove, return_value=proof),
              patch.object(module, witness)):
            return module._original_proof(
                private=Path("synthetic-only"), ready=ready, historical=False)

    def test_bsa321_a30_a31_real_signed_row_shape_without_surfacepath(self):
        for spec in self.CASES:
            with self.subTest(stage=spec[0].__name__):
                self.assertEqual(self._run(spec)[2]["taskId"], "c" * 64)
                source = inspect.getsource(getattr(spec[1], spec[4]))
                self.assertIn('task["surfacePath"] == "explanation"', source)

    def test_bsa321_false_signed_kind_status_digest_and_identity_rejected(self):
        tamper = (
            {"taskId": "e" * 64},
            {"kind": "COMPLETE_MULTILINGUAL_EQUIVALENCE"},
            {"status": "PASS"},
            {"surfaceSha256": "f" * 64},
            {"surfacePath": "prompt"},
        )
        for spec in self.CASES:
            for mutation in tamper:
                with self.subTest(module=spec[0].__name__, mutation=mutation):
                    with self.assertRaises(ValueError):
                        self._run(spec, mutation=mutation)

    def test_bsa321_duplicate_signed_task_row_rejected(self):
        for spec in self.CASES:
            with self.subTest(stage=spec[0].__name__):
                with self.assertRaises(ValueError):
                    self._run(spec, extra=True)

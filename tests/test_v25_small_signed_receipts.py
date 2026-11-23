"""BSA252: same historical BSA251 V24 safe signed receipt split."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from app_generator.runtime import v3_section91_formal_academic_dispatch as runtime
from app_generator.validation import section91_formal_physics as science

ROOT=Path(__file__).resolve().parents[1]


class SignedV25CheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=json.loads(
            (ROOT/"content/chapter-9/section-9-1/package.json").read_text(
                encoding="utf8"))
        cls.proofs=science._prove_exact_roster(src["activities"])
        cls.authorized={
            "sourcePdfSha256":science._SOURCE_SHA,
            "revisedCandidateSha256":science._CANDIDATE_SHA,
            "activityProofs":cls.proofs,
        }
        cls.identity={
            "gitHead":"b"*40,
            "proposalSha256":"c"*64,
            "sourceV24ReceiptSha256":"d"*64,
            "sourceV24AcademicQueueSha256":"e"*64,
        }

    def test_real_eighteen_proof_rows_split_below_historical_12000_cap(self):
        with tempfile.TemporaryDirectory() as root:
            folder=Path(root)
            first=runtime._persist_split_formal_witnesses(
                folder,self.identity,self.authorized)
            second=runtime._persist_split_formal_witnesses(
                folder,self.identity,self.authorized)
            self.assertEqual(first,second)
            self.assertEqual([x["formalModelFamily"] for x in first],
                             ["MCQ","INTERACTIVE"])
            self.assertEqual(sum(x["proofCount"] for x in first),18)
            actual=[]
            for item,path in zip(first,(runtime._V25_MCQ_PROOFS,
                                       runtime._V25_INTERACTIVE_PROOFS)):
                file=folder/path
                self.assertLess(file.stat().st_size,12000)
                contents=json.loads(file.read_text(encoding="utf8"))
                self.assertEqual(contents["integritySha256"],
                                 item["savedSha256"])
                self.assertEqual(contents["formalModelFamily"],
                                 item["formalModelFamily"])
                self.assertFalse(contents["publicationAuthorized"])
                actual+=contents["proofRows"]
            self.assertEqual(actual,self.proofs)

    def test_altered_saved_solution_digest_refused_on_restart(self):
        with tempfile.TemporaryDirectory() as root:
            folder=Path(root)
            runtime._persist_split_formal_witnesses(
                folder,self.identity,self.authorized)
            file=folder/runtime._V25_MCQ_PROOFS
            forged=json.loads(file.read_text(encoding="utf8"))
            forged["proofRows"][0]["answerPhysicsBoundedVerified"]=False
            file.write_text(json.dumps(forged),encoding="utf8")
            with self.assertRaisesRegex(ValueError,
                                          "V3_NATIVE_ADAPTER_V6_CHECKPOINT_CHANGED"):
                runtime._persist_split_formal_witnesses(
                    folder,self.identity,self.authorized)

    def test_formal_scope_mismatch_cannot_drop_or_swap_an_activity(self):
        cases=[]
        missing=deepcopy(self.authorized)
        missing["activityProofs"].pop()
        cases.append(missing)
        repeated=deepcopy(self.authorized)
        repeated["activityProofs"][0]=deepcopy(repeated["activityProofs"][1])
        cases.append(repeated)
        swapped=deepcopy(self.authorized)
        swapped["activityProofs"][0],swapped["activityProofs"][10]=(
            swapped["activityProofs"][10],swapped["activityProofs"][0])
        cases.append(swapped)
        for case in cases:
            with self.subTest(mutant=len(case["activityProofs"])):
                with tempfile.TemporaryDirectory() as root:
                    with self.assertRaisesRegex(ValueError,
                            "BSA252_EIGHTEEN_FORMAL_PROOFS_REQUIRED|BSA252_WRONG_FORMAL_PROOF_PARTITION"):
                        runtime._persist_split_formal_witnesses(
                            Path(root),self.identity,case)


if __name__=="__main__":
    unittest.main()

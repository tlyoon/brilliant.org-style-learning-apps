"""BSA270: first real finite-source MCQ science proof and mutation suite.

CI uses the *repo's real 18-activity package* and substitutes only the PDF
transport, never its physics or utterance semantics. Genuine owner verification
must additionally re-extract the actual one-textbook PDF.
"""
from __future__ import annotations
import copy
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app_generator.validation import section91_first_distractor_proof as science
from app_generator.runtime import v3_first_academic_proof_admission as admission

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/"content/chapter-9/section-9-1/package.json"
AXIOMS={
    "defined to be the product of the mass and velocity":1,
    "linear momentum is a vector":1,
}


class GenuineFirstAcademicTask(TestCase):
    def example(self,mutate=None,source_mutation=False):
        p=json.loads(PACKAGE.read_text(encoding="utf8"))
        if mutate is not None:
            mutate(p)
        with TemporaryDirectory() as t:
            src=Path(t)/"original.pdf"
            src.write_bytes(b"%PDF-test fixture only")
            can=Path(t)/"frozen.json"
            raw=json.dumps(p,ensure_ascii=False,sort_keys=True).encode("utf8")
            can.write_bytes(raw)
            source_sha=sha256(src.read_bytes()).hexdigest()
            can_sha=sha256(raw).hexdigest()
            fake_anchors=[{"activityId":a["id"],
                           "physicalPage":2,
                           "passageSha256":"d"*64,
                           "uniquePagePassageLocated":True}
                          for a in p["activities"]]
            with (patch.object(science,"_SOURCE_SHA",source_sha),
                  patch.object(science,"_CANDIDATE_SHA",can_sha),
                  patch.object(science,"_source_axioms",return_value=AXIOMS),
                  patch.object(science,"extract_pages",
                               return_value=("source1","source2","source3")),
                  patch.object(science,"_source_activity_anchors",
                               return_value=fake_anchors)):
                if source_mutation:
                    src.write_bytes(b"%PDF-falsified source")
                return science.independent_distractor_science(
                    source_pdf=src,candidate_path=can)

    def test_complete_three_locale_distractor_is_falsified_by_two_rationals(self):
        out=self.example()
        self.assertEqual(out["taskKind"],"MCQ_DISTRACTOR_SCIENCE")
        self.assertEqual(out["optionId"],"opt-c")
        self.assertEqual(out["acceptedAcademicTaskCount"],1)
        self.assertEqual(out["remainingFullAcademicTasks"],428)
        self.assertEqual(out["completeAcademicProofGatesStillOpen"],90)
        self.assertEqual(set(out["completeLocalizedFiniteGrammarDigests"]),
                         {"en","ms","zh"})
        self.assertEqual(len(out["exactRationalCounterexamples"]),2)
        self.assertFalse(out["otherTrilingualMeaningProofAccepted"])
        self.assertFalse(out["generalScientificLanguageUnderstandingClaimed"])
        self.assertFalse(out["publicationAuthorized"])

    def test_wrong_scientific_claim_is_not_accepted(self):
        def mutate(p):
            opt=p["activities"][0]["answerKey"]["options"][2]["label"]
            opt["en"]=opt["en"].replace("zero linear momentum","nonzero linear momentum")
        with self.assertRaisesRegex(ValueError,"UNINTERPRETED_OR_CHANGED_OPTION_EN"):
            self.example(mutate)

    def test_malay_negation_change_cannot_pass_lexical_cues(self):
        def mutate(p):
            opt=p["activities"][0]["answerKey"]["options"][2]["label"]
            opt["ms"]=opt["ms"].replace("sifar","bukan sifar")
        with self.assertRaisesRegex(ValueError,"UNINTERPRETED_OR_CHANGED_OPTION_MS"):
            self.example(mutate)

    def test_chinese_claim_reversal_cannot_pass(self):
        def mutate(p):
            opt=p["activities"][0]["answerKey"]["options"][2]["label"]
            opt["zh"]=opt["zh"].replace("均为零","均不为零")
        with self.assertRaisesRegex(ValueError,"UNINTERPRETED_OR_CHANGED_OPTION_ZH"):
            self.example(mutate)

    def test_extra_unexamined_scientific_sentence_fails_closed(self):
        def mutate(p):
            opt=p["activities"][0]["answerKey"]["options"][2]["label"]
            opt["en"]+=" Momentum always points upward."
        with self.assertRaisesRegex(ValueError,"UNINTERPRETED_OR_CHANGED_OPTION_EN"):
            self.example(mutate)

    def test_wrong_context_premise_fails_closed(self):
        def mutate(p):
            p["activities"][0]["prompt"]["en"]=(
                p["activities"][0]["prompt"]["en"].replace(
                    "opposite directions","same directions"))
        with self.assertRaisesRegex(ValueError,"UNINTERPRETED_OR_CHANGED_PREMISE_EN"):
            self.example(mutate)

    def test_forged_correct_option_fails(self):
        def mutate(p):
            p["activities"][0]["answerKey"]["correct"]="opt-c"
        with self.assertRaisesRegex(ValueError,"MC_KEY_OR_DISTRACTOR_IDENTITY"):
            self.example(mutate)

    def test_wrong_source_bytes_fail_even_if_source_axiom_mock_says_yes(self):
        with self.assertRaisesRegex(ValueError,"EXACT_ONE_TEXTBOOK"):
            self.example(source_mutation=True)

    def test_academic_lane_refuses_forged_bounded_evidence_and_zero_gate_bypass(self):
        base={"status":admission._CLAIM,"taskId":admission._ID,
              "sourceSha256":admission._SOURCE_SHA,
              "candidateSha256":admission._CANDIDATE_SHA,
              "taskKind":"MCQ_DISTRACTOR_SCIENCE",
              "acceptedAcademicTaskCount":1,
              "remainingFullAcademicTasks":428,
              "completeAcademicProofGatesStillOpen":90,
              "otherTrilingualMeaningProofAccepted":False,
              "publicationAuthorized":False,"newGeminiCalls":0}
        admission._check_recomputed(base)
        for k,v in (("acceptedAcademicTaskCount",2),
                    ("remainingFullAcademicTasks",427),
                    ("completeAcademicProofGatesStillOpen",89),
                    ("otherTrilingualMeaningProofAccepted",True),
                    ("publicationAuthorized",True)):
            forged=dict(base);forged[k]=v
            with self.subTest(forged=k),self.assertRaisesRegex(
                ValueError,"UNSUPPORTED_ACADEMIC_CLAIM"):
                admission._check_recomputed(forged)

    def test_second_independent_verifier_rejects_forged_rational(self):
        proof=self.example()
        # The synthetic CI source uses test-only hashes/task IDs. Replace only
        # those identities with the authenticated claim shape so the negative
        # mutation actually reaches the second independent arithmetic check.
        proof["sourceSha256"]=admission._SOURCE_SHA
        proof["candidateSha256"]=admission._CANDIDATE_SHA
        proof["taskId"]=admission._ID
        proof["exactRationalCounterexamples"][0]["momentumPositive"]="999"
        receipt={
            "status":admission._STATUS,
            "signedV36Sha256":"a"*64,
            "signedV36FirstPartitionSha256":"b"*64,
            "sourceSha256":admission._SOURCE_SHA,
            "candidateSha256":admission._CANDIDATE_SHA,
            "independentTaskProof":proof,
            "academicTaskAcceptances":1,
            "fullAcademicTasksStillOpen":428,
            "completeAcademicProofGatesStillOpen":90,
            "fullAcademicActivityPASS":0,
            "newProviderCalls":0,
            "publicationAuthorized":False,
        }
        ready={"gitHead":"f"*40,"proposalSha256":"e"*64}
        with (patch.object(admission,"_bound_inputs",
                           return_value=(ROOT,
                                         {"integritySha256":"a"*64},
                                         {"integritySha256":"b"*64},
                                         ROOT/"source.pdf",ROOT/"candidate.json")),
              patch.object(admission,"_signed",return_value=receipt),
              patch.object(admission,"independent_distractor_science",
                           return_value=proof)):
            with self.assertRaisesRegex(ValueError,
                    "INDEPENDENT_RATIONAL_COUNTEREXAMPLE_FAILED"):
                admission.verify_single_academic_receipt(
                    private=ROOT,ready=ready)

    def test_authentic_v36_partition_binding_uses_three_arg_signed_reader(self):
        # Historical BSA270 production failure: calling _signed(file, ready)
        # instead of _signed(folder, name, ready) passed CI unit tests but
        # crashed on real Yoga6. Exercise the REAL _bound_inputs call graph.
        ready={"gitHead":"a"*40,"proposalSha256":"b"*64}
        prior={
            **ready,
            "sourceSha256":admission._SOURCE_SHA,
            "candidateSha256":admission._CANDIDATE_SHA,
            "academicAcceptedProofTaskCount":0,
            "fullSemanticProofTasksStillOpen":429,
            "completeAcademicProofGatesStillOpen":90,
        }
        signed_v36={
            "status":admission._STATUS36,
            "sourceSha256":admission._SOURCE_SHA,
            "revisedCandidateSha256":admission._CANDIDATE_SHA,
            "semanticTasksAutomaticallyDispatched":429,
            "activitySignedPartitionCount":18,
            "fullAcademicProofTasksAccepted":0,
            "completeAcademicProofGatesStillOpen":90,
            "publicationAuthorized":False,
            "integritySha256":"c"*64,
            "signedPartitionHashes":[{
                "activityId":"act-mcq-01-vector-nature",
                "signedEvidenceSha256":"d"*64,
            }],
        }
        signed_first={
            "sourceSha256":admission._SOURCE_SHA,
            "candidateSha256":admission._CANDIDATE_SHA,
            "integritySha256":"d"*64,
            "activity":{"evidenceRows":[{
                "taskId":admission._ID,
                "kind":"MCQ_DISTRACTOR_SCIENCE",
                "status":"BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED",
            }]},
        }
        calls=[]
        def signed(folder,name,incoming):
            self.assertEqual(incoming,ready)
            calls.append(name)
            return {admission._V36:signed_v36,
                    "V36_PARTITION_01.json":signed_first}[name]
        with (patch.object(admission,"read_long_horizon_development",
                           return_value=prior),
              patch.object(admission,"_signed",side_effect=signed),
              patch.object(admission,"_trusted_json",
                           return_value={"sourcePdf":"C:/selected-original.pdf"})):
            folder,_,_,_,_=admission._bound_inputs(ROOT,ready)
        self.assertEqual(calls,[admission._V36,"V36_PARTITION_01.json"])
        self.assertEqual(folder.name,ready["proposalSha256"])

    def test_source_free_worker_never_publishes_our_academic_receipt(self):
        src=(ROOT/"scripts"/"run_v3_yoga6_recovery_worker.py").read_text(
            encoding="utf8")
        self.assertNotIn("admit_first_independent_distractor",src)
        self.assertNotIn("ACADEMIC_A1_SOURCE_BOUND_FIRST_MCQ_DISTRACTOR",src)
        lane=(ROOT/"scripts"/"run_bosla_first_academic_proof.py").read_text(
            encoding="utf8")
        self.assertIn("admit_first_independent_distractor",lane)
        self.assertIn("verify_first_academic_frontier",lane)

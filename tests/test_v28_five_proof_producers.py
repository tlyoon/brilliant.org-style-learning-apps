"""BSA256 five-channel real proof producers: adversarial and restart tests."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.validation import independent_academic_proof_producers as proof
from app_generator.runtime import v3_post_v27_five_proof_producers as runtime
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint

ROOT=Path(__file__).resolve().parents[1]


class IndependentFiveChannelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package=json.loads((ROOT/"content/chapter-9/section-9-1/package.json"
            ).read_text(encoding="utf8"))

    def case(self):
        return {
            "template":"mechanics.cart_collision_1d",
            "semanticParameters":{"phase":"before","track_orientation":"horizontal"},
            "entities":[
                {"id":"cart-a","kind":"cart","properties":{"mass":"2"}},
                {"id":"cart-b","kind":"cart","properties":{"mass":"4"}},
            ],
            "vectors":[
                {"entityId":"cart-a","quantity":"velocity",
                 "direction":"right","relativeMagnitude":0.5},
                {"entityId":"cart-b","quantity":"velocity",
                 "direction":"left","relativeMagnitude":0.25},
            ],
        }

    def test_bounded_real_renderable_cart_diagram_vector_physics(self):
        result=proof.audit_diagram_vector_physics(self.case())
        self.assertEqual(result["signedInitialMomenta"],["1","-1"])
        self.assertEqual(result["netInitialMomentum"],"0")
        self.assertTrue(result["oppositeDirections"])
        self.assertFalse(result["renderedPixelGeometryVerified"])
        self.assertFalse(result["completeAcademicPASS"])

    def test_diagram_wrong_arrow_and_phase_fail_closed(self):
        for change in ("same_direction","bad_phase","negative_mass",
                       "wrong_cart","missing_arrow","duplicated_entity"):
            item=self.case()
            if change=="same_direction":
                item["vectors"][1]["direction"]="right"
                # Physical arithmetic is not inherently wrong if both carts
                # travel right; only net-zero assumption must not be forged.
                result=proof.audit_diagram_vector_physics(item)
                self.assertEqual(result["netInitialMomentum"],"2")
                self.assertFalse(result["oppositeDirections"])
                continue
            elif change=="bad_phase":
                item["semanticParameters"]["phase"]="after"
            elif change=="negative_mass":
                item["entities"][0]["properties"]["mass"]=-2
            elif change=="wrong_cart":
                item["vectors"][0]["entityId"]="invisible-cart"
            elif change=="missing_arrow":
                item["vectors"].pop()
            else:
                item["entities"][1]["id"]="cart-a"
            with self.subTest(change=change):
                with self.assertRaisesRegex(ValueError,"BSA256_DIAGRAM"):
                    proof.audit_diagram_vector_physics(item)

    def test_chinese_numeric_source_section_reference_is_not_silently_dropped(self):
        self.assertEqual(proof._NUMERIC.findall("第9.1节 第9.1节"),["9.1","9.1"])
        self.assertEqual(proof._NUMERIC.findall("Section 9.1"),["9.1"])
        self.assertEqual(proof._NUMERIC.findall("p2 and X32"),[])
        self.assertEqual(proof._NUMERIC.findall("0.5 m/s"),["0.5"])

    def test_nine_real_mcq_model_truth_sets_are_independently_computed(self):
        from app_generator.validation.section91_formal_physics import _mcq_cases
        truth=_mcq_cases()
        self.assertEqual(len(truth),9)
        self.assertEqual(sum(not ok for rows in truth.values()
                             for ok in rows.values()),27)
        for activity in self.package["activities"][:9]:
            model=truth[activity["id"]]
            self.assertEqual(
                {x for x,v in model.items() if v},
                {activity["answerKey"]["correct"]})

    def test_explicit_numeric_wrong_answer_is_detected_by_model(self):
        from app_generator.validation.section91_formal_physics import (
            _mcq_cases, _prove_exact_roster,
        )
        activities=deepcopy(self.package["activities"])
        act=activities[0]
        false_key=next(k for k,v in _mcq_cases()[act["id"]].items() if not v)
        act["answerKey"]["correct"]=false_key
        with self.assertRaises(ValueError):
            _prove_exact_roster(activities)

    def test_private_source_is_sha_bound_before_any_expensive_check(self):
        with tempfile.TemporaryDirectory() as temp:
            pdf=Path(temp)/"source.pdf"
            candidate=Path(temp)/"package.json"
            pdf.write_bytes(b"%PDF-\nnot permitted original")
            candidate.write_text(json.dumps(self.package),encoding="utf8")
            with self.assertRaisesRegex(ValueError,"SHA_CHANGED"):
                proof.audit_five_proof_channels(
                    source_pdf=pdf,source_sha="0"*64,candidate_path=candidate)

    def test_partial_scientific_evidence_cannot_claim_full_academic_approval(self):
        baseline={
            "status":"BSA256_FIVE_INDEPENDENT_BOUNDED_PRODUCERS_EXECUTED",
            "sourceSha256":runtime._SOURCE_SHA,
            "candidateSha256":runtime._CANDIDATE_SHA,
            "sourceFidelity":{"pageAnchorsReextracted":18,
                "fullSourceStatementMeaningProven":False},
            "scientificExplanations":{"textbookAxiomsReextracted":9,
                "boundedMathWitnesses":68,
                "fullExplanationClauseTruthProven":False},
            "mcqIncorrectChoices":{"correctMCQKeysVerified":9,
                "falseMCQAlternativeCountermodels":27,
                "allDistractorNaturalLanguageSemanticsProven":False},
            "englishMalayChinese":{"localizedSurfacesInspected":222,
                "matchingNumericLiteralSurfaces":222,
                "numericLiteralReviewNeeded":0,
                "strictFormulaLiteralMatches":0,
                "unresolvedSymbolicFields":2,
                "fullTrilingualMeaningProven":False},
            "interactiveDiagrams":{"declaredDiagramsFound":0,
                "sourceGroundedVisualNecessityTasksOpen":18,
                "sourceSectionMentionsFigure91":True,
                "renderedVisualScienceApproved":False},
            "originalIndependentSemanticTasksPending":429,
            "completeAcademicProofGatesStillOpen":90,
            "formalAcademicPASS":0,"providerCalls":0,
            "additionalTextbooks":0,"publicationAuthorized":False,
        }
        runtime._assert_bounded_receipt(baseline)
        for section,key in [
            ("scientificExplanations","fullExplanationClauseTruthProven"),
            ("mcqIncorrectChoices","allDistractorNaturalLanguageSemanticsProven"),
            ("englishMalayChinese","fullTrilingualMeaningProven"),
            ("interactiveDiagrams","renderedVisualScienceApproved"),
        ]:
            changed=deepcopy(baseline)
            changed[section][key]=True
            with self.subTest(section=section):
                with self.assertRaisesRegex(ValueError,"FALSELY_PROMOTED"):
                    runtime._assert_bounded_receipt(changed)
        changed=deepcopy(baseline)
        changed["formalAcademicPASS"]=18
        with self.assertRaisesRegex(ValueError,"FALSELY_PROMOTED"):
            runtime._assert_bounded_receipt(changed)

    def test_wrong_v27_receipt_fails_before_opening_textbook(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)
            ready={"gitHead":"a"*40,"proposalSha256":"b"*64}
            old={"status":"FORGED","integritySha256":"x"*64}
            with (patch.object(runtime,"_preflight",
                               return_value=(folder,None,None,None,None)),
                  patch.object(runtime,"_signed",return_value=old),
                  patch.object(runtime,"_trusted_json",
                               side_effect=AssertionError("PDF must remain unopened"))):
                with self.assertRaisesRegex(ValueError,"SIGNED_V27"):
                    runtime.run_post_v27_five_proof_producers(
                        ROOT,folder,ready,{},{},{},old)

    def test_small_signed_checkpoint_restart_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/runtime._V28_RESULT
            original={"gitHead":"a"*40,"proposalSha256":"b"*64,
                      "status":"NO_ACADEMIC_PASS","publicationAuthorized":False,
                      "boundedMathWitnesses":68}
            one=_v6_checkpoint(target,original)
            self.assertLess(target.stat().st_size,12000)
            self.assertEqual(one,_v6_checkpoint(target,original))
            wrong=dict(original,boundedMathWitnesses=0)
            with self.assertRaisesRegex(ValueError,"CHECKPOINT_CHANGED"):
                _v6_checkpoint(target,wrong)

    def test_normal_worker_v28_is_not_skipped(self):
        worker=(ROOT/"scripts/run_v3_yoga6_recovery_worker.py").read_text(
            encoding="utf8")
        self.assertIn("run_post_v27_five_proof_producers(",worker)
        self.assertIn('result["fiveChannelProofProducers"]',worker)
        self.assertIn(runtime._STATUS28,worker)


if __name__=="__main__":
    unittest.main()

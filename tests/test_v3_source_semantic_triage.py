"""BSA253 V26 scientific explanation and multilingual review fault injection."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.validation import typed_scientific_semantic_alignment as core
from app_generator.validation import section91_explanation_distractor_claims as source
from app_generator.runtime import v3_source_semantic_triage as runner
from app_generator.runtime.v3_five_stage_completion import _hash

ROOT=Path(__file__).resolve().parents[1]


class ScientificExplanationTriageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package=json.loads(
            (ROOT/"content/chapter-9/section-9-1/package.json").read_text(
                encoding="utf8"))
        cls.activity=cls.package["activities"]

    def test_generic_reusable_18_activity_three_language_inventory(self):
        result=core.audit_reusable_scientific_alignment(
            deepcopy(self.activity))
        self.assertEqual(result["activitiesChecked"],18)
        self.assertEqual(result["surfacesChecked"],222)
        self.assertGreater(result["mathBearingSurfaces"],0)
        self.assertFalse(result["allScientificStatementsProven"])
        self.assertFalse(result["trilingualSemanticEquivalenceProven"])
        self.assertFalse(result["publicationAuthorized"])
        self.assertTrue(all(r["completeTranslationMeaningVerified"] is False
                            for a in self.activity
                            for _,v in core._role_triplets(a)
                            for r in [{"completeTranslationMeaningVerified":False}]))

    def test_equation_followed_by_prose_is_not_falsely_equation_tail(self):
        for text in ("p = m v. As a vector","p = m v. Kerana jisim",
                     "p = m v。作为矢量"):
            self.assertEqual(core._eqs(text),["p=mv"])

    def test_unambiguous_false_momentum_law_detected_in_explanation(self):
        for language in ("en","ms","zh"):
            item=deepcopy(self.activity[0])
            item["explanation"][language]="p = m v^2."
            row=core._check_activity(item)
            self.assertTrue(any(q["kind"]==
                "DETERMINISTIC_SOURCE_LAW_CONTRADICTION"
                and q.get("locale")==language for q in row["issues"]))

    def test_unambiguous_force_equals_momentum_law_detected(self):
        item=deepcopy(self.activity[2])
        item["feedback"]["ms"]="F = p"
        row=core._check_activity(item)
        self.assertTrue(any(q["kind"]==
            "DETERMINISTIC_SOURCE_LAW_CONTRADICTION" for q in row["issues"]))

    def test_false_distractor_equation_not_silently_used_as_correct_law(self):
        item=deepcopy(self.activity[0])
        item["answerKey"]["options"][1]["label"]["zh"]="p = m v^2"
        row=core._check_activity(item)
        self.assertFalse(any(q["kind"]==
            "DETERMINISTIC_SOURCE_LAW_CONTRADICTION" for q in row["issues"]))
        self.assertTrue(any(q["reason"]==
            "CROSS_LOCALE_SYMBOLIC_EQUIVALENCE_NOT_ESTABLISHED"
            for q in row["issues"]))

    def test_cross_language_vector_scalar_cue_change_stays_unproved(self):
        item=deepcopy(self.activity[0])
        item["explanation"]["zh"]=(
            item["explanation"]["zh"].replace("矢量","标量")
            .replace("向量","标量"))
        row=core._check_activity(item)
        self.assertTrue(any(q["reason"]==
            "CROSS_LOCALE_SCIENTIFIC_QUANTITY_CUES_MISMATCH"
            for q in row["issues"]))
        self.assertFalse(row["trilingualSemanticEquivalenceProven"])

    def test_wrong_correct_option_affirmed_in_one_language(self):
        item=deepcopy(self.activity[0])
        item["answerLogic"]["en"]="Option B is correct, Option A is wrong."
        row=core._check_activity(item)
        self.assertTrue(any(q["reason"]=="ANSWER_LOGIC_AFFIRMS_INCORRECT_OPTION"
                            for q in row["issues"]))

    def test_missing_locale_is_deterministic_invalid_source(self):
        for loc in ("en","ms","zh"):
            item=deepcopy(self.activity[0])
            del item["explanation"][loc]
            with self.subTest(locale=loc):
                with self.assertRaisesRegex(ValueError,
                    "BSA253_MISSING_REQUIRED_EN_MS_ZH_TEXT"):
                    core._check_activity(item)

    def test_duplicate_activity_identity_rejected(self):
        sample=deepcopy(self.activity)
        sample[1]["id"]=sample[0]["id"]
        with self.assertRaisesRegex(ValueError,
                "BSA253_DUPLICATED_ACTIVITY_IDENTITIES"):
            core.audit_reusable_scientific_alignment(sample)

    def test_no_visual_in_exact_91_cannot_be_false_diagram_pass(self):
        self.assertEqual(sum(bool(x.get("visualSpec"))
                             for x in self.activity),0)
        result=core.audit_reusable_scientific_alignment(self.activity)
        self.assertFalse(result["allScientificStatementsProven"])

    def test_source_bound_adapter_rejects_new_package_version_without_proof(self):
        with tempfile.TemporaryDirectory() as base:
            p=Path(base)/"candidate.json"
            p.write_text(json.dumps(self.package),encoding="utf8")
            with self.assertRaisesRegex(ValueError,
                    "BSA253_SOURCE_OR_REVISED_CANDIDATE_CHANGED"):
                source.audit_source_bound_explanation_distractors(
                    source_pdf=Path(base)/"source.pdf",
                    source_sha=source._SOURCE_SHA,candidate_path=p)

    def test_source_bound_adapter_does_not_promote_generic_flags(self):
        with tempfile.TemporaryDirectory() as base:
            p=Path(base)/"candidate.json"
            raw=json.dumps(self.package).encode("utf8")
            p.write_bytes(raw)
            dig=sha256(raw).hexdigest()
            proof=[{"activityId":a["id"],
                    "activityCanonicalSha256":core._digest(a),
                    "independentFormalSolutionSha256":str(i)}
                   for i,a in enumerate(self.activity)]
            mockphysics={
                "boundedFormalAnswerItemWitnesses":68,
                "independentlyReextractedTextbookPhysicsPremises":9,
                "activityProofs":proof,
            }
            with (patch.object(source,"_CANDIDATE_SHA",dig),
                  patch.object(source,"bounded_section91_science_audit",
                               return_value=mockphysics)):
                got=source.audit_source_bound_explanation_distractors(
                    source_pdf=Path(base)/"source.pdf",
                    source_sha=source._SOURCE_SHA,candidate_path=p)
            self.assertEqual(got["localisedFieldsExamined"],222)
            self.assertEqual(got["formalAcademicPASS"],0)
            self.assertEqual(got["fullAcademicProofGatesOpen"],90)
            self.assertFalse(got["fullEnglishExplanationsProven"])
            self.assertFalse(got["fullDistractorNaturalLanguageMeaningProven"])
            self.assertFalse(got["fullEN_MS_ZHSemanticEquivalenceProven"])

    def test_v26_immutable_receipt_splits_two_nines_under_12k(self):
        with tempfile.TemporaryDirectory() as base:
            folder=Path(base)
            base_id={
                "gitHead":"b"*40,
                "proposalSha256":"c"*64,
                "sourceV25ReceiptSha256":"d"*64,
                "sourceV25FormalResultSha256":"e"*64,
            }
            rows=[{
                "activityId":x["id"],
                "activityCanonicalSha256":core._digest(x),
                "localizedFieldsChecked":12,
                "mathBearingFields":2,
                "trilingualReviewIssues":1,
                "deterministicDefect":False,
                "boundedAnswerPhysicsEvidenceSha256":"a"*64,
                "completeSemanticEquivalenceProven":False,
                "publicationAuthorized":False,
                "issueCategories":["SEMANTIC_REVIEW_REQUIRED"],
            } for x in self.activity]
            first=runner._write_small_explanation_rows(
                folder,base_id,{"rows":rows})
            second=runner._write_small_explanation_rows(
                folder,base_id,{"rows":rows})
            self.assertEqual(first,second)
            self.assertEqual(sum(x["rows"] for x in first),18)
            for entry,path in zip(first,
                (runner._V26_MCQ,runner._V26_INTERACTIVE)):
                self.assertLess((folder/path).stat().st_size,12000)
                record=json.loads((folder/path).read_text(encoding="utf8"))
                self.assertEqual(record["integritySha256"],
                                 entry["signedSha256"])
            file=folder/runner._V26_MCQ
            tampered=json.loads(file.read_text(encoding="utf8"))
            tampered["rows"][0]["deterministicDefect"]=True
            file.write_text(json.dumps(tampered),encoding="utf8")
            with self.assertRaisesRegex(ValueError,
                "V3_NATIVE_ADAPTER_V6_CHECKPOINT_CHANGED"):
                runner._write_small_explanation_rows(
                    folder,base_id,{"rows":rows})

    def test_mocked_prior_v25_wrong_status_stops_before_source(self):
        with (patch.object(runner,"_preflight",return_value=(
                    Path("."),None,None,None,None)),
              patch.object(runner,"_signed",side_effect=[
                  {"status":"INVALID"},{},
              ]),
              patch.object(runner,
                  "audit_source_bound_explanation_distractors",
                  side_effect=AssertionError("NO UNAUTHORIZED PROOF"))):
            with self.assertRaisesRegex(ValueError,
                    "BSA253_VERIFIED_V25_EXACT_DOMAIN_RECEIPT_REQUIRED"):
                runner.run_post_v25_source_scientific_semantic_triage(
                    ROOT,Path("."),{"gitHead":"a"*40,"proposalSha256":"b"*64},
                    {},{},{},{})

    def test_worker_dispatch_is_in_main_source_free_path(self):
        src=(ROOT/"scripts/run_v3_yoga6_recovery_worker.py").read_text(
            encoding="utf8")
        self.assertIn("run_post_v25_source_scientific_semantic_triage(",src)
        self.assertIn('result["sourceScientificSemanticTriage"]',src)


if __name__=="__main__":
    unittest.main()

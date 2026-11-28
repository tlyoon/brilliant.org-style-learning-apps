"""BSA275: negative-controls for bounded proof batches and vector science."""
from __future__ import annotations
import copy
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app_generator.validation import academic_science_batch_execution as batch
from app_generator.validation import section91_vector_orientation_proof as science
from tests.test_v46_generic_academic_proof_registry import (
    GenericProofRegistry, FIRST, SECOND, THIRD,
)

ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=ROOT/"content/chapter-9/section-9-1/package.json"


def signed_report():
    return GenericProofRegistry().audit()


def controlled_science(mutate=None,source_corrupt=False,source_axioms=True):
    p=json.loads(CANDIDATE.read_text(encoding="utf8"))
    if mutate: mutate(p)
    with TemporaryDirectory() as temp:
        pdf=Path(temp)/"source.pdf"
        pdf.write_bytes(b"%PDF-bounded-synthetic-transport")
        candidate=Path(temp)/"candidate.json"
        candidate.write_text(json.dumps(p,ensure_ascii=False,sort_keys=True),
                             encoding="utf8")
        source_sha=sha256(pdf.read_bytes()).hexdigest()
        candidate_sha=sha256(candidate.read_bytes()).hexdigest()
        anchors=[{"activityId":a["id"],"physicalPage":2,
                  "passageSha256":"a"*64,
                  "uniquePagePassageLocated":True}
                 for a in p["activities"]]
        if source_corrupt: pdf.write_bytes(b"tampered")
        axioms={
            "defined to be the product of the mass and velocity":1,
            "linear momentum is a vector":1,
        } if source_axioms else {}
        with (patch.object(science,"_SOURCE_SHA",source_sha),
              patch.object(science,"_CANDIDATE_SHA",candidate_sha),
              patch.object(science,"_source_axioms",return_value=axioms),
              patch.object(science,"extract_pages",return_value=("a","b")),
              patch.object(science,"_source_activity_anchors",
                           return_value=anchors)):
            return science.verify_perpendicular_momentum_false(
                source_pdf=pdf,candidate_path=candidate)


class BoundedScienceBatch(TestCase):
    def test_verified_two_prior_academic_proofs_never_inflate_batch_count(self):
        report=signed_report()
        plan=batch.plan_next_science_batch(audit=report,cursor=0,maximum=4)
        self.assertEqual(plan["taskCount"],4)
        self.assertEqual(plan["acceptedAcademicTasksBeforeBatch"],2)
        self.assertEqual(plan["academicTasksAcceptedByBatch"],0)
        self.assertEqual(plan["completeAcademicProofGatesStillOpen"],90)
        self.assertEqual(plan["remainingAfterBatch"],21)
        result=batch.execute_source_bound_science_batch(batch=plan,rules=())
        self.assertEqual(result["verifiedWitnessCount"],0)
        self.assertEqual(result["academicTasksAcceptedByBatch"],0)
        self.assertEqual(len(result["results"]),4)
        self.assertTrue(all(x["status"].startswith("NOT_ELIGIBLE")
                            for x in result["results"]))

    def test_bounded_restart_cursor_and_closed_input_validation(self):
        report=signed_report()
        last=batch.plan_next_science_batch(audit=report,cursor=24,maximum=6)
        self.assertEqual(last["taskCount"],1)
        self.assertEqual(last["remainingAfterBatch"],0)
        for cursor,maximum in ((-1,4),(26,4),(0,7),(0,0),(True,3)):
            with self.subTest(cursor=cursor,maximum=maximum):
                with self.assertRaises(ValueError):
                    batch.plan_next_science_batch(
                        audit=report,cursor=cursor,maximum=maximum)

    def test_forged_academic_count_and_duplicate_pending_refused(self):
        report=signed_report()
        for key,value in (
            ("acceptedMcqDistractorTaskCount",3),
            ("fullAcademicTasksStillOpen",426),
            ("completeAcademicProofGatesStillOpen",89),
            ("publicationAuthorized",True),
        ):
            fake=copy.deepcopy(report);fake[key]=value
            with self.subTest(field=key),self.assertRaises(ValueError):
                batch.plan_next_science_batch(audit=fake)
        fake=copy.deepcopy(report)
        fake["pendingMcqTasks"][1]=copy.deepcopy(fake["pendingMcqTasks"][0])
        with self.assertRaisesRegex(ValueError,"INVALID_27_DISTRACTOR"):
            batch.plan_next_science_batch(audit=fake)

    def test_isolated_fault_does_not_strand_other_bounded_proofs(self):
        report=signed_report()
        plan=batch.plan_next_science_batch(audit=report,cursor=0,maximum=3)
        first,second=plan["taskIds"][:2]
        def broken():
            raise ValueError("failure in one scientific handler")
        def verified():
            return {
                "taskId":second,
                "sourceSha256":plan["sourceSha256"],
                "candidateSha256":plan["candidateSha256"],
                "surfaceSha256":plan["tasks"][1]["surfaceSha256"],
                "witnessSha256":"a"*64,
                "independentScienceWitnessVerified":True,
                "newProviderCalls":0,
                "publicationAuthorized":False,
            }
        r=batch.execute_source_bound_science_batch(
            batch=plan,rules=(
                batch.ScienceBatchRule(first,broken),
                batch.ScienceBatchRule(second,verified),
            ))
        self.assertEqual(r["quarantinedCount"],1)
        self.assertEqual(r["verifiedWitnessCount"],1)
        self.assertEqual(r["academicTasksAcceptedByBatch"],0)
        self.assertFalse(r["publicationAuthorized"])

    def test_prior_independent_batch_admission_is_excluded_on_restart(self):
        report=signed_report()
        already=report["pendingMcqTasks"][0]["taskId"]
        future=batch.plan_next_science_batch(
            audit=report,cursor=0,maximum=4,
            independently_admitted_new_task_ids=(already,))
        self.assertEqual(future["acceptedAcademicTasksBeforeBatch"],3)
        self.assertEqual(future["remainingAfterBatch"],20)
        self.assertEqual(future["taskCount"],4)
        self.assertNotIn(already,future["taskIds"])
        self.assertEqual(future["academicTasksAcceptedByBatch"],0)
        for extras in ((already,already),(FIRST,),("f"*64,)):
            with self.subTest(extras=extras),self.assertRaisesRegex(
                ValueError,"UNVERIFIED_NEW_ACADEMIC_FRONTIER_IDS"):
                batch.plan_next_science_batch(
                    audit=report,independently_admitted_new_task_ids=extras)

    def test_fake_witness_never_becomes_accepted(self):
        plan=batch.plan_next_science_batch(audit=signed_report())
        task=plan["tasks"][0]
        def fake():
            return {"taskId":task["taskId"],
                    "sourceSha256":plan["sourceSha256"],
                    "candidateSha256":plan["candidateSha256"],
                    "surfaceSha256":task["surfaceSha256"],
                    "witnessSha256":"bogus",
                    "independentScienceWitnessVerified":True,
                    "newProviderCalls":0,"publicationAuthorized":False}
        result=batch.execute_source_bound_science_batch(batch=plan,rules=(
            batch.ScienceBatchRule(task["taskId"],fake),))
        self.assertEqual(result["quarantinedCount"],1)
        self.assertEqual(result["academicTasksAcceptedByBatch"],0)


class ThirdScientificFalseChoice(TestCase):
    def test_real_three_locale_false_perpendicular_momentum_counterexamples(self):
        proof=controlled_science()
        self.assertEqual(proof["optionId"],"opt-d")
        self.assertFalse(proof["academicTaskAccepted"])
        self.assertEqual(set(proof["completeLocalizedFiniteGrammarDigests"]),
                         {"en","ms","zh"})
        science.independently_recheck_vector_witness(proof)
        self.assertEqual(len(proof["rationalVectorCountermodels"]),2)
        for c in proof["rationalVectorCountermodels"]:
            for drone in c["drones"]:
                self.assertGreater(Fraction(drone["dotVelocityMomentum"]),0)
                self.assertEqual(tuple(drone["crossVelocityMomentum"]),
                                 ("0","0","0"))
                self.assertEqual(drone["verticalMomentumComponent"],"0")

    def test_wrong_english_sense_refused(self):
        def wrong(p):
            t=p["activities"][0]["answerKey"]["options"][3]["label"]
            t["en"]=t["en"].replace("perpendicular to their flight path",
                                    "parallel to their flight path")
        with self.assertRaisesRegex(ValueError,"UNINTERPRETED_OR_CHANGED_BSA275_OPTION_EN"):
            controlled_science(wrong)

    def test_malay_and_chinese_negation_reversal_refused(self):
        for locale,term,new in (
            ("ms","sudut tepat","sehala"),
            ("zh","\u5782\u76f4","\u5e73\u884c"),
        ):
            def mutate(p):
                t=p["activities"][0]["answerKey"]["options"][3]["label"]
                t[locale]=t[locale].replace(term,new)
            with self.subTest(locale=locale),self.assertRaisesRegex(
                ValueError,"UNINTERPRETED_OR_CHANGED_BSA275_OPTION_"+locale.upper()):
                controlled_science(mutate)

    def test_source_or_key_change_refused(self):
        with self.assertRaisesRegex(ValueError,"ORIGINAL_TEXTBOOK"):
            controlled_science(source_corrupt=True)
        with self.assertRaisesRegex(ValueError,"MISSING_ORIGINAL_VECTOR_LAW"):
            controlled_science(source_axioms=False)
        def key(p):
            p["activities"][0]["answerKey"]["correct"]="opt-d"
        with self.assertRaisesRegex(ValueError,"FALSE_OPTION_OR_KEY_CHANGED"):
            controlled_science(key)

    def test_forged_rational_vector_witness_rejected(self):
        p=controlled_science()
        p["rationalVectorCountermodels"][0]["drones"][0]["dotVelocityMomentum"]="0"
        with self.assertRaisesRegex(ValueError,"VECTOR_WITNESS_INTEGRITY"):
            science.independently_recheck_vector_witness(p)
        # Even if an attacker updates a superficial digest, arithmetic MUST
        # be independently reconstructed from the exact rational premises.
        p["witnessSha256"]=science._digest(
            {k:v for k,v in p.items() if k!="witnessSha256"})
        with self.assertRaisesRegex(ValueError,"INDEPENDENT_VECTOR_ARITHMETIC"):
            science.independently_recheck_vector_witness(p)

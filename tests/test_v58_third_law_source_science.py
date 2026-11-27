"""BSA281 adversarial exact-rational Newton third-law false-choice witnesses.

CI tests validate algebra and fail-closed frozen trilingual clauses. Owner
Yoga6 also reopens original selected 3-page Serway PDF and signed V36 MCQ05;
synthetic CI tests alone NEVER admit source science or 90 full activities.
"""
from __future__ import annotations

from fractions import Fraction as F
from pathlib import Path
import json
from unittest import TestCase

from app_generator.validation import section91_third_law_false_options_proof as physics


def witness(option_id:str)->dict:
    body={
        "taskId":physics._TASK_IDS[option_id],
        "optionId":option_id,
        "falseScientificAssertion":physics._FALSE_CLASSES[option_id],
        "proofFamily":physics._PROOF,
        "premiseSemanticRole":physics._TRUE_SEMANTIC_ROLE,
        "completePromptLocaleDigests":physics._PROMPT_SHA,
        "completeFalseOptionLocaleDigests":physics._OPTION_SHA[option_id],
        "sourceSha256":physics._SOURCE_SHA,
        "candidateSha256":physics._CANDIDATE_SHA,
        "rationalIsolatedPairCountermodels":physics._models(),
        "independentScienceWitnessVerified":True,
        "academicTaskAccepted":False,
        "completeAcademicProofGatesStillOpen":90,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    }
    return {**body,"witnessSha256":physics._digest(body)}


def rehash(value:dict)->dict:
    value["witnessSha256"]=physics._digest({
        k:v for k,v in value.items() if k!="witnessSha256"})
    return value


class ThirdLawOriginalScienceModels(TestCase):
    def test_three_distinct_false_choices_independently_countermodelled(self):
        self.assertEqual(set(physics._FALSE_CLASSES),{"opt-b","opt-c","opt-d"})
        self.assertEqual(len(set(physics._FALSE_CLASSES.values())),3)
        self.assertEqual(len(set(physics._TASK_IDS.values())),3)
        for option in physics._FALSE_CLASSES:
            with self.subTest(option=option):
                physics.independently_check_third_law_witness(witness(option))

    def test_rational_force_impulse_acceleration_and_total_momentum(self):
        for row in physics._models():
            m1,m2=F(row["mass1"]),F(row["mass2"])
            j,dt=F(row["impulseOn1"]),F(row["interactionDuration"])
            p1,p2=F(row["particle1MomentumBefore"]),F(row["particle2MomentumBefore"])
            q1,q2=F(row["particle1MomentumAfter"]),F(row["particle2MomentumAfter"])
            f1,f2=F(row["forceOn1"]),F(row["forceOn2"])
            self.assertGreater(m1,0)
            self.assertGreater(m2,0)
            self.assertNotEqual(m1,m2)
            self.assertNotEqual(j,0)
            self.assertEqual(f1,-f2)
            self.assertEqual(q1-p1,j)
            self.assertEqual(q2-p2,-j)
            self.assertEqual(f1,(q1-p1)/dt)
            self.assertEqual(f2,(q2-p2)/dt)
            self.assertEqual(F(row["particle1Acceleration"]),f1/m1)
            self.assertEqual(F(row["particle2Acceleration"]),f2/m2)
            self.assertNotEqual(F(row["particle1Acceleration"]),0)
            self.assertNotEqual(F(row["particle2Acceleration"]),0)
            self.assertEqual(p1+p2,q1+q2)
            self.assertNotEqual(p1,q1)
            self.assertNotEqual(p2,q2)
            self.assertNotEqual(row["particle1VelocityAfter"],
                                row["particle2VelocityAfter"])

    def test_science_tampering_cannot_pass_even_with_fresh_fake_hash(self):
        variants=(
            ("opt-b","particle1MomentumAfter","2"),
            ("opt-c","particle1Acceleration","0"),
            ("opt-d","mass2","2"),
            ("opt-c","forceOn2","2"),
            ("opt-b","totalMomentumAfter","999"),
            ("opt-d","thirdLawRequiresEqualMassOrVelocity",True),
            ("opt-b","individualMomentaRemainConstant",True),
            ("opt-c","individualAccelerationsVanish",True),
        )
        for option,key,bad in variants:
            w=witness(option)
            w["rationalIsolatedPairCountermodels"][0][key]=bad
            with self.subTest(option=option,key=key),self.assertRaisesRegex(
                ValueError,"COUNTERMODELS_NOT_DISTINCT"):
                physics.independently_check_third_law_witness(rehash(w))

    def test_changed_source_or_candidate_or_claims_always_rejected(self):
        variants=(
            ("sourceSha256","0"*64),("candidateSha256","f"*64),
            ("academicTaskAccepted",True),("publicationAuthorized",True),
            ("newProviderCalls",1),("completeAcademicProofGatesStillOpen",89),
            ("falseScientificAssertion","REAL_TRUE"),
            ("taskId","a"*64),
            ("premiseSemanticRole","SOURCE_FREE"),
        )
        for key,bad in variants:
            w=witness("opt-b")
            w[key]=bad
            with self.subTest(key=key),self.assertRaises(ValueError):
                physics.independently_check_third_law_witness(rehash(w))

    def test_all_complete_three_language_literals_pinned_to_real_package(self):
        pkg=json.loads(
            Path("content/chapter-9/section-9-1/package.json").read_text(
                encoding="utf8"))
        activity=pkg["activities"][4]
        self.assertEqual(activity["id"],physics._ACTIVITY)
        self.assertEqual(
            physics._all_locales(activity["prompt"],physics._PROMPT_SHA),
            physics._PROMPT_SHA)
        for option in activity["answerKey"]["options"][1:]:
            id=option["id"]
            self.assertEqual(
                physics._all_locales(option["label"],
                                     physics._OPTION_SHA[id]),
                physics._OPTION_SHA[id])
            for lang in ("en","ms","zh"):
                for changed in (
                    option["label"][lang]+" unreviewed",
                    option["label"][lang][:-1],
                    option["label"][lang]+" NOT",
                ):
                    with self.subTest(option=id,lang=lang):
                        with self.assertRaises(ValueError):
                            physics._all_locales(
                                {**option["label"],lang:changed},
                                physics._OPTION_SHA[id])

    def test_missing_or_extra_language_fails_closed(self):
        for labels in (
            {"en":"a","ms":"b"},
            {"en":"a","ms":"b","zh":"c","fr":"d"},
            {"en":"a","ms":"b","zh":""},
        ):
            with self.assertRaises(ValueError):
                physics._all_locales(labels,physics._PROMPT_SHA)

    def test_degenerate_interaction_rejected(self):
        good=physics._CASE_PARAMETERS[0]
        for bad in (
            (F(0),*good[1:]),
            (good[0],good[0],*good[2:]),
            (*good[:4],F(0),good[-1]),
            (*good[:5],F(0)),
        ):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                physics._model(*bad)

    def test_no_academic_gate_or_release_is_granted_by_witness(self):
        w=witness("opt-d")
        self.assertIs(w["academicTaskAccepted"],False)
        self.assertIs(w["publicationAuthorized"],False)
        self.assertEqual(w["completeAcademicProofGatesStillOpen"],90)

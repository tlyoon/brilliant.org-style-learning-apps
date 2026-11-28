"""BSA278 original-source paired-glider rational science negative controls.

The selected original Serway PDF was separately reopened on Yoga6 with
complete genuine trilingual MCQ04 and source-bound task identities; these
synthetic algebra and sentence mutation tests cannot replace that proof.
"""
from __future__ import annotations

from fractions import Fraction
from unittest import TestCase

from app_generator.validation import section91_paired_glider_false_options_proof as glider


def witness(option_id:str)->dict:
    body={
        "optionId":option_id,
        "proofFamily":"PAIRED_OPPOSITE_VECTOR_MOMENTA_SCALAR_KINETIC_ENERGY",
        "sourceSha256":glider._SOURCE_SHA,
        "candidateSha256":glider._CANDIDATE_SHA,
        "falseScientificAssertion":glider._FALSE_CLASSES[option_id],
        "exactRationalSystemModels":glider._models(),
        "independentScienceWitnessVerified":True,
        "academicTaskAccepted":False,
        "completeAcademicProofGatesStillOpen":90,
        "newProviderCalls":0,
        "publicationAuthorized":False,
    }
    return {**body,"witnessSha256":glider._digest(body)}


class PairedGliderScience(TestCase):
    def test_all_three_distinct_wrong_paired_momentum_energy_claims(self):
        for option_id in ("opt-b","opt-c","opt-d"):
            with self.subTest(option_id=option_id):
                glider.independently_check_paired_glider_witness(
                    witness(option_id))
        self.assertEqual(len(set(glider._FALSE_CLASSES.values())),3)

    def test_independent_rational_vector_and_energy_arithmetic(self):
        for row in glider._models():
            mass,speed=Fraction(row["massEach"]),Fraction(row["speedMagnitudeEach"])
            self.assertGreater(mass,0)
            self.assertGreater(speed,0)
            self.assertEqual(Fraction(row["momentumForward"]),mass*speed)
            self.assertEqual(Fraction(row["momentumBackward"]),-mass*speed)
            self.assertEqual(Fraction(row["systemVectorMomentum"]),0)
            self.assertEqual(Fraction(row["systemScalarKineticEnergy"]),
                             mass*speed*speed)
            self.assertGreater(Fraction(row["kineticEnergyPerGlider"]),0)

    def test_rehashed_false_vector_model_still_fails(self):
        row=witness("opt-b")
        row["exactRationalSystemModels"][0]["systemVectorMomentum"]="10"
        row["witnessSha256"]=glider._digest({
            k:v for k,v in row.items() if k!="witnessSha256"})
        with self.assertRaisesRegex(ValueError,"RATIONAL_GLIDER"):
            glider.independently_check_paired_glider_witness(row)

    def test_rehashed_false_energy_model_still_fails(self):
        row=witness("opt-c")
        row["exactRationalSystemModels"][0]["systemScalarKineticEnergy"]="0"
        row["witnessSha256"]=glider._digest({
            k:v for k,v in row.items() if k!="witnessSha256"})
        with self.assertRaisesRegex(ValueError,"RATIONAL_GLIDER"):
            glider.independently_check_paired_glider_witness(row)

    def test_forged_source_cannot_be_claimed(self):
        for field,val in (
            ("sourceSha256","0"*64),
            ("candidateSha256","f"*64),
            ("academicTaskAccepted",True),
            ("publicationAuthorized",True),
            ("newProviderCalls",2),
            ("completeAcademicProofGatesStillOpen",89),
        ):
            row=witness("opt-d")
            row[field]=val
            with self.subTest(field=field),self.assertRaises(ValueError):
                glider.independently_check_paired_glider_witness(row)

    def test_english_malay_chinese_exact_sentence_negations_fail_closed(self):
        from app_generator.validation.section91_first_distractor_proof import (
            _parse_complete,
        )
        for option,translations in glider._OPTIONS.items():
            for lang,text in translations.items():
                _parse_complete(text,(text,),"BSA278_FINITE_LANG_"+lang)
                with self.subTest(option=option,lang=lang):
                    with self.assertRaises(ValueError):
                        _parse_complete(text+" unreviewed",
                                        (text,),"BSA278_FINITE_LANG_"+lang)
                    with self.assertRaises(ValueError):
                        _parse_complete(text[:-1],(text,),
                                        "BSA278_FINITE_LANG_"+lang)

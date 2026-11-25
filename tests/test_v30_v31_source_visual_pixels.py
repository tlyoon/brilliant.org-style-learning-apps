"""BSA258-259: screenshot pixel faults, source-MCQ polarity and automatic V29-31."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import check_v30_private_browser_velocity_pixels as screen
from app_generator.validation import section91_bounded_semantic_witness as semantic
from app_generator.runtime import v3_post_v29_real_browser_pixels as v30
from app_generator.runtime import v3_post_v30_bounded_mcq_semantics as v31
from app_generator.runtime import v3_auto_development_handoff as advance

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/"content"/"chapter-9"/"section-9-1"/"package.json"


def good_samples():
    return {"width":640,"height":360,
            "leftArrowPatch":[[23,107,81,255]]*35,
            "rightArrowPatch":[[217,119,6,255]]*35,
            "leftBackground":[255,255,255,255],
            "rightBackground":[255,255,255,255]}


class V30V31Tests(unittest.TestCase):
    def test_actual_screenshot_pixel_verifier_positive(self):
        result=screen.verify_browser_raster_pixels(good_samples())
        self.assertEqual(result["leftRasterGreenPixels"],35)
        self.assertEqual(result["rightRasterOrangePixels"],35)
        self.assertEqual(result["screenshotWidth"],640)

    def test_wrong_direction_color_patches_are_denied(self):
        s=good_samples()
        s["leftArrowPatch"],s["rightArrowPatch"]=(
            s["rightArrowPatch"],s["leftArrowPatch"])
        with self.assertRaisesRegex(ValueError,"OPPOSING_COLORED"):
            screen.verify_browser_raster_pixels(s)

    def test_blank_or_transparent_real_screenshot_rejected(self):
        for change in ("no_green","no_orange","transparent"):
            s=good_samples()
            if change=="no_green":
                s["leftArrowPatch"]=[[255,255,255,255]]*35
            elif change=="no_orange":
                s["rightArrowPatch"]=[[255,255,255,255]]*35
            else:
                s["leftArrowPatch"]=[[23,107,81,0]]*35
            with self.subTest(change=change):
                with self.assertRaisesRegex(ValueError,"OPPOSING_COLORED"):
                    screen.verify_browser_raster_pixels(s)

    def test_wrong_actual_screenshot_size_fails(self):
        s=good_samples()
        s["width"]=800
        with self.assertRaisesRegex(ValueError,"SIZE_OR_DECODE"):
            screen.verify_browser_raster_pixels(s)

    def test_pixels_equal_background_fails(self):
        s=good_samples()
        s["leftBackground"]=[23,107,81,255]
        with self.assertRaisesRegex(ValueError,"OPPOSING_COLORED"):
            screen.verify_browser_raster_pixels(s)

    def _source_witness(self,td,mutator=None):
        pdf=Path(td)/"synthetic-isolated-unit-test.pdf"
        pdf.write_bytes(b"%PDF- unit test only")
        pkg=json.loads(ORIGINAL.read_text(encoding="utf8"))
        if mutator:
            mutator(pkg)
        candidate=Path(td)/"candidate.json"
        candidate.write_text(json.dumps(pkg,ensure_ascii=False),
                             encoding="utf8")
        with (patch.object(semantic,"_SOURCE_SHA",sha256(pdf.read_bytes()).hexdigest()),
              patch.object(semantic,"_CANDIDATE_SHA",sha256(candidate.read_bytes()).hexdigest()),
              patch.object(semantic,"extract_pages",return_value=["one","two","three"]),
              patch.object(semantic,"_source_axioms",
                           return_value={str(i):True for i in range(9)})):
            return semantic.source_bound_four_choice_witness(
                source_pdf=pdf,package_file=candidate)

    def test_four_choice_rational_truth_and_three_language_roles(self):
        with tempfile.TemporaryDirectory() as td:
            result=self._source_witness(td)
        self.assertTrue(result["correctAnswerModelUniquelyTrue"])
        self.assertEqual(result["mathematicallyCounterexampledFalseChoices"],3)
        self.assertEqual(result["independentlyCheckedOptionLocales"],12)
        self.assertEqual(result["independentlyCheckedLocalizedRoleTexts"],18)
        self.assertFalse(result["fullTranslationSemanticEquivalenceProven"])
        self.assertFalse(result["entireActivityIndependentSemanticAccepted"])

    def test_wrong_correct_answer_rejected(self):
        def mutate(pkg):
            pkg["activities"][0]["answerKey"]["correct"]="opt-b"
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"FOUR_CHOICE_KEY"):
                self._source_witness(td,mutate)

    def test_false_choice_translation_polarity_drift_rejected(self):
        def mutate(pkg):
            pkg["activities"][0]["answerKey"]["options"][1]["label"]["ms"]=(
                "Momentum linear kedua-duanya serupa dan sentiasa sama.")
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"MISMATCH_ms_opt-b"):
                self._source_witness(td,mutate)

    def test_source_grounded_explanation_meaning_negation_rejected(self):
        def mutate(pkg):
            pkg["activities"][0]["explanation"]["en"]="Momentum is unrelated to mass."
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"MISMATCH_en_explanation"):
                self._source_witness(td,mutate)

    def test_v30_mandates_real_signed_v29(self):
        with tempfile.TemporaryDirectory() as td:
            bad={"status":"FORGED","integritySha256":"a"*64}
            ready={"gitHead":"a"*40,"proposalSha256":"b"*64}
            with (patch.object(v30,"_preflight",
                               return_value=(Path(td),None,None,None,None)),
                  patch.object(v30,"_signed",return_value=bad)):
                with self.assertRaisesRegex(ValueError,"SIGNED_EXACT_SOURCE_V29"):
                    v30.run_post_v29_real_browser_pixels(
                        ROOT,Path(td),ready,{},{},{},bad)

    def test_v31_mandates_real_signed_v30(self):
        with tempfile.TemporaryDirectory() as td:
            bad={"status":"FORGED","integritySha256":"a"*64}
            ready={"gitHead":"a"*40,"proposalSha256":"b"*64}
            with (patch.object(v31,"_preflight",
                               return_value=(Path(td),None,None,None,None)),
                  patch.object(v31,"_signed",return_value=bad)):
                with self.assertRaisesRegex(ValueError,"SIGNED_GENUINE_BROWSER_V30"):
                    v31.run_post_v30_independent_mcq_semantics(
                        ROOT,Path(td),ready,{},{},{},bad)

    def test_same_worker_executes_three_successors_without_handoff(self):
        prior={
            "status":advance._STATUS28,"newProviderCalls":0,
            "publicationAuthorized":False,"formalAcademicPASS":0,
            "completeAcademicProofGatesStillOpen":90,
        }
        calls=[]
        def runner(expected):
            def f(*args):
                calls.append(expected)
                return {
                    "status":expected,"publicationAuthorized":False,
                    "fullAcademicPASS":0,
                    "completeAcademicProofGatesStillOpen":90,
                    "newModelCalls":0,
                }
            return f
        handlers={
            advance._STATUS28:(advance._STATUS29,"privateSourceVisualPilot",
                               runner(advance._STATUS29)),
            advance._STATUS29:(advance._STATUS30,"privateBrowserPixelPilot",
                               runner(advance._STATUS30)),
            advance._STATUS30:(advance._STATUS31,"privateMcqSemanticsPilot",
                               runner(advance._STATUS31)),
        }
        with patch.dict(advance._TRANSITIONS,handlers,clear=True):
            output=advance.advance_eligible_verified_development_stages(
                repo=ROOT,private=ROOT,ready={},v9={},v11={},v12={},
                prior_stage=prior)
        self.assertEqual(calls,[advance._STATUS29,advance._STATUS30,
                                advance._STATUS31])
        self.assertEqual(output["stagesExecutedThisRun"],3)
        self.assertEqual(output["privateMcqSemanticsPilot"]["status"],
                         advance._STATUS31)
        self.assertEqual(output["academicPASS"],0)
        self.assertFalse(output["publicationAuthorized"])

    def test_new_stage_must_not_forge_academic_pass(self):
        prior={"status":advance._STATUS28,"newProviderCalls":0,
               "publicationAuthorized":False,"formalAcademicPASS":0,
               "completeAcademicProofGatesStillOpen":90}
        def forged(*args):
            return {"status":advance._STATUS29,
                    "fullAcademicPASS":1,"publicationAuthorized":False,
                    "completeAcademicProofGatesStillOpen":90,
                    "newModelCalls":0}
        with patch.dict(advance._TRANSITIONS,{
                advance._STATUS28:(advance._STATUS29,"bad",forged)},clear=True):
            with self.assertRaisesRegex(ValueError,"NOT_REALLY_ACCEPTED"):
                advance.advance_eligible_verified_development_stages(
                    repo=ROOT,private=ROOT,ready={},v9={},v11={},v12={},
                    prior_stage=prior)

    def test_worker_requires_both_new_pilots_to_exit_zero(self):
        source=(ROOT/"scripts"/"run_v3_yoga6_recovery_worker.py").read_text(
            encoding="utf8")
        self.assertIn("privateBrowserPixelPilot",source)
        self.assertIn("privateMcqSemanticsPilot",source)
        self.assertIn("stagesExecutedThisRun",source)

if __name__=="__main__":
    unittest.main()

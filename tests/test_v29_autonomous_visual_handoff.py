"""BSA257: automatic V28->V29 source-grounded visual and bounded continuation."""
from __future__ import annotations
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from app_generator.validation import section91_private_velocity_visual as scene
from app_generator.runtime import v3_post_v28_source_visual_pilot as runtime
from app_generator.runtime import v3_auto_development_handoff as advance

ROOT=Path(__file__).resolve().parents[1]


class V29AutonomousVisualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=(
            ROOT/"content/chapter-9/section-9-1/package.json"
        ).read_bytes()
        cls.package=json.loads(cls.original.decode("utf8"))

    def _mock_visual(self,td,package=None):
        """Use the real candidate with fake PDF *only* in isolated unit tests."""
        selected=deepcopy(package or self.package)
        pdf=Path(td)/"controlled.pdf"
        pdf.write_bytes(b"%PDF- fake isolated unit-only content")
        raw=Path(td)/"candidate.json"
        raw.write_bytes(json.dumps(selected,ensure_ascii=False).encode("utf8"))
        real_sha=hashlib.sha256(raw.read_bytes()).hexdigest()
        with (patch.object(scene,"_CANDIDATE_SHA",real_sha),
              patch.object(scene,"_SOURCE_SHA",
                           hashlib.sha256(pdf.read_bytes()).hexdigest()),
              patch.object(scene,"_source_axioms",
                           return_value={str(n):1 for n in range(9)}),
              patch.object(scene,"extract_pages",
                           return_value=("text","text","text")),
              patch.object(scene,"_source_activity_anchors",
                           return_value=[
                               {"activityId":a["id"],
                                "physicalPage":2,
                                "passageSha256":"a"*64,
                                "uniquePagePassageLocated":True}
                               for a in selected["activities"]])):
            return scene.make_opposite_velocity_private_visual(
                source_pdf=pdf,
                source_sha=hashlib.sha256(pdf.read_bytes()).hexdigest(),
                package_file=raw)

    def test_single_source_visual_is_an_unreleased_pedagogical_draft(self):
        with tempfile.TemporaryDirectory() as td:
            draft=self._mock_visual(td)
        self.assertEqual(draft["activityId"],"act-mcq-01-vector-nature")
        self.assertEqual(draft["originalSourcePhysicalPdfPage"],2)
        self.assertEqual(len(draft["spec"]["entities"]),2)
        self.assertEqual(
            [x["direction"] for x in draft["spec"]["vectors"]],
            ["left","right"])
        self.assertTrue(all(x["quantity"]=="velocity" for x in
                            draft["spec"]["vectors"]))
        self.assertEqual(draft["spec"]["grounding"][1]["origin"],
                         "pedagogical_simplification")
        self.assertFalse(draft["isOriginalTextbookFigure"])
        self.assertFalse(draft["isReleasedIntoOriginalPackage"])
        self.assertFalse(draft["publicationAuthorized"])
        self.assertEqual(draft["fullAcademicPASS"],0)

    def test_wrong_scenario_no_auto_diagram_substitution(self):
        changed=deepcopy(self.package)
        changed["activities"][0]["prompt"]["en"]="Same-direction objects."
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"SCENARIO_MISMATCH"):
                self._mock_visual(td,changed)

    def test_existing_visual_never_overwritten_by_draft(self):
        changed=deepcopy(self.package)
        changed["activities"][0]["visualSpec"]={"template":"unreviewed"}
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"REPLACE_EXISTING"):
                self._mock_visual(td,changed)

    def test_real_renderer_three_locales_equal_opposite_svg_vectors(self):
        with tempfile.TemporaryDirectory() as td:
            draft=self._mock_visual(td)
            receipt=Path(td)/"local-check.json"
            receipt.write_text(json.dumps(draft,ensure_ascii=False),
                               encoding="utf8")
            call=subprocess.run(
                ["node",str(ROOT/"scripts"/"verify_bosla_private_velocity_svg.js"),
                 str(receipt)],cwd=ROOT,capture_output=True,text=True,timeout=15)
            self.assertEqual(call.returncode,0,call.stderr)
            result=json.loads(call.stdout)
        self.assertTrue(result["equalOppositeArrowGeometry"])
        self.assertEqual(result["actualSvgVelocityArrowsVerified"],6)
        self.assertEqual(result["localesChecked"],3)
        self.assertFalse(result["sourceFigureExactMatchProven"])
        self.assertFalse(result["publicationAuthorized"])

    def test_domain_visual_contract_rejects_malformed_source_scene(self):
        from app_generator.domains.registry import resolve_domain
        domain=resolve_domain(ROOT)
        validator=domain.load_module("validation","visualValidatorModule")
        with tempfile.TemporaryDirectory() as td:
            spec=self._mock_visual(td)["spec"]
        self.assertEqual(validator.visual_spec_errors(spec,"visualSpec"),[])
        for change in ("wrong_direction","wrong_mass","unequal_speed",
                       "missing_arrow","revealed_momentum"):
            wrong=deepcopy(spec)
            if change=="wrong_direction":
                wrong["vectors"][0]["direction"]="right"
            elif change=="wrong_mass":
                wrong["entities"][1]["properties"]["relativeMass"]="different"
            elif change=="unequal_speed":
                wrong["vectors"][1]["relativeMagnitude"]=0.2
            elif change=="missing_arrow":
                wrong["vectors"].pop()
            else:
                wrong["vectors"][1]["quantity"]="momentum"
            with self.subTest(change=change):
                self.assertTrue(validator.visual_spec_errors(wrong,"visualSpec"))

    def test_wrong_geometry_refuses_forged_vectors(self):
        with tempfile.TemporaryDirectory() as td:
            draft=self._mock_visual(td)
            draft["spec"]["vectors"][1]["direction"]="left"
            receipt=Path(td)/"forged.json"
            receipt.write_text(json.dumps(draft,ensure_ascii=False),
                               encoding="utf8")
            call=subprocess.run(
                ["node",str(ROOT/"scripts"/"verify_bosla_private_velocity_svg.js"),
                 str(receipt)],cwd=ROOT,capture_output=True,text=True,timeout=15)
            self.assertNotEqual(call.returncode,0)

    def test_signed_v28_predecessor_is_mandatory(self):
        with tempfile.TemporaryDirectory() as td:
            fake={"status":"FORGED","integritySha256":"a"*64}
            ready={"gitHead":"a"*40,"proposalSha256":"b"*64}
            with (patch.object(runtime,"_preflight",
                               return_value=(Path(td),None,None,None,None)),
                  patch.object(runtime,"_signed",return_value=fake),
                  patch.object(runtime,"_trusted_json",
                               side_effect=AssertionError("NO_SOURCE_OPEN"))):
                with self.assertRaisesRegex(ValueError,"SIGNED_V28"):
                    runtime.run_post_v28_private_visual_pilot(
                        ROOT,Path(td),ready,{},{},{},fake)

    def _good_prior(self):
        return {
            "status":advance._STATUS28,
            "newProviderCalls":0,"publicationAuthorized":False,
            "formalAcademicPASS":0,
            "completeAcademicProofGatesStillOpen":90,
        }

    def _good_next(self):
        return {
            "status":advance._STATUS29,
            "publicationAuthorized":False,"fullAcademicPASS":0,
            "completeAcademicProofGatesStillOpen":90,
            "newModelCalls":0,"nextEligibleMilestone":
                "PRIVATE_ACTUAL_BROWSER_SCREENSHOTS_AND_DOMAIN_SCIENCE_PIXELS",
        }

    def test_next_safe_stage_is_dispatched_in_normal_run_without_prompt(self):
        with patch.object(advance,"run_post_v28_private_visual_pilot") as fn:
            # The registered callback was captured at registry construction.
            transition=(advance._STATUS29,"privateSourceVisualPilot",fn)
            with patch.dict(advance._TRANSITIONS,
                            {advance._STATUS28:transition},clear=True):
                fn.return_value=self._good_next()
                result=advance.advance_eligible_verified_development_stages(
                    repo=ROOT,private=ROOT,ready={},
                    v9={},v11={},v12={},prior_stage=self._good_prior())
        self.assertEqual(fn.call_count,1)
        self.assertEqual(result["stagesExecutedThisRun"],1)
        self.assertEqual(result["privateSourceVisualPilot"]["status"],
                         advance._STATUS29)
        self.assertFalse(result["publicationAuthorized"])

    def test_completed_stage_does_not_invent_model_or_academic_pass(self):
        with patch.object(advance,"run_post_v28_private_visual_pilot") as fn:
            transition=(advance._STATUS29,"privateSourceVisualPilot",fn)
            with patch.dict(advance._TRANSITIONS,
                            {advance._STATUS28:transition},clear=True):
                fn.return_value={**self._good_next(),"fullAcademicPASS":1}
                with self.assertRaisesRegex(ValueError,"NOT_REALLY_ACCEPTED"):
                    advance.advance_eligible_verified_development_stages(
                        repo=ROOT,private=ROOT,ready={},
                        v9={},v11={},v12={},prior_stage=self._good_prior())

    def test_no_repeat_cycle_or_unbounded_model_retry(self):
        with patch.object(advance,"run_post_v28_private_visual_pilot") as fn:
            fn.return_value=self._good_next()
            with patch.dict(advance._TRANSITIONS,{
                advance._STATUS28:(advance._STATUS29,"draft",fn),
                advance._STATUS29:(advance._STATUS28,"cycle",fn)},clear=True):
                with self.assertRaisesRegex(ValueError,"CYCLE"):
                    advance.advance_eligible_verified_development_stages(
                        repo=ROOT,private=ROOT,ready={},
                        v9={},v11={},v12={},prior_stage=self._good_prior())

    def test_normal_worker_executes_handoff_not_only_v28(self):
        source=(ROOT/"scripts"/"run_v3_yoga6_recovery_worker.py"
                ).read_text(encoding="utf8")
        self.assertIn("advance_eligible_verified_development_stages(",source)
        self.assertIn('result["autonomousDevelopmentContinuation"]',source)
        self.assertIn(advance._STATUS29,source)


if __name__=="__main__":
    unittest.main()

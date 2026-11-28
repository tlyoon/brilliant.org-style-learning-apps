"""BSA268: source-free engineering SUCCESS must never masquerade as academic progress.

The old V1–V36 stages are real engineering milestones, but their 429 source
semantic obligations and 90 five-gate academic acceptances are not completed.
Tests prevent repeating more proof-inventory milestones while preserving
independent fail-isolated recovery lanes and safety.
"""
from __future__ import annotations
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from app_generator.runtime import v3_auto_development_handoff as chain

ROOT=Path(__file__).resolve().parents[1]

def prior():
    return {
        "status":chain._STATUS28,
        "newProviderCalls":0,
        "publicationAuthorized":False,
        "formalAcademicPASS":0,
        "completeAcademicProofGatesStillOpen":90,
    }

def terminal(**updates):
    return {
        "status":chain._STATUS36,
        "publicationAuthorized":False,
        "fullAcademicPASS":0,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicProofTasksAccepted":0,
        "fullAcademicProofTasksStillOpen":429,
        "newModelCalls":0,
        **updates,
    }

def dispatch(transitions,isolated=False):
    with patch.dict(chain._TRANSITIONS,transitions,clear=True):
        if isolated:
            with patch.object(chain,"run_safe_isolated_development_lanes",
                              return_value={"status":"INDEPENDENT_SAFE_LANES_ALL_VERIFIED"}):
                return chain.advance_eligible_verified_development_stages(
                    repo=ROOT,private=ROOT,ready={},v9={},v11={},v12={},
                    prior_stage=prior(),run_independent_lanes=True)
        return chain.advance_eligible_verified_development_stages(
            repo=ROOT,private=ROOT,ready={},v9={},v11={},v12={},
            prior_stage=prior(),run_independent_lanes=False)

class NoDefectiveAcademicCycles(TestCase):
    def test_successful_engineering_handoff_explicitly_reports_no_academic_proof(self):
        out=dispatch({chain._STATUS28:(
            chain._STATUS36,"v36",lambda *args:terminal())})
        self.assertEqual(out["stagesExecutedThisRun"],1)
        self.assertEqual(out["developmentOutcomeClass"],
                         "ENGINEERING_VERIFIED_NOT_ACADEMIC_ACCEPTANCE")
        self.assertEqual(out["academicProofTasksAcceptedThisRun"],0)
        self.assertFalse(out["academicAcceptanceAdvanced"])
        self.assertTrue(out["academicProofProducerRequired"])
        self.assertTrue(out["engineeringOnlyFrontierTerminal"])

    def test_eighth_zero_proof_scaffolding_stage_is_rejected(self):
        transitions={
            chain._STATUS28:(chain._STATUS36,"v36",lambda *a:terminal()),
            chain._STATUS36:("STILL_NO_PROOF","v37",lambda *a:{
                **terminal(),"status":"STILL_NO_PROOF"
            }),
        }
        with self.assertRaisesRegex(ValueError,
                "BSA268_ZERO_PROOF_SCAFFOLDING_CYCLE_FORBIDDEN"):
            dispatch(transitions)

    def test_forged_academic_progress_in_source_free_lane_is_rejected(self):
        with self.assertRaisesRegex(ValueError,
                "BSA268_SOURCE_FREE_CANNOT_CLAIM_ACADEMIC_PROOF"):
            dispatch({chain._STATUS28:(
                chain._STATUS36,"v36",lambda *a:terminal(
                    fullAcademicProofTasksAccepted=1,
                    fullAcademicProofTasksStillOpen=428))})

    def test_forged_complete_acceptance_gate_is_rejected(self):
        with self.assertRaisesRegex(ValueError,
                "BSA257_SUCCESSOR_STAGE_NOT_REALLY_ACCEPTED"):
            dispatch({chain._STATUS28:(
                chain._STATUS36,"v36",lambda *a:terminal(
                    completeAcademicProofGatesStillOpen=89))})

    def test_independent_source_free_recovery_lanes_remain_available(self):
        out=dispatch({chain._STATUS28:(
            chain._STATUS36,"v36",lambda *a:terminal())},isolated=True)
        self.assertEqual(
            out["isolatedDevelopmentLanes"]["status"],
            "INDEPENDENT_SAFE_LANES_ALL_VERIFIED")
        self.assertFalse(out["academicAcceptanceAdvanced"])
        self.assertEqual(out["academicProofTasksAcceptedThisRun"],0)

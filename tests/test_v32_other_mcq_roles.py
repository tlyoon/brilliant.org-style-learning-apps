"""BSA260: complete nine-MCQ bounded role inventory and V31->V32 auto run."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.validation import section91_other_mcq_locale_roles as roles
from app_generator.runtime import v3_post_v31_other_mcq_locale_roles as v32
from app_generator.runtime import v3_auto_development_handoff as advance

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/"content"/"chapter-9"/"section-9-1"/"package.json"


class V32Tests(unittest.TestCase):
    def _synthetic_in_memory(self,td,mutate=None):
        source=Path(td)/"isolated-physics-source.pdf"
        source.write_bytes(b"%PDF V32 isolated tests, not real source")
        candidate=Path(td)/"candidate.json"
        raw=json.loads(PACKAGE.read_text(encoding="utf8"))
        if mutate:
            mutate(raw)
        candidate.write_text(json.dumps(raw,ensure_ascii=False),encoding="utf8")
        with (patch.object(roles,"_SOURCE_SHA",sha256(source.read_bytes()).hexdigest()),
              patch.object(roles,"_CANDIDATE_SHA",sha256(candidate.read_bytes()).hexdigest()),
              patch.object(roles,"_source_axioms",return_value={
                    "axiom "+str(i):1 for i in range(9)}),
              patch.object(roles,"extract_pages",return_value=["a","b","c"])):
            return roles.bound_all_other_mcq_locale_option_roles(
                source_pdf=source,package_file=candidate)

    def test_all_other_eight_real_mcq_source_lexical_roles(self):
        with tempfile.TemporaryDirectory() as td:
            data=self._synthetic_in_memory(td)
        self.assertEqual(data["otherMcqActivitiesChecked"],8)
        self.assertEqual(data["otherMcqLocalizedOptionRolesChecked"],96)
        self.assertEqual(data["otherMcqPromptExplanationRoleChecks"],48)
        self.assertEqual(data["otherMcqFormalTrueChoiceWitnesses"],8)
        self.assertEqual(data["otherMcqFormalFalseChoiceCounterexamples"],24)
        self.assertEqual(len(data["sourceBoundActivityWitnesses"]),8)
        self.assertFalse(data["fullTrilingualMeaningEquivalenceProven"])
        self.assertEqual(data["fullAcademicPASS"],0)
        self.assertFalse(data["publicationAuthorized"])

    def test_wrong_unproven_malay_option_polarity_is_denied(self):
        def mutate(data):
            data["activities"][1]["answerKey"]["options"][1]["label"]["ms"]=(
                "Momentum ditentukan sepenuhnya oleh arah gerakan sahaja.")
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"MISSING_act-mcq-02-si-units_ms_opt-b"):
                self._synthetic_in_memory(td,mutate)

    def test_wrong_chinese_directionality_role_rejected(self):
        def mutate(data):
            data["activities"][5]["answerKey"]["options"][0]["label"]["zh"]=(
                "货车与轿车具有完全相同的运动动量方向。")
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"MISSING_act-mcq-06-equal-speed-comparison_zh_opt-a"):
                self._synthetic_in_memory(td,mutate)

    def test_wrong_momentum_key_never_inherits_formal_model(self):
        def mutate(data):
            data["activities"][6]["answerKey"]["correct"]="opt-scout-greater"
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"WRONG_FORMAL_ANSWER"):
                self._synthetic_in_memory(td,mutate)

    def test_wrong_explanation_cue_fails_closed(self):
        def mutate(data):
            data["activities"][7]["explanation"]["en"]="Independent unsupported claim."
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"PROMPT_OR_REASONING"):
                self._synthetic_in_memory(td,mutate)

    def test_original_pdf_and_candidate_exact_hash_mandatory(self):
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/"pdf"
            source.write_bytes(b"fake")
            candidate=Path(td)/"candidate"
            candidate.write_text("{}",encoding="utf8")
            with self.assertRaisesRegex(ValueError,"DRIFT"):
                roles.bound_all_other_mcq_locale_option_roles(
                    source_pdf=source,package_file=candidate)

    def test_signed_v31_predecessor_is_required(self):
        with tempfile.TemporaryDirectory() as td:
            ready={"gitHead":"a"*40,"proposalSha256":"b"*64}
            bad={"status":"FORGED","integritySha256":"a"*64}
            with (patch.object(v32,"_preflight",
                               return_value=(Path(td),None,None,None,None)),
                  patch.object(v32,"_signed",return_value=bad)):
                with self.assertRaisesRegex(ValueError,"GENUINE_SIGNED_FIRST_MCQ"):
                    v32.run_post_v31_other_eight_mcq_localized_proofs(
                        ROOT,Path(td),ready,{},{},{},bad)

    def test_normal_worker_automatically_advances_all_four_stages(self):
        prior={"status":advance._STATUS28,"newProviderCalls":0,
               "publicationAuthorized":False,"formalAcademicPASS":0,
               "completeAcademicProofGatesStillOpen":90}
        calls=[]
        def successor(status):
            def execute(*args):
                calls.append(status)
                return {"status":status,"newModelCalls":0,"fullAcademicPASS":0,
                        "publicationAuthorized":False,
                        "completeAcademicProofGatesStillOpen":90}
            return execute
        transitions={
            advance._STATUS28:(advance._STATUS29,"privateSourceVisualPilot",
                               successor(advance._STATUS29)),
            advance._STATUS29:(advance._STATUS30,"privateBrowserPixelPilot",
                               successor(advance._STATUS30)),
            advance._STATUS30:(advance._STATUS31,"privateMcqSemanticsPilot",
                               successor(advance._STATUS31)),
            advance._STATUS31:(advance._STATUS32,"privateOtherMcqWitnessPilot",
                               successor(advance._STATUS32)),
        }
        with patch.dict(advance._TRANSITIONS,transitions,clear=True):
            output=advance.advance_eligible_verified_development_stages(
                repo=ROOT,private=ROOT,ready={},v9={},v11={},v12={},
                prior_stage=prior)
        self.assertEqual(calls,[advance._STATUS29,advance._STATUS30,
                                advance._STATUS31,advance._STATUS32])
        self.assertEqual(output["stagesExecutedThisRun"],4)
        self.assertEqual(output["privateOtherMcqWitnessPilot"]["status"],
                         advance._STATUS32)
        self.assertEqual(output["academicPASS"],0)
        self.assertFalse(output["publicationAuthorized"])

    def test_normal_worker_must_not_skip_v32_for_exit_zero(self):
        source=(ROOT/"scripts"/"run_v3_yoga6_recovery_worker.py").read_text(encoding="utf8")
        self.assertIn("privateOtherMcqWitnessPilot",source)
        self.assertIn("allNineMcqLocalizedOptionRolesChecked",source)
        self.assertIn("allNineMcqFormalFalseAlternativeCounterexamples",source)

    def test_invalid_new_model_call_in_v32_fails(self):
        prior={"status":advance._STATUS28,"newProviderCalls":0,
               "publicationAuthorized":False,"formalAcademicPASS":0,
               "completeAcademicProofGatesStillOpen":90}
        def forged(*args):
            return {"status":advance._STATUS29,
                    "newModelCalls":1,"fullAcademicPASS":0,
                    "publicationAuthorized":False,
                    "completeAcademicProofGatesStillOpen":90}
        with patch.dict(advance._TRANSITIONS,{
                advance._STATUS28:(advance._STATUS29,"blocked",forged)},
                clear=True):
            with self.assertRaisesRegex(ValueError,"NOT_REALLY_ACCEPTED"):
                advance.advance_eligible_verified_development_stages(
                    repo=ROOT,private=ROOT,ready={},v9={},v11={},v12={},
                    prior_stage=prior)

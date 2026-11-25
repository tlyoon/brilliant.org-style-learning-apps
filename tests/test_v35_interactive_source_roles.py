"""BSA263: genuine pinned-candidate role checks and fail-closed successor tests."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app_generator.validation import section91_interactive_source_roles as roles
from app_generator.runtime import v3_post_v34_interactive_source_roles as v35
from app_generator.runtime import v3_auto_development_handoff as chain

ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT/"content"/"chapter-9"/"section-9-1"/"package.json"

class V35Tests(TestCase):
    def synthetic(self,mutate=None):
        with TemporaryDirectory() as td:
            source=Path(td)/"synthetic.pdf"
            source.write_bytes(b"local fake source strictly for isolated negative tests")
            cand=Path(td)/"candidate.json"
            pkg=json.loads(PKG.read_text(encoding="utf8"))
            if mutate:
                mutate(pkg)
            cand.write_text(json.dumps(pkg,ensure_ascii=False),encoding="utf8")
            with (patch.object(roles,"_SOURCE_SHA",sha256(source.read_bytes()).hexdigest()),
                  patch.object(roles,"_CANDIDATE_SHA",sha256(cand.read_bytes()).hexdigest()),
                  patch.object(roles,"_source_axioms",return_value={
                      "axiom "+str(i):1 for i in range(9)})):
                return roles.audit_interactive_source_role_cues(
                    source_pdf=source,package_file=cand)

    def test_all_nine_27_language_prompt_and_item_role_witnesses(self):
        a=self.synthetic()
        self.assertEqual(a["interactiveActivitiesChecked"],9)
        self.assertEqual(a["trilingualPromptRoleCuesChecked"],27)
        self.assertEqual(a["trilingualFirstItemRoleCuesChecked"],27)
        self.assertEqual(a["localizedExplanationsBoundByDigest"],27)
        self.assertEqual(len(a["activityWitnesses"]),9)
        self.assertFalse(a["fullTrilingualMeaningEquivalenceProven"])
        self.assertEqual(a["fullAcademicPASS"],0)

    def test_malay_wrong_vector_to_scalar_prompt_is_blocked(self):
        def flip(x):
            x["activities"][9]["prompt"]["ms"]="Kelaskan semua kuantiti sebagai skalar sahaja."
        with self.assertRaisesRegex(ValueError,"PROMPT_SCIENCE_ROLE_DRIFT"):
            self.synthetic(flip)

    def test_chinese_wrong_direction_label_is_blocked(self):
        def flip(x):
            x["activities"][12]["interaction"]["items"][0]["label"]["zh"]="没有方向的标量"
        with self.assertRaisesRegex(ValueError,"ITEM_SCIENCE_ROLE_DRIFT"):
            self.synthetic(flip)

    def test_correct_looking_role_does_not_override_wrong_answer_key(self):
        def flip(x):
            x["activities"][13]["interaction"]["correctOrder"].reverse()
        with self.assertRaisesRegex(ValueError,"ANSWER_KEY_DEFECT"):
            self.synthetic(flip)

    def test_changed_source_or_candidate_never_accepted(self):
        with TemporaryDirectory() as td:
            source=Path(td)/"wrong.pdf";source.write_bytes(b"wrong")
            cand=Path(td)/"wrong.json";cand.write_text("{}")
            with self.assertRaisesRegex(ValueError,"SINGLE_SOURCE"):
                roles.audit_interactive_source_role_cues(
                    source_pdf=source,package_file=cand)

    def test_v35_requires_signed_exact_v34_predecessor(self):
        with TemporaryDirectory() as td:
            bad={"status":"FORGED"}
            ready={"gitHead":"a"*40,"proposalSha256":"b"*64}
            with (patch.object(v35,"_preflight",return_value=(
                    Path(td),None,None,None,None)),
                  patch.object(v35,"_signed",return_value=bad)):
                with self.assertRaisesRegex(ValueError,"SIGNED_V34"):
                    v35.run_post_v34_interactive_source_roles(
                        ROOT,Path(td),ready,{},{},{},bad)

    def test_worker_automatically_advances_all_six_stages(self):
        prior={"status":chain._STATUS28,"newProviderCalls":0,
               "publicationAuthorized":False,"formalAcademicPASS":0,
               "completeAcademicProofGatesStillOpen":90}
        states=[chain._STATUS29,chain._STATUS30,chain._STATUS31,
                chain._STATUS32,chain._STATUS34,chain._STATUS35]
        transitions={}
        curr=chain._STATUS28
        for index,state in enumerate(states):
            def handler(*args, s=state):
                return {"status":s,"newModelCalls":0,"fullAcademicPASS":0,
                        "completeAcademicProofGatesStillOpen":90,
                        "publicationAuthorized":False}
            transitions[curr]=(state,"stage"+str(index),handler)
            curr=state
        with patch.dict(chain._TRANSITIONS,transitions,clear=True):
            result=chain.advance_eligible_verified_development_stages(
                repo=ROOT,private=ROOT,ready={},v9={},v11={},v12={},
                prior_stage=prior)
        self.assertEqual(result["stagesExecutedThisRun"],6)
        self.assertEqual(result["academicPASS"],0)

    def test_real_normal_worker_requires_v35_for_exit_zero(self):
        script=(ROOT/"scripts"/"run_v3_yoga6_recovery_worker.py").read_text(encoding="utf8")
        self.assertIn("privateInteractiveSourceRolesPilot",script)
        self.assertIn("trilingualPromptRoleCuesChecked",script)
        self.assertIn("trilingualFirstItemRoleCuesChecked",script)

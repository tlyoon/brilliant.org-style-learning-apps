"""BSA262: real content structure, deliberately wrong interactive answers, and fail-closed V34."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.validation import section91_interactive_mutation_witness as checks
from app_generator.runtime import v3_post_v32_interactive_mutation_proofs as v34
from app_generator.runtime import v3_auto_development_handoff as advance

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/"content"/"chapter-9"/"section-9-1"/"package.json"

class V34InteractiveTests(unittest.TestCase):
    def source_bound_synthetic(self, mutate=None):
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/"isolated-source.pdf"
            source.write_bytes(b"%PDF-1.4 synthetic proof source for negative tests")
            candidate=Path(td)/"candidate.json"
            raw=json.loads(PACKAGE.read_text(encoding="utf8"))
            if mutate:
                mutate(raw)
            candidate.write_text(json.dumps(raw,ensure_ascii=False),encoding="utf8")
            with (patch.object(checks,"_SOURCE_SHA",sha256(source.read_bytes()).hexdigest()),
                  patch.object(checks,"_CANDIDATE_SHA",sha256(candidate.read_bytes()).hexdigest()),
                  patch.object(checks,"_source_axioms",return_value={
                    "axiom"+str(i):1 for i in range(9)})):
                return checks.audit_nine_interactive_mutants(
                    source_pdf=source,package_file=candidate)

    def test_real_section91_nine_interactive_answer_mutations_rejected(self):
        proof=self.source_bound_synthetic()
        self.assertEqual(proof["interactiveActivitiesChecked"],9)
        self.assertEqual(proof["independentlyRejectedWrongAnswerMutants"],9)
        self.assertEqual(proof["localizedPromptExplanationFieldsPresent"],54)
        self.assertGreaterEqual(proof["localizedItemLabelsPresent"],27)
        self.assertFalse(proof["fullTrilingualMeaningEquivalenceProven"])
        self.assertEqual(proof["fullAcademicPASS"],0)
        self.assertFalse(proof["publicationAuthorized"])

    def test_missing_chinese_item_is_denied(self):
        def break_item(raw):
            raw["activities"][9]["interaction"]["items"][0]["label"]["zh"]=""
        with self.assertRaisesRegex(ValueError,"MISSING_LOCALIZED_INTERACTIVE_ITEM"):
            self.source_bound_synthetic(break_item)

    def test_wrong_interactive_key_is_denied(self):
        def break_key(raw):
            raw["activities"][13]["interaction"]["correctOrder"].reverse()
        with self.assertRaisesRegex(ValueError,"ANSWER_KEY_DEFECT"):
            self.source_bound_synthetic(break_key)

    def test_changed_pdf_is_denied(self):
        with tempfile.TemporaryDirectory() as td:
            s=Path(td)/"s.pdf"; s.write_bytes(b"not the original")
            c=Path(td)/"c.json"; c.write_text("{}")
            with self.assertRaisesRegex(ValueError,"SOURCE_OR_CANDIDATE_CHANGED"):
                checks.audit_nine_interactive_mutants(source_pdf=s,package_file=c)

    def test_v34_must_have_signed_v32(self):
        with tempfile.TemporaryDirectory() as td:
            ready={"gitHead":"a"*40,"proposalSha256":"b"*64}
            bad={"status":"FORGED","integritySha256":"c"*64}
            with (patch.object(v34,"_preflight",return_value=(
                    Path(td),None,None,None,None)),
                  patch.object(v34,"_signed",return_value=bad)):
                with self.assertRaisesRegex(ValueError,"SIGNED_V32"):
                    v34.run_post_v32_interactive_mutation_proofs(
                        ROOT,Path(td),ready,{},{},{},bad)

    def test_normal_worker_auto_advances_five_stages(self):
        prior={"status":advance._STATUS28,"newProviderCalls":0,
               "publicationAuthorized":False,"formalAcademicPASS":0,
               "completeAcademicProofGatesStillOpen":90}
        status_sequence=[advance._STATUS29,advance._STATUS30,
                         advance._STATUS31,advance._STATUS32,advance._STATUS34]
        calls=[]
        def handler(status):
            def run(*args):
                calls.append(status)
                return {"status":status,"newModelCalls":0,"fullAcademicPASS":0,
                        "publicationAuthorized":False,
                        "completeAcademicProofGatesStillOpen":90}
            return run
        transitions={}
        previous=advance._STATUS28
        for index,status in enumerate(status_sequence):
            transitions[previous]=(status,"stage"+str(index),handler(status))
            previous=status
        with patch.dict(advance._TRANSITIONS,transitions,clear=True):
            result=advance.advance_eligible_verified_development_stages(
                repo=ROOT,private=ROOT,ready={},v9={},v11={},v12={},
                prior_stage=prior)
        self.assertEqual(calls,status_sequence)
        self.assertEqual(result["stagesExecutedThisRun"],5)
        self.assertEqual(result["academicPASS"],0)

    def test_worker_exit_gate_requires_real_v34(self):
        content=(ROOT/"scripts"/"run_v3_yoga6_recovery_worker.py").read_text(encoding="utf8")
        self.assertIn("privateInteractiveMutationPilot",content)
        self.assertIn("independentlyRejectedWrongAnswerMutants",content)
        self.assertIn("stagesExecutedThisRun\")>=5",content)

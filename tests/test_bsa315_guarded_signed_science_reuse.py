"""BSA315: adversarial evidence reuse, restart and speed regression.

Only mocked verifiers in these tests; no mocked result is a true Serway PASS.
Production will still require exact owner CI and original-source readback.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter, sleep
from unittest import TestCase
from unittest.mock import patch

from app_generator.runtime import v3_guarded_signed_science_reuse as cache

_HEAD_A="a"*40
_HEAD_B="b"*40
_PROPOSAL="c"*64


class ImmutableSignedScienceReuse(TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.private=Path(self.temp.name)
        self.source=self.private/"original.pdf"
        self.source.write_bytes(b"%PDF-FAKE-CONTRACT-SOURCE")
        self.text=b'{"activities":[{"id":"frozen"}]}'
        self.latest={"gitHead":_HEAD_A,"proposalSha256":_PROPOSAL}
        self.create_candidate(_HEAD_A)
        (self.private/"long-horizon-development").mkdir()
        (self.private/"long-horizon-development"/"ACADEMIC_FRONTIER.json").write_text(
            '{"identity":"a"}',encoding="utf8")
        (self.private/"bosla-selected-textbook-source-binding.json").write_text(
            '{"sourcePdf":"original.pdf"}',encoding="utf8")
        self.patches=[
            patch.object(cache,"read_long_horizon_development",side_effect=lambda private:self.latest),
            patch.object(cache,"_trusted_json",return_value={"sourcePdf":str(self.source)}),
            patch.object(cache,"_SOURCE_SHA",sha256(self.source.read_bytes()).hexdigest()),
            patch.object(cache,"_CANDIDATE_SHA",sha256(self.text).hexdigest()),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)
        self.calls=0

        def actual(*,private:Path):
            self.calls+=1
            if (sha256(self.source.read_bytes()).hexdigest()!=cache._SOURCE_SHA
                or not (private/"long-horizon-development"/"ACADEMIC_FRONTIER.json").exists()):
                raise ValueError("BSA315_FAKE_VERIFIER_REJECTS_CHANGED_SOURCE")
            return {"status":"ORIGINAL_SOURCE_GENUINELY_REVERIFIED",
                    "currentGitHead":self.latest["gitHead"],
                    "independentlyAcceptedAcademicTasks":28,
                    "fullAcademicTasksStillOpen":401,
                    "acceptedAcademicTaskIds":["x"*64]*28,
                    "newProviderCalls":0,"publicationAuthorized":False}
        self.verified=cache.verified_stage_reuse(actual)

    def create_candidate(self,head):
        folder=self.private/"owner-five-stage-completion"/head/_PROPOSAL
        folder.mkdir(parents=True)
        (folder/cache._CANDIDATE).write_bytes(self.text)
        (folder/"V36_PARTITION_01.json").write_text(
            '{"surfaceSha256":"old"}',encoding="utf8")

    def test_reuses_only_exact_unchanged_signed_evidence(self):
        with cache.verification_session(private=self.private) as session:
            first=self.verified(private=self.private)
            second=self.verified(private=self.private)
            self.assertEqual(self.calls,1)
            self.assertEqual(session["hits"],1)
            self.assertEqual(first,second)
            second["acceptedAcademicTaskIds"].clear()
            again=self.verified(private=self.private)
            self.assertEqual(len(again["acceptedAcademicTaskIds"]),28)
            self.assertEqual(self.calls,1)
            # Mutating signed evidence with the SAME number of bytes and
            # restoring mtime cannot trick a real content-hash comparison.
            receipt=self.private/"long-horizon-development"/"ACADEMIC_FRONTIER.json"
            before=receipt.stat()
            receipt.write_text('{"identity":"b"}',encoding="utf8")
            import os
            os.utime(receipt,ns=(before.st_atime_ns,before.st_mtime_ns))
            self.verified(private=self.private)
            self.assertEqual(self.calls,2)
            # Added new task receipt also invalidates old readback.
            other=self.private/"long-horizon-development"/"ACADEMIC_NEW.json"
            other.write_text('{"task":"another"}',encoding="utf8")
            self.verified(private=self.private)
            self.assertEqual(self.calls,3)
        with cache.verification_session(private=self.private) as new:
            self.verified(private=self.private)
            self.assertEqual(self.calls,4)
            self.assertEqual(new["hits"],0)

    def test_new_code_head_invalidates_even_with_same_candidate_bytes(self):
        with cache.verification_session(private=self.private) as session:
            self.verified(private=self.private)
            self.latest["gitHead"]=_HEAD_B
            self.create_candidate(_HEAD_B)
            self.verified(private=self.private)
            self.assertEqual(self.calls,2)
            self.assertEqual(session["hits"],0)

    def test_source_and_candidate_tampering_never_reuses_cache(self):
        with cache.verification_session(private=self.private) as session:
            self.verified(private=self.private)
            self.source.write_bytes(b"%PDF-FAKE-CONTRACT-SOURCf")
            with self.assertRaisesRegex(ValueError,"FAKE_VERIFIER_REJECTS_CHANGED_SOURCE"):
                self.verified(private=self.private)
            self.assertEqual(self.calls,2)
            self.assertEqual(session["hits"],0)
        self.source.write_bytes(b"%PDF-FAKE-CONTRACT-SOURCE")
        with cache.verification_session(private=self.private) as session:
            self.verified(private=self.private)
            candidate=self.private/"owner-five-stage-completion"/_HEAD_A/_PROPOSAL/cache._CANDIDATE
            candidate.write_bytes(self.text+b" ")
            self.verified(private=self.private)
            self.assertEqual(self.calls,4)
            self.assertEqual(session["hits"],0)

    def test_no_scope_or_custom_rules_never_cache(self):
        self.verified(private=self.private)
        self.verified(private=self.private)
        self.assertEqual(self.calls,2)
        with cache.verification_session(private=self.private) as session:
            self.verified(private=self.private)
            self.verified(private=self.private)
            self.assertEqual(self.calls,3)
            self.assertEqual(session["hits"],1)
        def with_rules(*,private:Path,rules:dict):
            return {"rules":rules}
        f=cache.verified_stage_reuse(with_rules)
        with cache.verification_session(private=self.private) as session:
            self.assertEqual(f(private=self.private,rules={"new":True}),
                             {"rules":{"new":True}})
            self.assertEqual(session["hits"],0)

    def test_failure_and_nonaccepted_result_are_not_cached(self):
        calls=[]
        @cache.verified_stage_reuse
        def fail(*,private:Path):
            calls.append(True)
            raise ValueError("NOT_SIGNED")
        with cache.verification_session(private=self.private):
            for _ in range(2):
                with self.assertRaisesRegex(ValueError,"NOT_SIGNED"):
                    fail(private=self.private)
        self.assertEqual(len(calls),2)
        @cache.verified_stage_reuse
        def not_independent(*,private:Path):
            calls.append(False)
            return {"status":"MOCK_REVERIFIED","currentGitHead":_HEAD_A,
                    "newProviderCalls":0,"publicationAuthorized":True,
                    "independentlyAcceptedAcademicTasks":429}
        with cache.verification_session(private=self.private) as session:
            not_independent(private=self.private)
            not_independent(private=self.private)
            self.assertEqual(session["hits"],0)
        self.assertEqual(calls.count(False),2)

    def test_cached_second_verification_avoids_expensive_real_call(self):
        @cache.verified_stage_reuse
        def slow(*,private:Path):
            sleep(0.12)
            return {"status":"SOURCE_SIGNED_REVERIFIED",
                    "currentGitHead":_HEAD_A,
                    "newProviderCalls":0,
                    "publicationAuthorized":False,
                    "independentlyAcceptedAcademicTasks":28}
        with cache.verification_session(private=self.private) as session:
            t0=perf_counter()
            slow(private=self.private)
            initial=perf_counter()-t0
            t1=perf_counter()
            slow(private=self.private)
            repeated=perf_counter()-t1
            self.assertEqual(session["verifiedCalls"],1)
            self.assertEqual(session["hits"],1)
            self.assertLess(repeated,initial*0.7)

from app_generator.runtime.v3_owner_science_step_checkpoint import (
    record_completed_owner_step,read_completed_owner_step,
)


class RestartSafeOwnerStepCheckpoint(TestCase):
    def test_completed_step_persists_without_authorizing_science(self):
        with TemporaryDirectory() as td:
            private=Path(td)
            first=record_completed_owner_step(
                private=private,head=_HEAD_A,step=1,
                action="CURRENT_EXACT_HEAD_NORMAL_V36_RESTORED",
                elapsed_seconds=150)
            self.assertFalse(first["academicAcceptanceAdvanced"])
            self.assertFalse(first["canSkipOriginalScienceOnRestart"])
            self.assertTrue(first["signedSourceReverificationStillMandatory"])
            second=record_completed_owner_step(
                private=private,head=_HEAD_A,step=2,
                action="CURRENT_HEAD_SIGNED_BSA274_REGISTRY_AUDIT",
                elapsed_seconds=3)
            observed=read_completed_owner_step(private=private,head=_HEAD_A)
            self.assertEqual(observed,second)
            # A failed/restarted early step cannot roll back the last proven
            # engineering *telemetry*, but must reverify real signed proofs.
            old=record_completed_owner_step(
                private=private,head=_HEAD_A,step=1,
                action="CURRENT_EXACT_HEAD_NORMAL_V36_RESTORED",
                elapsed_seconds=8)
            self.assertEqual(old["lastCompletedStep"],2)
            self.assertIsNone(read_completed_owner_step(
                private=private,head=_HEAD_B))
            third=record_completed_owner_step(
                private=private,head=_HEAD_B,step=1,
                action="CURRENT_EXACT_HEAD_NORMAL_V36_RESTORED",
                elapsed_seconds=9)
            self.assertEqual(third["head"],_HEAD_B)

    def test_malformed_checkpoint_and_forged_academic_pass_rejected(self):
        with TemporaryDirectory() as td:
            private=Path(td)
            initial=record_completed_owner_step(
                private=private,head=_HEAD_A,step=3,
                action="SIGNED_AND_INDEPENDENTLY_READ_A28_EXPLANATION_SCIENCE_TASK",
                elapsed_seconds=500)
            target=(private/"owner-science-stage-checkpoints"/_HEAD_A/
                    "BSA315_OWNER_SCIENCE_STEP_CHECKPOINT.json")
            forged={**initial,"academicAcceptanceAdvanced":True}
            import json
            target.write_text(json.dumps(forged),encoding="utf8")
            with self.assertRaisesRegex(ValueError,"NOT_AUTHENTIC"):
                read_completed_owner_step(private=private,head=_HEAD_A)
            with self.assertRaisesRegex(ValueError,"NOT_AUTHENTIC"):
                record_completed_owner_step(
                    private=private,head=_HEAD_A,step=4,
                    action="SIGNED_AND_INDEPENDENTLY_READ_A29_SCIENCE_TASK",
                    elapsed_seconds=500)

    def test_invalid_stage_and_owner_head_rejected(self):
        with TemporaryDirectory() as td:
            private=Path(td)
            for head,step,action,elapsed in (
                (_HEAD_A,True,"GOOD_SIGNED_STAGE",1),
                (_HEAD_A,1,"bad action",1),
                (_HEAD_A,1,"GOOD_SIGNED_STAGE",-1),
                ("not-a-head",1,"GOOD_SIGNED_STAGE",1),
            ):
                with self.subTest(head=head,step=step,action=action),self.assertRaises(ValueError):
                    record_completed_owner_step(
                        private=private,head=head,step=step,
                        action=action,elapsed_seconds=elapsed)

from app_generator.runtime.v3_science_recovery_outcome import (
    assess_signed_recovery_outcome,
)


class IndependentThroughputBasedRecovery(TestCase):
    def test_two_distinct_independently_signed_no_gain_heads_pivot_work(self):
        proof={"acceptedCount":28,"noGainOwnerHeads":2,
               "lastVerifiedHead":_HEAD_B,
               "independentReceiptSha256":"b"*64}
        state={"scienceAcceptance":proof,"cycle":93,
               "scienceExecution":{"lastStageCompleted":14}}
        outcome=assess_signed_recovery_outcome(state)
        self.assertTrue(outcome["pivotRequired"])
        self.assertEqual(outcome["acceptedCount"],28)
        self.assertEqual(outcome["pendingCount"],401)
        self.assertEqual(outcome["nextWorkFamily"],
            "INDEPENDENT_ORIGINAL_SOURCE_TRILINGUAL_OR_DIAGRAM_SEMANTIC_PROOF")
        self.assertFalse(outcome["publicationAuthorized"])

    def test_heartbeat_ci_or_untrusted_claim_never_triggers_pivot(self):
        self.assertFalse(assess_signed_recovery_outcome(
            {"scienceExecution":{"lastStageCompleted":14},
             "githubCI":"success"})["pivotRequired"])
        for bad in (True,2.0,"2",-1):
            proof={"acceptedCount":28,"noGainOwnerHeads":bad,
                   "lastVerifiedHead":_HEAD_B,
                   "independentReceiptSha256":"b"*64}
            outcome=assess_signed_recovery_outcome(
                {"scienceAcceptance":proof})
            self.assertFalse(outcome["pivotRequired"])
        proof={"acceptedCount":28,"noGainOwnerHeads":1,
               "lastVerifiedHead":_HEAD_B,
               "independentReceiptSha256":"b"*64}
        self.assertFalse(assess_signed_recovery_outcome(
            {"scienceAcceptance":proof})["pivotRequired"])


class HistoricalSignedOriginInvalidation(ImmutableSignedScienceReuse):
    def test_any_original_stage_evidence_mutation_forces_verifier(self):
        origin_head=_HEAD_B
        self.create_candidate(origin_head)
        frontier=self.private/"long-horizon-development"/"ACADEMIC_FRONTIER.json"
        import json,os
        frontier.write_text(json.dumps(
            {"gitHead":origin_head,"proposalSha256":_PROPOSAL}),
            encoding="utf8")
        historical=(self.private/"owner-five-stage-completion"/
                    origin_head/_PROPOSAL/"V36_PARTITION_01.json")
        with cache.verification_session(private=self.private) as session:
            self.verified(private=self.private)
            self.verified(private=self.private)
            self.assertEqual(self.calls,1)
            old=historical.stat()
            historical.write_text('{"surfaceSha256":"new"}',encoding="utf8")
            os.utime(historical,ns=(old.st_atime_ns,old.st_mtime_ns))
            self.verified(private=self.private)
            self.assertEqual(self.calls,2)
            self.assertEqual(session["hits"],1)

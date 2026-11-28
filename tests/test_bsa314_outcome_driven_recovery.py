"""BSA314 recovery contract: actual no-gain, preflight, escalation safeguards.

Synthetic mocks here never confer academic acceptance; only the owner Yoga6
signed original-source admission does so after hosted exact-head CI.
"""
from __future__ import annotations

from contextlib import redirect_stderr
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app_generator.runtime.v3_incremental_signed_science_progress import (
    apply_independent_progress,
)
from app_generator.runtime.v3_scientific_acceptance_watchdog import (
    investigate_zero_academic_gain,
)
from app_generator.runtime import v3_outcome_driven_science_preflight as pre
from app_generator.runtime import v3_autonomous_academic_advancement as academic
from scripts import bosla_persistent_development as owner


class SourceBoundNoGainAccounting(TestCase):
    def signed(self,head:str,count:int=27)->dict:
        return {"lastVerifiedHead":head,"acceptedCount":count,
                "pendingCount":429-count,"verifiedEvidenceSha256":"a"*64}

    def test_distinct_verified_head_counts_once_but_repeated_heartbeat_does_not(self):
        first,second="1"*40,"2"*40
        state={"scienceAcceptance":{"acceptedCount":27,
                "lastVerifiedHead":first,"noGainOwnerHeads":0,
                "lastIncreaseAt":"2026-11-28T05:06:57+00:00",
                "lastVerifiedCycle":85}}
        report=apply_independent_progress(state=state,verified=self.signed(second),
            head=second,now="2026-11-28T07:20:00+00:00",cycle=88)
        self.assertEqual(report["noGainOwnerHeads"],1)
        self.assertFalse(report["advancedThisObservation"])
        repeated=apply_independent_progress(state=state,verified=self.signed(second),
            head=second,now="2026-11-28T07:21:00+00:00",cycle=89)
        self.assertEqual(repeated["noGainOwnerHeads"],1)
        self.assertEqual(repeated["lastIncreaseAt"],"2026-11-28T05:06:57+00:00")
        third="3"*40
        report=apply_independent_progress(state=state,verified=self.signed(third),
            head=third,now="2026-11-28T07:22:00+00:00",cycle=90)
        self.assertEqual(report["noGainOwnerHeads"],2)
        stall=investigate_zero_academic_gain(
            state,now="2026-11-28T07:22:01+00:00",cycle=91)
        self.assertTrue(stall["triggered"])
        self.assertEqual(stall["classification"],
                         "INDEPENDENT_PROOF_PRODUCER_AND_SIGNED_ADMISSION_GAP")
        self.assertEqual(state["scienceAcceptance"]["acceptedCount"],27)
        self.assertFalse(state["scientificProgress"]["publicationAuthorized"])
        improved=apply_independent_progress(state=state,verified=self.signed(third,28),
            head=third,now="2026-11-28T07:24:00+00:00",cycle=91)
        self.assertTrue(improved["advancedThisObservation"])
        self.assertEqual(improved["noGainOwnerHeads"],0)

    def test_reject_malicious_counter_and_signed_rollback(self):
        head="2"*40
        for bad in (True,-1,"200"):
            with self.subTest(counter=bad):
                state={"scienceAcceptance":{"acceptedCount":27,
                    "lastVerifiedHead":"1"*40,"noGainOwnerHeads":bad}}
                with self.assertRaisesRegex(ValueError,"BSA314_INVALID_PREVIOUS_STALL_COUNTER"):
                    apply_independent_progress(state=state,verified=self.signed(head),
                        head=head,now="2026-11-28T07:20:00+00:00",cycle=88)
        state={"scienceAcceptance":{"acceptedCount":27,
            "lastVerifiedHead":"1"*40,"noGainOwnerHeads":0}}
        with self.assertRaisesRegex(ValueError,"ROLLBACK"):
            apply_independent_progress(state=state,verified=self.signed(head,26),
                head=head,now="2026-11-28T07:20:00+00:00",cycle=88)


class ActualSourcePreflightSafety(TestCase):
    NEW="2"*40
    OLD="1"*40
    PROPOSAL="b"*64

    def test_same_head_or_prior_signed_a28_never_replays_source(self):
        with TemporaryDirectory() as td:
            private=Path(td)
            last={"gitHead":self.NEW,"proposalSha256":self.PROPOSAL}
            with patch.object(pre,"read_long_horizon_development",return_value=last), \
                 patch.object(pre,"independently_prove_vector_explanation") as producer:
                result=pre.preflight_next_a28_before_rebuild(
                    private=private,current_head=self.NEW)
                self.assertEqual(result["status"],"BSA314_SAME_HEAD_NO_REBUILD")
                producer.assert_not_called()
            last["gitHead"]=self.OLD
            frontier=private/"long-horizon-development"/pre._FRONTIER
            frontier.parent.mkdir(parents=True)
            frontier.write_text("previously signed",encoding="utf8")
            with patch.object(pre,"read_long_horizon_development",return_value=last), \
                 patch.object(pre,"independently_prove_vector_explanation") as producer:
                result=pre.preflight_next_a28_before_rebuild(
                    private=private,current_head=self.NEW)
                self.assertEqual(result["status"],"BSA314_A28_ALREADY_SIGNED_NO_PREFLIGHT")
                producer.assert_not_called()

    def test_real_producer_and_signed_row_required_but_never_signs(self):
        with TemporaryDirectory() as td:
            private=Path(td)
            prior={"gitHead":self.OLD,"proposalSha256":self.PROPOSAL}
            witness={"taskId":"task-28","surfaceSha256":"digest"}
            row={"taskId":"task-28","surfaceSha256":"digest",
                 "kind":"COMPLETE_SCIENTIFIC_MEANING",
                 "status":"BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED"}
            with patch.object(pre,"read_long_horizon_development",return_value=prior), \
                 patch.object(pre,"_trusted_json",return_value={"sourcePdf":"original.pdf"}), \
                 patch.object(pre,"independently_prove_vector_explanation",return_value=witness), \
                 patch.object(pre,"independently_check_vector_explanation_witness"), \
                 patch.object(pre,"_signed",return_value={"activity":{"evidenceRows":[row]}}):
                result=pre.preflight_next_a28_before_rebuild(
                    private=private,current_head=self.NEW)
                self.assertEqual(result["status"],"BSA314_A28_ORIGINAL_SOURCE_PREFLIGHT_PASS")
                self.assertFalse(result["academicAcceptanceAdvanced"])
                self.assertFalse(result["publicationAuthorized"])
                self.assertTrue(result["mustRunNormalOwnerV36"])
            with patch.object(pre,"read_long_horizon_development",return_value=prior), \
                 patch.object(pre,"_trusted_json",return_value={"sourcePdf":"original.pdf"}), \
                 patch.object(pre,"independently_prove_vector_explanation",return_value=witness), \
                 patch.object(pre,"independently_check_vector_explanation_witness"), \
                 patch.object(pre,"_signed",return_value={"activity":{"evidenceRows":[
                     {**row,"surfaceSha256":"tampered"}]}}):
                with self.assertRaisesRegex(ValueError,"BSA314_A28_ORIGINAL_SOURCE_PREFLIGHT_FAILED"):
                    pre.preflight_next_a28_before_rebuild(
                        private=private,current_head=self.NEW)

    def test_preflight_failure_prevents_costly_rebuild_without_acceptance(self):
        with TemporaryDirectory() as td:
            with patch.object(academic,"_git_info",return_value=(self.NEW,"branch")), \
                 patch.object(academic,"_git_clean",return_value=True), \
                 patch.object(academic,"_hosted_runs",return_value=[]), \
                 patch.object(academic,"_exact_ci_success",return_value=True), \
                 patch.object(academic,"read_long_horizon_development",
                              return_value={"gitHead":self.OLD}), \
                 patch.object(academic,"preflight_next_a28_before_rebuild",
                              side_effect=ValueError("BSA314_A28_ORIGINAL_SOURCE_PREFLIGHT_FAILED")), \
                 patch.object(academic,"_owner_advance_worker") as worker:
                with redirect_stderr(StringIO()):
                    with self.assertRaisesRegex(ValueError,"BSA314_A28_ORIGINAL_SOURCE_PREFLIGHT_FAILED"):
                        academic.advance_all_eligible_academic_actions(
                            repo=Path(td),private=Path(td),max_steps=1)
                worker.assert_not_called()


class RootCauseEscalation(TestCase):
    def test_third_same_exact_failure_quarantines_only_failed_task(self):
        message=json.dumps({"status":"BSA276_ELIGIBLE_ACADEMIC_STEP_UNVERIFIED",
            "errorClass":"ValueError",
            "errorCode":"BSA292_EXPLANATION_SCIENCE_NOT_REPROVEN",
            "academicAcceptanceAdvanced":False,"publicationAuthorized":False})
        with TemporaryDirectory() as td:
            private=Path(td)
            logs=private/"logs"
            logs.mkdir()
            path=logs/"OWNER_REAL_SOURCE_ADMISSION.log"
            path.write_text(message+"\n",encoding="utf8")
            state={"schemaVersion":1,"cycle":88,"currentLog":str(path),
                   "scienceAcceptance":{"acceptedCount":27}}
            with patch.object(owner,"PRIVATE",private), \
                 patch.object(owner,"STATE",private/"state.json"), \
                 patch.object(owner,"JOURNAL",private/"events.jsonl"):
                first=owner._failed_owner_decision(
                    state,head="1"*40,exit_code=2)
                second=owner._failed_owner_decision(
                    state,head="2"*40,exit_code=2)
                third=owner._failed_owner_decision(
                    state,head="3"*40,exit_code=2)
            self.assertEqual(first["repairStrategy"],"FIRST_TARGETED_REPAIR")
            self.assertEqual(second["repairStrategy"],
                "DIFFERENTIAL_REAL_SOURCE_ROOT_CAUSE_DIAGNOSIS")
            self.assertEqual(third["repairStrategy"],
                "QUARANTINE_EXACT_BLOCKER_AND_BUILD_PARALLEL_PROOF")
            self.assertEqual(third["repairOutcomeComparedToPrevious"],
                "UNCHANGED_EXACT_SCIENCE_FAILURE")
            self.assertEqual(state["scienceRecoveryQuarantine"]["blockedTask"],
                "A28_VECTOR_EXPLANATION")
            self.assertTrue(state["scienceRecoveryQuarantine"]["cannotSignOrCountBlockedTask"])
            self.assertEqual(state["scienceAcceptance"]["acceptedCount"],27)

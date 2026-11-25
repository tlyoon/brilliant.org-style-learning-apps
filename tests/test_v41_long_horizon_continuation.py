"""BSA269: genuine restart-safe development frontier, not a fake proof."""
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from unittest import TestCase

from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_post_v35_semantic_task_dispatch import _V36,_STATUS36
from app_generator.runtime.v3_long_horizon_development import (
    persist_long_horizon_development,read_long_horizon_development
)
from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA,_CANDIDATE_SHA,
)

ROOT=Path(__file__).resolve().parents[1]


def signed_run(private,head,proposal="b"*64):
    ready={"gitHead":head,"proposalSha256":proposal}
    folder=private/"owner-five-stage-completion"/head/proposal
    folder.mkdir(parents=True,exist_ok=True)
    v36=_v6_checkpoint(folder/_V36,{
        **ready,
        "status":_STATUS36,
        "sourceSha256":_SOURCE_SHA,
        "revisedCandidateSha256":_CANDIDATE_SHA,
        "semanticTasksAutomaticallyDispatched":429,
        "activitySignedPartitionCount":18,
        "fullAcademicProofTasksAccepted":0,
        "fullAcademicProofTasksStillOpen":429,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicPASS":0,
        "publicationAuthorized":False,
    })
    development={
        "developmentOutcomeClass":"ENGINEERING_VERIFIED_NOT_ACADEMIC_ACCEPTANCE",
        "academicProofTasksAcceptedThisRun":0,
        "academicAcceptanceAdvanced":False,
        "academicProofProducerRequired":True,
        "engineeringOnlyFrontierTerminal":True,
        "academicPASS":0,
        "publicationAuthorized":False,
        "newModelCalls":0,
        "stagesExecutedThisRun":7,
        "privateSemanticTaskDispatch":v36,
    }
    return ready,development


class LongHorizonContinuation(TestCase):
    def test_cross_session_repeat_exact_head_does_not_reset_or_inflate(self):
        with TemporaryDirectory() as t:
            path=Path(t)
            ready,dev=signed_run(path,"a"*40)
            first=persist_long_horizon_development(
                private=path,ready=ready,development=dev)
            resumed=read_long_horizon_development(path)
            again=persist_long_horizon_development(
                private=path,ready=ready,development=dev)
            self.assertEqual(first,resumed)
            self.assertEqual(first,again)
            self.assertEqual(first["consecutiveZeroProofCodeHeads"],1)
            self.assertEqual(first["academicAcceptedProofTaskCount"],0)
            self.assertEqual(first["fullSemanticProofTasksStillOpen"],429)
            self.assertEqual(first["completeAcademicProofGatesStillOpen"],90)
            self.assertTrue(first["architecturalProofProducerEscalationRequired"])
            self.assertFalse(first["unboundedCodeWritingAgentConfiguredHere"])

    def test_new_code_head_carries_same_blocker_forward_and_escalates(self):
        with TemporaryDirectory() as t:
            path=Path(t)
            a,d=signed_run(path,"a"*40)
            prior=persist_long_horizon_development(
                private=path,ready=a,development=d)
            b,d2=signed_run(path,"c"*40)
            future=persist_long_horizon_development(
                private=path,ready=b,development=d2)
            self.assertEqual(future["consecutiveZeroProofCodeHeads"],2)
            self.assertEqual(
                future["predecessorEventSha256"],prior["currentEventSha256"])
            self.assertEqual(read_long_horizon_development(path),future)
            self.assertEqual(future["fullSemanticProofTasksStillOpen"],429)

    def test_forged_academic_acceptance_cannot_be_persisted(self):
        with TemporaryDirectory() as t:
            path=Path(t)
            ready,dev=signed_run(path,"a"*40)
            dev["academicProofTasksAcceptedThisRun"]=1
            with self.assertRaisesRegex(ValueError,"FALSE_ACADEMIC_PROGRESS"):
                persist_long_horizon_development(
                    private=path,ready=ready,development=dev)

    def test_unsigned_or_foreign_v36_cannot_set_horizon(self):
        with TemporaryDirectory() as t:
            path=Path(t)
            ready,dev=signed_run(path,"a"*40)
            dev["privateSemanticTaskDispatch"]={
                **dev["privateSemanticTaskDispatch"],"sourceSha256":"f"*64}
            with self.assertRaisesRegex(ValueError,"SIGNED_SOURCE_V36_REQUIRED"):
                persist_long_horizon_development(
                    private=path,ready=ready,development=dev)

    def test_corrupt_latest_pointer_is_not_silently_recreated(self):
        with TemporaryDirectory() as t:
            path=Path(t)
            ready,dev=signed_run(path,"a"*40)
            persist_long_horizon_development(
                private=path,ready=ready,development=dev)
            latest=path/"long-horizon-development"/"BOSLA_HORIZON_STATE.json"
            raw=json.loads(latest.read_text(encoding="utf8"))
            raw["fullSemanticProofTasksStillOpen"]=0
            latest.write_text(json.dumps(raw),encoding="utf8")
            with self.assertRaisesRegex(ValueError,"STATE_INTEGRITY"):
                read_long_horizon_development(path)
            with self.assertRaisesRegex(ValueError,"STATE_INTEGRITY"):
                persist_long_horizon_development(
                    private=path,ready=ready,development=dev)

    def test_normal_worker_automatically_persists_long_horizon(self):
        src=(ROOT/"scripts"/"run_v3_yoga6_recovery_worker.py").read_text(
            encoding="utf8")
        self.assertIn("persist_long_horizon=True",src)
        self.assertIn("advance_eligible_verified_development_stages",src)

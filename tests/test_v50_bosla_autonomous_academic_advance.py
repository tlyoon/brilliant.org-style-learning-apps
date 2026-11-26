"""BSA276 autonomous no-unnecessary-pauses source-bound acceptance controller.

No synthetic test pretends to sign an original textbook science proof:
math and owner-provenance tests are separate; here mocked finite gates test
restart behavior, ordered dispatch, CI lock, and mandatory continuation.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app_generator.runtime import v3_autonomous_academic_advancement as auto

HEAD="a"*40
PROPOSAL="b"*64


class AutonomousAcademicFlow(TestCase):
    def case(self,previous_head=False,failed_ci=False,
             auto_run=None,max_steps=8,raise_a3=False):
        with TemporaryDirectory() as temp:
            private=Path(temp)
            root=Path(temp)/"fake-root"
            root.mkdir()
            owner=private/"owner-five-stage-completion"/HEAD/PROPOSAL
            owner.mkdir(parents=True)
            state={"head":"c"*40 if previous_head else HEAD}
            calls=[]
            def latest(path):
                return {"gitHead":state["head"],"proposalSha256":PROPOSAL}
            def worker(repo):
                calls.append("owner")
                state["head"]=HEAD
            def audit_sign(private):
                calls.append("audit")
                (owner/auto._AUDIT_RECEIPT).write_text("{}")
                return {"independentlyAcceptedAcademicTasks":2,
                        "pendingMcqDistractorScienceTasks":25}
            def a3_admit(private):
                calls.append("a3")
                if raise_a3:
                    raise ValueError("ACTUAL_A3_SCIENTIFIC_PROOF_REQUIRED")
                frontier=private/"long-horizon-development"/auto._A3_FRONTIER
                frontier.parent.mkdir(exist_ok=True)
                frontier.write_text("{}")
                return {"independentlyAcceptedAcademicTasks":3}
            def si_admit(private):
                calls.append("a4_a6")
                frontier=private/"long-horizon-development"/auto._SI_FRONTIER
                frontier.parent.mkdir(exist_ok=True)
                frontier.write_text("{}")
                return {"independentlyAcceptedAcademicTasks":6,
                        "pendingMcqDistractorScienceTasks":21}
            with (patch.object(auto,"_git_info",return_value=(HEAD,"feature")),
                  patch.object(auto,"_git_clean",return_value=True),
                  patch.object(auto,"_hosted_runs",return_value=[]),
                  patch.object(auto,"_exact_ci_success",
                               return_value=not failed_ci),
                  patch.object(auto,"read_long_horizon_development",
                               side_effect=latest),
                  patch.object(auto,"_owner_advance_worker",side_effect=worker),
                  patch.object(auto,"sign_registry_audit",side_effect=audit_sign),
                  patch.object(auto,"verify_registry_audit",
                    return_value={"independentlyAcceptedAcademicTasks":2,
                                  "pendingMcqDistractorScienceTasks":25}),
                  patch.object(auto,"admit_new_scientific_batch",
                               side_effect=a3_admit),
                  patch.object(auto,"verify_academic_batch_across_git_heads",
                    return_value={"independentlyAcceptedAcademicTasks":3,
                                  "fullAcademicTasksStillOpen":426}),
                  patch.object(auto,"admit_si_unit_science_batch",
                               side_effect=si_admit),
                  patch.object(auto,"verify_si_unit_batch_across_git_heads",
                    return_value={"independentlyAcceptedAcademicTasks":6,
                                  "fullAcademicTasksStillOpen":423,
                                  "completeAcademicProofGatesStillOpen":90,
                                  "fullAcademicActivityPASS":0,
                                  "publicationAuthorized":False})):
                if auto_run is None:
                    result=auto.advance_all_eligible_academic_actions(
                        repo=root,private=private,max_steps=max_steps)
                    return result,calls
                if auto_run=="twice":
                    first=auto.advance_all_eligible_academic_actions(
                        repo=root,private=private,max_steps=max_steps)
                    second=auto.advance_all_eligible_academic_actions(
                        repo=root,private=private,max_steps=max_steps)
                    return (first,second),calls
                return auto.advance_all_eligible_academic_actions(
                    repo=root,private=private,max_steps=max_steps),calls

    def test_all_four_missing_boundaries_automatically_advance_in_one_run(self):
        result,actions=self.case(previous_head=True)
        self.assertEqual(actions,["owner","audit","a3","a4_a6"])
        self.assertEqual(result["academicProofTasksAccepted"],6)
        self.assertEqual(result["fullAcademicProofTasksStillOpen"],423)
        self.assertEqual(result["completeAcademicProofGatesStillOpen"],90)
        self.assertEqual(result["academicActivityPASS"],0)
        self.assertFalse(result["publicationAuthorized"])

    def test_idempotent_restart_does_not_reissue_old_proofs(self):
        result,actions=self.case(auto_run="twice")
        self.assertEqual(actions,["audit","a3","a4_a6"])
        first,second=result
        self.assertEqual(first["academicProofTasksAccepted"],6)
        self.assertEqual(second["academicProofTasksAccepted"],6)
        self.assertEqual(second["actionsExecuted"],[])

    def test_failed_exact_head_ci_stops_unsafe_admission(self):
        with self.assertRaisesRegex(ValueError,"EXACT_HEAD_HOSTED_CI"):
            self.case(failed_ci=True)

    def test_missing_original_academic_proof_stops_only_unsafe_acceptance(self):
        with self.assertRaisesRegex(ValueError,"ACTUAL_A3_SCIENTIFIC_PROOF_REQUIRED"):
            self.case(raise_a3=True)

    def test_bounded_steps_require_eventual_readback_not_false_success(self):
        with self.assertRaisesRegex(ValueError,"BOUNDED_ADVANCE_LIMIT"):
            self.case(previous_head=True,max_steps=2)

    def test_bad_batch_length_and_bool_rejected(self):
        for limit in (0,13,True,-2):
            with self.subTest(limit=limit),self.assertRaisesRegex(
                ValueError,"INVALID_BOUNDED"):
                self.case(max_steps=limit)

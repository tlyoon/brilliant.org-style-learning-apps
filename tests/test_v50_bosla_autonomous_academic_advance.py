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
             auto_run=None,max_steps=15,raise_a3=False):
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
            def newton_admit(private):
                calls.append("a7_a9")
                frontier=private/"long-horizon-development"/auto._NEWTON_FRONTIER
                frontier.parent.mkdir(exist_ok=True)
                frontier.write_text("{}")
                return {"independentlyAcceptedAcademicTasks":9,
                        "pendingMcqDistractorScienceTasks":18}
            def glider_admit(private):
                calls.append("a10_a12")
                frontier=private/"long-horizon-development"/auto._GLIDER_FRONTIER
                frontier.parent.mkdir(exist_ok=True)
                frontier.write_text("{}")
                return {"independentlyAcceptedAcademicTasks":12,
                        "pendingMcqDistractorScienceTasks":15}
            def third_law_admit(private):
                calls.append("a13_a15")
                frontier=private/"long-horizon-development"/auto._THIRD_LAW_FRONTIER
                frontier.parent.mkdir(exist_ok=True)
                frontier.write_text("{}")
                return {"independentlyAcceptedAcademicTasks":15,
                        "pendingMcqDistractorScienceTasks":12,
                        "fullAcademicTasksStillOpen":414}
            def equal_speed_admit(private):
                calls.append("a16_a18")
                frontier=private/"long-horizon-development"/auto._EQUAL_SPEED_FRONTIER
                frontier.parent.mkdir(exist_ok=True)
                frontier.write_text("{}")
                return {"independentlyAcceptedAcademicTasks":18,
                        "pendingMcqDistractorScienceTasks":9}
            def equal_energy_admit(private):
                calls.append("a19_a21")
                frontier=private/"long-horizon-development"/auto._EQUAL_ENERGY_FRONTIER
                frontier.parent.mkdir(exist_ok=True)
                frontier.write_text("{}")
                return {"independentlyAcceptedAcademicTasks":21,
                        "pendingMcqDistractorScienceTasks":6}
            energy_admit_patch=patch.object(auto,"admit_equal_energy_batch",side_effect=equal_energy_admit)
            energy_verify_patch=patch.object(auto,"verify_equal_energy_batch_across_git_heads",
                return_value={"independentlyAcceptedAcademicTasks":21,
                              "fullAcademicTasksStillOpen":408,
                              "pendingMcqDistractorScienceTasks":6,
                              "completeAcademicProofGatesStillOpen":90,
                              "fullAcademicActivityPASS":0,
                              "publicationAuthorized":False})
            energy_admit_patch.start()
            energy_verify_patch.start()
            self.addCleanup(energy_admit_patch.stop)
            self.addCleanup(energy_verify_patch.stop)
            def isolated_pair_admit(private):
                calls.append("a22_a24")
                frontier=private/"long-horizon-development"/auto._ISOLATED_PAIR_FRONTIER
                frontier.parent.mkdir(exist_ok=True)
                frontier.write_text("{}")
                return {"independentlyAcceptedAcademicTasks":24,
                        "pendingMcqDistractorScienceTasks":3}
            pair_admit_patch=patch.object(auto,"admit_isolated_pair_batch",side_effect=isolated_pair_admit)
            pair_verify_patch=patch.object(auto,"verify_isolated_pair_batch_across_git_heads",
                return_value={"independentlyAcceptedAcademicTasks":24,
                              "fullAcademicTasksStillOpen":405,
                              "pendingMcqDistractorScienceTasks":3,
                              "completeAcademicProofGatesStillOpen":90,
                              "fullAcademicActivityPASS":0,
                              "publicationAuthorized":False})
            pair_admit_patch.start()
            pair_verify_patch.start()
            self.addCleanup(pair_admit_patch.stop)
            self.addCleanup(pair_verify_patch.stop)
            def spring_admit(private):
                calls.append("a25_a27")
                frontier=private/"long-horizon-development"/auto._SPRING_BUFFER_FRONTIER
                frontier.parent.mkdir(exist_ok=True)
                frontier.write_text("{}")
                return {"independentlyAcceptedAcademicTasks":27,
                        "pendingMcqDistractorScienceTasks":0}
            spring_admit_patch=patch.object(auto,"admit_spring_buffer_batch",side_effect=spring_admit)
            spring_verify_patch=patch.object(auto,"verify_spring_buffer_batch_across_git_heads",
                return_value={"independentlyAcceptedAcademicTasks":27,
                              "fullAcademicTasksStillOpen":402,
                              "pendingMcqDistractorScienceTasks":0,
                              "completeAcademicProofGatesStillOpen":90,
                              "fullAcademicActivityPASS":0,
                              "publicationAuthorized":False})
            spring_admit_patch.start()
            spring_verify_patch.start()
            self.addCleanup(spring_admit_patch.stop)
            self.addCleanup(spring_verify_patch.stop)
            def explanation_admit(private):
                calls.append("a28")
                frontier=private/"long-horizon-development"/auto._VECTOR_EXPLANATION_FRONTIER
                frontier.parent.mkdir(exist_ok=True)
                frontier.write_text("{}")
                return {"independentlyAcceptedAcademicTasks":28,
                        "fullAcademicTasksStillOpen":401}
            explanation_admit_patch=patch.object(auto,"admit_vector_explanation",side_effect=explanation_admit)
            explanation_verify_patch=patch.object(auto,"verify_vector_explanation_across_git_heads",
                return_value={"independentlyAcceptedAcademicTasks":28,
                              "fullAcademicTasksStillOpen":401,
                              "completeAcademicProofGatesStillOpen":90,
                              "fullAcademicActivityPASS":0,
                              "publicationAuthorized":False})
            explanation_admit_patch.start()
            explanation_verify_patch.start()
            self.addCleanup(explanation_admit_patch.stop)
            self.addCleanup(explanation_verify_patch.stop)
            def si_explanation_admit(private):
                calls.append("a29")
                frontier=private/"long-horizon-development"/auto._SI_EXPLANATION_FRONTIER
                frontier.parent.mkdir(exist_ok=True)
                frontier.write_text("{}")
                return {"independentlyAcceptedAcademicTasks":29,
                        "fullAcademicTasksStillOpen":400}
            si_explanation_admit_patch=patch.object(auto,"admit_si_explanation",side_effect=si_explanation_admit)
            si_explanation_verify_patch=patch.object(auto,"verify_si_explanation_across_git_heads",
                return_value={"independentlyAcceptedAcademicTasks":29,
                              "fullAcademicTasksStillOpen":400,
                              "completeAcademicProofGatesStillOpen":90,
                              "fullAcademicActivityPASS":0,
                              "publicationAuthorized":False})
            si_explanation_admit_patch.start()
            si_explanation_verify_patch.start()
            self.addCleanup(si_explanation_admit_patch.stop)
            self.addCleanup(si_explanation_verify_patch.stop)
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
                                  "publicationAuthorized":False}),
                  patch.object(auto,"admit_newton_source_bound_batch",
                               side_effect=newton_admit),
                  patch.object(auto,"verify_newton_batch_across_git_heads",
                    return_value={"independentlyAcceptedAcademicTasks":9,
                                  "fullAcademicTasksStillOpen":420,
                                  "completeAcademicProofGatesStillOpen":90,
                                  "fullAcademicActivityPASS":0,
                                  "publicationAuthorized":False}),
                  patch.object(auto,"admit_paired_glider_batch",
                               side_effect=glider_admit),
                  patch.object(auto,"verify_paired_glider_batch_across_git_heads",
                    return_value={"independentlyAcceptedAcademicTasks":12,
                                  "fullAcademicTasksStillOpen":417,
                                  "completeAcademicProofGatesStillOpen":90,
                                  "fullAcademicActivityPASS":0,
                                  "publicationAuthorized":False}),
                  patch.object(auto,"admit_third_law_batch",
                               side_effect=third_law_admit),
                  patch.object(auto,"verify_third_law_batch_across_git_heads",
                    return_value={"independentlyAcceptedAcademicTasks":15,
                                  "fullAcademicTasksStillOpen":414,
                                  "pendingMcqDistractorScienceTasks":12,
                                  "completeAcademicProofGatesStillOpen":90,
                                  "fullAcademicActivityPASS":0,
                                  "publicationAuthorized":False}),
                  patch.object(auto,"admit_equal_speed_batch",
                               side_effect=equal_speed_admit),
                  patch.object(auto,"verify_equal_speed_batch_across_git_heads",
                    return_value={"independentlyAcceptedAcademicTasks":18,
                                  "fullAcademicTasksStillOpen":411,
                                  "pendingMcqDistractorScienceTasks":9,
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
        self.assertEqual(actions,["owner","audit","a3","a4_a6","a7_a9","a10_a12","a13_a15","a16_a18","a19_a21","a22_a24","a25_a27","a28","a29"])
        self.assertEqual(result["academicProofTasksAccepted"],29)
        self.assertEqual(result["fullAcademicProofTasksStillOpen"],400)
        self.assertEqual(result["completeAcademicProofGatesStillOpen"],90)
        self.assertEqual(result["academicActivityPASS"],0)
        self.assertFalse(result["publicationAuthorized"])

    def test_idempotent_restart_does_not_reissue_old_proofs(self):
        result,actions=self.case(auto_run="twice")
        self.assertEqual(actions,["audit","a3","a4_a6","a7_a9","a10_a12","a13_a15","a16_a18","a19_a21","a22_a24","a25_a27","a28","a29"])
        first,second=result
        self.assertEqual(first["academicProofTasksAccepted"],29)
        self.assertEqual(second["academicProofTasksAccepted"],29)
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
        for limit in (0,16,True,-2):
            with self.subTest(limit=limit),self.assertRaisesRegex(
                ValueError,"INVALID_BOUNDED"):
                self.case(max_steps=limit)

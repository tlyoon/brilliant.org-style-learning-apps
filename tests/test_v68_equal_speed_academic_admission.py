"""A16-A18 admission must rederive the signed source task partition."""
from __future__ import annotations

from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from app_generator.runtime import v3_equal_speed_academic_batch_admission as a


class EqualSpeedAdmission(TestCase):
    def test_prior_signed_fifteen_is_mandatory(self):
        good = {"independentlyAcceptedAcademicTasks": 15,
                "fullAcademicTasksStillOpen": 414,
                "pendingMcqDistractorScienceTasks": 12,
                "acceptedAcademicTaskIds": [str(i) for i in range(15)],
                "completeAcademicProofGatesStillOpen": 90,
                "fullAcademicActivityPASS": 0,
                "publicationAuthorized": False}
        with patch.object(a, "verify_third_law_batch_across_git_heads", return_value=good):
            self.assertEqual(a._prior_fifteen(None), good)
        for field, value in (("independentlyAcceptedAcademicTasks", 16),
                             ("fullAcademicActivityPASS", 1),
                             ("publicationAuthorized", True)):
            bad = {**good, field: value}
            with self.subTest(field=field), patch.object(
                    a, "verify_third_law_batch_across_git_heads", return_value=bad):
                with self.assertRaisesRegex(ValueError, "A1_A15_CHAIN"):
                    a._prior_fifteen(None)

    def test_partition_task_and_science_are_independently_rechecked(self):
        ready = {"gitHead": "a"*40, "proposalSha256": "b"*64}
        v36 = {"signedPartitionHashes": [{} for _ in range(18)],
               "semanticTasksAutomaticallyDispatched": 429,
               "fullAcademicProofTasksAccepted": 0,
               "completeAcademicProofGatesStillOpen": 90,
               "sourceSha256": a._SOURCE_SHA,
               "publicationAuthorized": False}
        v36["signedPartitionHashes"][5] = {
            "activityId": "act-mcq-06-equal-speed-comparison",
            "signedEvidenceSha256": "signed-sixth"}
        rows = [{"taskId": task, "kind": "MCQ_DISTRACTOR_SCIENCE",
                 "status": "BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED",
                 "surfaceSha256": "surface-"+option}
                for option, task in a._TASKS.items()]
        partition = {"integritySha256": "signed-sixth",
                     "activity": {"activityId": "act-mcq-06-equal-speed-comparison",
                                  "evidenceRows": rows},
                     "sourceSha256": a._SOURCE_SHA,
                     "candidateSha256": a._CANDIDATE_SHA,
                     "academicPASS": 0,
                     "publicationAuthorized": False}
        def producer(*, source_pdf, candidate_path, option_id):
            return {"taskId": a._TASKS[option_id], "optionId": option_id,
                    "surfaceSha256": "surface-"+option_id,
                    "sourceSha256": a._SOURCE_SHA,
                    "candidateSha256": a._CANDIDATE_SHA,
                    "newProviderCalls": 0, "publicationAuthorized": False}
        def run(part):
            with (patch.object(a, "_bound_inputs", return_value=(None, v36, None, "source", "candidate")),
                  patch.object(a, "_signed", return_value=part),
                  patch.object(a, "independently_prove_equal_speed_false_option", side_effect=producer),
                  patch.object(a, "independently_check_equal_speed_witness")):
                return a._original_equal_speed_proofs(private=Path("."), ready=ready, historical=False)
        _, _, proofs = run(partition)
        self.assertEqual([p["taskId"] for p in proofs], list(a._TASKS.values()))
        for changed in ("taskId", "surfaceSha256", "status"):
            altered = {**partition, "activity": {**partition["activity"],
                "evidenceRows": [dict(row) for row in rows]}}
            altered["activity"]["evidenceRows"][0][changed] = "forged"
            with self.subTest(changed=changed), self.assertRaisesRegex(
                    ValueError, "FALSE_OPTION_NOT_REPROVEN"):
                run(altered)
        wrong = {**partition, "integritySha256": "forged"}
        with self.assertRaisesRegex(ValueError, "PARTITION_CHANGED"):
            run(wrong)

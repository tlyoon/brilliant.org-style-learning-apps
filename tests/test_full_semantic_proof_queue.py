"""BSA253 adversarial exact-source semantic QA queue regression."""
from __future__ import annotations
from copy import deepcopy
import unittest

from app_generator.validation.full_semantic_proof_queue import (
    plan_full_semantic_proofs, verify_semantic_queue,
)

SOURCE = "e"*64


def L(s):
    return {"en": s, "ms": "BM " + s, "zh": "中文 " + s}


def fixture():
    return {"textbook": "one-source", "activities": [
        {"id": "a", "type": "mcq", "prompt": L("why"),
         "explanation": L("full mechanics explanation"),
         "feedback": L("use the law"),
         "answerKey": {"correct": "opt-a", "options": [
             {"id": "opt-a", "label": L("correct answer")},
             {"id": "opt-b", "label": L("false scientific claim")},
             {"id": "opt-c", "label": L("another false claim")}]},
         "visualSpec": {"template": "vector", "vectors": [{"dx": 1, "dy": 0}],
                        "accessibilityText": L("vector diagram")}},
        {"id": "b", "type": "interactive", "prompt": L("sort these"),
         "answerLogic": L("full reasoning"), "interaction": {
             "items": [{"id": "x", "label": L("value one")}]}}
    ]}


class FullSemanticProofQueueTests(unittest.TestCase):
    def test_complete_science_distractor_visual_and_trilingual_queue(self):
        q = plan_full_semantic_proofs(package=fixture(), source_sha256=SOURCE)
        self.assertEqual(q["activityCount"], 2)
        self.assertEqual(q["taskCounts"]["ORIGINAL_SOURCE_FIDELITY"], 2)
        self.assertEqual(q["taskCounts"]["MCQ_DISTRACTOR_SCIENCE"], 2)
        self.assertEqual(q["taskCounts"]["RENDERED_DIAGRAM_SCIENCE"], 1)
        self.assertGreaterEqual(q["taskCounts"]["COMPLETE_SCIENTIFIC_MEANING"], 5)
        self.assertGreaterEqual(q["taskCounts"]["TRILINGUAL_MEANING_EQUIVALENCE"], 9)
        self.assertTrue(all(t["status"] == "REVIEW_REQUIRED" for t in q["tasks"]))
        self.assertEqual(q["academicPASS"], 0)
        self.assertFalse(q["publicationAuthorized"])
        verify_semantic_queue(package=fixture(), source_sha256=SOURCE, queue=q)

    def test_private_learner_text_never_appears_in_queue(self):
        q = plan_full_semantic_proofs(package=fixture(), source_sha256=SOURCE)
        self.assertNotIn("full mechanics explanation", str(q))
        self.assertNotIn("false scientific claim", str(q))

    def test_changed_explanation_invalidates_saved_exact_version_queue(self):
        p = fixture()
        old = plan_full_semantic_proofs(package=p, source_sha256=SOURCE)
        p["activities"][0]["explanation"]["ms"] += " drift"
        with self.assertRaisesRegex(ValueError, "STALE_OR_FORGED"):
            verify_semantic_queue(package=p, source_sha256=SOURCE, queue=old)

    def test_changed_distractor_or_correct_key_invalidates_queue(self):
        for field in ("distractor", "key"):
            p = fixture()
            old = plan_full_semantic_proofs(package=p, source_sha256=SOURCE)
            if field == "key":
                p["activities"][0]["answerKey"]["correct"] = "opt-b"
            else:
                p["activities"][0]["answerKey"]["options"][1]["label"]["en"] += " altered"
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "STALE_OR_FORGED"):
                    verify_semantic_queue(package=p, source_sha256=SOURCE, queue=old)

    def test_diagram_or_source_change_invalidates_saved_queue(self):
        p = fixture()
        q = plan_full_semantic_proofs(package=p, source_sha256=SOURCE)
        with self.assertRaisesRegex(ValueError, "STALE_OR_FORGED"):
            verify_semantic_queue(package=p, source_sha256="f"*64, queue=q)
        p["activities"][0]["visualSpec"]["vectors"][0]["dx"] = -1
        with self.assertRaisesRegex(ValueError, "STALE_OR_FORGED"):
            verify_semantic_queue(package=p, source_sha256=SOURCE, queue=q)

    def test_no_academic_pass_accepted_by_queue_verifier(self):
        p = fixture()
        q = plan_full_semantic_proofs(package=p, source_sha256=SOURCE)
        q["academicPASS"] = 2
        with self.assertRaisesRegex(ValueError, "STALE_OR_FORGED"):
            verify_semantic_queue(package=p, source_sha256=SOURCE, queue=q)

    def test_no_missing_translations_or_activities_silently_dropped(self):
        for mutation in ("missing-lang", "missing-activity", "duplicate-id"):
            p = fixture()
            if mutation == "missing-lang":
                del p["activities"][0]["explanation"]["zh"]
            elif mutation == "missing-activity":
                p["activities"] = []
            else:
                p["activities"][1]["id"] = "a"
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    plan_full_semantic_proofs(package=p, source_sha256=SOURCE)

    def test_missing_distractor_structure_or_wrong_source_digest_fail_closed(self):
        for mutant in ("wrong-key", "duplicate-options", "missing-id"):
            p = fixture()
            k = p["activities"][0]["answerKey"]
            if mutant == "wrong-key":
                k["correct"] = "missing"
            elif mutant == "duplicate-options":
                k["options"][1]["id"] = "opt-a"
            else:
                del k["options"][1]["id"]
            with self.subTest(mutant=mutant):
                with self.assertRaises(ValueError):
                    plan_full_semantic_proofs(package=p, source_sha256=SOURCE)
        with self.assertRaisesRegex(ValueError, "INVALID_ORIGINAL_SOURCE"):
            plan_full_semantic_proofs(package=fixture(), source_sha256="bad")

    def test_generalizes_to_unseen_course_with_different_activity_roster(self):
        p = {"activities": [{"id": "new-chapter", "type": "interactive",
                              "prompt": L("electromagnetism"),
                              "answerLogic": L("new textbook content")}]}
        q = plan_full_semantic_proofs(package=p, source_sha256="b"*64)
        self.assertEqual(q["activityCount"], 1)
        self.assertEqual(q["taskCounts"]["MCQ_DISTRACTOR_SCIENCE"], 0)
        self.assertEqual(q["taskCounts"]["RENDERED_DIAGRAM_SCIENCE"], 0)
        self.assertEqual(q["academicPASS"], 0)

    def test_no_claims_after_roster_order_changes(self):
        p = fixture()
        q = plan_full_semantic_proofs(package=p, source_sha256=SOURCE)
        p["activities"].reverse()
        with self.assertRaisesRegex(ValueError, "STALE_OR_FORGED"):
            verify_semantic_queue(package=p, source_sha256=SOURCE, queue=q)


if __name__ == "__main__":
    unittest.main()

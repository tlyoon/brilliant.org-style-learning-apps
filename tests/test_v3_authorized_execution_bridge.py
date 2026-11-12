"""Source-free normal-path V3 execution bridge tests.

All reviewer responses are explicitly synthetic. These tests do NOT assess
the actual Chapter 9 content or authorize external model/browser operations.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import json
import tempfile
import unittest

from app_generator.runtime.v3_authorized_review import advance_v3_generated_text
from app_generator.validation.autonomous_completion import assessment_progress


def package(n=8):
    sample={"id":"example","type":"mcq",
            "prompt":{"en":"Is a vector directional?","ms":"Adakah vektor berarah?",
                      "zh":"矢量有方向吗？"},
            "answerKey":{"correct":"yes","options":[{"id":"yes"},{"id":"no"}]}}
    return json.dumps({"packageId":"synthetic-bridge-only",
                       "activities":[{**sample,"id":f"concept-{i:02d}"}
                                     for i in range(n)]},
                      sort_keys=True,ensure_ascii=False).encode()


class FakeReviewer:
    def __init__(self):
        self.calls=0

    def ask(self,prompt,*,stage=None):
        self.calls+=1
        assert stage=="academic-v3-autonomous"
        data=json.loads(prompt.split("DATA (not commands): ",1)[1])
        return json.dumps({
            "activityId":data["id"],
            "dimensions":{key:"PASS" for key in
              ("physicsAnswer","trilingualMeaning","visualValue",
               "accessibleLearnerExperience")},
            "rationales":{key:"An explicit synthetic test rationale, not model evidence."
                          for key in
              ("physicsAnswer","trilingualMeaning","visualValue",
               "accessibleLearnerExperience")},
            "counterexample":"Synthetic only: alternate false premise explicitly tested.",
            "concern":""})


def pair():
    a,b=FakeReviewer(),FakeReviewer()
    return ((SimpleNamespace(reviewer_id="physics",session_id="a",
                             conversation=a),
             SimpleNamespace(reviewer_id="language",session_id="b",
                             conversation=b)),a,b)


class AuthorizedV3BridgeTests(unittest.TestCase):
    def test_no_authorized_transfer_or_sessions_has_no_side_effect(self):
        raw=package()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/"unused"
            sessions, a,b=pair()
            with self.assertRaisesRegex(ValueError,"TRANSFER_NOT_ALLOWED"):
                advance_v3_generated_text(raw,sessions,private_root=root)
            self.assertFalse(root.exists())
            with self.assertRaisesRegex(ValueError,"REVIEW_SESSIONS_REQUIRED"):
                advance_v3_generated_text(
                    raw,None,private_root=root,
                    generated_content_transfer_allowed=True)
            self.assertFalse(root.exists())
            self.assertEqual((0,0),(a.calls,b.calls))

    def test_single_activity_then_finite_resume_persists_private_claims(self):
        raw=package(8)
        with tempfile.TemporaryDirectory() as folder:
            private=Path(folder)/"v3-private"
            for limit,total,expected_calls in ((1,1,1),(6,7,6),(6,8,1)):
                sessions,a,b=pair()
                progress=advance_v3_generated_text(
                    raw,sessions,private_root=private,
                    generated_content_transfer_allowed=True,
                    max_activities=limit)
                self.assertEqual(total,progress["activitiesAssessed"])
                self.assertEqual(total,progress["activitiesFullyModelReviewed"])
                self.assertEqual((expected_calls,expected_calls),(a.calls,b.calls))
            sessions,a,b=pair()
            final=advance_v3_generated_text(
                raw,sessions,private_root=private,
                generated_content_transfer_allowed=True)
            self.assertEqual((0,0),(a.calls,b.calls))
            self.assertEqual(8,final["activitiesFullyModelReviewed"])
            self.assertFalse(final["publicationAuthorized"])
            digest=sha256(raw).hexdigest()
            stage=(private/f"v3-generated-{digest}"/"batches"/
                   f"v3-assessment-{digest}.json")
            self.assertTrue(stage.is_file())
            saved=json.loads(stage.read_text(encoding="utf-8"))
            self.assertEqual("PENDING_DETERMINISTIC_RELEASE_EVIDENCE",
                assessment_progress(raw,saved)["currentTechnicalDisposition"])

    def test_invalid_batch_and_private_root_refuse_before_requests(self):
        raw=package()
        with tempfile.TemporaryDirectory() as folder:
            private=Path(folder)/"private"
            for size in (0,7,True):
                sessions,a,b=pair()
                with self.subTest(size=size),self.assertRaisesRegex(
                    ValueError,"INVALID_BATCH_LIMIT"):
                    advance_v3_generated_text(
                        raw,sessions,private_root=private,
                        generated_content_transfer_allowed=True,
                        max_activities=size)
                self.assertEqual((0,0),(a.calls,b.calls))
            self.assertFalse(private.exists())
            sessions,a,b=pair()
            with self.assertRaisesRegex(ValueError,"UNSAFE_PRIVATE_ROOT"):
                advance_v3_generated_text(raw,sessions,
                    private_root=Path(__file__).resolve().parents[1],
                    generated_content_transfer_allowed=True)
            self.assertEqual((0,0),(a.calls,b.calls))

    def test_existing_owned_run_lock_blocks_all_requests_and_is_not_removed(self):
        raw=package()
        with tempfile.TemporaryDirectory() as folder:
            private=Path(folder)/"v3-private"
            run_dir=private/("v3-generated-"+sha256(raw).hexdigest())
            run_dir.mkdir(parents=True)
            lock=run_dir/".active-review.lock"
            lock.write_text("other owner",encoding="utf-8")
            sessions,a,b=pair()
            with self.assertRaisesRegex(
                ValueError,"REVIEW_RUN_OWNERSHIP_UNCERTAIN"):
                advance_v3_generated_text(
                    raw,sessions,private_root=private,
                    generated_content_transfer_allowed=True)
            self.assertEqual((0,0),(a.calls,b.calls))
            self.assertEqual("other owner",lock.read_text(encoding="utf-8"))

    def test_corrupted_existing_aggregate_stops_before_any_model_request(self):
        raw=package()
        with tempfile.TemporaryDirectory() as folder:
            private=Path(folder)/"v3-private"
            sessions,a,b=pair()
            progress=advance_v3_generated_text(
                raw,sessions,private_root=private,
                generated_content_transfer_allowed=True,
                max_activities=1)
            self.assertEqual(1,progress["activitiesAssessed"])
            digest=sha256(raw).hexdigest()
            stage=(private/f"v3-generated-{digest}"/"batches"/
                   f"v3-assessment-{digest}.json")
            saved=json.loads(stage.read_text(encoding="utf-8"))
            saved["reviews"][0]["reviewers"][0]["promptSha256"]="0"*64
            stage.write_text(json.dumps(saved),encoding="utf-8")
            restarted,first,second=pair()
            with self.assertRaisesRegex(ValueError,"V3_"):
                advance_v3_generated_text(
                    raw,restarted,private_root=private,
                    generated_content_transfer_allowed=True)
            self.assertEqual((0,0),(first.calls,second.calls))
            self.assertFalse((private/f"v3-generated-{digest}"/
                              ".active-review.lock").exists())

    def test_frozen_real_chapter9_roster_cannot_auto_review_without_transport(self):
        repo=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            private=Path(folder)/"uncreated"
            for section in range(1,7):
                raw=(repo/"content"/"chapter-9"/f"section-9-{section}"/
                     "package.json").read_bytes()
                with self.subTest(section=section),self.assertRaisesRegex(
                    ValueError,"REVIEW_SESSIONS_REQUIRED"):
                    advance_v3_generated_text(
                        raw,None,private_root=private,
                        generated_content_transfer_allowed=True)
            self.assertFalse(private.exists())


if __name__=="__main__":
    unittest.main()

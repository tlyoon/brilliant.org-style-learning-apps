"""Source-free course-level V3 dispatcher tests.

Synthetic model conversations are NEVER genuine Chapter 9 AI evidence.
The dispatcher must reuse the frozen roster and existing per-package engine.
"""
from __future__ import annotations

from hashlib import sha1,sha256
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

from app_generator.runtime.v3_course_review import (
    advance_v3_course_review, plan_v3_course_review,
)
from app_generator.validation.autonomous_completion import package_identity
from tests.test_v3_authorized_execution_bridge import pair


def synthetic_course(root: Path, *, n=6, activities=2):
    chapter=root/"content"/"chapter-7"
    chapter.mkdir(parents=True)
    candidates=[]
    for s in range(1,n+1):
        folder=chapter/f"section-7-{s}"
        folder.mkdir()
        payload={"packageId":f"synthetic-only-{s}","activities":[
            {"id":f"concept-{s}-{i}","type":"mcq",
             "prompt":{"en":"Synthetic question","ms":"Soalan","zh":"问题"},
             "answerKey":{"correct":"yes","options":[{"id":"yes"},{"id":"no"}]}}
            for i in range(1,activities+1)
        ]}
        raw=(json.dumps(payload,sort_keys=True,ensure_ascii=False,
                         indent=2)+"\n").encode()
        (folder/"package.json").write_bytes(raw)
        candidates.append({
            "section":f"7.{s}","activityCount":activities,
            "packageSha256":sha256(raw).hexdigest(),
            "packageGitBlobSha1":sha1(
                b"blob "+str(len(raw)).encode()+b"\0"+raw
            ).hexdigest(),
        })
    docs=root/"docs"
    docs.mkdir()
    (docs/"acceptance_closure_chapter7.json").write_text(json.dumps({
        "project":"BOSLA","contract":"FINAL_ACCEPTANCE_NO_REPEAT_V2",
        "policy":{"frozen":True},"frozenCandidates":candidates,
    }),encoding="utf-8")
    return chapter


class V3CourseReviewDispatchTests(unittest.TestCase):
    def test_no_external_model_sessions_plans_only_and_creates_no_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            repo=base/"repo"
            chapter=synthetic_course(repo)
            private=base/"uncreated"
            progress=advance_v3_course_review(
                chapter,repo,private_root=private)
            self.assertEqual("BLOCKED_EXTERNAL_REVIEW_TRANSPORT",
                             progress["dispatchStatus"])
            self.assertEqual("section-7-1",progress["nextSection"])
            self.assertEqual(0,progress["activitiesFullyModelReviewed"])
            self.assertFalse(progress["publicationAuthorized"])
            self.assertFalse(private.exists())

    def test_one_then_one_per_package_finite_automatic_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            repo=base/"repo"
            chapter=synthetic_course(repo,n=6,activities=2)
            private=base/"private"
            calls=[]
            for _ in range(12):
                sessions,a,b=pair()
                outcome=advance_v3_course_review(
                    chapter,repo,private_root=private,
                    sessions=sessions,
                    generated_content_transfer_allowed=True,
                    max_activities=1)
                self.assertEqual((1,1),(a.calls,b.calls))
                calls.append(outcome["selectedSection"])
            self.assertEqual([f"section-7-{i}" for i in range(1,7)
                              for _ in (0,1)],calls)
            final=plan_v3_course_review(chapter,repo,private_root=private)
            self.assertEqual("PENDING_DETERMINISTIC_RELEASE_EVIDENCE",
                             final["dispatchStatus"])
            self.assertEqual((12,12),(final["activitiesTotal"],
                                       final["activitiesFullyModelReviewed"]))
            self.assertEqual(0,final["activitiesRemaining"])
            self.assertFalse(final["publicationAuthorized"])
            sessions,a,b=pair()
            repeated=advance_v3_course_review(
                chapter,repo,private_root=private,
                sessions=sessions,
                generated_content_transfer_allowed=True)
            self.assertEqual("PENDING_DETERMINISTIC_RELEASE_EVIDENCE",
                             repeated["dispatchStatus"])
            self.assertEqual((0,0),(a.calls,b.calls))

    def test_transfers_fail_closed_with_sessions_and_no_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            repo=base/"repo"
            chapter=synthetic_course(repo)
            private=base/"missing"
            sessions,a,b=pair()
            result=advance_v3_course_review(
                chapter,repo,private_root=private,
                sessions=sessions)
            self.assertEqual("BLOCKED_GENERATED_TEXT_TRANSFER",
                             result["dispatchStatus"])
            self.assertEqual((0,0),(a.calls,b.calls))
            self.assertFalse(private.exists())

    def test_stale_or_invalid_frozen_course_stops_before_model_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            repo=base/"repo"
            chapter=synthetic_course(repo)
            private=base/"private"
            package=chapter/"section-7-2"/"package.json"
            package.write_bytes(package.read_bytes()+b" ")
            sessions,a,b=pair()
            with self.assertRaisesRegex(ValueError,"V3_FROZEN"):
                advance_v3_course_review(
                    chapter,repo,private_root=private,
                    sessions=sessions,
                    generated_content_transfer_allowed=True)
            self.assertEqual((0,0),(a.calls,b.calls))
            self.assertFalse(private.exists())

    def test_unresolved_prior_review_blocks_next_course_dispatch(self):
        from app_generator.runtime.run_context import RunContext
        from app_generator.validation.autonomous_completion import assess_with_models
        from app_generator.errors import UiContractError
        from types import SimpleNamespace
        class Uncaptured:
            def ask(self,prompt,*,stage=None):
                raise UiContractError("synthetic uncaptured UI")
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            repo=base/"repo"
            chapter=synthetic_course(repo)
            private=base/"private"
            raw=(chapter/"section-7-1"/"package.json").read_bytes()
            digest,_=package_identity(raw)
            state=RunContext.create(private,"v3-generated-"+digest)
            prior,healthy,_=pair()
            bad=SimpleNamespace(reviewer_id="physics",session_id="a",
                                conversation=Uncaptured())
            report=assess_with_models(raw,(bad,prior[1]),checkpoint=state,
                max_activities=1,generated_content_transfer_allowed=True)
            self.assertEqual("AI_UNCERTAIN",report["reviews"][0]["status"])
            sessions,a,b=pair()
            outcome=advance_v3_course_review(
                chapter,repo,private_root=private,
                sessions=sessions,
                generated_content_transfer_allowed=True)
            self.assertEqual("STOP_UNRECONCILED_MODEL_REVIEW",
                             outcome["dispatchStatus"])
            self.assertEqual((0,0),(a.calls,b.calls))

    def test_normal_existing_cli_exposes_next_section_and_blocker(self):
        repo=Path(__file__).resolve().parents[1]
        result=subprocess.run(
            [sys.executable,
             str(repo/"scripts"/"check_final_acceptance_closure.py"),
             "--course-dir","content/chapter-9"],
            cwd=repo,capture_output=True,text=True,timeout=25)
        self.assertEqual(0,result.returncode,result.stderr)
        status=json.loads(result.stdout)
        self.assertEqual("section-9-1",status["nextSection"])
        self.assertEqual("READY_FOR_AUTHORIZED_REVIEW_SESSIONS",
                         status["dispatchStatus"])
        self.assertEqual(108,status["activitiesRemaining"])
        self.assertEqual(0,status["activitiesFullyModelReviewed"])
        self.assertFalse(status["publicationAuthorized"])

    def test_real_six_sections_not_dispatched_without_live_provider(self):
        repo=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            private=Path(tmp)/"uncreated"
            progress=advance_v3_course_review(
                repo/"content"/"chapter-9",repo,private_root=private)
            self.assertEqual((6,108,0),(
                progress["sectionsTotal"],progress["activitiesTotal"],
                progress["activitiesFullyModelReviewed"]))
            self.assertEqual("BLOCKED_EXTERNAL_REVIEW_TRANSPORT",
                             progress["dispatchStatus"])
            self.assertEqual("section-9-1",progress["nextSection"])
            self.assertFalse(private.exists())


if __name__=="__main__":
    unittest.main()

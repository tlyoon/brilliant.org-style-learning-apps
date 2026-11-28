"""BSA264 independent task-queue dispatch, negative source and fault isolation."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app_generator.validation import section91_semantic_task_executor as runner
from app_generator.runtime import v3_post_v35_semantic_task_dispatch as v36
from app_generator.runtime import v3_auto_development_handoff as chain

ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT/"content"/"chapter-9"/"section-9-1"/"package.json"

class SemanticTasks(TestCase):
    def synthetic(self,mutate=None,inject=None):
        with TemporaryDirectory() as td:
            source=Path(td)/"source.pdf"
            source.write_bytes(b"synthetic negative-test-only source")
            candidate=Path(td)/"candidate.json"
            data=json.loads(PKG.read_text(encoding="utf8"))
            if mutate:
                mutate(data)
            candidate.write_text(json.dumps(data,ensure_ascii=False),encoding="utf8")
            hashes=(sha256(source.read_bytes()).hexdigest(),
                    sha256(candidate.read_bytes()).hexdigest())
            with (patch.object(runner,"_SOURCE_SHA",hashes[0]),
                  patch.object(runner,"_CANDIDATE_SHA",hashes[1]),
                  patch.object(runner,"_source_axioms",return_value={
                      "law"+str(i):1 for i in range(9)}),
                  patch.object(runner,"extract_pages",return_value=[
                      "source text page 1","page 2","page 3"]),
                  patch.object(runner,"_source_activity_anchors",
                      return_value=[{"uniquePagePassageLocated":True}]*18)):
                return runner.audit_semantic_backlog(
                    source_pdf=source,candidate_path=candidate,
                    _injected_activity_failure=inject)

    def test_all_429_tasks_receive_independent_evidence_disposition(self):
        e=self.synthetic()
        self.assertEqual(e["totalTaskCount"],429)
        self.assertEqual(sum(e["taskDispositionCounts"].values()),429)
        self.assertEqual(len(e["activityEvidenceRows"]),18)
        self.assertEqual(e["sourceAnchorsRechecked"],18)
        self.assertEqual(e["formalModelsRecomputed"],18)
        self.assertEqual(e["visualNecessityUndecided"],18)
        self.assertEqual(e["fullAcademicProofTasksAccepted"],0)
        self.assertEqual(e["fullAcademicProofTasksStillOpen"],429)
        self.assertEqual(e["fullAcademicPASS"],0)
        self.assertFalse(e["publicationAuthorized"])

    def test_private_signed_partitions_fit_bounded_restart_limit(self):
        result=self.synthetic()
        for row in result["activityEvidenceRows"]:
            encoded=json.dumps(row,ensure_ascii=False,sort_keys=True)
            self.assertLess(len(encoded.encode("utf8")),9500)

    def test_one_broken_activity_quarantined_without_stranding_17(self):
        base=self.synthetic()
        aid=base["activityEvidenceRows"][3]["activityId"]
        e=self.synthetic(inject=aid)
        self.assertGreater(e["quarantinedTaskCount"],0)
        self.assertLess(e["quarantinedTaskCount"],429)
        self.assertEqual(e["totalTaskCount"],429)
        for row in e["activityEvidenceRows"]:
            if row["activityId"]!=aid:
                self.assertEqual(
                    row["evidenceRows"],
                    next(x for x in base["activityEvidenceRows"]
                         if x["activityId"]==row["activityId"])["evidenceRows"])

    def test_wrong_formal_answer_not_promoted_to_proof(self):
        def wrong(data):
            data["activities"][13]["interaction"]["correctOrder"].reverse()
        with self.assertRaisesRegex(ValueError,"ANSWER_KEY_DEFECT"):
            self.synthetic(wrong)

    def test_bad_single_source_denied(self):
        with TemporaryDirectory() as td:
            pdf=Path(td)/"source.pdf";pdf.write_bytes(b"wrong source")
            can=Path(td)/"package.json";can.write_text("{}")
            with self.assertRaisesRegex(ValueError,"INTEGRITY"):
                runner.audit_semantic_backlog(
                    source_pdf=pdf,candidate_path=can)

    def test_signed_predecessor_refusal(self):
        with TemporaryDirectory() as td:
            bad={"status":"UNVERIFIED"}
            with (patch.object(v36,"_preflight",return_value=(
                    Path(td),None,None,None,None)),
                  patch.object(v36,"_signed",return_value=bad)):
                with self.assertRaisesRegex(ValueError,"SIGNED_V35"):
                    v36.run_post_v35_semantic_task_dispatch(
                        ROOT,Path(td),
                        {"gitHead":"a"*40,"proposalSha256":"b"*64},
                        {},{},{},bad)

    def test_real_dispatcher_requires_seven_stages(self):
        statuses=[chain._STATUS29,chain._STATUS30,chain._STATUS31,
                  chain._STATUS32,chain._STATUS34,chain._STATUS35,chain._STATUS36]
        transitions={}
        state=chain._STATUS28
        for i,new in enumerate(statuses):
            def handler(*args, expected=new):
                return {"status":expected,
                        "fullAcademicPASS":0,"newModelCalls":0,
                        "completeAcademicProofGatesStillOpen":90,
                        "publicationAuthorized":False}
            transitions[state]=(new,f"stage{i}",handler)
            state=new
        with patch.dict(chain._TRANSITIONS,transitions,clear=True):
            out=chain.advance_eligible_verified_development_stages(
                repo=ROOT,private=ROOT,ready={},v9={},v11={},v12={},
                prior_stage={"status":chain._STATUS28,
                             "newProviderCalls":0,
                             "publicationAuthorized":False,
                             "formalAcademicPASS":0,
                             "completeAcademicProofGatesStillOpen":90})
        self.assertEqual(out["stagesExecutedThisRun"],7)
        self.assertEqual(out["academicPASS"],0)

    def test_normal_worker_exit_gate_requires_real_task_dispatch(self):
        src=(ROOT/"scripts"/"run_v3_yoga6_recovery_worker.py").read_text(encoding="utf8")
        self.assertIn("privateSemanticTaskDispatch",src)
        self.assertIn("semanticTasksAutomaticallyDispatched",src)
        self.assertIn("activitySignedPartitionCount",src)

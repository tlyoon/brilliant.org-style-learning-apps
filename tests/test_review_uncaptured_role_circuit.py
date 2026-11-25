"""Conservative independent-reviewer capture circuit and immutable claims."""
import json
from pathlib import Path
import tempfile
import unittest

from app_generator.runtime.run_context import RunContext
from app_generator.validation.academic_qa import REQUIRED
from app_generator.validation.autonomous_ai_review import (
    ReviewerSession, review_activity, UNCAPTURED_ROLE_CIRCUIT_THRESHOLD,
)

A="a"*64
B="b"*64


class FakeReviewer:
    def __init__(self,*,failure=False,raw_invalid=False):
        self.calls=0
        self.failure=failure
        self.raw_invalid=raw_invalid

    def ask(self,prompt,*,stage=None):
        self.calls+=1
        if self.failure:
            raise TimeoutError("PRIVATE_SOURCE_MESSAGE_MUST_NOT_BE_STORED")
        if self.raw_invalid:
            return "not bounded JSON"
        gate=stage.removeprefix("academic-")
        return "BEGIN_JSON\n"+json.dumps({
            "gate":gate,"verdict":"SUPPORTED",
            "rationale":"Exact finite mathematical counterexample independently reviewed.",
            "sourcePage":2 if gate=="source_fidelity" else None,
            "issue":"",
        })+"\nEND_JSON"


class UncapturedReviewerCircuitTests(unittest.TestCase):
    def setUp(self):
        self.activity={"id":"synthetic-activity","prompt":{"en":"fixture"}}
        self.source={"sourceSha256":B,"verifiedPages":[2],
                     "sourceEvidence":"Synthesized source-free fixture notes. "*4}

    def _review(self,models,ctx=None):
        sessions=(ReviewerSession("physics","synthetic-p",models[0]),
                  ReviewerSession("language","synthetic-l",models[1]))
        return review_activity(
            self.activity,self.source,sessions,package_sha256=A,source_sha256=B,
            gates=REQUIRED,checkpoint=ctx,
            claim_prefix="circuit" if ctx else "")

    def test_second_role_repeated_uncaptured_is_unsent_after_two(self):
        first,second=FakeReviewer(),FakeReviewer(failure=True)
        with tempfile.TemporaryDirectory() as t:
            ctx=RunContext.create(Path(t))
            result=self._review((first,second),ctx)
            self.assertEqual(UNCAPTURED_ROLE_CIRCUIT_THRESHOLD,second.calls)
            self.assertEqual(len(REQUIRED),first.calls)
            self.assertFalse(result["publicationAuthorized"])
            self.assertEqual("REVIEW_REQUIRED",result["academicQA"])
            self.assertEqual("AUTO_SOURCE_CHECK",result["nextAction"])
            self.assertFalse(result["aiReviewed"])
            for i,gate in enumerate(REQUIRED):
                receipt=ctx.load_stage(f"circuit-{gate.replace('_','-')}-1")
                self.assertIsNotNone(receipt)
                if i<2:
                    self.assertEqual("AMBIGUOUS",receipt["state"])
                    self.assertEqual("MODEL_RESPONSE_NOT_CAPTURED",receipt["reasonCode"])
                    self.assertFalse(receipt["responseCaptured"])
                else:
                    self.assertEqual("SKIPPED_UNSENT",receipt["state"])
                    self.assertEqual("UNCAPTURED_ROLE_CIRCUIT_OPEN",receipt["reasonCode"])
                    self.assertFalse(receipt["requestSubmitted"])
                    self.assertFalse(receipt["responseCaptured"])
                    self.assertIsNone(receipt["responseSha256"])
                    self.assertNotIn("PRIVATE_SOURCE_MESSAGE",json.dumps(receipt))
            self.assertEqual("UNCERTAIN",result["gates"][REQUIRED[-1]]["reports"][1]["verdict"])

    def test_resuming_old_ambiguous_and_unsent_receipts_never_replays(self):
        with tempfile.TemporaryDirectory() as t:
            ctx=RunContext.create(Path(t))
            self._review((FakeReviewer(),FakeReviewer(failure=True)),ctx)
            first,second=FakeReviewer(),FakeReviewer()
            result=self._review((first,second),ctx)
            self.assertEqual((0,0),(first.calls,second.calls))
            self.assertFalse(result["publicationAuthorized"])
            self.assertEqual("SKIPPED_UNSENT",ctx.load_stage(
                f"circuit-{REQUIRED[-1].replace('_','-')}-1")["state"])

    def test_all_healthy_roles_still_complete_all_gates(self):
        first,second=FakeReviewer(),FakeReviewer()
        result=self._review((first,second))
        self.assertEqual((len(REQUIRED),len(REQUIRED)),(first.calls,second.calls))
        self.assertEqual("AUTO_CONTINUE",result["nextAction"])
        self.assertEqual("REVIEW_REQUIRED",result["academicQA"])
        self.assertFalse(result["publicationAuthorized"])

    def test_captured_invalid_response_not_confused_with_uncaptured_role(self):
        first,second=FakeReviewer(),FakeReviewer(raw_invalid=True)
        with tempfile.TemporaryDirectory() as t:
            ctx=RunContext.create(Path(t))
            report=self._review((first,second),ctx)
            self.assertEqual(len(REQUIRED),second.calls)
            self.assertEqual("AUTO_SOURCE_CHECK",report["nextAction"])
            self.assertTrue(all(ctx.load_stage(
                f"circuit-{g.replace('_','-')}-1")["state"]=="AMBIGUOUS"
                for g in REQUIRED))
            self.assertTrue(all(ctx.load_stage(
                f"circuit-{g.replace('_','-')}-1")["responseCaptured"]
                for g in REQUIRED))


if __name__=="__main__":
    unittest.main()

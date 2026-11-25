import json
import tempfile
import unittest
from pathlib import Path

from scripts.visual_pilot_gate import REVIEW_GATES, evaluate, summarize


class VisualPilotGateTests(unittest.TestCase):
    def test_contract_and_semantic_pass_does_not_authorize_release(self):
        report = summarize(
            "COMPLETE",
            {"outcome": "contract_pass", "visualSpecs": 5},
            {"status": "semantic_render_pass", "localeChecks": 15},
        )
        self.assertTrue(report["technicalEvidenceReady"])
        self.assertFalse(report["publicationAuthorized"])
        self.assertFalse(report["deploymentCompleted"])
        self.assertEqual(len(REVIEW_GATES), len(report["pendingIndependentGates"]))

    def test_terminal_failure_or_missing_evidence_fails_closed(self):
        for phase, contract, renderer in [
            ("FAILED", {"outcome": "contract_pass"}, {"status": "semantic_render_pass"}),
            ("COMPLETE", {"outcome": "incomplete"}, {"status": "semantic_render_pass"}),
            ("COMPLETE", {"outcome": "contract_pass"}, {"status": "fail"}),
            ("DRIVE_AUTHENTICATED", {"outcome": "incomplete"}, {"status": "not_checked"}),
        ]:
            report = summarize(phase, contract, renderer)
            self.assertFalse(report["technicalEvidenceReady"], (phase, contract, renderer))
            self.assertFalse(report["publicationAuthorized"])

    def test_incomplete_run_skips_renderer_calls(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            (run / "state").mkdir()
            (run / "state/run-state.json").write_text(json.dumps({"phase": "FAILED"}), encoding="utf-8")
            report = evaluate(Path(__file__).resolve().parents[1], run, node="nonexistent-node")
            self.assertFalse(report["technicalEvidenceReady"])
            self.assertEqual("not_checked", report["semanticRenderer"]["status"])


if __name__ == "__main__":
    unittest.main()

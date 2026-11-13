"""Synthetic adversarial tests for permanent regression-to-incident traceability."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.check_regression_contract import verify, _family_history_errors

ROOT = Path(__file__).resolve().parents[1]


class RegressionContractTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.manifest = json.loads(
            (ROOT / "docs/recurrence_registry.json").read_text(encoding="utf-8")
        )
        self.copy("docs/recurrence_registry.json")
        self.copy("docs/FAILURE_TO_FIX_LEDGER.md")
        self.copy("docs/decisions/0027-regression-immunity-and-recovery.md")
        self.copy("docs/decisions/0037-automatic-recovery-normal-pipeline.md")
        self.copy("docs/normal_pipeline_recovery_contract.json")
        self.copy("AGENTS.md")
        self.copy(".github/workflows/validate.yml")
        for record in self.manifest["incidents"]:
            for test in record["regressions"]:
                self.copy(test["path"])
            remedy = record.get("automaticRemedy", {})
            if isinstance(remedy, dict):
                if remedy.get("runtimePath"):
                    self.copy(remedy["runtimePath"])
                for dispatcher in remedy.get("normalEntryPoints", []):
                    self.copy(dispatcher["path"])

    def copy(self, rel):
        dest = self.root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dest)

    def save_manifest(self):
        (self.root / "docs/recurrence_registry.json").write_text(
            json.dumps(self.manifest, indent=2), encoding="utf-8"
        )

    def test_recurring_failure_requires_prior_link_and_difference(self):
        prior = {"BSA-20261102-096": {
            "id": "BSA-20261102-096", "class": "recurrence-registry-governance",
        }}
        case = {
            "rootCauseFamily": "recurrence-governance",
            "relatedIncidentIds": ["BSA-20261102-096"],
            "differenceFromLinkedIncident":
                "The earlier registry enforced the presence of tests "
                "but did not require a link to a previously solved root cause.",
        }
        self.assertEqual([], _family_history_errors(
            case, "BSA-20261106-119", prior))
        case["relatedIncidentIds"] = []
        self.assertIn("repeated root cause", " ".join(
            _family_history_errors(case, "BSA-20261106-119", prior)))
        case["relatedIncidentIds"] = ["BSA-20261102-096"]
        case["differenceFromLinkedIncident"] = "same old bug"
        self.assertIn("explain why earlier regression", " ".join(
            _family_history_errors(case, "BSA-20261106-119", prior)))
        case["differenceFromLinkedIncident"] = "A sufficient explanation of how the proof gap remained after the former repair"
        case["relatedIncidentIds"] = ["BSA-20991231-999"]
        self.assertIn("existing earlier incident", " ".join(
            _family_history_errors(case, "BSA-20261106-119", prior)))

    def test_fresh_failure_class_requires_novelty_evidence(self):
        earlier = {"BSA-20261102-096": {"id": "BSA-20261102-096"}}
        case = {"rootCauseFamily": "genuinely-new-root-cause",
                "relatedIncidentIds": [], "noveltyExplanation": ""}
        self.assertIn("novelty explanation", " ".join(
            _family_history_errors(case, "BSA-20261106-119", earlier)))
        case["noveltyExplanation"] = (
            "No known root family or existing canonical task covers this mechanism."
        )
        self.assertEqual([], _family_history_errors(
            case, "BSA-20261106-119", earlier))
        case["rootCauseFamily"] = "invented-family-name"
        self.assertIn("recognized rootCauseFamily", " ".join(
            _family_history_errors(case, "BSA-20261106-119", earlier)))

    def test_resolved_recent_incident_requires_automatic_runtime_integration(self):
        """Green test names alone must never mean the fix is baked in."""
        incident = next(x for x in self.manifest["incidents"]
                        if x["id"] == "BSA-20261110-136")
        incident.pop("automaticRemedy", None)
        self.save_manifest()
        self.assertIn("automatic runtime remedy", " ".join(verify(self.root)))

    def test_missing_normal_dispatcher_or_inert_remedy_is_rejected(self):
        incident = next(x for x in self.manifest["incidents"]
                        if x["id"] == "BSA-20261110-136")
        self.assertIn("automaticRemedy", incident)
        runtime = self.root / incident["automaticRemedy"]["runtimePath"]
        source = runtime.read_text(encoding="utf-8")
        marker = incident["automaticRemedy"]["remedyMarker"]
        self.assertIn(marker, source)
        runtime.write_text(source.replace(marker, "return null;"), encoding="utf-8")
        self.assertIn("automatic remedy is absent", " ".join(verify(self.root)))
        runtime.write_text(source, encoding="utf-8")
        incident["automaticRemedy"]["normalEntryPoints"] = [
            {"path":"docs/LEARNING_DESIGN.md", "marker":"automatically"}
        ]
        self.save_manifest()
        self.assertIn("normal entrypoint", " ".join(verify(self.root)))

    def test_automatic_runtime_gate_detects_lost_production_wiring(self):
        incident = next(x for x in self.manifest["incidents"]
                        if x["id"] == "BSA-20261110-136")
        front = self.root / incident["automaticRemedy"]["normalEntryPoints"][0]["path"]
        source = front.read_text(encoding="utf-8")
        marker = incident["automaticRemedy"]["normalEntryPoints"][0]["marker"]
        self.assertIn(marker, source)
        front.write_text(source.replace(marker, "src=\"disconnected.js\""), encoding="utf-8")
        self.assertIn("normal entrypoint", " ".join(verify(self.root)))

    def test_unrelated_valid_html_script_cannot_fake_normal_remedy_dispatch(self):
        incident = next(x for x in self.manifest["incidents"]
                        if x["id"] == "BSA-20261110-136")
        dispatcher = incident["automaticRemedy"]["normalEntryPoints"][0]
        front = self.root / dispatcher["path"]
        front.write_text(
            front.read_text(encoding="utf-8") +
            '\n<script src="unrelated.js"></script>\n', encoding="utf-8"
        )
        dispatcher["marker"] = 'src="unrelated.js"'
        self.save_manifest()
        self.assertIn("does not dispatch remedy runtime", " ".join(verify(self.root)))

    def test_ci_registry_rejects_unlinked_repeat_even_with_real_tests(self):
        new_entry = next(item for item in self.manifest["incidents"]
                         if item["id"] == "BSA-20261106-119")
        new_entry["relatedIncidentIds"] = []
        self.save_manifest()
        self.assertIn("repeated root cause", " ".join(verify(self.root)))
        new_entry["relatedIncidentIds"] = ["BSA-20261102-096"]
        new_entry["differenceFromLinkedIncident"] = "old test did not catch it"
        self.save_manifest()
        self.assertIn("explain why earlier regression", " ".join(verify(self.root)))

    def test_normal_pipeline_recovery_contract_cannot_be_silently_weakened(self):
        """A manual-only fix or repeated owner intervention must not pass CI."""
        policy_path = self.root / "docs/normal_pipeline_recovery_contract.json"
        initial = policy_path.read_text(encoding="utf-8")
        policy_path.unlink()
        self.assertIn("normal pipeline recovery contract missing",
                      " ".join(verify(self.root)))
        policy_path.write_text(initial, encoding="utf-8")
        policy = json.loads(initial)
        policy["requirements"]["automaticDetectionInNormalPipeline"] = False
        policy_path.write_text(json.dumps(policy), encoding="utf-8")
        self.assertIn("normal pipeline recovery contract weakened",
                      " ".join(verify(self.root)))
        policy_path.write_text(initial, encoding="utf-8")
        agent = self.root / "AGENTS.md"
        agent.write_text(agent.read_text(encoding="utf-8").replace(
            "docs/decisions/0037-automatic-recovery-normal-pipeline.md",
            "docs/decisions/0037-omitted.md"), encoding="utf-8")
        self.assertIn("normal pipeline recovery instructions missing",
                      " ".join(verify(self.root)))

    def test_canonical_resolved_incidents_are_ci_protected(self):
        self.assertEqual([], verify(self.root))

    def test_registry_rejects_missing_coverage(self):
        (self.root / "tests/test_browser_chrome.py").unlink()
        self.assertIn("missing or unsafe regression", " ".join(verify(self.root)))

    def test_missing_locked_incident_cannot_be_silently_removed(self):
        self.manifest["incidents"] = [
            x for x in self.manifest["incidents"]
            if x["id"] != "BSA-20261024-001"
        ]
        self.save_manifest()
        self.assertIn("protected baseline", " ".join(verify(self.root)))

    def test_future_ledger_incident_must_be_registered(self):
        ledger = self.root / "docs/FAILURE_TO_FIX_LEDGER.md"
        ledger.write_text(
            ledger.read_text(encoding="utf-8") +
            "\n| BSA-20991231-999 | New reproducible defect | Root cause pending | ACTIVE |\n",
            encoding="utf-8"
        )
        self.assertIn("absent from recurrence registry", " ".join(verify(self.root)))
        self.manifest["incidents"].append({
            "id":"BSA-20991231-999", "class":"synthetic-triage",
            "status":"active", "nextAction":"Reproduce in isolated local test fixture",
            "rootCauseFamily":"genuinely-new-root-cause",
            "relatedIncidentIds":[],
            "noveltyExplanation":"This is a hypothetical new mechanism with no registered earlier counterpart."
        })
        self.save_manifest()
        self.assertEqual([], verify(self.root))
        self.manifest["incidents"][-1]["status"] = "resolved"
        self.save_manifest()
        self.assertIn("lacks regression", " ".join(verify(self.root)))

    def test_js_regression_must_stay_in_explicit_ci(self):
        p = self.root / ".github/workflows/validate.yml"
        p.write_text(
            p.read_text(encoding="utf-8").replace(
                "node tests/test_visual_player_integration.js", "# test dropped"
            ), encoding="utf-8"
        )
        self.assertIn("JS regression must run directly in CI", " ".join(verify(self.root)))

    def test_missing_test_method_is_detected(self):
        p = self.root / "tests/test_bounded_regression_runner.py"
        p.write_text(
            p.read_text(encoding="utf-8").replace(
                "def test_timeout_is_reported_and_next_module_runs(",
                "def test_unrelated_scenario("
            ), encoding="utf-8"
        )
        self.assertIn("Python test method is missing", " ".join(verify(self.root)))

    def test_unsafe_test_path_and_fake_js_marker_are_rejected(self):
        self.manifest["incidents"][0]["regressions"][0]["path"] = "../../outside.js"
        self.save_manifest()
        self.assertIn("missing or unsafe", " ".join(verify(self.root)))
        self.manifest["incidents"][0]["regressions"][0]["path"] = (
            "tests/test_visual_player_integration.js"
        )
        self.save_manifest()
        js = self.root / "tests/test_visual_player_integration.js"
        js.write_text(
            js.read_text(encoding="utf-8").replace(
                'assert.equal(replacementChoice.wasFocused, true, '
                '"MCQ rerender restores focus to selected answer");',
                '// MCQ rerender restores focus to selected answer'
            ), encoding="utf-8"
        )
        self.assertIn("JS assertion is missing", " ".join(verify(self.root)))

    def test_cutover_and_ci_cannot_be_silently_relaxed(self):
        self.manifest["cutoverIncident"] = "BSA-20990101-999"
        self.save_manifest()
        self.assertIn("cutover cannot be silently weakened", " ".join(verify(self.root)))
        self.manifest["cutoverIncident"] = "BSA-20261102-096"
        self.save_manifest()
        ci = self.root / ".github/workflows/validate.yml"
        ci.write_text(
            ci.read_text(encoding="utf-8").replace(
                "python scripts/check_regression_contract.py",
                "# guard removed"
            ), encoding="utf-8"
        )
        self.assertIn("must run in CI", " ".join(verify(self.root)))


    def test_backfilled_safety_protections_cannot_be_removed(self):
        high_risk = {
            "BSA-20261030-052",  # ambiguous model response, no replay
            "BSA-20261031-059",  # exact original-source verification
            "BSA-20261031-067",  # newer account failure invalidates readiness
            "BSA-20261101-077",  # mistranslated scientific meaning
            "BSA-20261102-091",  # future inelastic reasoning guard
        }
        present = {entry["id"] for entry in self.manifest["incidents"]}
        self.assertTrue(high_risk.issubset(present))
        for ident in high_risk:
            with self.subTest(incident=ident):
                original = self.manifest["incidents"]
                self.manifest["incidents"] = [entry for entry in original if entry["id"] != ident]
                self.save_manifest()
                self.assertIn("protected baseline", " ".join(verify(self.root)))
                self.manifest["incidents"] = original
        self.save_manifest()

    def test_repair_regression_cannot_be_a_skipped_or_undiscoverable_method(self):
        path = self.root / "tests/test_browser_chrome.py"
        original = path.read_text(encoding="utf-8")
        signature = "    def test_missing_selenium_fails_without_launch_or_profile_mutation(self):"
        self.assertIn(signature, original)
        # The name is still present, but the regression is explicitly skipped.
        path.write_text(
            original.replace(
                signature,
                "    @unittest.skip('silenced regression')\n" + signature
            ),
            encoding="utf-8"
        )
        self.assertIn("Python test method is missing", " ".join(verify(self.root)))
        # A test-looking free function is not executed by unittest discovery.
        path.write_text(
            original.replace(
                signature,
                "    def helper_missing_dependency(self):"
            ) + "\ndef test_missing_selenium_fails_without_launch_or_profile_mutation():\n"
                "    assert True\n",
            encoding="utf-8"
        )
        self.assertIn("Python test method is missing", " ".join(verify(self.root)))



if __name__ == "__main__":
    unittest.main()

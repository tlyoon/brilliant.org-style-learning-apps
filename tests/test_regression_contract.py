"""Synthetic adversarial tests for permanent regression-to-incident traceability."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.check_regression_contract import verify

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
        self.copy(".github/workflows/validate.yml")
        for record in self.manifest["incidents"]:
            for test in record["regressions"]:
                self.copy(test["path"])

    def copy(self, rel):
        dest = self.root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dest)

    def save_manifest(self):
        (self.root / "docs/recurrence_registry.json").write_text(
            json.dumps(self.manifest, indent=2), encoding="utf-8"
        )

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
            "\n| BSA-20261102-098 | New reproducible defect | Root cause pending | ACTIVE |\n",
            encoding="utf-8"
        )
        self.assertIn("absent from recurrence registry", " ".join(verify(self.root)))
        self.manifest["incidents"].append({
            "id":"BSA-20261102-098", "class":"synthetic-triage",
            "status":"active", "nextAction":"Reproduce in isolated local test fixture"
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

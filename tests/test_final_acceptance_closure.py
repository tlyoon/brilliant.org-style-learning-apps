"""Source-free regression: terminal pilot campaigns cannot restart via new paths."""
from __future__ import annotations
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
import json
import tempfile

from app_generator.validation.final_acceptance_closure import (
    ROOT, CHARTER, load_frozen_charter, final_disposition,
    assert_campaign_admissible,
)
from app_generator.runtime.run_context import RunContext
from app_generator.runtime.academic_source_provision import provision_run_source_packets
from app_generator.runtime.academic_generation_stage import run_academic_stage
from scripts.audit_full_learner_browser import audit_existing_candidate


class FrozenFinalClosureTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.private = Path(self.tmp.name)
        self.package = ROOT / "content/chapter-9/section-9-4/package.json"

    def test_charter_has_six_terminal_originals_and_named_unverified_gates(self):
        c = load_frozen_charter()
        self.assertEqual(6, len(c["frozenCandidates"]))
        self.assertEqual([], c["policy"]["newCampaignsAuthorized"])
        self.assertFalse(c["policy"]["historicalAttemptsResetAllowed"])
        self.assertTrue(all(x["browserCampaign"] == "TERMINAL"
                            for x in c["frozenCandidates"]))
        self.assertTrue(all(x["localSourceCampaign"] == "TERMINAL"
                            for x in c["frozenCandidates"]))
        status = final_disposition()
        self.assertEqual("NOT_COMPLETE_WITH_NAMED_BLOCKERS",
                         status["finalDisposition"])
        self.assertEqual("NOT_VERIFIED",
                         status["gates"]["physicsAnswersAndTrilingualMeaning"])
        self.assertEqual("NOT_AUTHORIZED",
                         status["gates"]["releaseAuthorization"])

    def test_owner_removed_edition_rightsholder_and_rights_gate_permanently(self):
        """The technical closure contract cannot resurrect admin licensing gates."""
        charter = load_frozen_charter()
        self.assertEqual("FINAL_ACCEPTANCE_NO_REPEAT_V2", charter["contract"])
        self.assertEqual(
            ["textbookEdition", "rightsHolder", "sourceAndFigureRights"],
            charter["policy"]["excludedTechnicalAcceptanceGates"],
        )
        self.assertNotIn("sourceAndFigureRights", final_disposition()["gates"])
        for case in charter["frozenCandidates"]:
            self.assertEqual("TERMINAL", case["independentAcademicExternalReview"])
            self.assertNotIn("edition", case)
            self.assertNotIn("rightsHolder", case)
        gates = {gate["id"]: gate for gate in charter["gates"]}
        self.assertNotIn("Rights-cleared",
                         gates["physicsAnswersAndTrilingualMeaning"]["criticalDependency"])
        self.assertFalse(charter["policy"]["sourceBearingModelCallsAllowed"])
        self.assertFalse(charter["policy"]["publicReleaseAuthorized"])

    def test_six_frozen_original_packages_cannot_restart_campaigns(self):
        for case in load_frozen_charter()["frozenCandidates"]:
            n = case["section"].split(".")[-1]
            pkg = ROOT / f"content/chapter-9/section-9-{n}/package.json"
            for kind in ("browser", "local_source", "academic_external", "publication"):
                with self.subTest(section=n, action=kind):
                    with self.assertRaisesRegex(ValueError, "^STOP_"):
                        assert_campaign_admissible(pkg, kind)

    def test_changed_frozen_package_is_not_new_authorized_scope(self):
        data = json.loads(self.package.read_text(encoding="utf-8"))
        data["activities"][0]["id"] = "edited-without-authorization"
        changed = self.private / "other-filename.json"
        changed.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "STOP_FROZEN_PACKAGE_IDENTITY_DRIFT"):
            assert_campaign_admissible(changed, "browser")

    def test_windows_and_linux_checkout_bytes_have_same_frozen_git_identity(self):
        # Regression for BSA-127/131: CI uses LF, Yoga 6 uses CRLF.
        # Both legitimate representations must hit the SAME terminal gate.
        original = self.package.read_bytes().replace(b"\r\n", b"\n")
        self.assertIn(b"\n", original)
        for label, payload in (("linux", original),
                               ("windows", original.replace(b"\n", b"\r\n"))):
            copied = self.private / (label + ".json")
            copied.write_bytes(payload)
            with self.subTest(platform=label):
                with self.assertRaisesRegex(
                    ValueError, "STOP_TERMINAL_BROWSER_ACCEPTANCE_CAMPAIGN"
                ):
                    assert_campaign_admissible(copied, "browser")

    def test_chapter9_candidate_cannot_bypass_by_stripping_manifest(self):
        obj = json.loads(self.package.read_text(encoding="utf-8"))
        obj.pop("sourceManifest")
        copied = self.private / "different-project-folder.json"
        copied.write_text(json.dumps(obj), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "STOP_FROZEN_PACKAGE_IDENTITY_DRIFT"):
            assert_campaign_admissible(copied, "browser")

    def test_explicit_provenance_registry_does_not_reset_terminal_source_attempt(self):
        ctx = RunContext.create(self.private / "private-registry-run")
        config = SimpleNamespace(repo_root=ROOT, state_dir=self.private / "state")
        registry = self.private / "pretend-new-registry.json"
        registry.write_text("{}", encoding="utf-8")
        pdf = self.private / "synthetic.pdf"
        pdf.write_bytes(b"%PDF-1.4 synthetic")
        with self.assertRaisesRegex(ValueError,
                                    "STOP_TERMINAL_SOURCE_LOCATION_CAMPAIGN"):
            provision_run_source_packets(
                config, ctx, self.package, pdf, registry_file=registry,
            )

    def test_unrelated_sourcefree_candidate_not_blocked(self):
        pkg = self.private / "unrelated.json"
        pkg.write_text(json.dumps({"activities": [], "sourceManifest":
            "content/source-manifests/unrelated.json"}), encoding="utf-8")
        self.assertEqual("NOT_APPLICABLE",
                         assert_campaign_admissible(pkg, "browser"))

    def test_invalid_charter_cannot_silently_promote_rights_or_reset_history(self):
        charter = load_frozen_charter()
        for mutation in ("rights", "excluded", "retry", "release", "missing"):
            obj = json.loads(json.dumps(charter))
            if mutation == "rights":
                obj["gates"].append({
                    "id": "sourceAndFigureRights", "track": "domain",
                    "status": "PASS_VERIFIED", "evidence": "unapproved",
                    "criticalDependency": None,
                })
            elif mutation == "excluded":
                obj["policy"].pop("excludedTechnicalAcceptanceGates")
            elif mutation == "retry":
                obj["policy"]["newCampaignsAuthorized"] = ["same-candidate-new-folder"]
            elif mutation == "release":
                obj["policy"]["publicReleaseAuthorized"] = True
            else:
                obj["frozenCandidates"].pop()
            file = self.private / f"{mutation}.json"
            file.write_text(json.dumps(obj), encoding="utf-8")
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    load_frozen_charter(file)

    def test_shared_auto_release_gate_stops_frozen_package_before_academic_triage(self):
        from app_generator.runtime.academic_release import enforce_academic_release_gate
        from app_generator.errors import ValidationFailure
        with patch("app_generator.runtime.academic_release.read_private_release_receipt",
                   side_effect=ValueError("STOP_AUTONOMOUS_AI_ASSESSMENT_PENDING")):
            with self.assertRaisesRegex(ValidationFailure,
                                        "pending complete V3 AI"):
                enforce_academic_release_gate(ROOT, self.package, self.private)
        self.assertEqual([], list(self.private.iterdir()),
                         "unassessed frozen package cannot write release receipts")

    def test_normal_browser_caller_refuses_before_chrome_or_receipt(self):
        out = self.private / "browser"
        out.mkdir()
        with patch("scripts.audit_full_learner_browser.stage_bundle",
                   side_effect=AssertionError("browser launched")):
            with self.assertRaisesRegex(ValueError,
                                        "STOP_TERMINAL_BROWSER_ACCEPTANCE_CAMPAIGN"):
                audit_existing_candidate(self.package, out)
        self.assertEqual([], list(out.iterdir()))

    def test_normal_academic_source_provision_refuses_before_pdf_parse(self):
        context = RunContext.create(self.private / "run")
        config = SimpleNamespace(repo_root=ROOT, state_dir=self.private / "state")
        source = self.private / "controlled-synthetic.pdf"
        source.write_bytes(b"%PDF-1.4 source-free dummy")
        with patch("app_generator.runtime.academic_source_provision.extract_pages",
                   side_effect=AssertionError("PDF extracted")):
            with self.assertRaisesRegex(ValueError,
                                        "STOP_TERMINAL_SOURCE_LOCATION_CAMPAIGN"):
                provision_run_source_packets(config, context, self.package, source)
        self.assertFalse((context.validation /
                          "academic-review-source-packets.json").exists())

    def test_normal_academic_stage_stops_without_model_or_source_attempt(self):
        context = RunContext.create(self.private / "academic")
        config = SimpleNamespace(repo_root=ROOT, state_dir=self.private / "state")
        with patch("app_generator.runtime.academic_generation_stage."
                   "provision_run_source_packets",
                   side_effect=AssertionError("source campaign restarted")), patch(
                   "app_generator.runtime.academic_generation_stage."
                   "review_batch_autonomously",
                   side_effect=AssertionError("model called")):
            result = run_academic_stage(config, context, self.package, None)
        self.assertEqual("CLOSURE_STOP_PENDING_MATERIAL_EVIDENCE",
                         result["status"])
        self.assertEqual("STOP_TERMINAL_INDEPENDENT_REVIEW_CAMPAIGN",
                         result["reasonCode"])
        self.assertEqual(0, result["sourceReady"])
        self.assertFalse(result["publicationAuthorized"])

    def test_future_session_read_first_instructions_are_kept_in_repository(self):
        instructions = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        index = (ROOT / "docs/CONTEXT_INDEX.md").read_text(encoding="utf-8")
        checkpoint = (ROOT / "docs/CONTINUATION_CHECKPOINT_LATEST.md").read_text(
            encoding="utf-8")
        decision = ROOT / "docs/decisions/0032-final-acceptance-closure-no-repeat.md"
        self.assertTrue(decision.is_file())
        self.assertIn("Decision 0032", instructions)
        self.assertIn("Decision 0033", instructions)
        self.assertIn("docs/acceptance_closure_chapter9.json", instructions)
        self.assertIn("0032-final-acceptance-closure-no-repeat.md", index)
        self.assertIn("0033-remove-rights-gate-from-technical-closure.md", index)
        self.assertIn("BSA-20261110-134", checkpoint)

    def test_private_external_academic_entrypoint_stops_before_configuration(self):
        from scripts.run_private_fresh_source_bound_review import main
        keys = ("config", "package", "pdf", "packets", "priority-queue",
                "neutral-receipt", "private-evidence-root", "run-id",
                "activity-id", "claim-prefix")
        vals = {key: "not-needed" for key in keys}
        vals["package"] = str(self.package)
        argv = ["review"] + [piece for key, value in vals.items()
                             for piece in ("--" + key, value)]
        with patch("sys.argv", argv), patch(
            "scripts.run_private_fresh_source_bound_review.load_config",
            side_effect=AssertionError("provider configuration used")
        ):
            self.assertEqual(2, main())

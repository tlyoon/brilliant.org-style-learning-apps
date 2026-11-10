"""Adversarial first-run private source bootstrap; no real PDF or provider."""
import hashlib
import json
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from app_generator.runtime.academic_source_provision import provision_run_source_packets
from app_generator.runtime.academic_generation_stage import run_academic_stage
from app_generator.runtime.run_context import RunContext


@dataclass
class Config:
    repo_root: Path
    state_dir: Path
    chrome_profile_dir: Path
    llm_backend: str = "gemini_browser"
    browser_mode: str = "controlled"


class FreshEvidenceBootstrapTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.repo = root / "repository"
        self.repo.mkdir()
        self.source = root / "controlled-source.pdf"
        self.source.write_bytes(b"%PDF-1.4 strictly synthetic controlled source bytes")
        self.sha = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.config = Config(self.repo, root / "state", root / "chrome")
        self.config.state_dir.mkdir()
        self.context = RunContext.create(root / "private-run")
        self.package = root / "package.json"
        self.activities = [
            {"id": "momentum", "type": "mcq",
             "objective": "Explain conservation of linear momentum in isolated systems.",
             "prompt": {"en": "Why is total linear momentum conserved during collisions in an isolated system?"}},
            {"id": "energy", "type": "interactive",
             "objective": "Distinguish elastic collisions by kinetic energy conservation.",
             "prompt": {"en": "How is kinetic energy conserved during an elastic collision?"}},
        ]
        self.package.write_text(json.dumps({
            "sourceManifest": "content/source-manifests/pilot.json",
            "activities": self.activities,
        }), encoding="utf-8")
        self.manifest = self.repo / "content" / "source-manifests" / "pilot.json"
        self.manifest.parent.mkdir(parents=True)
        self.manifest.write_text(json.dumps({
            "sha256": self.sha,
            "rightsNote": "Instructor-authorized controlled source; use is limited to original transformation and provenance.",
        }), encoding="utf-8")
        self.pages = (
            "In this isolated system the total linear momentum of colliding objects is conserved "
            "during the collision because external forces are negligible and momentum is a vector quantity.",
            "An elastic collision conserves the total kinetic energy of the objects in the system "
            "before and after the impact, in addition to conserving their total linear momentum.",
        )
        self.dest = self.context.validation / "academic-review-source-packets.json"

    def _provision(self):
        with patch("app_generator.runtime.academic_source_provision.extract_pages", return_value=self.pages):
            return provision_run_source_packets(self.config, self.context, self.package, self.source)

    def test_new_source_recovers_without_prior_proof_receipts(self):
        result = self._provision()
        self.assertEqual("LOCAL_SOURCE_LOCATIONS_VERIFIED_PENDING_RIGHTS", result["status"])
        self.assertEqual(2, result["verifiedSourceLocations"])
        self.assertFalse(result["publicationAuthorized"])
        self.assertTrue(self.dest.is_file())
        packet = json.loads(self.dest.read_text(encoding="utf-8"))
        self.assertEqual("AUTOMATED_LOCAL_TEXT", packet["sourcePacketOrigin"])
        self.assertFalse(packet["modelSubmissionAuthorized"])
        self.assertFalse(packet["sourceInterpretationVerified"])
        self.assertEqual(set(a["id"] for a in self.activities), set(packet["packets"]))
        for anchor in packet["packets"].values():
            self.assertEqual(self.sha, anchor["sourceSha256"])
            self.assertFalse(anchor["sourceInterpretationVerified"])

    def test_auto_packet_never_reaches_browser_reviewer_without_rights(self):
        # Even with model browser profiles already present, local provenance is
        # not permission to transmit protected textbook passages externally.
        self._provision()
        for role in ("physics", "semantics"):
            (self.config.chrome_profile_dir / "academic-reviewers" / role / "gemini-browser").mkdir(parents=True)
        def forbidden(*args, **kwargs):
            raise AssertionError("unapproved source excerpt was sent to AI")
        with patch("app_generator.runtime.academic_generation_stage.extract_pages", return_value=self.pages):
            result = run_academic_stage(self.config, self.context, self.package, self.source,
                                        reviewer_factory_type=forbidden)
        self.assertEqual(2, result["sourceLocated"])
        self.assertEqual(0, result["sourceReady"])
        self.assertTrue(all(x["nextAction"] == "AUTO_RIGHTS_CHECK" for x in result["queue"]))
        self.assertFalse(result["publicationAuthorized"])

    def test_complementary_passages_support_multiconcept_activity(self):
        # Neither source paragraph alone covers enough distinct question
        # terms; the bounded union does. Old one-passage bootstrap failed.
        self.activities[0]["objective"] = ""
        self.activities[0]["prompt"]["en"] = (
            "isolated colliding conserved forces elastic kinetic energy impact "
            "linear momentum contact orientation geometry direction speed "
            "measurement trajectory calibration angle displacement impulse "
            "coefficient spring mass mechanical deformation cohesion rotation "
            "feedback evaluation"
        )
        package = json.loads(self.package.read_text(encoding="utf-8"))
        package["activities"] = self.activities
        self.package.write_text(json.dumps(package), encoding="utf-8")
        result = self._provision()
        self.assertEqual("LOCAL_SOURCE_LOCATIONS_VERIFIED_PENDING_RIGHTS", result["status"])
        packets = json.loads(self.dest.read_text(encoding="utf-8"))["packets"]
        self.assertGreaterEqual(len(packets["momentum"]["sourceAnchors"]), 2)
        self.assertFalse(packets["momentum"]["sourceInterpretationVerified"])

    def test_manifest_hash_mismatch_fails_closed(self):
        self.manifest.write_text(json.dumps({
            "sha256": "0" * 64, "rightsNote": "Instructor-authorized controlled source;"
        }), encoding="utf-8")
        result = self._provision()
        self.assertEqual("BLOCKED_SOURCE_MANIFEST_MISMATCH", result["status"])
        self.assertFalse(self.dest.exists())

    def test_missing_controlled_rights_note_blocks_source_read(self):
        self.manifest.write_text(json.dumps({"sha256": self.sha}), encoding="utf-8")
        with patch("app_generator.runtime.academic_source_provision.extract_pages",
                   side_effect=AssertionError("read attempted without controlled use")):
            result = provision_run_source_packets(self.config, self.context, self.package, self.source)
        self.assertEqual("BLOCKED_SOURCE_USE_SCOPE", result["status"])
        self.assertFalse(self.dest.exists())

    def test_irrelevant_source_does_not_create_misleading_proof(self):
        self.pages = ("This passage discusses distant stars and their visible color across the "
                      "nighttime sky during long astronomical observation sessions.",)
        result = self._provision()
        self.assertEqual("LOCAL_SOURCE_RELEVANCE_NOT_VERIFIED", result["status"])
        self.assertFalse(self.dest.exists())

    def test_first_packet_is_immutable_and_stale_change_cannot_inherit_pass(self):
        self._provision()
        frozen = self.dest.read_bytes()
        result = self._provision()
        self.assertEqual("RUN_PACKET_EXISTS_RECHECK_IN_STAGE", result["status"])
        self.assertEqual(frozen, self.dest.read_bytes())
        altered = json.loads(self.package.read_text(encoding="utf-8"))
        altered["activities"][0]["prompt"]["en"] = "Unrelated new question"
        self.package.write_text(json.dumps(altered), encoding="utf-8")
        with patch("app_generator.runtime.academic_generation_stage.extract_pages", return_value=self.pages):
            stage = run_academic_stage(self.config, self.context, self.package, self.source)
        self.assertEqual(0, stage["sourceReady"])
        self.assertEqual(0, stage["sourceLocated"])
        self.assertTrue(all(x["nextAction"] == "AUTO_SOURCE_CHECK" for x in stage["queue"]))


    def test_partial_local_source_packets_auto_route_matching_and_missing(self):
        # Source-free fixture: one legitimate original quote and one unrelated
        # activity. Previous all-or-nothing logic discarded the good packet.
        self.activities[1]["objective"] = ""
        self.activities[1]["prompt"]["en"] = (
            "Spectroscopy chromatograph ultraviolet nebula pollen botany "
            "interstellar galaxies plasma fractal ultraviolet"
        )
        data = json.loads(self.package.read_text(encoding="utf-8"))
        data["activities"] = self.activities
        self.package.write_text(json.dumps(data), encoding="utf-8")
        first = self._provision()
        self.assertEqual("LOCAL_SOURCE_LOCATIONS_PARTIAL_PENDING_REVIEW", first["status"])
        self.assertEqual(1, first["verifiedSourceLocations"])
        self.assertEqual(1, first["unlocatedActivities"])
        packet_path = self.dest
        payload = json.loads(packet_path.read_text(encoding="utf-8"))
        self.assertEqual({"momentum"}, set(payload["packets"]))
        self.assertEqual(["energy"], payload["unlocatedActivityIds"])
        self.assertFalse(payload["modelSubmissionAuthorized"])
        self.assertFalse(payload["sourceInterpretationVerified"])
        original = packet_path.read_bytes()
        self.assertEqual("RUN_PACKET_EXISTS_RECHECK_IN_STAGE", self._provision()["status"])
        self.assertEqual(original, packet_path.read_bytes())

        def forbidden(*args, **kwargs):
            raise AssertionError("model session must not receive private source text")
        with patch("app_generator.runtime.academic_generation_stage.extract_pages",
                   return_value=self.pages):
            stage = run_academic_stage(
                self.config, self.context, self.package, self.source,
                reviewer_factory_type=forbidden,
            )
        self.assertEqual(1, stage["sourceLocated"])
        self.assertEqual(0, stage["sourceReady"])
        by_id = {row["activityId"]: row["nextAction"]
                 for row in stage["queue"] if row["activityId"] in {"momentum","energy"}}
        self.assertEqual({"momentum":"AUTO_RIGHTS_CHECK",
                          "energy":"AUTO_SOURCE_CHECK"}, by_id)
        self.assertEqual("REVIEW_REQUIRED", stage["academicQA"])
        self.assertFalse(stage["publicationAuthorized"])

    def test_partial_packets_do_not_survive_changed_activity_identity(self):
        self.activities[1]["objective"] = ""
        self.activities[1]["prompt"]["en"] = (
            "Spectroscopy chromatograph ultraviolet nebula pollen botany"
        )
        data = json.loads(self.package.read_text(encoding="utf-8"))
        data["activities"] = self.activities
        self.package.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual("LOCAL_SOURCE_LOCATIONS_PARTIAL_PENDING_REVIEW",
                         self._provision()["status"])
        original = self.dest.read_bytes()
        data["activities"][0]["prompt"]["en"] = (
            "An entirely different question from the same sample"
        )
        self.package.write_text(json.dumps(data), encoding="utf-8")
        with patch("app_generator.runtime.academic_generation_stage.extract_pages",
                   return_value=self.pages):
            output = run_academic_stage(
                self.config, self.context, self.package, self.source,
            )
        self.assertEqual(0, output["sourceLocated"])
        self.assertTrue(all(row["nextAction"] == "AUTO_SOURCE_CHECK"
                            for row in output["queue"]))
        self.assertEqual(original, self.dest.read_bytes())
        self.assertFalse(output["publicationAuthorized"])


if __name__ == "__main__":
    unittest.main()

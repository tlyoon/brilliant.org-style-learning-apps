"""BSA247: real prior academic checker dispatch, hash-bound 9.1 source and faults."""
from __future__ import annotations

from hashlib import sha256
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime import v3_historical_academic_audit as m
from app_generator.validation.academic_coverage_gate import _canonical_activity_sha
from app_generator.validation.academic_qa import REQUIRED
from app_generator.validation.source_passages import _normalized


class HistoricalAcademicAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.top = Path(self.tmp.name)
        self.repo = self.top / "repo"
        self.repo.mkdir()
        self.private = self.top / "private"
        self.private.mkdir()
        self.folder = self.top / "signed"
        self.folder.mkdir()
        self.package = {
            "packageId": "chapter-9-section-9-1",
            "activities": [{"id": f"act-{i:02d}", "type": "mcq"}
                           for i in range(18)],
        }
        self.pkgpath = self.repo / m._PACKAGE
        self.pkgpath.parent.mkdir(parents=True)
        raw = (json.dumps(self.package) + "\n").encode("utf8")
        self.pkgpath.write_bytes(raw)
        self.pkgsha = sha256(raw).hexdigest()
        self.pdf = self.private / "source-root" / "9" / "9.1" / "source.pdf"
        self.pdf.parent.mkdir(parents=True)
        self.pdf.write_bytes(b"%PDF-FAKE_TEST_ONLY")
        self.pdfsha = sha256(self.pdf.read_bytes()).hexdigest()
        self.manifest_file = self.repo / "content/source-manifests/chapter-9-section-9-1.json"
        self.manifest_file.parent.mkdir(parents=True)
        self.manifest_file.write_text(json.dumps({"sha256": self.pdfsha}), encoding="utf8")
        self.manifest_sha = sha256(self.manifest_file.read_bytes()).hexdigest()
        self.identity = {"gitHead": "a"*40, "proposalSha256": "b"*64}
        self.binding = _v6_checkpoint(
            self.private / m._SOURCE_BINDING,
            {"contract": "BOSLA_SELECTED_SERWAY_TEXTBOOK_LOCAL_BINDING_V1",
             "section": "9.1", "sourcePdf": str(self.pdf),
             "sourceRoot": str(self.private / "source-root"),
             "sourceSha256": self.pdfsha, "externalFallbackAllowed": False,
             "sourcePdfUploaded": False},
        )
        self.anchor_text = (
            "Linear momentum is defined by the product of the mass of a "
            "particle and its velocity, so the linear momentum is a vector "
            "whose direction equals that of the velocity of the particle. "
            "This is an authoritative textbook passage on the momentum law."
        )
        digest = sha256(_normalized(self.anchor_text).encode("utf8")).hexdigest()
        self.anchors = [
            {"activityId": a["id"],
             "activitySha256": _canonical_activity_sha(a),
             "physicalPage": 1, "passageSha256": digest,
             "uniquePagePassageLocated": True,
             "scientificMeaningVerified": False}
            for a in self.package["activities"]
        ]
        self.source = _v6_checkpoint(
            self.folder / "V18_SELECTED_TEXTBOOK_SCIENCE_RESULT.json",
            {**self.identity, "state": "ONE_REAL_TEXTBOOK_SOURCE_AUDIT_COMPLETE",
             "audit": {"activityCount": 18, "formalAcademicPassCount": 0,
                       "sourceSha256": self.pdfsha,
                       "sourceManifestSha256": self.manifest_sha,
                       "packageSha256": self.pkgsha, "sourceAnchors": self.anchors}},
        )
        self.v18 = _v6_checkpoint(
            self.folder / m._V18,
            {**self.identity, "status": m._STATUS,
             "resultSha256": self.source["integritySha256"],
             "publicationAuthorized": False},
        )
        self.v19 = _v6_checkpoint(
            self.folder / m._V19,
            {**self.identity, "status": m._STATUS19,
             "sourceV18ReceiptSha256": self.v18["integritySha256"],
             "reusedIndependentTwoRolePairs": 17,
             "oldUncertainRoleReplayed": False, "newModelCalls": 0,
             "independentAcademicProofsStillOpen": 90,
             "publicationAuthorized": False},
        )

    def report(self):
        return {
            "activityCount": 18, "packageSha256": self.pkgsha,
            "sourceSha256": self.pdfsha, "publicationAuthorized": False,
            "academicQA": "REVIEW_REQUIRED",
            "counts": {"PASS": 0, "FAIL": 0, "REVIEW_REQUIRED": 18},
            "activities": [
                {"activityId": a["id"],
                 "activitySha256": _canonical_activity_sha(a),
                 "sourceLocationVerified": True,
                 "gates": {gate: "REVIEW_REQUIRED" for gate in REQUIRED},
                 "academicQA": "REVIEW_REQUIRED",
                 "answerStructureErrors": [],
                 "visualContractErrorCount": 0}
                for a in self.package["activities"]],
        }

    def execute(self, v18=None, v19=None, report=None):
        with (
            patch.object(m, "_preflight", return_value=(
                self.folder, None, None, None, None)),
            patch.object(m, "audit_activity_matrix",
                         return_value=self.report() if report is None else report),
            patch.object(m, "_rehydrate_exact_source_packets",
                         return_value={"packageSha256": self.pkgsha,
                                       "sourceSha256": self.pdfsha,
                                       "packets": {}}),
        ):
            return m.run_post_v19_historical_academic_audit(
                self.repo, self.private, self.identity, {}, {}, {},
                self.v18 if v18 is None else v18,
                self.v19 if v19 is None else v19,
            )

    def test_exact_historical_verifier_dispatch_is_persistent_idempotent(self):
        first = self.execute()
        self.assertEqual(first, self.execute())
        self.assertEqual(first["status"], m._STATUS20)
        self.assertEqual(first["verifiedOriginalSourceLocations"], 18)
        self.assertEqual(first["verifiedActivityGateEvaluations"], 90)
        self.assertEqual(first["formalAcademicPASS"], 0)
        result = json.loads((self.folder / m._RESULT).read_text(encoding="utf8"))
        self.assertEqual(len(result["nextActionQueue"]), 18)
        self.assertTrue(all(x["nextAction"] ==
                            "AUTO_INDEPENDENT_SEMANTIC_VISUAL_TRANSLATION_PROOFS"
                            for x in result["nextActionQueue"]))
        self.assertNotIn(self.anchor_text, str(result))
        self.assertFalse(result["publicationAuthorized"])

    def test_tampered_v19_in_memory_does_not_dispatch(self):
        with self.assertRaisesRegex(ValueError, "V20_AUTHENTIC"):
            self.execute(v19={**self.v19, "newModelCalls": 1})
        self.assertFalse((self.folder / m._PRE).exists())

    def test_old_uncertain_role_replayed_is_not_accepted(self):
        from app_generator.runtime.v3_five_stage_completion import _hash
        altered = {**{k: v for k, v in self.v19.items()
                      if k != "integritySha256"},
                   "oldUncertainRoleReplayed": True}
        self.v19 = {**altered, "integritySha256": _hash(altered)}
        (self.folder / m._V19).write_text(
            json.dumps(self.v19), encoding="utf8")
        with self.assertRaisesRegex(ValueError, "V20_INCONSISTENT"):
            self.execute()
        self.assertFalse((self.folder / m._PRE).exists())

    def test_actual_pdf_hash_change_fails_closed(self):
        self.pdf.write_bytes(b"%PDF-DIFFERENT_SOURCE")
        with self.assertRaisesRegex(ValueError, "V20_EXACT"):
            self.execute()
        self.assertFalse((self.folder / m._PRE).exists())

    def test_forged_formal_academic_pass_report_rejected(self):
        report = self.report()
        report["counts"]["PASS"] = 1
        with self.assertRaisesRegex(ValueError, "V20_HISTORICAL"):
            self.execute(report=report)

    def test_historical_source_passages_are_reextracted_not_just_trusted(self):
        with patch.object(m, "extract_pages", return_value=(self.anchor_text,)):
            packets = m._rehydrate_exact_source_packets(
                pdf=self.pdf, source_sha=self.pdfsha, package=self.package,
                package_sha=self.pkgsha, anchors=self.anchors,
            )
        self.assertEqual(len(packets["packets"]), 18)
        self.assertEqual(packets["packageSha256"], self.pkgsha)
        self.assertTrue(all(self.anchor_text in x["sourceEvidence"]
                            for x in packets["packets"].values()))

    def test_changed_saved_source_digest_blocks_rehydration(self):
        bad = [dict(x) for x in self.anchors]
        bad[3]["passageSha256"] = "0" * 64
        with patch.object(m, "extract_pages", return_value=(self.anchor_text,)):
            with self.assertRaisesRegex(ValueError, "V20_SOURCE_ANCHOR_NOT_REFOUND"):
                m._rehydrate_exact_source_packets(
                    pdf=self.pdf, source_sha=self.pdfsha, package=self.package,
                    package_sha=self.pkgsha, anchors=bad,
                )

    def test_worker_invokes_actual_reused_historical_verifier(self):
        worker = (self.repo.parent / "unused")
        script = (Path(__file__).resolve().parents[1] /
                  "scripts/run_v3_yoga6_recovery_worker.py").read_text(encoding="utf8")
        self.assertIn("run_post_v19_historical_academic_audit(", script)
        self.assertIn('result["historicalAcademicFiveGateAudit"]', script)
        self.assertIn('"historicFiveGateVerifierActuallyExecuted") is True', script)


if __name__ == "__main__":
    unittest.main()

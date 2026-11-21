"""BSA244 selected-textbook real PDF science evidence and injected bad inputs."""
from __future__ import annotations

from contextlib import ExitStack
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app_generator.runtime import v3_selected_textbook_scientific_provenance as m
from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint


HERE = Path(__file__).resolve().parents[1]


class SourceFixture(TestCase):
    def setUp(self):
        temp = TemporaryDirectory(prefix="bosla-v18-")
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        self.repo = base / "checkout"
        self.repo.mkdir()
        self.private = base / "private"
        self.private.mkdir()
        self.folder = base / "receipts"
        self.folder.mkdir()
        self.pdfroot = base / "only-existing-textbook"
        self.pdf = self.pdfroot / "9" / "9.1" / "source.pdf"
        self.pdf.parent.mkdir(parents=True)
        self.pdf.write_bytes(b"%PDF-1.7\nsynthetic local fixture only\n%%EOF\n")
        self.sha = sha256(self.pdf.read_bytes()).hexdigest()
        self.pkgfile = self.repo / m._PACKAGE
        self.pkgfile.parent.mkdir(parents=True)
        self.pkgfile.write_bytes((HERE / m._PACKAGE).read_bytes())
        pkg = json.loads(self.pkgfile.read_text(encoding="utf8"))
        self.pages = ("\n\n".join(
            str(a.get("explanation", {}).get("en", ""))
            for a in pkg["activities"] if a.get("explanation", {}).get("en")
        ), )
        self.manifest = self.repo / m._SOURCE_MANIFEST
        self.manifest.parent.mkdir(parents=True)
        self.manifest.write_text(json.dumps({
            "sha256": self.sha,
            "sources": [{"sha256": self.sha,
                         "controlledFilename": "source.pdf",
                         "role": "primary"}],
        }), encoding="utf8")
        self.readiness = {"gitHead": "a" * 40, "proposalSha256": "b" * 64}
        pre = {
            **self.readiness, "status": "V17_REAL_SCIENCE_C3_GAP_AUDITS_EXECUTED_NO_RELEASE",
            "quarantinedTaskIds": [], "historicalC3": "FAILED_LIMITED_CAMPAIGN",
            "publicationAuthorized": False,
        }
        self.v17 = _v6_checkpoint(self.folder / m._V17, pre)
        self.binding = {
            "contract": "BOSLA_SELECTED_SERWAY_TEXTBOOK_LOCAL_BINDING_V1",
            "section": "9.1", "sourceRoot": str(self.pdfroot),
            "sourcePdf": str(self.pdf),
            "sourceSha256": self.sha, "sourceFilename": "source.pdf",
            "sourcePdfUploaded": False, "externalFallbackAllowed": False,
        }
        self._write_binding()

    def _write_binding(self):
        self.binding["integritySha256"] = _hash({
            k:v for k,v in self.binding.items() if k != "integritySha256"
        })
        (self.private / m._SOURCE_BINDING).write_text(
            json.dumps(self.binding), encoding="utf8")

    def verify(self):
        with patch.object(m, "extract_pages", return_value=self.pages):
            return m.verify_real_selected_source(
                repo=self.repo, source_pdf=self.pdf, expected_source_sha=self.sha,
            )

    def run_stage(self):
        with ExitStack() as stack:
            stack.enter_context(patch.object(
                m, "_v13_preflight",
                return_value=(self.folder, {}, {}, "branch", [])))
            stack.enter_context(patch.object(
                m, "extract_pages", return_value=self.pages))
            return m.run_post_v17_selected_textbook(
                self.repo, self.private, self.readiness,
                {}, {}, {}, self.v17)


class OneSelectedTextbookProofTests(SourceFixture):
    def test_source_hash_and_passages_have_real_scope_and_no_passage_leak(self):
        result = self.verify()
        self.assertEqual(result["pageSpecificSourceLocationsVerified"],18)
        self.assertEqual(result["independentExactArithmeticWitnessCount"],6)
        self.assertTrue(all(result["independentExactArithmeticWitnesses"].values()))
        self.assertEqual(result["boundedMCQPatternCount"],5)
        self.assertEqual(result["formalAcademicPassCount"],0)
        self.assertEqual(result["academicQA"],"REVIEW_REQUIRED")
        self.assertFalse(result["publicationAuthorized"])
        self.assertNotIn("synthetic local fixture",json.dumps(result))
        self.assertNotIn("quotedText",json.dumps(result))
        self.assertNotIn("sourceEvidence",json.dumps(result))

    def test_actual_bytes_changed_rejected_without_fallback(self):
        self.pdf.write_bytes(self.pdf.read_bytes()+b"changed")
        with self.assertRaisesRegex(ValueError,"PDF_SHA_CHANGED"):
            self.verify()

    def test_wrong_manifest_primary_or_multi_source_rejected(self):
        doc=json.loads(self.manifest.read_text(encoding="utf8"))
        doc["sources"].append({"sha256":"c"*64,"controlledFilename":"extra.pdf",
                               "role":"supplementary"})
        self.manifest.write_text(json.dumps(doc),encoding="utf8")
        with self.assertRaisesRegex(ValueError,"MANIFEST_SOURCE_IDENTITY"):
            self.verify()

    def test_activity_correct_choice_tampering_rejected(self):
        doc=json.loads(self.pkgfile.read_text(encoding="utf8"))
        doc["activities"][0]["answerKey"]["correct"]="opt-b"
        self.pkgfile.write_text(json.dumps(doc),encoding="utf8")
        with self.assertRaisesRegex(ValueError,"CORRECT_CHOICE_CHANGED"):
            self.verify()

    def test_real_source_insufficient_content_cannot_grant_pass(self):
        with patch.object(m,"extract_pages",return_value=(
                "This is an unrelated PDF about horticulture and botanical classification. "*4,)):
            with self.assertRaisesRegex(ValueError,"EXPECTED_SOURCE_SCIENCE_ABSENT"):
                m.verify_real_selected_source(
                    repo=self.repo,source_pdf=self.pdf,expected_source_sha=self.sha)

    def test_forged_independent_math_witness_rejected(self):
        with patch.object(m,"extract_pages",return_value=self.pages),patch.object(
                m,"_bounded_math_witnesses",
                return_value={"momentum_formula":False}):
            with self.assertRaisesRegex(ValueError,"DETERMINISTIC_PHYSICS_WITNESS_FAILED"):
                m.verify_real_selected_source(
                    repo=self.repo,source_pdf=self.pdf,expected_source_sha=self.sha)

    def test_changed_topic_path_cannot_be_used_for_other_section(self):
        moved=self.pdfroot/"9"/"9.2"/"source.pdf"
        moved.parent.mkdir()
        moved.write_bytes(self.pdf.read_bytes())
        with patch.object(m,"extract_pages",return_value=self.pages):
            with self.assertRaisesRegex(ValueError,"WRONG_TOPIC"):
                m.verify_real_selected_source(
                    repo=self.repo,source_pdf=moved,expected_source_sha=self.sha)

    def test_real_source_bound_v18_preserves_immutable_v17(self):
        before=(self.folder/m._V17).read_bytes()
        a=self.run_stage()
        self.assertEqual(a["status"],m._STATUS)
        self.assertTrue(a["realSingleTextbookPdfOpened"])
        self.assertTrue(a["nextTaskDispatchActuallyExecuted"])
        self.assertIsNotNone(a["academicGapAuditReceiptSha256"])
        self.assertFalse(a["additionalExternalPdfsRequired"])
        self.assertFalse(a["independentScientificAcceptanceComplete"])
        self.assertEqual(a["newModelCalls"],0)
        self.assertFalse(a["publicationAuthorized"])
        self.assertTrue((self.folder/m._V18).exists())
        self.assertTrue((self.folder/"V18_SELECTED_TEXTBOOK_SCIENCE_PRE_CALL.json").exists())
        self.assertTrue((self.folder/"V18_SELECTED_TEXTBOOK_SCIENCE_RESULT.json").exists())
        academic_result = json.loads((
            self.folder/"V18_ACADEMIC_GAP_AUDIT_RESULT.json"
        ).read_text(encoding="utf8"))
        self.assertEqual(
            academic_result["result"]["unverifiedGateInstances"],90)
        self.assertEqual(academic_result["result"]["academicQA"],"REVIEW_REQUIRED")
        self.assertEqual((self.folder/m._V17).read_bytes(),before)
        b=self.run_stage()
        self.assertEqual(a,b)

    def test_invalid_existing_source_binding_fails_closed_without_model(self):
        self.binding["externalFallbackAllowed"]=True
        self._write_binding()
        result=self.run_stage()
        self.assertEqual(result["status"],"V18_REAL_SELECTED_TEXTBOOK_SOURCE_AUDIT_QUARANTINED")
        self.assertEqual(result["newModelCalls"],0)
        self.assertEqual(result["newOutsidePdfDownloads"],0)
        self.assertFalse(result["realSingleTextbookPdfOpened"])
        self.assertFalse(result["publicationAuthorized"])

    def test_gap_audit_fault_cannot_erase_prior_signed_source_result(self):
        with patch.object(
            m, "_selected_textbook_academic_gap_audit",
            side_effect=RuntimeError("synthetic gap task blocked")
        ):
            result = self.run_stage()
        self.assertEqual(
            result["status"], "V18_REAL_SELECTED_TEXTBOOK_SOURCE_AUDIT_QUARANTINED")
        original=json.loads((
            self.folder/"V18_SELECTED_TEXTBOOK_SCIENCE_RESULT.json"
        ).read_text(encoding="utf8"))
        gap=json.loads((
            self.folder/"V18_ACADEMIC_GAP_AUDIT_RESULT.json"
        ).read_text(encoding="utf8"))
        self.assertEqual(
            original["state"],"ONE_REAL_TEXTBOOK_SOURCE_AUDIT_COMPLETE")
        self.assertEqual(gap["state"],"REAL_ACADEMIC_GAP_AUDIT_QUARANTINED")
        self.assertFalse(result["nextTaskDispatchActuallyExecuted"])
        self.assertFalse(result["publicationAuthorized"])

    def test_private_binding_checksum_tamper_quarantined(self):
        path=self.private/m._SOURCE_BINDING
        record=json.loads(path.read_text(encoding="utf8"))
        record["sourceSha256"]="f"*64
        path.write_text(json.dumps(record),encoding="utf8")
        result=self.run_stage()
        self.assertEqual(
            result["status"],"V18_REAL_SELECTED_TEXTBOOK_SOURCE_AUDIT_QUARANTINED")
        self.assertEqual(result["newModelCalls"],0)

    def test_unsigned_v17_does_not_read_original_pdf(self):
        self.v17["integritySha256"]="0"*64
        with patch.object(m,"_v13_preflight",return_value=(
                self.folder,{},{},"branch",[])), patch.object(
                m,"extract_pages",side_effect=AssertionError("PDF must not be touched")):
            with self.assertRaisesRegex(ValueError,"SIGNED_V17_REQUIRED"):
                m.run_post_v17_selected_textbook(
                    self.repo,self.private,self.readiness,{},{},{},self.v17)
        self.assertFalse((self.folder/"V18_SELECTED_TEXTBOOK_SCIENCE_PRE_CALL.json").exists())


if __name__ == "__main__":
    import unittest
    unittest.main()

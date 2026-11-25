"""General, source-free acquisition recovery and no-replay negative controls."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from app_generator.sources.bounded_acquisition import (
    AcquisitionStop, acquire_frozen_sources, validate_acquisition_plan,
    MAX_PDF_BYTES, fetch_trusted_pdf_once, classify_source_suitability,
)

REPO = Path(__file__).resolve().parents[1]


def blob(i: int) -> bytes:
    return b"%PDF-1.7\n" + bytes([65 + i]) * (300 + i) + b"\n%%EOF\n"


def plan(reuse: Path | None = None) -> dict:
    cases = [
        {"caseId": "sample-momentum", "topicFamily": "mechanics",
         "filename": "momentum.pdf",
         "sourceURL": "https://ocw.mit.edu/tests/momentum.pdf"},
        {"caseId": "sample-gauss", "topicFamily": "electromagnetism",
         "filename": "gauss.pdf",
         "sourceURL": "https://ocw.mit.edu/tests/gauss.pdf"},
        {"caseId": "sample-thermo", "topicFamily": "thermodynamics",
         "filename": "thermo.pdf",
         "sourceURL": "https://ocw.mit.edu/tests/thermo.pdf"},
    ]
    if reuse is not None:
        cases[0]["reuseLocalPath"] = str(reuse)
        cases[0]["reuseSha256"] = sha256(reuse.read_bytes()).hexdigest()
    return {
        "schemaVersion": 1, "campaignId": "acquisition-recovery-synthetic",
        "selectionWitnessCommit": "1" * 40,
        "selectionWitnessFile": "docs/decisions/0030-test-witness.md",
        "generatorBaselineGitSha": "2" * 40,
        "priorStopReceiptSha256": "3" * 64,
        "previousSourceSha256s": ["f" * 64],
        "allowedSourceHosts": ["ocw.mit.edu"],
        "maxNewDownloads": 2 if reuse else 3,
        "modelCallsAllowed": False,
        "publicationAllowed": False,
        "cases": cases,
    }


def meta(_path: Path) -> dict:
    return {
        "pages": 6, "approxWords": 850,
        "rightsIndicatorsDetected": [],
        "sourceSuitabilityCategory": "PASS",
        "textSuitabilityPass": True,
    }


class BoundedSourceAcquisitionTests(unittest.TestCase):
    def test_borderline_slide_deck_is_preserved_as_review_not_pass(self):
        self.assertEqual(classify_source_suitability(
            pages=7, words=260, rights_indicators=[]),
            "BORDERLINE_REVIEW_REQUIRED")
        self.assertEqual(classify_source_suitability(
            pages=7, words=300, rights_indicators=[]), "PASS")
        self.assertEqual(classify_source_suitability(
            pages=6, words=230, rights_indicators=[]),
            "INSUFFICIENT_SOURCE_CONTENT")
        self.assertEqual(classify_source_suitability(
            pages=10, words=900, rights_indicators=["courtesy of"]),
            "RIGHTS_REVIEW_REQUIRED")
        self.assertEqual(classify_source_suitability(
            pages=4, words=500, rights_indicators=[]),
            "INSUFFICIENT_SOURCE_CONTENT")

    def test_prevalidate_all_case_keys_before_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            reuse = Path(tmp) / "existing.pdf"
            reuse.write_bytes(blob(0))
            good = plan(reuse)
            # This is the exact historical mismatch: producer sourceSha256,
            # consumer sha256. It is rejected BEFORE a new public request.
            good["cases"][1]["sha256"] = "1" * 64
            with self.assertRaisesRegex(AcquisitionStop, "INVALID_SOURCE_ROW_FIELDS"):
                validate_acquisition_plan(good)

    def test_reuses_verified_existing_pdf_and_fetches_only_two_new_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            existing = root / "existing.pdf"
            existing.write_bytes(blob(0))
            output = root / "fresh-output"
            output.mkdir()
            fake_fetch = Mock(side_effect=(blob(1), blob(2)))
            with patch("app_generator.sources.bounded_acquisition.verify_selection_witness",
                       return_value="a" * 64):
                report = acquire_frozen_sources(
                    plan(existing), repo=REPO, output_root=output,
                    fetch=fake_fetch, inspector=meta)
            self.assertEqual(report["status"], "ALL_THREE_PRIVATE_SOURCES_ACQUIRED")
            self.assertEqual(fake_fetch.call_count, 2)
            self.assertEqual([row["topicFamily"] for row in report["sources"]],
                             ["mechanics", "electromagnetism", "thermodynamics"])
            self.assertEqual([row["reuseVerifiedNoRedownload"]
                              for row in report["sources"]], [True, False, False])
            for i, name in enumerate(("momentum.pdf", "gauss.pdf", "thermo.pdf")):
                self.assertEqual((output / "pdfs" / name).read_bytes(), blob(i))
            self.assertFalse(report["publicationAuthorized"])
            self.assertEqual(report["sourceBearingModelCalls"], 0)
            self.assertEqual(len(list((output / "attempts").glob("*-finished.json"))), 3)

    def test_recovery_directory_refuses_second_invocation_before_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "fresh-output"
            output.mkdir()
            mock_fetch = Mock(side_effect=(blob(0), blob(1), blob(2)))
            with patch("app_generator.sources.bounded_acquisition.verify_selection_witness",
                       return_value="a" * 64):
                acquire_frozen_sources(plan(), repo=REPO, output_root=output,
                                       fetch=mock_fetch, inspector=meta)
                with self.assertRaisesRegex(AcquisitionStop,
                                            "UNSAFE_OR_REUSED_PRIVATE_OUTPUT"):
                    acquire_frozen_sources(plan(), repo=REPO, output_root=output,
                                           fetch=mock_fetch, inspector=meta)
            self.assertEqual(mock_fetch.call_count, 3)

    def test_duplicate_sha_fails_closed_no_third_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "run"
            output.mkdir()
            fetch = Mock(side_effect=[blob(0), blob(0), blob(2)])
            with patch("app_generator.sources.bounded_acquisition.verify_selection_witness",
                       return_value="a" * 64):
                with self.assertRaisesRegex(AcquisitionStop,
                                            "DUPLICATE_OR_MISMATCHED_PDF_IDENTITY"):
                    acquire_frozen_sources(plan(), repo=REPO, output_root=output,
                                           fetch=fetch, inspector=meta)
            self.assertEqual(fetch.call_count, 2)
            self.assertTrue((output / "terminal_stop.json").is_file())
            self.assertFalse((output / "source_integrity.json").exists())

    def test_ambiguous_network_error_stops_without_retry_or_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "run"
            output.mkdir()
            fetch = Mock(side_effect=TimeoutError("SECRET_TOKEN_123"))
            with patch("app_generator.sources.bounded_acquisition.verify_selection_witness",
                       return_value="a" * 64):
                with self.assertRaisesRegex(AcquisitionStop,
                                            "UNEXPECTED_ACQUISITION_STOP"):
                    acquire_frozen_sources(plan(), repo=REPO, output_root=output,
                                           fetch=fetch, inspector=meta)
            self.assertEqual(fetch.call_count, 1)
            stop = (output / "terminal_stop.json").read_text()
            self.assertNotIn("SECRET_TOKEN_123", stop)
            self.assertFalse((output / "pdfs" / "momentum.pdf").exists())

    def test_bad_precommitted_witness_prevents_any_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "run"
            output.mkdir()
            fetch = Mock()
            with patch("app_generator.sources.bounded_acquisition.verify_selection_witness",
                       side_effect=AcquisitionStop("SOURCE_NOT_IN_PRECOMMITTED_WITNESS")):
                with self.assertRaisesRegex(AcquisitionStop,
                                            "SOURCE_NOT_IN_PRECOMMITTED_WITNESS"):
                    acquire_frozen_sources(plan(), repo=REPO, output_root=output,
                                           fetch=fetch, inspector=meta)
            fetch.assert_not_called()
            self.assertEqual(list(output.iterdir()), [])

    def test_reuse_digest_mismatch_rejects_before_model_or_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            existing = Path(tmp) / "old.pdf"
            existing.write_bytes(blob(0))
            broken = plan(existing)
            broken["cases"][0]["reuseSha256"] = "e" * 64
            with self.assertRaisesRegex(AcquisitionStop, "REUSED_PDF_MISMATCH"):
                validate_acquisition_plan(broken)

    def test_unsafe_source_and_release_flags_rejected(self):
        cases = (
            ("publicationAllowed", True, "UNSAFE_PUBLICATION_OR_MODEL_FLAGS"),
            ("modelCallsAllowed", True, "UNSAFE_PUBLICATION_OR_MODEL_FLAGS"),
            ("maxNewDownloads", 5, "DOWNLOAD_BUDGET_MISMATCH"),
        )
        for key, value, category in cases:
            with self.subTest(key=key):
                bad = plan()
                bad[key] = value
                with self.assertRaisesRegex(AcquisitionStop, category):
                    validate_acquisition_plan(bad)
        bad = plan()
        bad["cases"][1]["filename"] = "../../escape.pdf"
        with self.assertRaisesRegex(AcquisitionStop, "INVALID_SOURCE_ROW_IDENTITY"):
            validate_acquisition_plan(bad)
        bad = plan()
        bad["cases"][2]["sourceURL"] = "https://evil.example.com/thermo.pdf"
        with self.assertRaisesRegex(AcquisitionStop, "NONTRUSTED_SOURCE_URL"):
            validate_acquisition_plan(bad)

    def test_rights_or_identity_injected_metadata_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "run"
            output.mkdir()
            fetch = Mock(side_effect=[blob(0), blob(1), blob(2)])
            def dangerous_meta(_path):
                item = meta(_path)
                item["sourceSha256"] = "0" * 64
                return item
            with patch("app_generator.sources.bounded_acquisition.verify_selection_witness",
                       return_value="a" * 64):
                with self.assertRaisesRegex(AcquisitionStop,
                                            "SOURCE_STRUCTURE_OR_RIGHTS_REVIEW_STOP"):
                    acquire_frozen_sources(plan(), repo=REPO, output_root=output,
                                           fetch=fetch, inspector=dangerous_meta)
            self.assertEqual(fetch.call_count, 1)

    def test_trusted_host_allowlist_rejects_invalid_families_and_origins(self):
        broken = plan()
        broken["allowedSourceHosts"] = ["ocw.mit.edu", "ocw.mit.edu"]
        with self.assertRaisesRegex(AcquisitionStop,
                                    "INVALID_TRUSTED_HOST_ALLOWLIST"):
            validate_acquisition_plan(broken)
        broken = plan()
        broken["cases"][0]["topicFamily"] = ["not-an-allowed-family"]
        with self.assertRaisesRegex(AcquisitionStop,
                                    "INVALID_SOURCE_ROW_IDENTITY"):
            validate_acquisition_plan(broken)

    def test_http_redirect_never_follows_untrusted_host(self):
        from unittest.mock import MagicMock
        response = MagicMock()
        response.url = "https://ocw.mit.edu/tests/gauss.pdf"
        response.is_redirect = True
        response.headers = {
            "Content-Type": "application/pdf",
            "Location": "https://evil.example.com/source.pdf",
        }
        response.raise_for_status.return_value = None
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=None)
        session = Mock()
        session.get.return_value = response
        with patch("requests.Session", return_value=session):
            with self.assertRaisesRegex(AcquisitionStop,
                                        "SOURCE_REDIRECT_OUT_OF_SCOPE"):
                fetch_trusted_pdf_once(
                    "https://ocw.mit.edu/tests/gauss.pdf", ("ocw.mit.edu",))
        self.assertFalse(session.get.call_args.kwargs["allow_redirects"])
        self.assertEqual(session.get.call_count, 1)
        session.close.assert_called_once()

    def test_bounded_same_host_redirect_can_complete_one_logical_fetch(self):
        from unittest.mock import MagicMock
        redirect = MagicMock()
        redirect.is_redirect = True
        redirect.headers = {"Location": "/files/new.pdf"}
        redirect.__enter__.return_value = redirect
        final = MagicMock()
        final.is_redirect = False
        final.headers = {"Content-Type": "application/pdf"}
        final.iter_content.return_value = [blob(0)]
        final.__enter__.return_value = final
        session = MagicMock()
        session.get.side_effect = [redirect, final]
        with patch("requests.Session", return_value=session):
            data = fetch_trusted_pdf_once(
                "https://ocw.mit.edu/original.pdf", ("ocw.mit.edu",))
        self.assertEqual(data, blob(0))
        self.assertEqual(session.get.call_count, 2)
        self.assertEqual(session.get.call_args_list[-1].args[0],
                         "https://ocw.mit.edu/files/new.pdf")
        self.assertTrue(all(call.kwargs["allow_redirects"] is False
                            for call in session.get.call_args_list))
        session.close.assert_called_once()

    def test_borderline_source_retains_acquired_pdf_receipt_before_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "run"
            output.mkdir()
            fetch = Mock(side_effect=[blob(0), blob(1), blob(2)])
            def borderline(_path):
                return {
                    "pages": 7, "approxWords": 260,
                    "rightsIndicatorsDetected": [],
                    "textSuitabilityPass": False,
                    "sourceSuitabilityCategory": "BORDERLINE_REVIEW_REQUIRED",
                }
            with patch("app_generator.sources.bounded_acquisition.verify_selection_witness",
                       return_value="a" * 64):
                with self.assertRaisesRegex(AcquisitionStop,
                                            "SOURCE_STRUCTURE_OR_RIGHTS_REVIEW_STOP"):
                    acquire_frozen_sources(plan(), repo=REPO, output_root=output,
                                           fetch=fetch, inspector=borderline)
            self.assertEqual(fetch.call_count, 1)
            self.assertTrue((output / "pdfs" / "momentum.pdf").is_file())
            acquired = json.loads((output / "attempts" /
                                  "sample-momentum-acquired.json").read_text())
            self.assertEqual(acquired["sourceSha256"], sha256(blob(0)).hexdigest())
            stop = json.loads((output / "terminal_stop.json").read_text())
            self.assertEqual(stop["retainedVerifiedPdfCases"], ["sample-momentum"])
            self.assertEqual(stop["unacceptedSourceSuitabilityCategory"],
                             "BORDERLINE_REVIEW_REQUIRED")

    def test_invalid_structure_stops_before_third_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "run"
            output.mkdir()
            fetch = Mock(side_effect=[blob(0), blob(1), blob(2)])
            count = 0
            def inspect(_path):
                nonlocal count
                count += 1
                result = meta(_path)
                if count == 2:
                    result["textSuitabilityPass"] = False
                return result
            with patch("app_generator.sources.bounded_acquisition.verify_selection_witness",
                       return_value="a" * 64):
                with self.assertRaisesRegex(AcquisitionStop,
                                            "SOURCE_STRUCTURE_OR_RIGHTS_REVIEW_STOP"):
                    acquire_frozen_sources(plan(), repo=REPO, output_root=output,
                                           fetch=fetch, inspector=inspect)
            self.assertEqual(fetch.call_count, 2)


if __name__ == "__main__":
    unittest.main()

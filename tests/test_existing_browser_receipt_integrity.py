"""Source-free regressions for browser receipt Git/Windows identity recovery."""
from hashlib import sha256
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zlib

from app_generator.validation.git_checkout_identity import verify_git_checkout_sha
from app_generator.validation.learner_browser_receipt_integrity import (
    _png_valid, reconcile_browser_receipts,
)
from scripts.reconcile_existing_learner_browser_receipts import main

FROZEN = "a" * 40


class GitCheckoutIdentityTests(unittest.TestCase):
    def test_previous_windows_crlf_receipt_is_auto_reconciled(self):
        blob = b"line one\nline two\n"
        raw_windows = blob.replace(b"\n", b"\r\n")
        completed = type("Response", (), {"returncode": 0, "stdout": blob})()
        with patch("app_generator.validation.git_checkout_identity.subprocess.run",
                   return_value=completed):
            self.assertEqual(
                "VERIFIED_WINDOWS_CRLF",
                verify_git_checkout_sha(
                    Path("."), FROZEN, "app/app.js",
                    sha256(raw_windows).hexdigest(),
                ),
            )

    def test_exact_git_blob_remains_supported(self):
        blob = b"fixed script\n"
        response = type("Response", (), {"returncode": 0, "stdout": blob})()
        with patch("app_generator.validation.git_checkout_identity.subprocess.run",
                   return_value=response):
            self.assertEqual(
                "EXACT_GIT_BLOB",
                verify_git_checkout_sha(
                    Path("."), FROZEN, "scripts/audit_full_learner_browser.py",
                    sha256(blob).hexdigest(),
                ),
            )

    def test_real_code_change_is_not_silently_normalized(self):
        blob = b"valid original\n"
        forged = sha256(b"valid original\nchanged behavior\n").hexdigest()
        response = type("Response", (), {"returncode": 0, "stdout": blob})()
        with patch("app_generator.validation.git_checkout_identity.subprocess.run",
                   return_value=response):
            with self.assertRaisesRegex(ValueError, "RAW_EXECUTION_SHA"):
                verify_git_checkout_sha(
                    Path("."), FROZEN, "app/app.js", forged,
                )

    def test_frozen_sha_and_paths_must_be_authoritative(self):
        for bad in ("../../private.env", r"scripts\private.py", "/etc/passwd"):
            with self.assertRaisesRegex(ValueError, "UNSAFE"):
                verify_git_checkout_sha(
                    Path("."), FROZEN, bad, "b" * 64,
                )
        with self.assertRaisesRegex(ValueError, "INVALID_FROZEN"):
            verify_git_checkout_sha(
                Path("."), "main", "app/app.js", "b" * 64,
            )


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload)) + kind + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)
    )


def _png(width=128, height=90):
    data = (b"\x00" + (b"\x01\x02\x03" * width)) * height
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(data))
        + _chunk(b"IEND", b"")
    )


class ExistingBrowserIntegrityTests(unittest.TestCase):
    def test_png_checks_crc_and_bounded_decompression(self):
        image = _png()
        _png_valid(image, 128)
        altered = image[:-8] + b"\x01" + image[-7:]
        with self.assertRaises(ValueError):
            _png_valid(altered, 128)
        with self.assertRaisesRegex(ValueError, "DIMENSIONS"):
            _png_valid(image, 390)

    def _setup_case(self, tmp):
        repo = Path(tmp) / "repo"
        evidence = Path(tmp) / "evidence"
        evidence.mkdir()
        relative = "content/example/package.json"
        package_path = repo / relative
        package_path.parent.mkdir(parents=True)
        pkg = {"activities": [{"id": "activity-one", "type": "mcq"}]}
        raw = json.dumps(pkg).encode()
        package_path.write_bytes(raw)
        digest = sha256(raw).hexdigest()
        folder = evidence / ("learner-browser-" + digest[:16])
        folder.mkdir()
        rows = []
        for language in ("en", "ms", "zh"):
            for width in (390, 1280):
                name = "01-" + language + "-" + str(width) + ".png"
                img = _png(width)
                (folder / name).write_bytes(img)
                rows.append({
                    "activityId": "activity-one", "locale": language,
                    "viewportWidth": width, "rendered": True,
                    "responsive": True, "keyboardOperable": True,
                    "answerInteractionExercised": True,
                    "screenshotFile": name,
                    "screenshotSha256": sha256(img).hexdigest(),
                })
        identity = {
            "packageSha256": digest,
            "auditScriptSha256": "a" * 64,
            "learnerPlayerSha256": "b" * 64,
            "publicationAuthorized": False,
        }
        (folder / "learner-receipt.json").write_text(json.dumps({
            **identity, "checks": rows,
        }))
        (folder / "summary.json").write_text(json.dumps({
            **identity, "status": "COMPLETE_BROWSER_COVERAGE_UNDER_INDEPENDENT_REVIEW",
            "academicAcceptanceGranted": False,
            "technicalAcceptanceGranted": False,
        }))
        return repo, evidence, relative, folder

    def test_six_real_shape_receipts_remain_metadata_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, evidence, relative, folder = self._setup_case(tmp)
            with patch(
                "app_generator.validation.learner_browser_receipt_integrity."
                "verify_git_checkout_sha", return_value="VERIFIED_WINDOWS_CRLF"
            ) as verify:
                result = reconcile_browser_receipts(
                    repo, frozen_commit=FROZEN, packages=[relative],
                    receipt_root=evidence,
                )
            self.assertEqual(3, verify.call_count)
            self.assertEqual("EXISTING_BROWSER_FILE_INTEGRITY_VERIFIED", result["status"])
            self.assertEqual(6, result["screenshotsShaAndPngIntegrityVerified"])
            self.assertFalse(result["browserInteractionsIndependentlyVerified"])
            self.assertFalse(result["academicAcceptanceGranted"])
            self.assertFalse(result["publicationAuthorized"])

    def test_screenshot_changed_after_capture_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, evidence, relative, folder = self._setup_case(tmp)
            (folder / "01-ms-390.png").write_bytes(b"replaced")
            with patch(
                "app_generator.validation.learner_browser_receipt_integrity."
                "verify_git_checkout_sha", return_value="VERIFIED_WINDOWS_CRLF"
            ):
                with self.assertRaisesRegex(ValueError, "SCREENSHOT_DIGEST"):
                    reconcile_browser_receipts(
                        repo, frozen_commit=FROZEN, packages=[relative],
                        receipt_root=evidence,
                    )

    def test_private_output_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            outfile = Path(tmp) / "receipt.json"
            outfile.write_text("owner existing receipt")
            args = ["--frozen-git-sha", FROZEN, "--packages",
                    "content/example/package.json", "--receipt-root",
                    tmp, "--out", str(outfile)]
            self.assertEqual(2, main(args))
            self.assertEqual("owner existing receipt", outfile.read_text())

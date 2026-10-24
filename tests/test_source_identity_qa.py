import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from app_generator.validation.source_identity import verify_source_identity

class SourceIdentityQATests(unittest.TestCase):
    def test_identity_is_not_textbook_fidelity(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            pdf=root/"source.pdf";pdf.write_bytes(b"%PDF-1.4 synthetic")
            h=hashlib.sha256(pdf.read_bytes()).hexdigest()
            meta=root/"manifest.json"
            meta.write_text(json.dumps({"sha256":h, "sources":[{"sha256":h, "role":"primary"}]}), encoding="utf-8")
            self.assertEqual("REVIEW_REQUIRED",verify_source_identity(meta,pdf).result)
            self.assertIn("source bytes match",verify_source_identity(meta,pdf).detail)
            pdf.write_bytes(b"%PDF-1.4 tampered")
            self.assertEqual("FAIL",verify_source_identity(meta,pdf).result)
            self.assertEqual("REVIEW_REQUIRED",verify_source_identity(meta).result)

    def test_conflicting_manifest_identity_fails(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/"manifest.json"
            file.write_text(json.dumps({"sha256":"a"*64,"sources":[{"sha256":"b"*64,"role":"primary"}]}))
            self.assertEqual("FAIL",verify_source_identity(file).result)
            file.write_text("{}")
            self.assertEqual("REVIEW_REQUIRED",verify_source_identity(file).result)

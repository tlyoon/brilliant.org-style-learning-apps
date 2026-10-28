"""Synthetic browser capture evidence tamper resistance; no private files in Git."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from app_generator.validation.private_browser_visual_evidence import (
    verify_browser_visual_evidence,
)


def png_bytes():
    width, height = 400, 150
    raw = b"".join(b"\0" + bytes(((x+y*7) % 256 for x in range(width*3)))
                   for y in range(height))
    def chunk(t, data):
        return struct.pack(">I", len(data)) + t + data + struct.pack(
            ">I", zlib.crc32(t + data) & 0xffffffff
        )
    return (bytes.fromhex("89504e470d0a1a0a")
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


class PrivateVisualEvidenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        r = Path(temp.name)
        self.pkg, self.pdf, self.dir = r/"source-package.json",r/"original.pdf",r/"screens"
        self.dir.mkdir()
        self.pkg.write_text(json.dumps({"activities": [
            {"id":"v1","visualSpec":{"template":"mechanics.cart_collision_1d"}},
            {"id":"plain"},
        ]}),encoding="utf-8")
        self.pdf.write_bytes(b"%PDF-1.4 controlled private fixture")
        self.pkg_sha = sha256(self.pkg.read_bytes()).hexdigest()
        self.pdf_sha = sha256(self.pdf.read_bytes()).hexdigest()
        png = png_bytes()
        self.assertGreater(len(png), 1000)
        self.rows = []
        i=0
        for locale in ("en","ms","zh"):
            for width in (390,1280):
                i += 1
                name=f"{i:03d}-v1-{locale}-{width}.png"
                (self.dir/name).write_bytes(png)
                self.rows.append({
                    "activityId":"v1","locale":locale,"viewportWidth":width,
                    "file":name,"bytes":len(png),"sha256":sha256(png).hexdigest(),
                    "reviewStatus":"unreviewed",
                })
        self.manifest = {
            "packageSha256":self.pkg_sha,
            "browserSmokeOutcome":"browser_dom_smoke_pass",
            "responsiveChecks":6,"keyboardSelectionChecks":6,"issues":[],
            "screenshots":self.rows,"pixelQualityReviewed":False,
            "academicAccuracyReviewed":False,
        }
        self.flush()

    def flush(self):
        (self.dir/"review-manifest.json").write_text(
            json.dumps(self.manifest),encoding="utf-8"
        )

    def verify(self):
        return verify_browser_visual_evidence(
            package_file=self.pkg,source_pdf=self.pdf,evidence_dir=self.dir,
            expected_package_sha256=self.pkg_sha,
            expected_source_sha256=self.pdf_sha,expected_count=2,
        )

    def test_exact_six_screenshots_verify_no_academic_approval(self):
        r=self.verify()
        self.assertEqual(6,r["screenshotsHashVerified"])
        self.assertEqual(6,r["keyboardSelectionChecks"])
        self.assertFalse(r["academicAccuracyReviewed"])
        self.assertFalse(r["publicationAuthorized"])

    def test_missing_or_duplicate_visual_screen_fails_closed(self):
        self.manifest["screenshots"]=self.rows[1:]
        self.flush()
        with self.assertRaises(ValueError):self.verify()
        self.manifest["screenshots"]=self.rows[:5]+[self.rows[0]]
        self.flush()
        with self.assertRaises(ValueError):self.verify()

    def test_tampered_image_and_traversal_name_blocked(self):
        name=self.rows[0]["file"]
        (self.dir/name).write_bytes(b"tamper")
        with self.assertRaisesRegex(ValueError,"corrupted"):self.verify()
        (self.dir/name).write_bytes(png_bytes())
        self.rows[0]["file"]="../outside.png"
        self.flush()
        with self.assertRaisesRegex(ValueError,"unsafe"):self.verify()

    def test_forged_browser_pass_and_academic_approval_blocked(self):
        self.manifest["issues"]=[{"reason":"missing geometry"}]
        self.flush()
        with self.assertRaises(ValueError):self.verify()
        self.manifest["issues"]=[]
        self.manifest["academicAccuracyReviewed"]=True
        self.flush()
        with self.assertRaises(ValueError):self.verify()

    def test_stale_source_or_package_blocked(self):
        self.pdf.write_bytes(b"%PDF-1.4 changed")
        with self.assertRaisesRegex(ValueError,"identity mismatch"):self.verify()
        self.pdf.write_bytes(b"%PDF-1.4 controlled private fixture")
        self.pkg.write_bytes(self.pkg.read_bytes()+b" ")
        with self.assertRaisesRegex(ValueError,"identity mismatch"):self.verify()


if __name__=="__main__":
    unittest.main()
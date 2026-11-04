"""Source-free synthetic PNG tests; no real textbook/screenshot committed."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zlib
from app_generator.validation.private_visual_pixel_integrity import (
    _png_rgb_pixels, audit_private_visual_pixel_integrity,
)


def chunk(label: bytes, payload: bytes) -> bytes:
    return (struct.pack(">I",len(payload))+label+payload+
            struct.pack(">I",zlib.crc32(label+payload)&0xffffffff))


def png(*, color: bool=True, filter_mode: int=0, corrupt_crc: bool=False) -> bytes:
    width,height=128,90
    row=b""
    for x in range(width):
        val=(x*3)%256 if color else 255
        row+=bytes((val,255 if not color else 20+(x%30),255 if not color else 70))
    data=b"".join(bytes((filter_mode,))+row for _ in range(height))
    raw=(b"\x89PNG\r\n\x1a\n"+
         chunk(b"IHDR",struct.pack(">IIBBBBB",width,height,8,2,0,0,0))+
         chunk(b"IDAT",zlib.compress(data))+
         chunk(b"IEND",b""))
    if corrupt_crc:
        raw=raw[:-5]+bytes((raw[-5]^1,))+raw[-4:]
    return raw


class SourceBoundPixelIntegrityTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root=Path(folder.name)
        self.image=self.root/"sample.png"
        self.image.write_bytes(png())
        self._manifest()

    def _manifest(self):
        raw=self.image.read_bytes()
        manifest={"screenshots":[{
             "file":self.image.name,"sha256":sha256(raw).hexdigest(),
             "activityId":"synthetic-activity","locale":"en",
             "viewportWidth":390}]}
        (self.root/"review-manifest.json").write_text(json.dumps(manifest))

    def _audit(self):
        with patch("app_generator.validation.private_visual_pixel_integrity.verify_browser_visual_evidence",
                   return_value={"status":"SOURCE_BOUND_BROWSER_VISUAL_CAPTURE_VERIFIED"}):
            return audit_private_visual_pixel_integrity(
                package_file=self.root/"dummy.json",source_pdf=self.root/"dummy.pdf",
                evidence_dir=self.root,
                expected_package_sha256="a"*64,expected_source_sha256="b"*64)

    def test_valid_chrome_rgb_pixel_capture_is_nonblank_but_not_semantically_approved(self):
        data=self._audit()
        self.assertEqual(1,data["screenCapturesChecked"])
        self.assertTrue(data["technicalPixelIntegrityChecked"])
        self.assertFalse(data["pixelQualityReviewed"])
        self.assertFalse(data["academicAccuracyReviewed"])
        self.assertFalse(data["publicationAuthorized"])
        self.assertEqual("REVIEW_REQUIRED",data["academicQA"])

    def test_blank_white_image_rejected_even_with_correct_new_hash(self):
        self.image.write_bytes(png(color=False))
        self._manifest()
        with self.assertRaisesRegex(ValueError,"near-uniform"):
            self._audit()

    def test_changed_image_without_matching_manifest_hash_rejected(self):
        self.image.write_bytes(png(color=False))
        with self.assertRaisesRegex(ValueError,"changed"):
            self._audit()

    def test_png_crc_error_rejected(self):
        with self.assertRaisesRegex(ValueError,"CRC"):
            _png_rgb_pixels(png(corrupt_crc=True))

    def test_invalid_png_filter_rejected(self):
        with self.assertRaisesRegex(ValueError,"filter"):
            _png_rgb_pixels(png(filter_mode=5))

    def test_non_png_rejected(self):
        with self.assertRaisesRegex(ValueError,"not PNG"):
            _png_rgb_pixels(b"not PNG")


if __name__=="__main__":
    unittest.main()

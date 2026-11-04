"""Verify immutable real-browser screenshot coverage against exact private source.

This proves source/capture identity, SVG DOM checks and screenshot integrity,
NOT scientific correctness of pictures, translation, or academic approval.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import struct
from typing import Any

WIDTHS = (390, 1280)
LANGS = ("en", "ms", "zh")
PNG_SIG = bytes.fromhex("89504e470d0a1a0a")


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verify_browser_visual_evidence(
    *, package_file: Path, source_pdf: Path, evidence_dir: Path,
    expected_package_sha256: str, expected_source_sha256: str,
    expected_count: int = 18,
) -> dict[str, Any]:
    if not evidence_dir.is_dir():
        raise ValueError("private visual screenshot evidence folder missing")
    if (not package_file.is_file() or not source_pdf.is_file() or
        _sha(package_file) != expected_package_sha256 or
        _sha(source_pdf) != expected_source_sha256 or
        source_pdf.read_bytes()[:5] != b"%PDF-"):
        raise ValueError("controlled original PDF/package identity mismatch")
    package = json.loads(package_file.read_text(encoding="utf-8"))
    activities = package.get("activities")
    if not isinstance(activities, list) or len(activities) != expected_count:
        raise ValueError("exact original activity count mismatch")
    visual_ids = [a["id"] for a in activities if a.get("visualSpec")]
    if not visual_ids or len(set(visual_ids)) != len(visual_ids):
        raise ValueError("original visual IDs absent or duplicate")
    path = evidence_dir / "review-manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    expected = {(aid, lang, width) for aid in visual_ids
                for lang in LANGS for width in WIDTHS}
    rows = data.get("screenshots")
    if (data.get("packageSha256") != expected_package_sha256 or
        data.get("browserSmokeOutcome") != "browser_dom_smoke_pass" or
        data.get("pixelQualityReviewed") is not False or
        data.get("academicAccuracyReviewed") is not False or
        not isinstance(rows, list) or len(rows) != len(expected) or
        data.get("responsiveChecks") != len(expected) or
        data.get("keyboardSelectionChecks") != len(expected) or
        data.get("issues") != []):
        raise ValueError("browser audit metadata missing or stale")
    covered = set()
    files = set()
    for frame in rows:
        if not isinstance(frame, dict):
            raise ValueError("invalid browser screenshot record")
        key = (frame.get("activityId"), frame.get("locale"), frame.get("viewportWidth"))
        if key not in expected or key in covered:
            raise ValueError("visual screenshot missing or duplicate coverage")
        covered.add(key)
        name = frame.get("file")
        if (not isinstance(name, str) or not name.endswith(".png")
            or Path(name).name != name or name in files):
            raise ValueError("unsafe or duplicate screenshot filename")
        files.add(name)
        image = evidence_dir / name
        if image.is_symlink() or not image.is_file():
            raise ValueError("browser screenshot missing or linked")
        raw = image.read_bytes()
        if (len(raw) < 1000 or raw[:8] != PNG_SIG or
            len(raw) != frame.get("bytes") or
            sha256(raw).hexdigest() != frame.get("sha256") or
            frame.get("reviewStatus") != "unreviewed"):
            raise ValueError("corrupted or falsely approved screenshot evidence")
        if raw[12:16] != b"IHDR":
            raise ValueError("PNG dimensions unavailable")
        pixel_width, pixel_height = struct.unpack(">II", raw[16:24])
        if not (100 <= pixel_width <= 1800 and 80 <= pixel_height <= 1000):
            raise ValueError("screenshot dimensions not plausible")
    if covered != expected:
        raise ValueError("browser screenshot coverage incomplete")
    return {
        "status": "SOURCE_BOUND_BROWSER_VISUAL_CAPTURE_VERIFIED",
        "sourceSha256": expected_source_sha256,
        "packageSha256": expected_package_sha256,
        "visualActivities": len(visual_ids),
        "responsiveLocaleChecks": len(expected),
        "keyboardSelectionChecks": len(expected),
        "screenshotsHashVerified": len(expected),
        "pixelQualityReviewed": False,
        "academicAccuracyReviewed": False,
        "academicQA": "REVIEW_REQUIRED",
        "publicationAuthorized": False,
    }
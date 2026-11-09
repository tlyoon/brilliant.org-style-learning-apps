"""Read-only, source-free integrity reconciliation for existing learner audits.

Verifies exact immutable Git code identity (including Windows LF/CRLF
materialization), saved receipt/package binding, row coverage, PNG SHA256,
chunk CRC and bounded decode. It does not rerun the browser or certify its
behavior, scientific content, translation, visual meaning or release.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import struct
import zlib

from app_generator.validation.git_checkout_identity import verify_git_checkout_sha
from app_generator.validation.learner_coverage_gate import audit_full_learner_coverage

_PNG_SIG = b"\x89PNG\r\n\x1a\n"
_CODE_FILES = ("scripts/audit_full_learner_browser.py", "app/app.js")


def _png_valid(raw: bytes, viewport_width: int) -> None:
    if not (64 < len(raw) < 8_000_000) or not raw.startswith(_PNG_SIG):
        raise ValueError("SCREENSHOT_NOT_PNG")
    p = len(_PNG_SIG)
    wh = None
    idat = []
    end_seen = False
    while p < len(raw):
        if p + 12 > len(raw):
            raise ValueError("SCREENSHOT_TRUNCATED")
        size = struct.unpack(">I", raw[p:p+4])[0]
        tag = raw[p+4:p+8]
        nxt = p + size + 12
        if size > 8_000_000 or nxt > len(raw):
            raise ValueError("SCREENSHOT_CHUNK_INVALID")
        payload = raw[p+8:p+8+size]
        crc = struct.unpack(">I", raw[nxt-4:nxt])[0]
        if (zlib.crc32(tag + payload) & 0xffffffff) != crc:
            raise ValueError("SCREENSHOT_CRC_INVALID")
        if tag == b"IHDR":
            if wh is not None or size != 13:
                raise ValueError("SCREENSHOT_HEADER_INVALID")
            w, h, bits, color, compression, flt, interlace = (
                struct.unpack(">IIBBBBB", payload)
            )
            if (w != viewport_width or not 80 <= h <= 1200 or
                (bits, color, compression, flt, interlace) != (8, 2, 0, 0, 0)):
                raise ValueError("SCREENSHOT_DIMENSIONS_OR_FORMAT_INVALID")
            wh = (w, h)
        elif tag == b"IDAT":
            if wh is None:
                raise ValueError("SCREENSHOT_MISSING_HEADER")
            idat.append(payload)
        elif tag == b"IEND":
            if size != 0 or nxt != len(raw):
                raise ValueError("SCREENSHOT_TERMINATOR_INVALID")
            end_seen = True
            break
        p = nxt
    if not end_seen or not wh or not idat:
        raise ValueError("SCREENSHOT_INCOMPLETE")
    expected = (wh[0] * 3 + 1) * wh[1]
    if expected > 8_000_000:
        raise ValueError("SCREENSHOT_DECODE_OVERSIZE")
    decoder = zlib.decompressobj()
    pixels = decoder.decompress(b"".join(idat), expected + 1)
    if (len(pixels) != expected or not decoder.eof or
        decoder.unconsumed_tail or decoder.unused_data):
        raise ValueError("SCREENSHOT_DECODE_INVALID")


def _read_json(path: Path) -> dict:
    if not path.is_file() or path.is_symlink():
        raise ValueError("MISSING_OR_LINKED_PRIVATE_RECEIPT")
    raw = path.read_bytes()
    if len(raw) > 1_200_000:
        raise ValueError("OVERSIZE_PRIVATE_RECEIPT")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("INVALID_PRIVATE_RECEIPT")
    return parsed


def reconcile_browser_receipts(
    repo: Path, *, frozen_commit: str, packages: list[str],
    receipt_root: Path,
) -> dict:
    """Return bounded metadata after exact existing-file verification only."""
    root = repo.resolve(strict=True)
    dest = receipt_root.resolve(strict=True)
    if (not root.is_dir() or not dest.is_dir() or dest.is_relative_to(root) or
        receipt_root.is_symlink() or
        not isinstance(packages, list) or not 1 <= len(packages) <= 12 or
        len(set(packages)) != len(packages)):
        raise ValueError("INVALID_RECEIPT_SCOPE")
    rows_total = 0
    images_total = 0
    cases = []
    script_modes: set[str] = set()
    player_modes: set[str] = set()
    for relative in packages:
        # Exact repo-contained, non-symlink package; never open source PDFs.
        if not isinstance(relative, str) or not relative.startswith("content/"):
            raise ValueError("INVALID_PACKAGE_SCOPE")
        package_path = root.joinpath(*relative.split("/"))
        if (package_path.is_symlink() or not package_path.is_file() or
            not package_path.resolve().is_relative_to(root)):
            raise ValueError("INVALID_PACKAGE_SCOPE")
        package_bytes = package_path.read_bytes()
        package_hash = sha256(package_bytes).hexdigest()
        package_mode = verify_git_checkout_sha(
            root, frozen_commit, relative, package_hash,
        )
        package = json.loads(package_bytes)
        activity_ids = [a["id"] for a in package["activities"]]
        if len(activity_ids) != len(set(activity_ids)):
            raise ValueError("INVALID_PACKAGE_ACTIVITIES")
        folder = dest / ("learner-browser-" + package_hash[:16])
        if folder.is_symlink() or not folder.is_dir():
            raise ValueError("MISSING_RECEIPT_DIRECTORY")
        evidence = _read_json(folder / "learner-receipt.json")
        summary = _read_json(folder / "summary.json")
        if (evidence.get("packageSha256") != package_hash or
            summary.get("packageSha256") != package_hash or
            evidence.get("publicationAuthorized") is not False or
            summary.get("publicationAuthorized") is not False or
            summary.get("academicAcceptanceGranted") is not False or
            summary.get("technicalAcceptanceGranted") is not False or
            summary.get("status") !=
            "COMPLETE_BROWSER_COVERAGE_UNDER_INDEPENDENT_REVIEW"):
            raise ValueError("CONTRADICTORY_ACCEPTANCE_CLAIM")
        script_mode = verify_git_checkout_sha(
            root, frozen_commit, _CODE_FILES[0], evidence.get("auditScriptSha256")
        )
        player_mode = verify_git_checkout_sha(
            root, frozen_commit, _CODE_FILES[1], evidence.get("learnerPlayerSha256")
        )
        if (summary.get("auditScriptSha256") != evidence.get("auditScriptSha256")
            or summary.get("learnerPlayerSha256") != evidence.get("learnerPlayerSha256")):
            raise ValueError("RECEIPT_CODE_IDENTITY_CONFLICT")
        coverage = audit_full_learner_coverage(package, evidence)
        if coverage["status"] != "COMPLETE_COVERAGE_METADATA_UNVERIFIED":
            raise ValueError("INCOMPLETE_REPORTED_INTERACTION_COVERAGE")
        records = evidence["checks"]
        expected_files = set()
        for row in records:
            name = row.get("screenshotFile")
            index = activity_ids.index(row["activityId"]) + 1
            required_name = f"{index:02d}-{row['locale']}-{row['viewportWidth']}.png"
            if name != required_name or name in expected_files:
                raise ValueError("SCREENSHOT_REUSED_OR_UNSAFE_NAME")
            expected_files.add(name)
            path = folder / name
            if path.is_symlink() or not path.is_file():
                raise ValueError("MISSING_OR_LINKED_SCREENSHOT")
            data = path.read_bytes()
            if sha256(data).hexdigest() != row.get("screenshotSha256"):
                raise ValueError("SCREENSHOT_DIGEST_MISMATCH")
            _png_valid(data, row["viewportWidth"])
            images_total += 1
        if {p.name for p in folder.glob("*.png")} != expected_files:
            raise ValueError("SCREENSHOT_FILE_ROSTER_MISMATCH")
        rows_total += len(records)
        cases.append({
            "packageSha256": package_hash,
            "existingRows": len(records),
            "screenshotsIntegrityVerified": len(records),
            "packageCheckoutMode": package_mode,
        })
        script_modes.add(script_mode)
        player_modes.add(player_mode)
    return {
        "status": "EXISTING_BROWSER_FILE_INTEGRITY_VERIFIED",
        "frozenGitSha": frozen_commit,
        "packagesChecked": len(cases),
        "existingRowsChecked": rows_total,
        "screenshotsShaAndPngIntegrityVerified": images_total,
        "scriptCheckoutModes": sorted(script_modes),
        "playerCheckoutModes": sorted(player_modes),
        "cases": cases,
        "browserInteractionsIndependentlyVerified": False,
        "scientificOrMultilingualSemanticsVerified": False,
        "visualPedagogyVerified": False,
        "academicAcceptanceGranted": False,
        "technicalAcceptanceGranted": False,
        "publicationAuthorized": False,
    }

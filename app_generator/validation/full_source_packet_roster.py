"""Full-roster independent original PDF passage identity audit (never academic PASS).

Private source text exists only in memory. The report contains digests and
physical PDF page indices, never passages, prompts or model responses.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.validation.reviewer_source_packets import source_packets_for_activities


def verify_full_source_packet_roster(
    *, package_file: Path, source_pdf: Path, packets_file: Path,
    expected_count: int = 18,
) -> dict[str, Any]:
    if type(expected_count) is not int or not 1 <= expected_count <= 100:
        raise ValueError("bounded expected source packet count required")
    package_bytes = package_file.read_bytes()
    pdf_bytes = source_pdf.read_bytes()
    manifest = json.loads(packets_file.read_text(encoding="utf-8"))
    package = json.loads(package_bytes.decode("utf-8"))
    if not isinstance(manifest, dict) or not isinstance(package, dict):
        raise ValueError("invalid private source manifest or package")
    source_sha = sha256(pdf_bytes).hexdigest()
    package_sha = sha256(package_bytes).hexdigest()
    if (not pdf_bytes.startswith(b"%PDF-") or
            manifest.get("packageSha256") != package_sha or
            manifest.get("sourceSha256") != source_sha):
        raise ValueError("original PDF or corrected package hash mismatch")
    activities = package.get("activities")
    if not isinstance(activities, list) or len(activities) != expected_count:
        raise ValueError("exact expected source activity count mismatch")
    if any(not isinstance(a, dict) or not isinstance(a.get("id"), str) or
           not a["id"] for a in activities):
        raise ValueError("invalid private source activity ID")
    ids = [a["id"] for a in activities]
    if len(set(ids)) != expected_count:
        raise ValueError("duplicate original-source activity")
    packets = manifest.get("packets")
    if not isinstance(packets, dict) or set(packets) != set(ids):
        raise ValueError("source packet roster does not match package activity IDs")
    anchors = []
    for aid in ids:
        packet = packets[aid]
        if not isinstance(packet, dict) or not isinstance(packet.get("sourceAnchors"), list):
            raise ValueError("source packet missing mandatory exact passage anchors")
        anchors.extend(packet["sourceAnchors"])
    # Re-extract original PDF once, independently verify every quote in context.
    verified = source_packets_for_activities(source_pdf, source_sha, package, anchors)
    if set(verified) != set(ids):
        raise ValueError("fresh original source packet coverage mismatch")
    results = []
    for aid in ids:
        received, declared = verified[aid], packets[aid]
        for field in ("sourceEvidence", "sourceAnchors", "passageSha256",
                      "verifiedPages", "passageCount", "sourceSha256"):
            if field not in declared or declared[field] != received[field]:
                raise ValueError("private source passage/physical page receipt mismatch")
        results.append({
            "activityId": aid,
            "verifiedPhysicalPdfPages": received["verifiedPages"],
            "passageCount": received["passageCount"],
            "allPassagesReextracted": True,
            "sourceMeaningProven": False,
        })
    return {
        "status": "EXACT_ORIGINAL_SOURCE_ROSTER_REVERIFIED",
        "packageSha256": package_sha, "sourceSha256": source_sha,
        "sourcePacketRosterCount": len(ids),
        "newlyReverifiedSourceActivities": len(results),
        "newlyReverifiedSourcePassages": sum(r["passageCount"] for r in results),
        "activityEvidence": results,
        "sourceInterpretationVerified": False,
        "translationVerified": False,
        "visualSemanticsVerified": False,
        "academicQA": "REVIEW_REQUIRED",
        "formalAcademicPASS": False,
        "publicationAuthorized": False,
    }

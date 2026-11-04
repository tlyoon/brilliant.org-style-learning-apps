"""Bind private immutable reviewer claim inventory to the actual controlled source.

Strictly read-only. Original PDFs, private package text, model responses and
quoted source passages never enter an output artifact or public logs.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.validation.academic_claim_inventory import audit_immutable_claims
from app_generator.validation.autonomous_ai_review import canonical_digest
from app_generator.validation.reviewer_source_packets import verified_source_packet


def audit_source_bound_claim_run(
    *, package_file: Path, pdf_file: Path, packets_file: Path,
    claims_dir: Path, activity_id: str, claim_prefix: str,
) -> dict[str, Any]:
    """Re-extract exact original PDF passage before reading claim metadata."""
    package_bytes=package_file.read_bytes()
    pdf_bytes=pdf_file.read_bytes()
    packet_manifest=json.loads(packets_file.read_text(encoding="utf-8"))
    package=json.loads(package_bytes.decode("utf-8"))
    activities=package.get("activities",[])
    if (not isinstance(activities,list) or not activities or
            any(not isinstance(a,dict) or not isinstance(a.get("id"),str) for a in activities)):
        raise ValueError("valid nonempty private generated activity package required")
    ids=[a["id"] for a in activities]
    if len(set(ids))!=len(ids) or activity_id not in ids:
        raise ValueError("requested activity absent or duplicated in corrected package")
    if not isinstance(packet_manifest,dict):
        raise ValueError("invalid source packet manifest")
    declared=packet_manifest.get("packets")
    if not isinstance(declared,dict) or set(declared)!=set(ids):
        raise ValueError("private source-packet roster does not match exact package")
    package_sha=sha256(package_bytes).hexdigest()
    source_sha=sha256(pdf_bytes).hexdigest()
    if (packet_manifest.get("packageSha256")!=package_sha or
            packet_manifest.get("sourceSha256")!=source_sha or
            pdf_bytes[:5]!=b"%PDF-"):
        raise ValueError("controlled original PDF or corrected package SHA mismatch")
    candidate=declared[activity_id]
    if not isinstance(candidate,dict) or not isinstance(candidate.get("sourceAnchors"),list):
        raise ValueError("private activity has no source anchors")
    context=verified_source_packet(
        pdf_file,source_sha,activity_id,candidate["sourceAnchors"],
    )
    if (context["sourceEvidence"]!=candidate.get("sourceEvidence") or
            context["passageSha256"]!=candidate.get("passageSha256") or
            context["verifiedPages"]!=candidate.get("verifiedPages")):
        raise ValueError("private packet differs from independently re-extracted original source")
    activity=next(a for a in activities if a["id"]==activity_id)
    result=audit_immutable_claims(
        claims_dir,claim_prefix=claim_prefix,activity_id=activity_id,
        activity_sha256=canonical_digest(activity),
        package_sha256=package_sha,source_sha256=source_sha,
        source_context_sha256=canonical_digest(context),
    )
    # Only THIS selected activity's passage is independently re-extracted.
    # A complete roster does not assert that the other passages were checked.
    result["sourcePacketRosterCount"]=len(ids)
    result["sourcePacketReverifiedCount"]=1
    result["originalSourcePassageReverified"]=True
    result["sourcePhysicalPages"]=context["verifiedPages"]
    result["sourceInterpretationVerified"]=False
    result["translationVerified"]=False
    result["visualSemanticsVerified"]=False
    result["formalAcademicPASS"]=False
    result["publicationAuthorized"]=False
    return result

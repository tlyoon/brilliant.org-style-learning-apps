"""Populate a private run's reviewer source packets from versioned local evidence.

The registry is private under state_dir, not in the public repository. The
operator supplies provenance ONCE; subsequent matching generator runs use it
without manual academic sign-off. No source passages or credentials enter Git.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.filesystem.outputs import write_json_atomic
from app_generator.runtime.run_context import RunContext
from app_generator.validation.source_anchor_migration import migrate_anchor_packets

REGISTRY_DIR="academic-review-provenance"
RUN_PACKET_NAME="academic-review-source-packets.json"

def _canonical_private_file(value: Any, *, repo_root: Path,
                            allow_repo_readonly: bool=False) -> Path:
    if not isinstance(value,str):
        raise ValueError("private provenance path must be a string")
    path=Path(value)
    if not path.is_absolute() or not path.is_file():
        raise ValueError("private provenance input missing or not absolute")
    path=path.resolve()
    if path.is_relative_to(repo_root.resolve()) and not allow_repo_readonly:
        raise ValueError("private proof receipts cannot be read from Git checkout")
    return path

def provision_run_source_packets(
    config: Any, context: RunContext,
    package_file: Path, source_pdf: Path | None,
    *, registry_file: Path | None=None,
) -> dict[str,Any]:
    """Read bounded provenance; never overwrite a run's existing source packet.

    Never attempt network authentication or a Gemini request. Exceptions
    indicate stale evidence and should be recorded as AUTO_SOURCE_CHECK.
    """
    repository=config.repo_root.resolve()
    dest=context.validation/RUN_PACKET_NAME
    if dest.resolve().is_relative_to(repository):
        raise ValueError("private source packet destination inside Git checkout")
    if registry_file is None:
        if source_pdf is None or not source_pdf.is_file():
            return {"status":"NO_CONTROLLED_SOURCE_FOR_PROVENANCE",
                    "packetCreated":False,"academicQA":"REVIEW_REQUIRED",
                    "publicationAuthorized":False}
        source_digest=sha256(source_pdf.read_bytes()).hexdigest()
        registry=config.state_dir/REGISTRY_DIR/f"{source_digest}.json"
    else:
        registry=registry_file
    registry=registry.resolve()
    if registry.is_relative_to(repository):
        raise ValueError("academic provenance registry cannot be inside Git")
    if not registry.is_file():
        return {"status":"NO_PRIVATE_PROVENANCE_REGISTRY",
                "packetCreated":False,"academicQA":"REVIEW_REQUIRED",
                "publicationAuthorized":False}
    evidence=json.loads(registry.read_text(encoding="utf-8"))
    if (not isinstance(evidence,dict) or evidence.get("version")!=1 or
        set(evidence)!={"version","sourceSha256","priorPackage","proofReceipts"} or
        not isinstance(evidence["proofReceipts"],list) or
        len(evidence["proofReceipts"])!=2):
        raise ValueError("private source registry malformed or unsupported")
    expected=evidence["sourceSha256"]
    if (not isinstance(expected,str) or len(expected)!=64 or
        any(ch not in "0123456789abcdef" for ch in expected)):
        raise ValueError("invalid source SHA in private registry")
    if source_pdf is None or not source_pdf.is_file():
        raise ValueError("automatic academic packet requires one controlled local PDF")
    if sha256(source_pdf.read_bytes()).hexdigest()!=expected:
        raise ValueError("controlled source differs from private academic registry")
    if not package_file.is_file():
        raise ValueError("validated output package absent")
    # Generated prior package is read-only and may be inside protected
    # historical Git checkout. Never write it or copy source evidence there.
    prior=_canonical_private_file(evidence["priorPackage"],repo_root=repository,
                                  allow_repo_readonly=True)
    receipts=[
        _canonical_private_file(p,repo_root=repository)
        for p in evidence["proofReceipts"]
    ]
    if len({p.resolve() for p in receipts})!=len(receipts):
        raise ValueError("two distinct independent evidence receipts required")
    if dest.exists():
        # Keep the already captured run data immutable: downstream verifies
        # exact SHA/source contents; stale packet produces a safe follow-up.
        return {"status":"RUN_PACKET_EXISTS_RECHECK_IN_STAGE",
                "packetCreated":False,"academicQA":"REVIEW_REQUIRED",
                "publicationAuthorized":False}
    result=migrate_anchor_packets(
        pdf=source_pdf,source_sha256=expected,prior_package=prior,
        target_package=package_file,prior_receipts=receipts,
    )
    # Use exact packet shape consumed by academic_generation_stage.
    write_json_atomic(dest,result)
    if sha256(package_file.read_bytes()).hexdigest()!=result["packageSha256"]:
        raise ValueError("target package changed during source packet creation")
    return {
        "status":"SOURCE_PACKET_VERIFIED_AND_SAVED",
        "packetCreated":True,
        "sourceSha256":expected,
        "packageSha256":result["packageSha256"],
        "activityCount":result["activityCount"],
        "verifiedSourceLocations":result["verifiedSourceLocations"],
        "changedActivityCount":len(result["changedActivityIds"]),
        "sourceInterpretationVerified":False,
        "academicQA":"REVIEW_REQUIRED",
        "publicationAuthorized":False,
    }

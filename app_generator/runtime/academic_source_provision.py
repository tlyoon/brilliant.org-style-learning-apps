"""Populate a private run's reviewer source packets from versioned local evidence.

The registry is private under state_dir, not in the public repository. The
operator supplies provenance ONCE; subsequent matching generator runs use it
without manual academic sign-off. No source passages or credentials enter Git.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from pathlib import Path
from typing import Any

from app_generator.filesystem.outputs import write_json_atomic
from app_generator.runtime.run_context import RunContext
from app_generator.validation.source_anchor_migration import migrate_anchor_packets
from app_generator.validation.source_passages import extract_pages
from app_generator.validation.reviewer_source_packets import verified_source_packet

REGISTRY_DIR="academic-review-provenance"
RUN_PACKET_NAME="academic-review-source-packets.json"

# Local source location is *not* semantic proof or authority to transmit
# copyright-controlled passages to a remote model.
_STOPWORDS = {
    "about", "after", "before", "because", "between", "during", "explain",
    "following", "given", "their", "there", "these", "those", "which", "where",
    "while", "using", "total", "system", "systems", "objects", "object",
    "could", "would", "should", "describe", "determine", "whether", "through",
    "different", "during", "with", "from", "what", "when", "have", "does",
}

def _topic_terms(text: str) -> set[str]:
    return set(re.findall(r"[a-z]{4,}", text.lower())) - _STOPWORDS

def _passages(page: str):
    """Yield bounded literal PDF-text spans; never synthesize textbook prose."""
    for paragraph in re.split(r"\n[ \t]*\n", page):
        clean = re.sub(r"\s+", " ", paragraph).strip()
        if "\ufffd" in clean:
            continue
        # Long paragraphs are split without semantic rewriting; every
        # candidate must still occur literally in its original PDF page.
        for start in range(0, len(clean), 750):
            quote = clean[start:start + 750].strip()
            if len(quote) >= 60 and len(quote.split()) >= 9:
                yield quote

def _bootstrap_local_source_locations(
    config: Any, context: RunContext, package_file: Path,
    source_pdf: Path, dest: Path, expected: str,
) -> dict[str, Any]:
    """Recover first-run *local* page anchors, never source/model permission."""
    root = config.repo_root.resolve()
    if source_pdf.resolve().is_relative_to(root):
        return {"status": "BLOCKED_PRIVATE_SOURCE_IN_REPOSITORY",
                "packetCreated": False, "publicationAuthorized": False}
    package = json.loads(package_file.read_text(encoding="utf-8"))
    relative = package.get("sourceManifest")
    if not isinstance(relative, str) or not relative.startswith("content/source-manifests/"):
        return {"status": "NO_VERIFIED_SOURCE_MANIFEST",
                "packetCreated": False, "publicationAuthorized": False}
    manifest_path = (root / relative).resolve()
    if not manifest_path.is_relative_to((root / "content" / "source-manifests").resolve()):
        return {"status": "BLOCKED_SOURCE_MANIFEST_PATH",
                "packetCreated": False, "publicationAuthorized": False}
    if not manifest_path.is_file():
        return {"status": "NO_VERIFIED_SOURCE_MANIFEST",
                "packetCreated": False, "publicationAuthorized": False}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("sha256") != expected:
        return {"status": "BLOCKED_SOURCE_MANIFEST_MISMATCH",
                "packetCreated": False, "publicationAuthorized": False}
    rights = manifest.get("rightsNote")
    # A controlled transformation/provenance declaration supports only this
    # on-device local-text operation, NOT third-party image rights or model use.
    if not isinstance(rights, str) or not rights.startswith("Instructor-authorized controlled source"):
        return {"status": "BLOCKED_SOURCE_USE_SCOPE",
                "packetCreated": False, "publicationAuthorized": False}
    activities = package.get("activities")
    if (not isinstance(activities, list) or not activities or
        any(not isinstance(x, dict) or not isinstance(x.get("id"), str)
            or not x["id"] for x in activities) or
        len({x["id"] for x in activities}) != len(activities)):
        return {"status": "LOCAL_SOURCE_RELEVANCE_NOT_VERIFIED",
                "packetCreated": False, "publicationAuthorized": False}
    pages = extract_pages(source_pdf)
    candidates = []
    for page_index, page in enumerate(pages, 1):
        for quote in _passages(page):
            candidates.append((page_index, quote, _topic_terms(quote)))
    packets = {}
    for activity in activities:
        prompt = activity.get("prompt")
        prompt_en = prompt.get("en", "") if isinstance(prompt, dict) else ""
        objective = activity.get("objective", "")
        query = _topic_terms(" ".join(x for x in (prompt_en, objective) if isinstance(x, str)))
        if len(query) < 3:
            break
        # A multi-concept question can need more than one source passage.
        # Cover complementary terms rather than weakening the minimum
        # aggregate relevance requirement to force a single-passage PASS.
        covered = set()
        anchors = []
        unused = list(candidates)
        for _ in range(3):
            ranked = sorted(
                ((len((query - covered) & words), page, quote, words)
                 for page, quote, words in unused),
                key=lambda x: (-x[0], x[1], x[2]),
            )
            if not ranked or ranked[0][0] < 3:
                break
            _score, page, quote, words = ranked[0]
            anchors.append({"activityId": activity["id"],
                            "pageIndex": page, "quotedText": quote})
            covered.update(query & words)
            unused = [x for x in unused if (x[0], x[1]) != (page, quote)]
            if len(covered) / len(query) >= 0.25:
                break
        if not anchors or len(covered) / len(query) < 0.25:
            break
        try:
            packet = verified_source_packet(
                source_pdf, expected, activity["id"], anchors,
                extractor=lambda _: pages,
            )
        except (ValueError, OSError):
            break
        packets[activity["id"]] = packet
    if len(packets) != len(activities):
        return {"status": "LOCAL_SOURCE_RELEVANCE_NOT_VERIFIED",
                "packetCreated": False, "verifiedSourceLocations": 0,
                "academicQA": "REVIEW_REQUIRED", "publicationAuthorized": False}
    result = {
        "packageSha256": sha256(package_file.read_bytes()).hexdigest(),
        "sourceSha256": expected, "packets": packets,
        "sourcePacketOrigin": "AUTOMATED_LOCAL_TEXT",
        "modelSubmissionAuthorized": False,
        "sourceInterpretationVerified": False,
        "academicQA": "REVIEW_REQUIRED", "publicationAuthorized": False,
    }
    write_json_atomic(dest, result)
    return {
        "status": "LOCAL_SOURCE_LOCATIONS_VERIFIED_PENDING_RIGHTS",
        "packetCreated": True, "verifiedSourceLocations": len(packets),
        "sourceInterpretationVerified": False,
        "modelSubmissionAuthorized": False,
        "academicQA": "REVIEW_REQUIRED", "publicationAuthorized": False,
    }

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
        if registry_file is None and package_file.is_file():
            package = json.loads(package_file.read_text(encoding="utf-8"))
            if isinstance(package, dict) and isinstance(package.get("sourceManifest"), str):
                if dest.exists():
                    # Existing claim remains immutable even if source or
                    # package versions have since changed.
                    return {"status": "RUN_PACKET_EXISTS_RECHECK_IN_STAGE",
                            "packetCreated": False, "academicQA": "REVIEW_REQUIRED",
                            "publicationAuthorized": False}
                return _bootstrap_local_source_locations(
                    config, context, package_file, source_pdf, dest, source_digest,
                )
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

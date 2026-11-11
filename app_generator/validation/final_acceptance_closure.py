"""Mandatory fail-closed Chapter 9 final-acceptance admission, not a retry engine.

This policy reads the owner-approved frozen roster and terminal receipts.
It cannot manufacture rights or permit attempts because a path/chat changed.
Only a separately authorized new scope and material evidence may amend policy.
Source-free; no external actions, model, browser or PDF reads.
"""
from __future__ import annotations

from hashlib import sha256
from app_generator.validation.git_checkout_identity import canonical_git_blob_sha1
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
CHARTER = ROOT / "docs" / "acceptance_closure_chapter9.json"
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_BLOB = re.compile(r"[0-9a-f]{40}\Z")
_SECTION = tuple(f"9.{n}" for n in range(1, 7))
_REQUIRED_GATES = frozenset({
    "pilotScope", "originalSourceIdentity", "sourceLocation",
    "physicsAnswersAndTrilingualMeaning",
    "diagramVisualPedagogy", "learnerViewportAndAccessibility",
    "adaptivePrivacyOperations", "engineeringHeadCI", "releaseAuthorization",
})
_EXCLUDED_TECHNICAL_GATES = (
    "textbookEdition", "rightsHolder", "sourceAndFigureRights",
)
_ACTIONS = frozenset({"browser", "local_source", "academic_external", "publication"})
_STATUSES = frozenset({
    "PASS_VERIFIED", "FAIL_REPRODUCED", "NOT_VERIFIED",
    "BLOCKED_EXTERNAL", "NOT_AUTHORIZED", "DEFERRED_APPROVED",
    "NOT_APPLICABLE",
})


def load_frozen_charter(file: Path = CHARTER) -> dict:
    """Validate owner-updated V2 technical gates and preserve finite stop controls."""
    if file.is_symlink() or not file.is_file() or file.stat().st_size > 50000:
        raise ValueError("CLOSURE_CHARTER_MISSING_OR_UNSAFE")
    record = json.loads(file.read_text(encoding="utf-8"))
    if (not isinstance(record, dict) or record.get("schemaVersion") != 1
        or record.get("project") != "BOSLA"
        or record.get("contract") != "FINAL_ACCEPTANCE_NO_REPEAT_V2"
        or record.get("policy", {}).get("frozen") is not True
        or record["policy"].get("newCampaignsAuthorized") != []
        or record["policy"].get("excludedTechnicalAcceptanceGates") != list(_EXCLUDED_TECHNICAL_GATES)
        or record["policy"].get("historicalAttemptsResetAllowed") is not False
        or record["policy"].get("sourceBearingModelCallsAllowed") is not False
        or record["policy"].get("publicReleaseAuthorized") is not False
        or record.get("repeatedInvocationsWithoutNewEvidence") != "CLOSURE_STALL"
        or record.get("finalDisposition") != "NOT_COMPLETE_WITH_NAMED_BLOCKERS"):
        raise ValueError("FROZEN_CLOSURE_CONTRACT_CHANGED")
    cases = record.get("frozenCandidates")
    if not isinstance(cases, list) or len(cases) != 6:
        raise ValueError("FROZEN_SIX_SECTION_ROSTER_CHANGED")
    for n, case in enumerate(cases, 1):
        section = f"9.{n}"
        if (not isinstance(case, dict) or case.get("section") != section
            or case.get("manifest") !=
            f"content/source-manifests/chapter-9-section-9-{n}.json"
            or not isinstance(case.get("packageSha256"), str)
            or not _SHA.fullmatch(case["packageSha256"])
            or not isinstance(case.get("packageGitBlobSha1"), str)
            or not _BLOB.fullmatch(case["packageGitBlobSha1"])
            or case.get("activityCount") != 18
            or case.get("browserCampaign") != "TERMINAL"
            or case.get("localSourceCampaign") != "TERMINAL"
            or case.get("independentAcademicExternalReview") !=
            "TERMINAL"
            or case.get("exactViewportVerified") is not False):
            raise ValueError("FROZEN_CANDIDATE_STOP_CHANGED")
    gates = record.get("gates")
    if (not isinstance(gates, list) or len(gates) != len(_REQUIRED_GATES)
        or {g.get("id") for g in gates if isinstance(g, dict)} != _REQUIRED_GATES
        or any(not isinstance(g, dict) or g.get("status") not in _STATUSES
               for g in gates)):
        raise ValueError("FROZEN_ACCEPTANCE_GATES_CHANGED")
    by = {g["id"]: g for g in gates}
    if (by["releaseAuthorization"]["status"] != "NOT_AUTHORIZED"
        or by["physicsAnswersAndTrilingualMeaning"]["status"] != "NOT_VERIFIED"
        or by["learnerViewportAndAccessibility"]["status"] != "NOT_VERIFIED"):
        raise ValueError("UNSUPPORTED_ACCEPTANCE_PROMOTION")
    return record


def assert_campaign_admissible(
    package_file: Path, action: str, *, charter_file: Path = CHARTER,
) -> str:
    """Prevent repeats before external/PDF/browser work or private run creation.

    Returns NOT_APPLICABLE for unrelated packages. Any recognized original
    source with a different package hash is drift, not a new authorized trial.
    """
    if action not in _ACTIONS:
        raise ValueError("UNKNOWN_ACCEPTANCE_CAMPAIGN")
    charter = load_frozen_charter(charter_file)
    if package_file.is_symlink() or not package_file.is_file():
        raise ValueError("PACKAGE_MISSING_OR_LINKED")
    raw = package_file.read_bytes()
    if len(raw) > 2_000_000:
        raise ValueError("PACKAGE_TOO_LARGE")
    pkg = json.loads(raw.decode("utf-8"))
    if not isinstance(pkg, dict):
        raise ValueError("INVALID_PACKAGE")
    source_manifest = pkg.get("sourceManifest")
    matches = [c for c in charter["frozenCandidates"]
               if c["manifest"] == source_manifest]
    if not matches:
        # Stripping/changing the manifest cannot disguise an existing frozen
        # chapter-section candidate as a fresh authorized campaign.
        subtopic = pkg.get("subchapter")
        if (pkg.get("chapter") == "Chapter 9"
            and isinstance(subtopic, str)
            and any(subtopic.startswith(section + " ")
                    for section in _SECTION)):
            raise ValueError("STOP_FROZEN_PACKAGE_IDENTITY_DRIFT")
        return "NOT_APPLICABLE"
    case = matches[0]
    # Reuse the established Git/CRLF recovery family (BSA-127/131).
    # A historical frozen Git blob identity is portable across actual LF
    # Linux checkouts and CRLF Windows checkouts; raw SHA-256 alone is not.
    if canonical_git_blob_sha1(raw) != case["packageGitBlobSha1"]:
        raise ValueError("STOP_FROZEN_PACKAGE_IDENTITY_DRIFT")
    if action == "browser":
        raise ValueError("STOP_TERMINAL_BROWSER_ACCEPTANCE_CAMPAIGN")
    if action == "local_source":
        raise ValueError("STOP_TERMINAL_SOURCE_LOCATION_CAMPAIGN")
    if action == "academic_external":
        raise ValueError("STOP_TERMINAL_INDEPENDENT_REVIEW_CAMPAIGN")
    raise ValueError("STOP_RELEASE_NOT_AUTHORIZED")


def final_disposition(file: Path = CHARTER) -> dict:
    record = load_frozen_charter(file)
    return {
        "project": "BOSLA",
        "scope": "chapter-9-sections-9.1-through-9.6",
        "finalDisposition": record["finalDisposition"],
        "gates": {g["id"]: g["status"] for g in record["gates"]},
        "frozenCandidates": len(record["frozenCandidates"]),
        "newCampaignsAuthorized": 0,
        "closureStall": True,
        "academicAcceptanceGranted": False,
        "publicationAuthorized": False,
    }

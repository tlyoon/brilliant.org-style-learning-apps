"""Reuse historical Section9.4 conservation-terminology auto-repair on 9.1.

Create a private, immutable new candidate version, never edit the old
source-pinned package, and never transfer an old review claim to new text.
Source location on this new candidate must be independently reverified
before scientific admission; absence of a known defect is not PASS.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.validation.academic_acceptance_matrix import audit_activity_matrix
from app_generator.validation.academic_qa import REQUIRED
from app_generator.validation.language_qa import check_multilingual_surface
from app_generator.validation.malay_conservation_lexicon import (
    _replace_in_malay, conservation_lexicon_flags, ROOTS,
)

_CANDIDATE = "V20_MALAY_CONSERVATION_VERSIONED_CANDIDATE.json"
_RECEIPT = "V20_MALAY_CONSERVATION_TARGETED_REPAIR_RECEIPT.json"
_REPAIR_STATUS = "KNOWN_MALAY_CONSERVATION_NEGATIVE_FAILURES_REPAIRED_VERSIONED"


def auto_repair_known_malay_science_defects(
    *, repo: Path, folder: Path, original_package: dict[str, Any],
    original_package_sha: str, source_pdf: Path, source_sha: str,
    original_audit: dict[str, Any], identity: dict[str, str],
) -> dict[str, Any]:
    """Run historical locale-only fix if AND ONLY IF these are all the FAILs."""
    rows = original_audit.get("activities", [])
    acts = original_package.get("activities", [])
    if not isinstance(rows, list) or not isinstance(acts, list) or len(rows) != 18:
        raise ValueError("V20_REPAIR_REAL_ORIGINAL_18_REQUIRED")
    by_id = {a.get("id"): a for a in acts if isinstance(a, dict)}
    if len(by_id) != 18 or len({r.get("activityId") for r in rows}) != 18:
        raise ValueError("V20_REPAIR_ORIGINAL_ACTIVITY_IDENTITY_INVALID")
    failing = {r["activityId"] for r in rows if r.get("academicQA") == "FAIL"}
    if any(aid not in by_id for aid in failing):
        raise ValueError("V20_REPAIR_UNKNOWN_ORIGINAL_ACTIVITY")
    if not failing:
        return {"status": "NO_DETERMINISTIC_FAILS_TO_REPAIR", "repairedActivityCount": 0,
                "publicationAuthorized": False}
    # The historical repair fixes only the flagged term roots. All other
    # academic failure classes remain in the independent repair queue.
    qualified = (
        all(
            r.get("academicQA") != "FAIL"
            or (
                r.get("gates", {}).get("multilingual_meaning") == "FAIL"
                and all(
                    r["gates"][gate] != "FAIL" for gate in REQUIRED
                    if gate != "multilingual_meaning"
                )
                and check_multilingual_surface(by_id[r["activityId"]]).result == "FAIL"
                and bool(conservation_lexicon_flags(by_id[r["activityId"]]))
            )
            for r in rows
        )
    )
    if not qualified:
        return {"status": "UNRELATED_DETERMINISTIC_FAILS_REQUIRE_SEPARATE_REPAIR",
                "repairedActivityCount": 0, "publicationAuthorized": False}

    counts = {source: 0 for source, _, _ in ROOTS}
    paths: list[str] = []
    candidate = _replace_in_malay(original_package, "", paths, counts)
    replacement_count = sum(counts.values())
    expected_changed = {aid for aid in by_id
                        if by_id[aid] != next(x for x in candidate["activities"]
                                               if x["id"] == aid)}
    if (not 0 < replacement_count <= 200
            or not paths or len(paths) != len(set(paths))
            or expected_changed != failing
            or any(not re.fullmatch(r"/activities/\d+/[\w/\d-]+/ms", path)
                   for path in paths)
            or conservation_lexicon_flags(candidate)
            or any(check_multilingual_surface(a).result == "FAIL"
                   for a in candidate["activities"])
            or original_package == candidate
            or sha256(json.dumps(
                original_package,sort_keys=True,ensure_ascii=False,
                separators=(",", ":")).encode("utf8")).hexdigest()
            == sha256(json.dumps(
                candidate,sort_keys=True,ensure_ascii=False,
                separators=(",", ":")).encode("utf8")).hexdigest()):
        raise ValueError("V20_REPAIR_HISTORICAL_MALAY_SCOPE_OR_RECHECK_FAILED")
    # Verify all non-Malay bytes/fields are *structurally* unchanged by
    # reverting the eight localized fields and comparing full objects.
    restored = json.loads(json.dumps(candidate, ensure_ascii=False))
    for path in paths:
        parts = path.strip("/").split("/")
        original_node: Any = original_package
        new_node: Any = restored
        for part in parts[:-1]:
            key = int(part) if part.isdecimal() else part
            original_node, new_node = original_node[key], new_node[key]
        new_node["ms"] = original_node["ms"]
    if restored != original_package:
        raise ValueError("V20_REPAIR_CROSSED_NON_MALAY_FIELD_BOUNDARY")

    raw = (json.dumps(candidate, ensure_ascii=False, indent=2) + "\n").encode("utf8")
    digest = sha256(raw).hexdigest()
    path = folder / _CANDIDATE
    if path.exists():
        if path.is_symlink() or path.read_bytes() != raw:
            raise ValueError("V20_REPAIR_PRIVATE_CANDIDATE_TAMPERED")
    else:
        with path.open("xb") as stream:
            stream.write(raw)
    if sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError("V20_REPAIR_PRIVATE_CANDIDATE_WRITE_CHANGED")
    # The existing academic checker is executed AGAIN on the actual new
    # candidate. No old source-packet or old reviewer is allowed to certify
    # the revised version. The source fidelity remains REVIEW_REQUIRED.
    checked = audit_activity_matrix(
        repo_root=repo, package_path=path, source_pdf=source_pdf,
        source_sha256=source_sha, source_packets=None, expected_count=18,
    )
    if (checked.get("counts") != {"PASS": 0, "FAIL": 0, "REVIEW_REQUIRED": 18}
            or checked.get("packageSha256") != digest
            or checked.get("sourceSha256") != source_sha
            or checked.get("publicationAuthorized") is not False
            or any(r.get("sourceLocationVerified") is not False
                   for r in checked["activities"])):
        raise ValueError("V20_REPAIR_NEW_VERSION_GATES_NOT_RECHECKED")
    receipt = _v6_checkpoint(folder / _RECEIPT, {
        **identity, "status": _REPAIR_STATUS,
        "originalPackageSha256": original_package_sha,
        "newPrivateCandidateSha256": digest,
        "affectedOriginalActivityIds": sorted(failing),
        "repairedActivityCount": len(failing),
        "changedMalayFieldCount": len(paths),
        "correctedScientificTerminologyInstances": replacement_count,
        "sourcePdfSha256Unchanged": source_sha,
        "originalPackageModified": False,
        "otherLocalesOrAnswerKeysModified": False,
        "newCandidateFiveGateNegativeFindings": 0,
        "newCandidateSourceLocationFreshlyVerified": False,
        "newCandidateAll18AcademicQA": "REVIEW_REQUIRED",
        "oldGeminiReviewerClaimsTransferred": False,
        "newGeminiRequests": 0,
        "publicationAuthorized": False,
    })
    return {
        "status": _REPAIR_STATUS,
        "receiptSha256": receipt["integritySha256"],
        "candidateSha256": digest,
        "repairedActivityCount": len(failing),
        "correctedTerms": replacement_count,
        "publicationAuthorized": False,
    }

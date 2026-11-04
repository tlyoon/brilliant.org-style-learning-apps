"""Conservative machine action from exact-version scientific contradiction evidence.

This does not verify translated meaning or issue an academic PASS. It consumes
a previously reconciled private activity dossier, not self-asserted model output.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from app_generator.validation.bounded_physics_transfer import digest
from app_generator.validation.impulse_qualifier_repair import ACTIVITY_ID
from app_generator.validation.impulse_v3_audit import ITEM_ID, check_first_option

LOCALES = ("en", "ms", "zh")


def route_source_bound_defect(
    *, package_file: Path, source_pdf: Path, dossier_file: Path,
    expected_package_sha256: str, expected_source_sha256: str,
) -> dict[str, Any]:
    """Verify exact identities and identify known contradictory scope claims."""
    raw = package_file.read_bytes()
    source_raw = source_pdf.read_bytes()
    if source_raw[:5] != b"%PDF-":
        raise ValueError("controlled source is not a PDF")
    package_sha = sha256(raw).hexdigest()
    source_sha = sha256(source_raw).hexdigest()
    if package_sha != expected_package_sha256 or source_sha != expected_source_sha256:
        raise ValueError("controlled original source or candidate version differs")
    package = json.loads(raw)
    dossier = json.loads(dossier_file.read_text(encoding="utf-8"))
    acts = package.get("activities")
    if not isinstance(acts, list) or not acts:
        raise ValueError("source-bound package activities absent")
    ids = [a.get("id") if isinstance(a, dict) else None for a in acts]
    if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("missing or duplicate activity identity")
    selected = [a for a in acts if a["id"] == ACTIVITY_ID]
    if len(selected) != 1:
        raise ValueError("known original activity absent or duplicated")
    activity = selected[0]
    expected = {
        "packageSha256": package_sha,
        "sourceSha256": source_sha,
        "activityId": ACTIVITY_ID,
        "activitySha256": digest(activity),
    }
    if any(dossier.get(k) != v for k, v in expected.items()):
        raise ValueError("private academic dossier does not match exact candidate")
    if (dossier.get("sourceLocationVerifiedInMatrix") is not True or
        dossier.get("boundedPhysicsReceiptMatched") is not True or
        dossier.get("publicationAuthorized") is not False or
        dossier.get("fullAcademicPass") is not False or
        dossier.get("academicQA") not in ("REVIEW_REQUIRED", "FAIL")):
        raise ValueError("independent partial evidence incomplete or prematurely approved")
    ix = activity.get("interaction", {})
    if not isinstance(ix, dict) or not isinstance(ix.get("items"), list):
        raise ValueError("expected original selection structure missing")
    if activity.get("interactionMode") != "selection":
        raise ValueError("original interaction answer mode changed")
    items = ix["items"]
    matches = [(i, item) for i, item in enumerate(items)
               if isinstance(item, dict) and item.get("id") == ITEM_ID]
    if len(matches) != 1:
        raise ValueError("known answer option absent or duplicated")
    index, item = matches[0]
    bounded = check_first_option(item)
    objections = []
    unresolved = []
    for language in LOCALES:
        result = bounded[language]
        for code in result["explicitContradictionCodes"]:
            objections.append({
                "language": language,
                "code": code,
                "path": ["interaction", "items", index, "label", language],
            })
        if result["status"] != "BOUNDED_CONCEPT_PRESENT" and not result["explicitContradictionCodes"]:
            unresolved.append(language)
    mode = ("AUTO_REPAIR" if objections else
            "AUTO_SOURCE_CHECK" if unresolved else
            "AUTO_INDEPENDENT_SEMANTIC_VISUAL_REVIEW")
    return {
        **expected,
        "boundedPhysicsReceiptMatched": True,
        "sourceLocationVerifiedInMatrix": True,
        "objections": objections,
        "unresolvedLanguages": unresolved,
        "nextAction": mode,
        "repairEligible": bool(objections),
        "independentReverificationRequired": True,
        "fullSemanticEquivalenceVerified": False,
        "renderedVisualVerified": False,
        "academicQA": "REVIEW_REQUIRED",
        "publicationAuthorized": False,
        "humanAcademicApprovalRequired": False,
    }
"""Privacy-safe exact-version reconciliation of academic matrix and bounded physics.

This links independent partial evidence, NOT an academic PASS. Receipts alone
cannot demonstrate semantic translation quality or rendered physics.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.validation.academic_qa import REQUIRED
from app_generator.validation.bounded_physics_transfer import digest

VALID_PHYSICS = {
    "UNCHANGED_BOUNDED_PHYSICS_REVERIFIED",
    "REVISED_BOUNDED_PHYSICS_VERIFIED",
}
VALID_OUTCOMES = {"PASS", "FAIL", "REVIEW_REQUIRED"}


def _unique_index(rows: Any, field: str, *, label: str) -> dict[str, dict]:
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{label} must be a nonempty list")
    out = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get(field), str) or not row[field]:
            raise ValueError(f"{label} contains invalid identifiers")
        if row[field] in out:
            raise ValueError(f"{label} contains duplicate identifiers")
        out[row[field]] = row
    return out


def reconcile_activity_evidence(
    *, package_file: Path, source_pdf: Path, matrix_file: Path,
    physics_file: Path, activity_id: str,
) -> dict[str, Any]:
    """Match all activities before extracting one safe activity-specific dossier."""
    data = package_file.read_bytes()
    package_sha = sha256(data).hexdigest()
    source_sha = sha256(source_pdf.read_bytes()).hexdigest()
    if source_pdf.read_bytes()[:5] != b"%PDF-":
        raise ValueError("source file is not a PDF")
    package = json.loads(data)
    matrix = json.loads(matrix_file.read_text(encoding="utf-8"))
    physics = json.loads(physics_file.read_text(encoding="utf-8"))
    acts = _unique_index(package.get("activities"), "id", label="package activities")
    m = _unique_index(matrix.get("activities"), "activityId", label="matrix activities")
    p = _unique_index(physics.get("activities"), "activityId", label="bounded witnesses")
    if activity_id not in acts:
        raise ValueError("selected activity not present")
    if set(acts) != set(m) or set(acts) != set(p):
        raise ValueError("activity coverage is not identical across reports")
    if (
        matrix.get("packageSha256") != package_sha
        or physics.get("revisedPackageSha256") != package_sha
        or physics.get("revisedPackageCanonicalSha256") != digest(package)
        or matrix.get("sourceSha256") != source_sha
        or physics.get("sourceSha256") != source_sha
        or matrix.get("activityCount") != len(acts)
        or physics.get("activityCount") != len(acts)
        or physics.get("boundedPropositionsVerified") != len(acts)
    ):
        raise ValueError("stale or mismatched original package/source evidence")
    if (
        matrix.get("publicationAuthorized") is not False
        or physics.get("publicationAuthorized") is not False
        or physics.get("fullyAcademicallyApproved") != 0
    ):
        raise ValueError("preacceptance receipts cannot authorize publication or approval")
    actual = {s: sum(row.get("academicQA") == s for row in m.values())
              for s in VALID_OUTCOMES}
    if matrix.get("counts") != actual:
        raise ValueError("matrix summary inconsistent with individual outcomes")
    for aid, activity in acts.items():
        digest_now = digest(activity)
        mr, pr = m[aid], p[aid]
        if mr.get("activitySha256") != digest_now or pr.get("currentActivitySha256") != digest_now:
            raise ValueError("activity receipt digest mismatch")
        if (
            mr.get("academicQA") not in VALID_OUTCOMES
            or set(mr.get("gates", {})) != set(REQUIRED)
            or any(s not in VALID_OUTCOMES for s in mr["gates"].values())
            or mr["academicQA"] == "PASS"
            or pr.get("fullAcademicPass") is not False
            or pr.get("publicationAuthorized") is not False
            or pr.get("status") not in VALID_PHYSICS
        ):
            raise ValueError("unsupported or prematurely approved academic evidence")
        pages=mr.get("sourcePages")
        if (not isinstance(pages,list) or
            any(type(page) is not int or page < 1 for page in pages) or
            (mr.get("sourceLocationVerified") is True and not pages) or
            mr.get("sourceLocationVerified") not in (True,False)):
            raise ValueError("invalid PDF page evidence")
        outcome=("FAIL" if "FAIL" in mr["gates"].values()
                 else "PASS" if all(x=="PASS" for x in mr["gates"].values())
                 else "REVIEW_REQUIRED")
        if outcome!=mr["academicQA"]:
            raise ValueError("matrix gate outcomes contradict reported status")
        if mr.get("publicationAuthorized") is not False:
            raise ValueError("individual academic receipt cannot authorize release")
    selected = m[activity_id]
    proof = p[activity_id]
    next_action = (
        "AUTO_REPAIR" if selected["academicQA"] == "FAIL"
        else "AUTO_SOURCE_CHECK" if not selected["sourceLocationVerified"]
        else "AUTO_INDEPENDENT_SEMANTIC_VISUAL_REVIEW"
    )
    return {
        "activityId": activity_id,
        "packageSha256": package_sha,
        "sourceSha256": source_sha,
        "activitySha256": digest(acts[activity_id]),
        "sourceLocationVerifiedInMatrix": selected["sourceLocationVerified"],
        "sourcePages": selected["sourcePages"] if selected["sourceLocationVerified"] else [],
        "boundedPhysicsReceiptMatched": True,
        "boundedPhysicsEvidenceKind": proof["status"],
        "answerStructureErrorCount": len(selected.get("answerStructureErrors", [])),
        "visualContractErrorCount": selected.get("visualContractErrorCount"),
        "gates": selected["gates"],
        "nextAction": next_action,
        "academicQA": selected["academicQA"],
        "fullAcademicPass": False,
        "meaningVerified": False,
        "renderedVisualVerified": False,
        "publicationAuthorized": False,
        "humanAcademicApprovalRequired": False,
        "qualification": (
            "An independently produced exact-version source-location matrix and bounded "
            "physics receipt align; semantic, distractor, translation and rendered-visual "
            "correctness are not established by this reconciliation."
        ),
    }
"""Source-free academic evidence gap inventory, bound to exact candidate revisions.

A matrix claim or a source page's existence is not independent proof of
scientific accuracy, translation equivalence or diagram meaning. This module
cannot grant academic PASS or publication, even if every supplied status says
PASS. Genuine proof requires separate source-bound verifier receipts.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any

from app_generator.validation.academic_qa import REQUIRED

SHA = re.compile(r"[0-9a-f]{64}\Z")
STATES = frozenset(("PASS", "FAIL", "REVIEW_REQUIRED"))
NEXT = {
    "source_fidelity": "VERIFY_EXACT_ORIGINAL_PASSAGE_AND_RIGHTS",
    "answer_correctness": "INDEPENDENT_ANSWER_PROOF",
    "physics_consistency": "INDEPENDENT_DOMAIN_SCIENCE_PROOF",
    "visual_semantics": "INDEPENDENT_DIAGRAM_SEMANTIC_PROOF",
    "multilingual_meaning": "INDEPENDENT_EN_MS_ZH_EQUIVALENCE_PROOF",
}


def _canonical_activity_sha(activity: dict[str, Any]) -> str:
    return sha256(json.dumps(
        activity, sort_keys=True, ensure_ascii=False,
        separators=(",", ":")).encode("utf-8")).hexdigest()


def audit_academic_coverage(
    *, package_bytes: bytes, matrix: dict[str, Any],
    source_sha256: str,
) -> dict[str, Any]:
    """Reject mismatched matrices and report independently missing proof scope."""
    if not isinstance(source_sha256, str) or not SHA.fullmatch(source_sha256):
        raise ValueError("original source SHA-256 required")
    if not isinstance(package_bytes, bytes) or not package_bytes:
        raise ValueError("actual package bytes required")
    package_sha256 = sha256(package_bytes).hexdigest()
    try:
        package = json.loads(package_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("malformed candidate package JSON") from exc
    if not isinstance(package, dict) or not isinstance(matrix, dict):
        raise ValueError("academic inputs must be objects")
    acts = package.get("activities")
    if not isinstance(acts, list) or not acts:
        raise ValueError("nonempty candidate package required")
    ids = [a.get("id") if isinstance(a, dict) else None for a in acts]
    if (any(not isinstance(aid, str) or not aid for aid in ids) or
        len(ids) != len(set(ids))):
        raise ValueError("invalid or duplicate candidate activity IDs")
    if (matrix.get("packageSha256") != package_sha256 or
        matrix.get("sourceSha256") != source_sha256 or
        matrix.get("activityCount") != len(acts) or
        matrix.get("publicationAuthorized") is not False):
        raise ValueError("academic matrix not bound to exact source/package")
    rows = matrix.get("activities")
    if not isinstance(rows, list) or len(rows) != len(acts):
        raise ValueError("academic matrix lacks exact activity coverage")
    expected = {a["id"]: _canonical_activity_sha(a) for a in acts}
    statuses = {"PASS": 0, "FAIL": 0, "REVIEW_REQUIRED": 0}
    pending = {gate: 0 for gate in REQUIRED}
    failures = {gate: 0 for gate in REQUIRED}
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("non-structured academic matrix row")
        aid = row.get("activityId")
        if (aid not in expected or aid in seen or
            row.get("activitySha256") != expected[aid] or
            row.get("publicationAuthorized") is not False):
            raise ValueError("stale, duplicate, or mismatched activity evidence")
        seen.add(aid)
        gates = row.get("gates")
        if not isinstance(gates, dict) or set(gates) != set(REQUIRED):
            raise ValueError("missing or invented academic gate")
        if any(value not in STATES for value in gates.values()):
            raise ValueError("invalid academic gate state")
        if (gates["source_fidelity"] == "PASS" and
                row.get("sourceLocationVerified") is not True):
            raise ValueError("source fidelity claim lacks verified original passage")
        expected_state = (
            "FAIL" if "FAIL" in gates.values()
            else "PASS" if all(v == "PASS" for v in gates.values())
            else "REVIEW_REQUIRED"
        )
        if row.get("academicQA") != expected_state:
            raise ValueError("academic row aggregate contradicts gate states")
        statuses[expected_state] += 1
        for gate in REQUIRED:
            if gates[gate] != "PASS":
                pending[gate] += 1
            if gates[gate] == "FAIL":
                failures[gate] += 1
    if seen != set(expected) or matrix.get("counts") != statuses:
        raise ValueError("academic matrix aggregate or activity roster mismatch")
    expected_overall = (
        "FAIL" if statuses["FAIL"] else
        "PASS" if statuses["PASS"] == len(acts) else "REVIEW_REQUIRED"
    )
    if matrix.get("academicQA") != expected_overall:
        raise ValueError("academic matrix overall state contradicts activity rows")
    # None of the matrix rows includes an independently validated proof receipt.
    # Thus even 18/18 claimed PASS here cannot grant academic acceptance.
    return {
        "status": "DETERMINISTIC_FAILURES_REQUIRE_CORRECTION" if statuses["FAIL"]
                  else "INDEPENDENT_ACADEMIC_PROOF_REQUIRED",
        "sourceSha256": source_sha256,
        "packageSha256": package_sha256,
        "activityCount": len(acts),
        "matrixClaimedStatuses": statuses,
        "perGateOutstanding": pending,
        "perGateFailures": failures,
        "independentProofNextActions": {
            gate: NEXT[gate] for gate in REQUIRED
        },
        "sourceIdentityCheckedAgainstPdfHere": False,
        "academicEvidenceIndependentlyVerifiedHere": False,
        "academicQA": "FAIL" if statuses["FAIL"] else "REVIEW_REQUIRED",
        "formalAcademicPassCount": 0,
        "humanInterventionRequiredByThisTool": False,
        "publicationAuthorized": False,
    }

"""Private, fail-closed admission for a never-reviewed source-bound activity.

A passing admission never means academic correctness, approval or permission
to replay any previous remote claim. No browser or network is touched.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from app_generator.validation.reviewer_source_packets import verified_source_packet

SAFE = re.compile(r"^[a-z0-9-]+$")
NEW_PRIORITIES = frozenset({
    "INDEPENDENT_MULTILINGUAL_SEMANTIC_REVIEW",
    "SUBMIT_FRESH_INDEPENDENT_REVIEW_WHEN_AUTHORIZED",
})


def admit_fresh_academic_review(
    *, package_file: Path, source_pdf: Path, packets_file: Path,
    priority_queue_file: Path, neutral_receipt_file: Path,
    private_evidence_root: Path, run_id: str, activity_id: str,
    claim_prefix: str, repository_root: Path,
) -> dict[str, Any]:
    """Verify exact source, queue, neutral preflight and old private receipts."""
    if any(not isinstance(x, str) or not SAFE.fullmatch(x)
           for x in (run_id, claim_prefix)):
        raise ValueError("unique safe run and claim identifiers required")
    if not isinstance(activity_id, str) or not activity_id.strip():
        raise ValueError("stable activity identifier required")
    repo = repository_root.resolve(strict=True)
    evidence = private_evidence_root.resolve(strict=True)
    inputs = (package_file, source_pdf, packets_file,
              priority_queue_file, neutral_receipt_file)
    if (not evidence.is_dir() or evidence.is_relative_to(repo) or
            any(not p.is_file() or p.is_symlink() or
                not p.resolve().is_relative_to(evidence) for p in inputs)):
        raise ValueError("all private review inputs must remain under authorized private evidence root")
    target = evidence / "academic-new-review-runs" / run_id
    if target.exists() or target.is_symlink():
        raise ValueError("previous review run exists; never replay")
    package_raw = package_file.read_bytes()
    source_raw = source_pdf.read_bytes()
    pkg_sha, src_sha = sha256(package_raw).hexdigest(), sha256(source_raw).hexdigest()
    if not source_raw.startswith(b"%PDF-"):
        raise ValueError("controlled original PDF required")
    package = json.loads(package_raw.decode("utf-8"))
    manifest = json.loads(packets_file.read_text(encoding="utf-8"))
    priority = json.loads(priority_queue_file.read_text(encoding="utf-8"))
    neutral = json.loads(neutral_receipt_file.read_text(encoding="utf-8"))
    activities = package.get("activities") if isinstance(package, dict) else None
    if (not isinstance(activities, list) or len(activities) != 18 or
            any(not isinstance(x, dict) or not isinstance(x.get("id"), str)
                for x in activities)):
        raise ValueError("corrected original 18-activity package required")
    ids = [item["id"] for item in activities]
    if len(set(ids)) != 18 or ids.count(activity_id) != 1:
        raise ValueError("activity must be unique within corrected source package")
    if (not isinstance(manifest, dict) or
            manifest.get("packageSha256") != pkg_sha or
            manifest.get("sourceSha256") != src_sha or
            not isinstance(manifest.get("packets"), dict) or
            set(manifest["packets"]) != set(ids)):
        raise ValueError("source packet roster identity mismatch")
    if (not isinstance(priority, dict) or
            priority.get("status") != "SOURCE_BOUND_AUTONOMOUS_ACADEMIC_REVIEW_QUEUE" or
            priority.get("packageSha256") != pkg_sha or
            priority.get("sourceSha256") != src_sha or
            priority.get("activityCount") != 18 or
            priority.get("publicationAuthorized") is not False):
        raise ValueError("academic work queue is stale or not source-bound")
    rows = priority.get("activities")
    if (not isinstance(rows, list) or len(rows) != 18 or
            any(not isinstance(row, dict) for row in rows) or
            len({row.get("activityId") for row in rows}) != 18 or
            {row.get("activityId") for row in rows} != set(ids)):
        raise ValueError("academic work queue activity roster incomplete")
    selected = next(row for row in rows if row["activityId"] == activity_id)
    if (selected.get("priority") not in NEW_PRIORITIES or
            type(selected.get("missingOrUnsentReviewSlots")) is not int or
            selected["missingOrUnsentReviewSlots"] != 10 or
            selected.get("unreconciledSubmittedOrSkippedClaims") != 0 or
            selected.get("publicationAuthorized") is not False):
        raise ValueError("previous or unresolved reviewer claims cannot be replayed")
    roles = neutral.get("roles") if isinstance(neutral, dict) else None
    if (neutral.get("status") != "NEUTRAL_TWO_CONTEXTS_CONFIRMED" or
            not isinstance(roles, dict) or
            any(not isinstance(roles.get(role), dict) or
                roles[role].get("state") != "COMPLETE_CAPTURED" or
                roles[role].get("responseCaptured") is not True
                for role in ("physics", "semantics"))):
        raise ValueError("fresh source-free two-context Gemini preflight required")
    # A stale queue is insufficient: independently scan every visible private
    # immutable claim. Unknown/corrupt JSON is a blocker, not implicit absence.
    for path in evidence.rglob("batches/*.json"):
        if path.is_symlink() or not path.is_file():
            raise ValueError("private academic claim path is not an owned file")
        record = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            raise ValueError("unrecognized private academic claim receipt")
        if (record.get("activityId") == activity_id and
                record.get("sourceHash") == src_sha and
                record.get("packageHash") == pkg_sha and
                record.get("state") in ("IN_FLIGHT", "AMBIGUOUS", "COMPLETE",
                                        "SKIPPED_UNSENT")):
            raise ValueError("existing private activity review claim; never replay")
    candidate = manifest["packets"][activity_id]
    if not isinstance(candidate, dict) or not isinstance(candidate.get("sourceAnchors"), list):
        raise ValueError("private original-source anchors required")
    source_context = verified_source_packet(
        source_pdf, src_sha, activity_id, candidate["sourceAnchors"]
    )
    for field in ("sourceEvidence", "sourceAnchors", "passageSha256", "verifiedPages"):
        if candidate.get(field) != source_context[field]:
            raise ValueError("original PDF passage/page no longer matches immutable packet")
    return {
        "activityId": activity_id,
        "runId": run_id,
        "claimPrefix": claim_prefix,
        "sourceSha256": src_sha,
        "packageSha256": pkg_sha,
        "activity": next(x for x in activities if x["id"] == activity_id),
        "sourceContext": source_context,
        "privateRunDirectory": target,
        "academicQA": "REVIEW_REQUIRED",
        "publicationAuthorized": False,
    }

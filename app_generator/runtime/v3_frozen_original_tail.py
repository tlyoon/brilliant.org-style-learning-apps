"""Frozen-original V3 independent activity queue beyond an unreplayable role.

This source-free planner never reopens old provider requests. An untouched
original activity receives a deterministic, separate ONE-activity review
identity; results remain supplemental and never upgrade the original course
aggregate, original ambiguous role, admission, or publication.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import shutil
from typing import Any

from app_generator.validation.autonomous_completion import (
    assessment_progress, make_prompt, package_identity,
)
from app_generator.validation.v3_course_readiness import course_readiness
from app_generator.validation.autonomous_ai_review import canonical_digest

_SECTION = "section-9-6"
_SCHEMA = "BOSLA_V3_FROZEN_ORIGINAL_INDEPENDENT_ACTIVITY_V1"
_HEX = set("0123456789abcdef")


def _bytes(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False)
            + "\n").encode("utf8")


def _hash(value: dict) -> str:
    return sha256(json.dumps(value, sort_keys=True,
                             separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _source(course: Path, repo: Path, private: Path, section: str) -> tuple[dict, bytes, str, list[dict], dict]:
    if (private.is_symlink() or not private.is_absolute()
            or private.resolve() == repo.resolve()
            or private.resolve().is_relative_to(repo.resolve())):
        raise ValueError("V3_TAIL_UNSAFE_PRIVATE_ROOT")
    progress = course_readiness(course, repo, private_root=private)
    if (progress["scopeSource"] != "FROZEN_CANDIDATE_MANIFEST"
            or progress["sectionsTotal"] != 6
            or progress["publicationAuthorized"] is not False):
        raise ValueError("V3_TAIL_NOT_FROZEN_SCOPE")
    row = next((r for r in progress["sectionProgress"]
                if r["section"] == section), None)
    if row is None:
        raise ValueError("V3_TAIL_SECTION_NOT_IN_FROZEN_ROSTER")
    file = course / section / "package.json"
    if file.is_symlink() or not file.is_file():
        raise ValueError("V3_TAIL_UNSAFE_SOURCE")
    source = file.read_bytes()
    digest, activities = package_identity(source)
    if digest != row["packageSha256"] or len(activities) != row["activitiesTotal"]:
        raise ValueError("V3_TAIL_SOURCE_CHANGED")
    if (row["modelUncertainActivities"] < 1
            or row["modelRepairRequiredActivities"] != 0
            or row["unreconciledRoleClaims"] != 0
            or row["reviewerRequestsSkippedUnsent"] != 0
            or row["activitiesAssessedRows"] >= len(activities)):
        raise ValueError("V3_TAIL_NOT_ISOLATED_UNCERTAIN_PREFIX")
    assessment_file = (private / ("v3-generated-" + digest)
                       / "batches" / ("v3-assessment-" + digest + ".json"))
    if assessment_file.is_symlink() or not assessment_file.is_file():
        raise ValueError("V3_TAIL_MISSING_ORIGINAL_EVIDENCE")
    original = json.loads(assessment_file.read_text(encoding="utf8"))
    assessment_progress(source, original)
    reviews = original["reviews"]
    if (len(reviews) != row["activitiesAssessedRows"]
            or reviews[-1]["status"] != "AI_UNCERTAIN"
            or any(r["status"] == "AI_REPAIR_REQUIRED" for r in reviews)):
        raise ValueError("V3_TAIL_ORIGINAL_UNCERTAINTY_CHANGED")
    return progress, source, digest, activities, row


def _slice(source_sha: str, section: str, index: int, item: dict) -> tuple[bytes, str, dict]:
    package = {
        "schema": _SCHEMA,
        "sourcePackageSha256": source_sha,
        "sourceSection": section,
        "sourceActivityIndex": index,
        "activities": [item],
    }
    raw = _bytes(package)
    digest, parsed = package_identity(raw)
    if len(parsed) != 1 or parsed[0] != item:
        raise ValueError("V3_TAIL_INVALID_REVIEW_SLICE")
    info = {
        "schema": _SCHEMA,
        "scope": "FROZEN_ORIGINAL_UNCHANGED_SUPPLEMENTAL_REVIEW_NOT_ADMITTED",
        "slicePackageSha256": digest,
        "sourcePackageSha256": source_sha,
        "sourceSection": section,
        "sourceActivityIndex": index,
        "activityId": item["id"],
        "originalActivitySha256": canonical_digest(item),
        "physicsPromptSha256": sha256(make_prompt(
            item, "physics-adversary").encode("utf8")).hexdigest(),
        "semanticsPromptSha256": sha256(make_prompt(
            item, "language-and-learner-adversary").encode("utf8")).hexdigest(),
        "modelRequestsSubmitted": 0,
        "originalRoleReplayed": False,
        "versionedScopeAdmitted": False,
        "publicationAuthorized": False,
    }
    return raw, digest, {**info, "integritySha256": _hash(info)}


def _safe_evidence(private: Path, source_sha: str, index: int, slice_sha: str) -> str:
    original = private / ("v3-generated-" + source_sha) / "batches"
    original_prefix = f"v3-review-{source_sha[:12]}-{index:03d}-"
    if any(original.glob(original_prefix + "*.json")):
        return "ORIGINAL_ROLE_CLAIM_PRESENT_DO_NOT_REPLAY"
    base = private / ("v3-generated-" + slice_sha) / "batches"
    aggregate = base / ("v3-assessment-" + slice_sha + ".json")
    if base.is_symlink() or aggregate.is_symlink():
        raise ValueError("V3_TAIL_UNSAFE_PRIVATE_EVIDENCE")
    if aggregate.is_file():
        # Caller validates exact returned evidence against recomputed slice.
        return "AGGREGATE_EXISTS"
    if any(base.glob(f"v3-review-{slice_sha[:12]}-000-*.json")):
        return "ROLE_CLAIM_PRESENT_DO_NOT_REPLAY"
    attempt = private / "frozen-original-review-attempts" / (slice_sha + ".json")
    if attempt.is_symlink():
        raise ValueError("V3_TAIL_UNSAFE_ATTEMPT")
    if attempt.exists():
        if not attempt.is_file() or attempt.stat().st_size > 4096:
            raise ValueError("V3_TAIL_INVALID_ATTEMPT")
        row = json.loads(attempt.read_text(encoding="utf8"))
        if (row.get("slicePackageSha256") != slice_sha
                or row.get("sourcePackageSha256") != source_sha
                or row.get("sourceActivityIndex") != index
                or row.get("publicationAuthorized") is not False):
            raise ValueError("V3_TAIL_ATTEMPT_IDENTITY_MISMATCH")
        return "ATTEMPT_RESERVED_DO_NOT_REPLAY"
    return "UNREVIEWED_ELIGIBLE"


def plan_frozen_original_tail(
    course: Path, repo: Path, private: Path, *,
    section: str = _SECTION,
) -> dict:
    """Read-only plan; never opens a provider or creates a file."""
    progress, source, source_sha, activities, row = _source(
        course, repo, private, section)
    original_done = row["activitiesAssessedRows"]
    totals = {"passed": 0, "uncertain": 0, "failed": 0,
              "reserved": 0, "eligible": 0}
    next_item = None
    rows = []
    for index in range(original_done, len(activities)):
        raw, digest, manifest = _slice(
            source_sha, section, index, activities[index])
        state = _safe_evidence(private, source_sha, index, digest)
        if state == "AGGREGATE_EXISTS":
            aggregate = (private / ("v3-generated-" + digest) / "batches"
                         / ("v3-assessment-" + digest + ".json"))
            if aggregate.stat().st_size > 8_000_000:
                raise ValueError("V3_TAIL_AGGREGATE_TOO_LARGE")
            report = json.loads(aggregate.read_text(encoding="utf8"))
            result = assessment_progress(raw, report)
            if result["activitiesAssessed"] != 1:
                raise ValueError("V3_TAIL_AGGREGATE_NOT_ONE_ACTIVITY")
            if result["modelConsensusPassActivities"] == 1:
                state = "GENUINE_SUPPLEMENTAL_CONSENSUS_PASS"
                totals["passed"] += 1
            elif result["modelRepairRequiredActivities"] == 1:
                state = "SUPPLEMENTAL_SCIENTIFIC_REPAIR_REQUIRED"
                totals["failed"] += 1
            else:
                state = "SUPPLEMENTAL_UNCERTAIN_NO_REPLAY"
                totals["uncertain"] += 1
        elif state == "UNREVIEWED_ELIGIBLE":
            totals["eligible"] += 1
            if next_item is None:
                next_item = {
                    "index": index, "activityId": activities[index]["id"],
                    "slicePackageSha256": digest,
                    "sourcePackageSha256": source_sha,
                }
        else:
            totals["reserved"] += 1
        rows.append({"index": index, "activityId": activities[index]["id"],
                     "slicePackageSha256": digest, "state": state})
    return {
        "schema": _SCHEMA,
        "status": "READY_FOR_AUTHORIZED_FROZEN_ORIGINAL_TAIL_REVIEW"
            if next_item else "STOP_NO_UNREVIEWED_ELIGIBLE_ORIGINAL_TAIL",
        "sourceSection": section, "sourcePackageSha256": source_sha,
        "originalAssessedUnchanged": original_done,
        "originalModelConsensusPassesUnchanged": row["modelConsensusPassActivities"],
        "next": next_item, "supplemental": totals, "rows": rows,
        "originalUncertaintyPreserved": True,
        "versionedScopeAdmitted": False, "publicationAuthorized": False,
    }


def stage_frozen_original_tail_slice(
    course: Path, repo: Path, private: Path, *,
    section: str = _SECTION, index: int,
) -> tuple[bytes, dict]:
    """Immutable private one-original-activity review package (NO API call)."""
    progress, source, source_sha, activities, row = _source(
        course, repo, private, section)
    if type(index) is not int or not row["activitiesAssessedRows"] <= index < len(activities):
        raise ValueError("V3_TAIL_INDEX_NOT_UNTOUCHED_ORIGINAL")
    raw, digest, manifest = _slice(
        source_sha, section, index, activities[index])
    state = _safe_evidence(private, source_sha, index, digest)
    if state != "UNREVIEWED_ELIGIBLE":
        raise ValueError("V3_TAIL_ALREADY_ATTEMPTED_NO_REPLAY")
    folder = private / "frozen-original-review-slices"
    final = folder / digest
    receipt = _bytes(manifest)
    if folder.is_symlink() or final.is_symlink():
        raise ValueError("V3_TAIL_UNSAFE_SLICE_DIR")
    if final.exists():
        if (not final.is_dir()
                or any(p.is_symlink() for p in (
                    final / "package.json", final / "review-slice.json"))
                or (final / "package.json").read_bytes() != raw
                or (final / "review-slice.json").read_bytes() != receipt):
            raise ValueError("V3_TAIL_STAGED_IDENTITY_CONFLICT")
    else:
        folder.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix=".v3-tail-stage-", dir=folder))
        try:
            for filename, data in (
                ("package.json", raw), ("review-slice.json", receipt)
            ):
                with (temporary / filename).open("xb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
            temporary.rename(final)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
    if (course / section / "package.json").read_bytes() != source:
        raise ValueError("V3_TAIL_SOURCE_CHANGED_DURING_STAGE")
    return raw, manifest


def reserve_frozen_original_tail_attempt(
    private: Path, *, source_sha: str, index: int, slice_sha: str,
) -> None:
    """Durable independent PRE_CALL claim; never resend after uncertainty."""
    if (not isinstance(source_sha, str) or len(source_sha) != 64
            or not isinstance(slice_sha, str) or len(slice_sha) != 64
            or set(source_sha) - _HEX or set(slice_sha) - _HEX
            or type(index) is not int or index < 0):
        raise ValueError("V3_TAIL_BAD_RESERVATION")
    root = private / "frozen-original-review-attempts"
    if root.is_symlink():
        raise ValueError("V3_TAIL_UNSAFE_RESERVATION_ROOT")
    root.mkdir(parents=True, exist_ok=True)
    file = root / (slice_sha + ".json")
    if file.is_symlink():
        raise ValueError("V3_TAIL_UNSAFE_ATTEMPT")
    message = _bytes({
        "sourcePackageSha256": source_sha,
        "sourceActivityIndex": index,
        "slicePackageSha256": slice_sha,
        "state": "PRE_CALL_NO_REPLAY",
        "publicationAuthorized": False,
    })
    try:
        with file.open("xb") as stream:
            stream.write(message)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        raise ValueError("V3_TAIL_PREVIOUS_ATTEMPT_NO_REPLAY") from None

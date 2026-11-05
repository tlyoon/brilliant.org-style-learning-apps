"""Finite cross-topic evidence orchestration; no model, PDF, browser or release.

Exactly three distinct topic families are inspected once each through the
existing learner and academic coverage gates. Their output remains METADATA,
never independent scientific, translation, interaction or publication proof.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Callable

from app_generator.validation.academic_coverage_gate import audit_academic_coverage
from app_generator.validation.learner_coverage_gate import audit_full_learner_coverage

_ID = re.compile(r"[a-z][a-z0-9-]{2,63}\Z")
_SHA = re.compile(r"[a-f0-9]{64}\Z")
_TOPICS = frozenset((
    "mechanics", "electromagnetism", "thermodynamics", "waves-optics",
    "quantum", "modern-physics", "other-physics",
))
_REQUIRED = frozenset((
    "campaignId", "baselineGitSha", "mode", "maxCases",
    "maxChecksPerCase", "modelCallsAllowed", "pdfReadsAllowed",
    "publicationAllowed", "cases",
))
_CASE = frozenset((
    "caseId", "topicFamily", "sourceSha256", "packageSha256",
    "package", "learnerReceipt", "academicMatrix",
))


def canonical_digest(obj: dict[str, Any]) -> str:
    return sha256(json.dumps(
        obj, sort_keys=True, ensure_ascii=True, separators=(",", ":")
    ).encode("ascii")).hexdigest()


def validate_cross_topic_manifest(manifest: dict[str, Any]) -> None:
    if not isinstance(manifest, dict) or set(manifest) != _REQUIRED:
        raise ValueError("strict cross-topic manifest required")
    identifier = manifest["campaignId"]
    if (not isinstance(identifier, str) or not _ID.fullmatch(identifier) or
            not identifier.startswith("sourcefree-") or
            identifier.startswith("sourcefree-c3-")):
        raise ValueError("new source-free campaign identity required")
    sha = manifest["baselineGitSha"]
    if not isinstance(sha, str) or not re.fullmatch("[a-f0-9]{40}", sha):
        raise ValueError("exact frozen code head required")
    if (manifest["mode"] != "OFFLINE_EXISTING_EVIDENCE_ONLY" or
            type(manifest["maxCases"]) is not int or
            manifest["maxCases"] != 3 or
            type(manifest["maxChecksPerCase"]) is not int or
            manifest["maxChecksPerCase"] != 1 or
            any(manifest[key] is not False for key in (
                "modelCallsAllowed", "pdfReadsAllowed", "publicationAllowed"))):
        raise ValueError("bounded source-free no-publication scope required")
    cases = manifest["cases"]
    if not isinstance(cases, list) or len(cases) != 3:
        raise ValueError("exactly three finite topic cases required")
    identifiers: set[str] = set()
    topics: set[str] = set()
    sources: set[str] = set()
    packages: set[str] = set()
    for item in cases:
        if not isinstance(item, dict) or set(item) != _CASE:
            raise ValueError("exactly seven per-case metadata fields required")
        name = item["caseId"]
        topic = item["topicFamily"]
        if (not isinstance(name, str) or not _ID.fullmatch(name) or
                name in identifiers or topic not in _TOPICS or topic in topics):
            raise ValueError("duplicate, unknown or unsafe case/topic")
        source_sha = item["sourceSha256"]
        package_sha = item["packageSha256"]
        if (not isinstance(source_sha, str) or not _SHA.fullmatch(source_sha) or
                not isinstance(package_sha, str) or not _SHA.fullmatch(package_sha) or
                source_sha in sources or package_sha in packages):
            raise ValueError("repeated or unbound source/package digest")
        for field in ("package", "learnerReceipt", "academicMatrix"):
            value = item[field]
            if (not isinstance(value, str) or not value or
                len(value) > 180 or not value.endswith(".json") or
                value.startswith(("/", "\\\\")) or
                ":" in value or "\\" in value or
                any(not part or part in (".", "..") for part in value.split("/"))):
                raise ValueError("unsafe or ambiguous evidence artifact path")
        if len({item[x] for x in ("package", "learnerReceipt", "academicMatrix")}) != 3:
            raise ValueError("distinct evidence files required per case")
        identifiers.add(name)
        topics.add(topic)
        sources.add(source_sha)
        packages.add(package_sha)


def assess_cross_topic_evidence(
    manifest: dict[str, Any],
    loader: Callable[[str], bytes],
    *,
    observed_git_sha: str,
) -> dict[str, Any]:
    """Inspect each declared case at most once, preserving source-free limits.

    A loader is supplied by a restricted local-file CLI (or synthetic test).
    If a receipt is invalid, record a bounded categorical error, not a raw
    exception or private content. Later cases still get one inspection.
    """
    validate_cross_topic_manifest(manifest)
    if (not isinstance(observed_git_sha, str) or
            observed_git_sha != manifest["baselineGitSha"]):
        raise ValueError("frozen inspected branch differs from manifest")
    cases = []
    for item in manifest["cases"]:
        status = "INVALID_EVIDENCE"
        learner_status = "NOT_EVALUATED"
        academic_status = "NOT_EVALUATED"
        missing_checks = None
        academic_pending: dict[str, int] | None = None
        error_category = None
        try:
            raw = loader(item["package"])
            if not isinstance(raw, bytes) or sha256(raw).hexdigest() != item["packageSha256"]:
                raise ValueError("package lineage mismatch")
            package = json.loads(raw.decode("utf-8"))
            learner = json.loads(loader(item["learnerReceipt"]).decode("utf-8"))
            matrix = json.loads(loader(item["academicMatrix"]).decode("utf-8"))
            if (not isinstance(learner, dict) or
                    learner.get("packageSha256") != item["packageSha256"] or
                    learner.get("publicationAuthorized") is not False):
                raise ValueError("learner receipt lacks exact package lineage")
            learner_result = audit_full_learner_coverage(package, learner)
            academic_result = audit_academic_coverage(
                package_bytes=raw, matrix=matrix, source_sha256=item["sourceSha256"])
            learner_status = learner_result["status"]
            academic_status = academic_result["status"]
            missing_checks = (learner_result["missingCheckCount"] +
                              learner_result["failedCheckCount"])
            academic_pending = academic_result["perGateOutstanding"]
            if academic_result["status"] == "DETERMINISTIC_FAILURES_REQUIRE_CORRECTION":
                status = "REPORTED_DETERMINISTIC_DEFECTS"
            elif learner_status != "COMPLETE_COVERAGE_METADATA_UNVERIFIED":
                status = "MISSING_LEARNER_OBSERVATIONS"
            else:
                status = "METADATA_COMPLETE_PROOF_UNVERIFIED"
        except (ValueError, TypeError, KeyError, AttributeError, OSError,
                UnicodeError, json.JSONDecodeError):
            # Avoid logging exception messages, private source text, model
            # responses or untrusted path strings. Never retry this case.
            error_category = "INVALID_OR_UNBOUND_EVIDENCE"
        cases.append({
            "caseId": item["caseId"],
            "topicFamily": item["topicFamily"],
            "status": status,
            "learnerScope": learner_status,
            "academicEvidence": academic_status,
            "missingLearnerChecks": missing_checks,
            "outstandingAcademicGates": academic_pending,
            "errorCategory": error_category,
            "checksPerformed": 1,
            "independentBrowserProven": False,
            "scientificMeaningProven": False,
            "multilingualEquivalenceProven": False,
            "academicQA": "REVIEW_REQUIRED",
            "publicationAuthorized": False,
        })
    counts = {
        status: sum(row["status"] == status for row in cases)
        for status in (
            "METADATA_COMPLETE_PROOF_UNVERIFIED",
            "MISSING_LEARNER_OBSERVATIONS",
            "REPORTED_DETERMINISTIC_DEFECTS",
            "INVALID_EVIDENCE",
        )
    }
    if counts["REPORTED_DETERMINISTIC_DEFECTS"]:
        disposition = "STOP_REPORTED_DEFECTS"
    elif counts["INVALID_EVIDENCE"] or counts["MISSING_LEARNER_OBSERVATIONS"]:
        disposition = "STOP_INCOMPLETE_OR_INVALID_EVIDENCE"
    else:
        disposition = "STOP_INDEPENDENT_VERIFICATION_REQUIRED"
    return {
        "status": "FINITE_CROSS_TOPIC_METADATA_DISPOSITION",
        "manifestSha256": canonical_digest(manifest),
        "baselineGitSha": manifest["baselineGitSha"],
        "sourceFreeOnly": True,
        "caseCount": 3,
        "checksPerCaseMaximum": 1,
        "casesChecked": sum(row["checksPerformed"] for row in cases),
        "topicFamilies": sorted(row["topicFamily"] for row in cases),
        "counts": counts,
        "caseResults": cases,
        "terminalDisposition": disposition,
        "stoppingConditionMet": True,
        "repeatEvaluationAllowed": False,
        "newProviderOrPdfCallsAllowed": False,
        "interactiveLearnerAcceptanceGranted": False,
        "academicAcceptanceGranted": False,
        "technicalAcceptanceGranted": False,
        "publicationAuthorized": False,
    }

"""Source-free, bounded held-out PDF generalization evidence gate.

Evaluates metadata only. It does not process PDFs, send model requests, prove
unseen selection, verify external receipts, grant academic PASS, or publish.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any

SHA256 = re.compile(r"[a-f0-9]{64}\Z")
GIT_SHA = re.compile(r"[a-f0-9]{40}\Z")
IDENT = re.compile(r"[a-z][a-z0-9-]{2,63}\Z")
TOPICS = frozenset({
    "mechanics", "electromagnetism", "thermodynamics", "waves-optics",
    "quantum", "modern-physics", "other-physics",
})
STAGES = (
    "domain_binding", "source_ingestion", "draft_schema",
    "interactive_learner", "trilingual_render",
)
STAGE_STATES = frozenset(("PASS", "FAIL", "BLOCKED_EXTERNAL", "NOT_RUN"))
ACADEMIC_STATES = frozenset(("PASS", "FAIL", "REVIEW_REQUIRED"))


def canonical_sha256(payload: dict[str, Any]) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True).encode("ascii")).hexdigest()


def _digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise ValueError(label + " requires a lowercase SHA256")
    return value


def _sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or not GIT_SHA.fullmatch(value):
        raise ValueError(label + " requires an exact 40-character commit SHA")
    return value


def _id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not IDENT.fullmatch(value):
        raise ValueError(label + " requires a bounded canonical identifier")
    return value


def validate_manifest(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Validate a predeclared set of diverse sources for at most two campaigns."""
    if not isinstance(manifest, dict) or set(manifest) != {
        "schemaVersion", "campaignId", "round", "baselineGitSha",
        "profileId", "selectionWitnessSha256", "sources", "priorCampaign",
    } or type(manifest["schemaVersion"]) is not int or manifest["schemaVersion"] != 1:
        raise ValueError("unsupported or incomplete holdout manifest")
    _id(manifest["campaignId"], "campaignId")
    _sha(manifest["baselineGitSha"], "baselineGitSha")
    _id(manifest["profileId"], "profileId")
    _digest(manifest["selectionWitnessSha256"], "selectionWitnessSha256")
    if type(manifest["round"]) is not int or manifest["round"] not in (1, 2):
        raise ValueError("one primary and at most one correction round supported")
    if manifest["round"] == 1:
        if manifest["priorCampaign"] is not None:
            raise ValueError("primary campaign cannot claim previous trial")
    else:
        prior = manifest["priorCampaign"]
        if not isinstance(prior, dict) or set(prior) != {
            "receiptSha256", "genericFixRegressionSha256", "sourceSha256s",
        }:
            raise ValueError("one generic correction needs pinned previous evidence")
        _digest(prior["receiptSha256"], "previous result")
        _digest(prior["genericFixRegressionSha256"], "generic regression")
        if (not isinstance(prior["sourceSha256s"], list) or
                len(prior["sourceSha256s"]) < 3 or
                len(set(prior["sourceSha256s"])) != len(prior["sourceSha256s"])):
            raise ValueError("previously exposed source roster invalid")
        for digest in prior["sourceSha256s"]:
            _digest(digest, "previous PDF")
    sources = manifest["sources"]
    if not isinstance(sources, list) or len(sources) != 3:
        raise ValueError("exactly three previously unseen held-out PDFs required")
    roster: dict[str, dict[str, Any]] = {}
    seen_sha: set[str] = set()
    topics: set[str] = set()
    forbidden = (set(manifest["priorCampaign"]["sourceSha256s"])
                 if manifest["priorCampaign"] is not None else set())
    for source in sources:
        if not isinstance(source, dict) or set(source) != {
            "caseId", "sourceSha256", "topicFamily", "declaredUnseen",
            "rightsCleared",
        }:
            raise ValueError("source manifest must contain private-safe metadata only")
        sid = _id(source["caseId"], "caseId")
        digest = _digest(source["sourceSha256"], "source PDF")
        topic = source["topicFamily"]
        if (sid in roster or digest in seen_sha or digest in forbidden or
                topic not in TOPICS or topic in topics):
            raise ValueError("repeated source, previously used source or topic")
        if source["declaredUnseen"] is not True or source["rightsCleared"] is not True:
            raise ValueError("unseen/rights assertions are required before a pilot")
        roster[sid] = source
        seen_sha.add(digest)
        topics.add(topic)
    return roster


def evaluate_campaign(manifest: dict[str, Any],
                      results: dict[str, Any]) -> dict[str, Any]:
    """Check version, coverage and internal consistency, not external truth."""
    roster = validate_manifest(manifest)
    digest = canonical_sha256(manifest)
    if not isinstance(results, dict) or set(results) != {
        "schemaVersion", "campaignId", "manifestSha256", "engineGitSha",
        "cases",
    } or type(results["schemaVersion"]) is not int or results["schemaVersion"] != 1:
        raise ValueError("unsupported or incomplete campaign evidence")
    if (results["campaignId"] != manifest["campaignId"] or
            results["manifestSha256"] != digest or
            results["engineGitSha"] != manifest["baselineGitSha"]):
        raise ValueError("candidate code changed or holdout manifest is stale")
    rows = results["cases"]
    if not isinstance(rows, list) or len(rows) != len(roster):
        raise ValueError("all three held-out source result rows are required")
    outcomes = {}
    complete = 0
    failures = []
    blockers = []
    academic = {"PASS": 0, "FAIL": 0, "REVIEW_REQUIRED": 0}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "caseId", "sourceSha256", "engineGitSha", "stages",
            "packageSha256", "academicQA", "bespokeCodeChanges",
            "publicationAuthorized",
        }:
            raise ValueError("result contains unknown or missing fields")
        sid = _id(row["caseId"], "caseId")
        if sid not in roster or sid in outcomes or row["sourceSha256"] != roster[sid]["sourceSha256"]:
            raise ValueError("results contain stale, duplicate or substituted PDF identity")
        if row["engineGitSha"] != manifest["baselineGitSha"]:
            raise ValueError("per-source code revision differs from frozen baseline")
        if row["bespokeCodeChanges"] is not False or row["publicationAuthorized"] is not False:
            raise ValueError("PDF-specific code edits or publication flags are forbidden")
        if row["academicQA"] not in ACADEMIC_STATES:
            raise ValueError("invalid academic status")
        academic[row["academicQA"]] += 1
        stages = row["stages"]
        if not isinstance(stages, dict) or set(stages) != set(STAGES):
            raise ValueError("all five generic technical stages required")
        values = []
        for stage in STAGES:
            item = stages[stage]
            if not isinstance(item, dict) or set(item) != {"status", "evidenceSha256"}:
                raise ValueError("stage requires a status and bounded receipt")
            status = item["status"]
            if status not in STAGE_STATES:
                raise ValueError("unsupported stage outcome")
            if status == "PASS":
                _digest(item["evidenceSha256"], "stage receipt")
            elif item["evidenceSha256"] is not None:
                raise ValueError("failed, denied or missing work cannot claim a PASS receipt")
            values.append(status)
        package_sha = row["packageSha256"]
        if all(status == "PASS" for status in values):
            _digest(package_sha, "validated candidate package")
            complete += 1
            status = "DRAFT_PIPELINE_REPORTED_COMPLETE"
        else:
            if package_sha is not None:
                _digest(package_sha, "candidate package")
            if "FAIL" in values:
                failures.append(sid)
                status = "FAILED"
            elif "BLOCKED_EXTERNAL" in values:
                blockers.append(sid)
                status = "BLOCKED_EXTERNAL"
            else:
                status = "INCOMPLETE"
        outcomes[sid] = status
    if set(outcomes) != set(roster):
        raise ValueError("results omit an original held-out source")
    if failures:
        result = "FAILED_LIMITED_CAMPAIGN"
    elif blockers:
        result = "BLOCKED_EXTERNAL"
    elif complete == len(roster):
        result = "READY_FOR_TRUSTED_PROVENANCE_AUDIT"
    else:
        result = "INCOMPLETE"
    return {
        "status": "SOURCE_FREE_GENERALIZATION_METADATA_GATE",
        "campaignId": manifest["campaignId"],
        "round": manifest["round"],
        "baselineGitSha": manifest["baselineGitSha"],
        "manifestSha256": digest,
        "topicFamilies": sorted(x["topicFamily"] for x in roster.values()),
        "sourceCount": len(roster),
        "draftsReportedComplete": complete,
        "caseOutcomes": outcomes,
        "academicStatusCounts": academic,
        "technicalResult": result,
        "stopAfterThisRoundIfFailed": manifest["round"] == 2,
        "selectionAndRightsIndependentlyVerified": False,
        "sourceReceiptsIndependentlyVerifiedHere": False,
        "realPdfExecutionPerformedHere": False,
        "technicalAcceptanceGranted": False,
        "academicAcceptanceGranted": False,
        "publicationAuthorized": False,
    }

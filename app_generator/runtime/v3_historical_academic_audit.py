"""BSA247 V20: automatically execute the EXISTING academic verifier after V19.

The historical Section 9.4 checker is reused on the *real* Section 9.1
package and exactly one instructor-bound textbook PDF. Passage text exists
only in memory; signed receipts contain metadata. No gate is promoted merely
from a source quotation, valid shape, or a model review claim.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_public_nonmerging_draft_pr import _preflight
from app_generator.runtime.v3_original_reviewer_evidence_reuse import _V19, _STATUS19
from app_generator.runtime.v3_selected_textbook_scientific_provenance import (
    _V18, _STATUS, _PACKAGE, _SOURCE_BINDING, _source_candidates,
)
from app_generator.validation.academic_acceptance_matrix import audit_activity_matrix
from app_generator.validation.academic_qa import REQUIRED
from app_generator.validation.reviewer_source_packets import verified_source_packet
from app_generator.validation.source_passages import _normalized, check_anchor, extract_pages

_V20 = "V20_HISTORICAL_ACADEMIC_VERIFIER_EXECUTION.json"
_PRE = "V20_HISTORICAL_ACADEMIC_VERIFIER_PRE_CALL.json"
_RESULT = "V20_HISTORICAL_ACADEMIC_VERIFIER_RESULT.json"
_STATUS20 = "V20_REAL_ORIGINAL_FIVE_GATE_ACADEMIC_AUDIT_EXECUTED_NO_RELEASE"


def _rehydrate_exact_source_packets(
    *, pdf: Path, source_sha: str, package: dict[str, Any],
    package_sha: str, anchors: list[dict[str, Any]],
) -> dict[str, Any]:
    """Match saved V18 SHA-only anchors to newly read REAL PDF passage bytes.

    Reject a stale label, wrong page, ambiguous digest or differing activity.
    Nothing containing quoted textbook paragraphs is written to a receipt.
    """
    pages = extract_pages(pdf)
    candidates: dict[tuple[int, str], str] = {}
    for number, excerpt, _ in _source_candidates(pages):
        key = (number, sha256(_normalized(excerpt).encode("utf8")).hexdigest())
        if key in candidates and candidates[key] != excerpt:
            raise ValueError("V20_AMBIGUOUS_SOURCE_PASSAGE_DIGEST")
        candidates[key] = excerpt
    activities = package.get("activities", [])
    if not isinstance(activities, list) or len(activities) != 18 or len(anchors) != 18:
        raise ValueError("V20_EXACT_18_ACTIVITY_ROSTER_REQUIRED")
    by_id = {a.get("id"): a for a in activities if isinstance(a, dict)}
    by_anchor = {a.get("activityId"): a for a in anchors if isinstance(a, dict)}
    if len(by_id) != 18 or len(by_anchor) != 18 or set(by_id) != set(by_anchor):
        raise ValueError("V20_SOURCE_ACTIVITY_IDENTITY_MISMATCH")
    packets = {}
    for aid, activity in by_id.items():
        saved = by_anchor[aid]
        if (saved.get("activitySha256") != _hash(activity)
                or saved.get("uniquePagePassageLocated") is not True
                or saved.get("scientificMeaningVerified") is not False):
            raise ValueError("V20_STALE_OR_FALSELY_APPROVED_SOURCE_ANCHOR")
        page, digest = saved.get("physicalPage"), saved.get("passageSha256")
        if type(page) is not int or not isinstance(digest, str):
            raise ValueError("V20_MALFORMED_SOURCE_ANCHOR")
        quote = candidates.get((page, digest))
        if quote is None:
            raise ValueError("V20_SOURCE_ANCHOR_NOT_REFOUND_IN_ORIGINAL_PDF")
        anchor = {"activityId": aid, "pageIndex": page, "quotedText": quote}
        check = check_anchor(pages, anchor)
        if check.get("status") != "VERIFIED_TEXT_ONLY" or check.get("quoteSha256") != digest:
            raise ValueError("V20_SOURCE_ANCHOR_FAILED_NEW_INDEPENDENT_CHECK")
        packets[aid] = verified_source_packet(
            pdf, source_sha, aid, [anchor], extractor=lambda _pdf: pages,
        )
    return {
        "packageSha256": package_sha,
        "sourceSha256": source_sha,
        "packets": packets,
    }


def run_post_v19_historical_academic_audit(
    repo: Path, private: Path, ready: dict[str, Any],
    v9: dict, v11: dict, v12: dict, v18: dict, v19: dict,
) -> dict[str, Any]:
    """Execute the old trusted negative-evidence academic verifier on 9.1."""
    folder, _, _, _, _ = _preflight(repo, private, ready, v9, v11, v12)
    prev18 = _trusted_json(folder / _V18)
    prev19 = _trusted_json(folder / _V19)
    for signed, received, status in (
        (prev18, v18, _STATUS), (prev19, v19, _STATUS19),
    ):
        if (signed != received or signed.get("status") != status
                or signed.get("integritySha256") != _hash({
                    k: v for k, v in signed.items() if k != "integritySha256"})
                or signed.get("gitHead") != ready.get("gitHead")
                or signed.get("proposalSha256") != ready.get("proposalSha256")
                or signed.get("publicationAuthorized") is not False):
            raise ValueError("V20_AUTHENTIC_SIGNED_V18_V19_REQUIRED")
    if (prev19.get("sourceV18ReceiptSha256") != prev18["integritySha256"]
            or prev19.get("reusedIndependentTwoRolePairs") != 17
            or prev19.get("oldUncertainRoleReplayed") is not False
            or prev19.get("newModelCalls") != 0
            or prev19.get("independentAcademicProofsStillOpen") != 90):
        raise ValueError("V20_INCONSISTENT_HISTORICAL_REVIEW_CHAIN")
    source = _trusted_json(folder / "V18_SELECTED_TEXTBOOK_SCIENCE_RESULT.json")
    if (prev18.get("resultSha256") != source.get("integritySha256")
            or source.get("state") != "ONE_REAL_TEXTBOOK_SOURCE_AUDIT_COMPLETE"):
        raise ValueError("V20_SIGNED_SOURCE_AUDIT_REQUIRED")
    audit = source.get("audit", {})
    manifest = json.loads((repo / "content/source-manifests/chapter-9-section-9-1.json")
                          .read_text(encoding="utf8"))
    package_file = repo / _PACKAGE
    package_raw = package_file.read_bytes()
    package = json.loads(package_raw.decode("utf8"))
    binding = _trusted_json(private / _SOURCE_BINDING)
    source_path = Path(binding["sourcePdf"])
    source_root = Path(binding["sourceRoot"])
    source_sha = binding["sourceSha256"]
    if (binding.get("integritySha256") != _hash({
            k: v for k, v in binding.items() if k != "integritySha256"})
            or binding.get("contract") != "BOSLA_SELECTED_SERWAY_TEXTBOOK_LOCAL_BINDING_V1"
            or binding.get("section") != "9.1"
            or binding.get("externalFallbackAllowed") is not False
            or binding.get("sourcePdfUploaded") is not False
            or source_path.is_symlink() or source_path.name.casefold() != "source.pdf"
            or source_path.resolve() != (source_root / "9" / "9.1" / "source.pdf").resolve()
            or not source_path.is_file()
            or source_path.resolve().is_relative_to(repo.resolve())
            or sha256(source_path.read_bytes()).hexdigest() != source_sha
            or source_sha != audit.get("sourceSha256")
            or source_sha != manifest.get("sha256")
            or sha256(package_raw).hexdigest() != audit.get("packageSha256")
            or sha256((repo / "content/source-manifests/chapter-9-section-9-1.json")
                      .read_bytes()).hexdigest() != audit.get("sourceManifestSha256")
            or audit.get("activityCount") != 18
            or audit.get("formalAcademicPassCount") != 0):
        raise ValueError("V20_EXACT_PRIVATE_PDF_PACKAGE_BINDING_REQUIRED")

    identity = {
        "gitHead": ready["gitHead"],
        "proposalSha256": ready["proposalSha256"],
        "sourceV19ReceiptSha256": prev19["integritySha256"],
        "sourceV18ResultSha256": source["integritySha256"],
    }
    _v6_checkpoint(folder / _PRE, {
        **identity, "status": "PRE_CALL_EXISTING_TRUSTED_FIVE_GATE_CHECKER",
        "historicalReviewerReplayAllowed": False,
        "newProviderRequestsAllowed": False,
        "externalPdfsAllowed": False, "publicationAuthorized": False,
    })
    packets = _rehydrate_exact_source_packets(
        pdf=source_path, source_sha=source_sha,
        package=package, package_sha=sha256(package_raw).hexdigest(),
        anchors=audit["sourceAnchors"],
    )
    if packets["packageSha256"] != audit["packageSha256"]:
        raise ValueError("V20_RECONSTRUCTED_PACKAGE_CANONICAL_MISMATCH")
    # Existing Section 9.4 verifier, not a new synthetic or simplified audit.
    report = audit_activity_matrix(
        repo_root=repo, package_path=package_file, source_pdf=source_path,
        source_sha256=source_sha, source_packets=packets, expected_count=18,
    )
    rows = report.get("activities", [])
    if (report.get("activityCount") != 18 or len(rows) != 18
            or report.get("packageSha256") != audit["packageSha256"]
            or report.get("sourceSha256") != source_sha
            or report.get("publicationAuthorized") is not False
            or any(row.get("sourceLocationVerified") is not True for row in rows)
            or any(set(row.get("gates", {})) != set(REQUIRED) for row in rows)
            or report.get("counts", {}).get("PASS") != 0):
        raise ValueError("V20_HISTORICAL_VERIFIER_IDENTITY_OR_GATE_CONTRACT_FAILED")
    # BSA247: recover the *known* negative-only Malay terminology failure
    # using the prior Section9.4 remedy. Keep a NEW versioned private draft;
    # old source/reviewer evidence does not authorize its academic PASS.
    from app_generator.runtime.v3_malay_auto_revision import (
        auto_repair_known_malay_science_defects,
    )
    repair = auto_repair_known_malay_science_defects(
        repo=repo, folder=folder, original_package=package,
        original_package_sha=audit["packageSha256"],
        source_pdf=source_path, source_sha=source_sha,
        original_audit=report, identity=identity,
    )
    # No prose, PDF quote, prompt, option label or human identity is persisted.
    issues = [{
        "activityId": row["activityId"],
        "activitySha256": row["activitySha256"],
        "academicQA": row["academicQA"],
        # Fixed gate order below: P=PASS, F=FAIL, R=REVIEW_REQUIRED.
        "gateStates": "".join({
            "PASS": "P", "FAIL": "F", "REVIEW_REQUIRED": "R",
        }[row["gates"][gate]] for gate in REQUIRED),
        "answerStructureDefectCount": len(row["answerStructureErrors"]),
        "visualContractDefectCount": row["visualContractErrorCount"],
        "nextAction": (
            "AUTO_TARGETED_VERSIONED_REPAIR" if row["academicQA"] == "FAIL"
            else "AUTO_INDEPENDENT_SEMANTIC_VISUAL_TRANSLATION_PROOFS"
        ),
    } for row in rows]
    missing = sum(value != "PASS" for row in rows
                  for value in row["gates"].values())
    result = _v6_checkpoint(folder / _RESULT, {
        **identity,
        "status": "ACTUAL_EXISTING_ACADEMIC_VERIFIER_EXECUTED_ON_9_1",
        "historicalVerifierReused": "academic_acceptance_matrix.audit_activity_matrix",
        "actualOriginalPdfReopened": True,
        "all18SourcePassagesReverified": True,
        "activityCount": 18,
        "academicGateEvaluations": 90,
        "gateOrder": list(REQUIRED),
        "gateProofsStillOutstanding": missing,
        "deterministicFailActivities": report["counts"]["FAIL"],
        "automaticKnownMalayRepairStatus": repair["status"],
        "automaticRepairedActivityCount": repair["repairedActivityCount"],
        "formalAcademicPASS": 0,
        "reviewerClaimsReused": 17,
        "historicalUncertainReviewerReplayed": False,
        "automaticHistoricalMalayRepair": repair,
        "nextActionQueue": issues,
        "academicQA": report["academicQA"],
        "newModelCalls": 0, "externalPdfDownloads": 0,
        "publicationAuthorized": False,
    })
    return _v6_checkpoint(folder / _V20, {
        **identity, "status": _STATUS20,
        "resultSha256": result["integritySha256"],
        "nextTaskDispatchActuallyExecuted": True,
        "historicFiveGateVerifierActuallyExecuted": True,
        "verifiedOriginalSourceLocations": 18,
        "verifiedActivityGateEvaluations": 90,
        "independentAcademicProofSlotsStillOpen": missing,
        "deterministicFailActivities": report["counts"]["FAIL"],
        "automaticKnownMalayRepairStatus": repair["status"],
        "automaticRepairedActivityCount": repair["repairedActivityCount"],
        "formalAcademicPASS": 0,
        "historicalUncertainReviewerReplayed": False,
        "newModelCalls": 0, "additionalExternalPdfsRequired": False,
        "publicationAuthorized": False,
        "nextEligibleMilestone": "EXECUTE_SOURCE_BOUND_SEMANTIC_VISUAL_TRANSLATION_VERIFIERS",
    })

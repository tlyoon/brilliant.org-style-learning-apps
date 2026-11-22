"""BSA248 V21: automatically rebind 18 private textbook anchors to V20 revision.

Earlier Section9.4 source_anchor_migration established the reusable contract:
reopen the exact PDF, reverify original passage location, bind each new activity
digest, and NEVER copy a prior scientific or reviewer PASS to revised content.
V21 executes this in the normal Yoga6 recovery worker after signed V20.
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
from app_generator.runtime.v3_selected_textbook_scientific_provenance import (
    _V18, _STATUS as _STATUS18, _PACKAGE, _SOURCE_BINDING,
    _bounded_math_witnesses, _bounded_mcq_labels,
)
from app_generator.runtime.v3_original_reviewer_evidence_reuse import (
    _V19, _STATUS19,
)
from app_generator.runtime.v3_historical_academic_audit import (
    _V20, _RESULT as _RESULT20, _STATUS20, _rehydrate_exact_source_packets,
)
from app_generator.runtime.v3_malay_auto_revision import (
    _CANDIDATE, _RECEIPT as _MALAY_RECEIPT, _REPAIR_STATUS,
)
from app_generator.validation.academic_acceptance_matrix import audit_activity_matrix
from app_generator.validation.academic_qa import REQUIRED
from app_generator.validation.source_passages import extract_pages
from app_generator.validation.reviewer_source_packets import verified_source_packet

_PRE21 = "V21_REVISED_SOURCE_PROOF_REBIND_PRE_CALL.json"
_RESULT21 = "V21_REVISED_SOURCE_PROOF_REBIND_RESULT.json"
_V21 = "V21_REVISED_91_REAL_SOURCE_REBIND_NO_RELEASE.json"
_STATUS21 = "V21_REVISED_18_SOURCE_LOCATIONS_REVERIFIED_SEMANTIC_PROOFS_OPEN"


def _signed(folder: Path, name: str, ready: dict[str, Any]) -> dict:
    value = _trusted_json(folder / name)
    if (value.get("integritySha256") !=
            _hash({key: val for key, val in value.items() if key != "integritySha256"})
            or value.get("gitHead") != ready.get("gitHead")
            or value.get("proposalSha256") != ready.get("proposalSha256")
            or value.get("publicationAuthorized") is not False):
        raise ValueError("V21_EXACT_SIGNED_PREVIOUS_STAGE_REQUIRED")
    return value


def independently_rebind_revision(
    *, pdf: Path, source_sha: str, original: dict[str, Any],
    candidate: dict[str, Any], original_sha: str, candidate_sha: str,
    original_anchors: list[dict[str, Any]],
    expected_changed_ids: set[str],
) -> tuple[dict[str, Any], list[str]]:
    """Reverify PDF quotes once and rebind each to its exact revised activity.

    The historical 9.4 migration is not mistaken for academic meaning proof.
    If target activity content differs beyond the controlled locale edit,
    abort before retaining any source evidence.
    """
    if (pdf.is_symlink() or not pdf.is_file() or
            sha256(pdf.read_bytes()).hexdigest() != source_sha):
        raise ValueError("V21_SELECTED_ORIGINAL_PDF_SHA_MISMATCH")
    old = original.get("activities")
    new = candidate.get("activities")
    if (not isinstance(old, list) or not isinstance(new, list)
            or len(old) != 18 or len(new) != 18):
        raise ValueError("V21_BOTH_EXACT_18_ROSTERS_REQUIRED")
    old_by_id = {a.get("id"): a for a in old if isinstance(a, dict)}
    new_by_id = {a.get("id"): a for a in new if isinstance(a, dict)}
    if (len(old_by_id) != 18 or len(new_by_id) != 18
            or set(old_by_id) != set(new_by_id)):
        raise ValueError("V21_REVISED_ROSTER_IDENTITY_OR_DUPLICATE_INVALID")
    changed = {aid for aid in old_by_id if
               _hash(old_by_id[aid]) != _hash(new_by_id[aid])}
    if changed != expected_changed_ids or len(changed) != 4:
        raise ValueError("V21_UNREVIEWED_CANDIDATE_ACTIVITY_CHANGE")
    # Previous scoped vocabulary correction only changed Malay strings.
    # A modified answer, visual, English or Chinese field is not admissible.
    for aid in old_by_id:
        prior = json.loads(json.dumps(old_by_id[aid], ensure_ascii=False))
        revised = json.loads(json.dumps(new_by_id[aid], ensure_ascii=False))
        def remove_malay(x: Any) -> Any:
            if isinstance(x, dict):
                return {k: remove_malay(v) for k, v in x.items() if k != "ms"}
            if isinstance(x, list):
                return [remove_malay(xi) for xi in x]
            return x
        if remove_malay(prior) != remove_malay(revised):
            raise ValueError("V21_REVISED_NON_MALAY_FIELD_CHANGED")
    old_packets = _rehydrate_exact_source_packets(
        pdf=pdf, source_sha=source_sha, package=original,
        package_sha=original_sha, anchors=original_anchors,
    )
    pages = extract_pages(pdf)
    packets = {}
    for aid, current in new_by_id.items():
        former = old_packets["packets"][aid]
        # Re-extract the literal passage against the real PDF, don't reuse
        # just the saved digest or a past model's citation assertion.
        context = verified_source_packet(
            pdf, source_sha, aid, former["sourceAnchors"],
            extractor=lambda _pdf: pages,
        )
        if (context["passageSha256"] != former["passageSha256"]
                or context["sourceEvidence"] != former["sourceEvidence"]
                or context["verifiedPages"] != former["verifiedPages"]):
            raise ValueError("V21_FRESH_SOURCE_PASSAGE_DIVERGED")
        context.update({
            "priorActivitySha256": _hash(old_by_id[aid]),
            "targetActivitySha256": _hash(current),
            "activityChangedSinceOriginal": aid in changed,
            "priorModelReviewTransferred": False,
            "sourceLocationOnly": True,
            "sourceInterpretationVerified": False,
        })
        packets[aid] = context
    return ({
        "sourceSha256": source_sha,
        "packageSha256": candidate_sha,
        "packets": packets,
    }, sorted(changed))


def run_post_v20_revised_source_rebind(
    repo: Path, private: Path, ready: dict[str, Any],
    v9: dict, v11: dict, v12: dict, v18: dict, v19: dict, v20: dict,
) -> dict[str, Any]:
    """Authentic normal-path V21 from signed V18-V20 and private revised PDF."""
    folder, _, _, _, _ = _preflight(repo, private, ready, v9, v11, v12)
    signed18 = _signed(folder, _V18, ready)
    signed19 = _signed(folder, _V19, ready)
    signed20 = _signed(folder, _V20, ready)
    for signed, received, status in (
        (signed18, v18, _STATUS18),
        (signed19, v19, _STATUS19),
        (signed20, v20, _STATUS20),
    ):
        if signed != received or signed["status"] != status:
            raise ValueError("V21_REVISED_SOURCE_INVALID_V18_V20_RECEIPT")
    result20 = _signed(folder, _RESULT20, ready)
    repair20 = _signed(folder, _MALAY_RECEIPT, ready)
    source18 = _signed(folder, "V18_SELECTED_TEXTBOOK_SCIENCE_RESULT.json", ready)
    if (signed19.get("sourceV18ReceiptSha256") != signed18["integritySha256"]
            or signed20.get("sourceV19ReceiptSha256") != signed19["integritySha256"]
            or signed20.get("sourceV18ResultSha256") != source18["integritySha256"]
            or signed20.get("resultSha256") != result20["integritySha256"]
            or result20.get("automaticHistoricalMalayRepair",{}).get(
                "receiptSha256") != repair20["integritySha256"]
            or signed20.get("automaticKnownMalayRepairStatus") != _REPAIR_STATUS
            or repair20.get("status") != _REPAIR_STATUS
            or repair20.get("newCandidateFiveGateNegativeFindings") != 0
            or repair20.get("newCandidateAll18AcademicQA") != "REVIEW_REQUIRED"
            or repair20.get("oldGeminiReviewerClaimsTransferred") is not False
            or repair20.get("otherLocalesOrAnswerKeysModified") is not False
            or repair20.get("originalPackageModified") is not False
            or signed20.get("formalAcademicPASS") != 0
            or signed20.get("newModelCalls") != 0
            or signed20.get("independentAcademicProofSlotsStillOpen") != 90):
        raise ValueError("V21_V20_AUTHENTIC_REVISED_CANDIDATE_CHAIN_REQUIRED")
    binding = _trusted_json(private / _SOURCE_BINDING)
    root = Path(binding["sourceRoot"])
    pdf = Path(binding["sourcePdf"])
    source_sha = binding["sourceSha256"]
    if (binding.get("integritySha256") != _hash({
            k:v for k,v in binding.items() if k != "integritySha256"
        })
            or binding.get("contract") !=
                "BOSLA_SELECTED_SERWAY_TEXTBOOK_LOCAL_BINDING_V1"
            or binding.get("section") != "9.1"
            or binding.get("externalFallbackAllowed") is not False
            or binding.get("sourcePdfUploaded") is not False
            or pdf.is_symlink()
            or pdf.name.casefold() != "source.pdf"
            or pdf.resolve() != (root / "9" / "9.1" / "source.pdf").resolve()
            or pdf.resolve().is_relative_to(repo.resolve())
            or not pdf.is_file()
            or sha256(pdf.read_bytes()).hexdigest() != source_sha
            or source18["audit"]["sourceSha256"] != source_sha):
        raise ValueError("V21_EXACT_ONE_INSTRUCTOR_TEXTBOOK_REQUIRED")
    original_file = repo / _PACKAGE
    original_raw = original_file.read_bytes()
    candidate_file = folder / _CANDIDATE
    if candidate_file.is_symlink() or not candidate_file.is_file():
        raise ValueError("V21_PRIVATE_REVISED_CANDIDATE_MISSING_OR_SYMLINK")
    candidate_raw = candidate_file.read_bytes()
    original_sha = sha256(original_raw).hexdigest()
    candidate_sha = sha256(candidate_raw).hexdigest()
    if (original_sha != repair20.get("originalPackageSha256")
            or original_sha != source18["audit"]["packageSha256"]
            or candidate_sha != repair20.get("newPrivateCandidateSha256")
            or candidate_sha == original_sha):
        raise ValueError("V21_STALE_OR_CHANGED_REVISED_PACKAGE_SHA")
    original = json.loads(original_raw.decode("utf8"))
    candidate = json.loads(candidate_raw.decode("utf8"))
    identity = {
        "gitHead": ready["gitHead"],
        "proposalSha256": ready["proposalSha256"],
        "sourceV20ReceiptSha256": signed20["integritySha256"],
        "sourceV20RevisedReceiptSha256": repair20["integritySha256"],
    }
    _v6_checkpoint(folder / _PRE21, {
        **identity,
        "status": "PRE_CALL_EXACT_CANDIDATE_AND_PRIVATE_SOURCE_REBIND",
        "previousReviewerClaimReplayAllowed": False,
        "newProviderRequestsAllowed": False,
        "publicationAuthorized": False,
    })
    packets, changed = independently_rebind_revision(
        pdf=pdf, source_sha=source_sha, original=original,
        candidate=candidate, original_sha=original_sha,
        candidate_sha=candidate_sha,
        original_anchors=source18["audit"]["sourceAnchors"],
        expected_changed_ids=set(repair20["affectedOriginalActivityIds"]),
    )
    if (len(changed) != repair20.get("repairedActivityCount")
            or len(packets["packets"]) != 18):
        raise ValueError("V21_CANDIDATE_SCOPE_OR_SOURCE_COVERAGE_DRIFT")
    # The actual prior academic engine consumes newly reverified source
    # packets for the EXACT updated package, unlike V20's negative-only
    # draft check without source packets.
    report = audit_activity_matrix(
        repo_root=repo, package_path=candidate_file, source_pdf=pdf,
        source_sha256=source_sha, source_packets=packets, expected_count=18,
    )
    rows = report.get("activities", [])
    exact_candidate = {
        activity["id"]: sha256(json.dumps(
            activity, sort_keys=True, ensure_ascii=False,
            separators=(",", ":")).encode("utf8")).hexdigest()
        for activity in candidate["activities"]
    }
    report_by_id = {
        row.get("activityId"): row for row in rows if isinstance(row, dict)
    }
    if (len(report_by_id) != 18 or set(report_by_id) != set(exact_candidate)
            or any(report_by_id[aid].get("activitySha256") != digest
                   for aid, digest in exact_candidate.items())):
        raise ValueError("V21_REVISED_AUDIT_WRONG_ACTIVITY_CONTENT_IDENTITY")
    if (report.get("packageSha256") != candidate_sha
            or report.get("sourceSha256") != source_sha
            or report.get("activityCount") != 18 or len(rows) != 18
            or report.get("counts") != {
                "PASS":0, "FAIL":0, "REVIEW_REQUIRED":18}
            or any(row.get("sourceLocationVerified") is not True
                   for row in rows)
            or any(set(row.get("gates",{})) != set(REQUIRED) for row in rows)
            or report.get("publicationAuthorized") is not False):
        raise ValueError("V21_REVISED_FIVE_GATE_REAL_SOURCE_AUDIT_FAILED")
    math = _bounded_math_witnesses()
    bounded = _bounded_mcq_labels(candidate["activities"])
    if not all(math.values()) or len(math) != 6 or len(bounded) != 5:
        raise ValueError("V21_REVISED_BOUNDED_MATH_OR_ENGLISH_ANSWER_WITNESS_FAILED")
    if (sha256(original_file.read_bytes()).hexdigest() != original_sha or
            sha256(candidate_file.read_bytes()).hexdigest() != candidate_sha or
            sha256(pdf.read_bytes()).hexdigest() != source_sha):
        raise ValueError("V21_SOURCE_PACKAGE_CHANGED_DURING_REAL_QA")
    # Only safe metadata is persisted; no protected PDF text, model
    # responses, new answer paragraphs or student data enters Git.
    rows_meta = [{
        "activityId": row["activityId"],
        "revisedActivitySha256": row["activitySha256"],
        "sourcePhysicalPagesReverified": row["sourcePages"],
        "changedSinceOriginal": row["activityId"] in changed,
        "gateStates": "".join({"PASS":"P","FAIL":"F","REVIEW_REQUIRED":"R"}[
            row["gates"][gate]] for gate in REQUIRED),
        "modelPriorRoleClaimsTransferred":False,
        "academicQA": row["academicQA"],
        "nextAction":"AUTO_INDEPENDENT_CANDIDATE_SOURCE_SCIENCE_VISUAL_LANGUAGE_PROOF",
    } for row in rows]
    result = _v6_checkpoint(folder / _RESULT21, {
        **identity, "status":"REAL_REVISED_SOURCE_REBOUND_AND_FIVE_GATES_RECHECKED",
        "originalPackageSha256":original_sha,
        "revisedCandidateSha256":candidate_sha,
        "sourceSha256":source_sha,
        "revisedPrivateSourceLocationsVerified":18,
        "distinctChangedMalayActivitiesReverified":len(changed),
        "unchangedActivitiesSourceReverified":18-len(changed),
        "boundedIndependentExactArithmeticWitnesses":len(math),
        "boundedMCQKeyEnglishChecks":len(bounded),
        "gateOrder":list(REQUIRED),
        "gateEvidenceStillReviewRequired":90,
        "candidateAcademicPASS":0, "candidateDeterministicFAIL":0,
        "candidateRows":rows_meta,
        "originalReviewerRoleClaimsTransferred":0,
        "newGeminiCalls":0, "outsidePdfDownloads":0,
        "publicationAuthorized":False,
    })
    return _v6_checkpoint(folder / _V21, {
        **identity,
        "status":_STATUS21,
        "resultSha256":result["integritySha256"],
        "originalSelectedPdfReopened":True,
        "candidateSourceLocationsActuallyReverified":18,
        "revisedActivityCount":18,
        "changedActivitiesReverified":4,
        "priorModelReviewerClaimsTransferred":0,
        "verifiedBoundedMathIdentities":6,
        "verifiedBoundedMCQCorrectKeyPatterns":5,
        "independentAcademicProofSlotsStillOpen":90,
        "candidateDeterministicFAIL":0,
        "candidateFormalAcademicPASS":0,
        "newGeminiCalls":0,
        "publicationAuthorized":False,
        "nextEligibleMilestone":"ACTUAL_NEW_REVISED_SOURCE_BOUND_INDEPENDENT_SEMANTIC_REVIEW",
    })

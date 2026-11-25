"""BSA245: reuse genuine historical review claims after signed V18.

This is an executable, read-only next stage in the normal Yoga6 worker.
A two-reviewer model consensus is NOT independent academic source, answer,
physics, visual or translation acceptance. Never replay an uncertain role.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_public_nonmerging_draft_pr import _preflight
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _V18, _STATUS
from app_generator.runtime.v3_standing_paid_science import (
    section91_evidence, verified_section91_standing_passes,
)

_V19 = "V19_EXISTING_91_ORIGINAL_REVIEW_REUSE.json"
_PRE = "V19_PRIOR_REVIEW_RECONCILIATION_PRE_CALL.json"
_RESULT = "V19_PRIOR_REVIEW_RECONCILIATION_RESULT.json"
_STATUS19 = "V19_17_EXISTING_REVIEW_PAIRS_RECONCILED_ACADEMIC_PROOFS_STILL_OPEN"


def run_post_v18_original_review_reuse(
    repo: Path, private: Path, ready: dict,
    v9: dict, v11: dict, v12: dict, v18: dict,
) -> dict:
    """Execute BSA245 history reconciliation once, with signed receipts.

    A clean rerun checks immutable receipts rather than calling Gemini again.
    No source PDF is opened here; the signed V18 evidence remains authoritative.
    """
    folder, _, _, _, _ = _preflight(repo, private, ready, v9, v11, v12)
    signed = _trusted_json(folder / _V18)
    if (
        signed != v18
        or signed.get("status") != _STATUS
        or signed.get("integritySha256") != _hash({
            key: val for key, val in signed.items()
            if key != "integritySha256"
        })
        or signed.get("gitHead") != ready.get("gitHead")
        or signed.get("proposalSha256") != ready.get("proposalSha256")
        or signed.get("realSingleTextbookPdfOpened") is not True
        or signed.get("nextTaskDispatchActuallyExecuted") is not True
        or signed.get("additionalExternalPdfsRequired") is not False
        or signed.get("newModelCalls") != 0
        or signed.get("publicationAuthorized") is not False
    ):
        raise ValueError("V19_GENUINE_IMMUTABLE_V18_REQUIRED")

    source = _trusted_json(folder / "V18_SELECTED_TEXTBOOK_SCIENCE_RESULT.json")
    gaps = _trusted_json(folder / "V18_ACADEMIC_GAP_AUDIT_RESULT.json")
    if (
        signed.get("resultSha256") != source.get("integritySha256")
        or signed.get("academicGapAuditReceiptSha256") != gaps.get("integritySha256")
        or source.get("state") != "ONE_REAL_TEXTBOOK_SOURCE_AUDIT_COMPLETE"
        or gaps.get("state") != "REAL_SOURCE_BOUND_ACADEMIC_GAP_AUDIT_COMPLETE"
        or source.get("audit", {}).get("activityCount") != 18
        or source.get("audit", {}).get("formalAcademicPassCount") != 0
        or gaps.get("result", {}).get("unverifiedGateInstances") != 90
        or gaps.get("result", {}).get("formalAcademicPASS") is not False
    ):
        raise ValueError("V19_V18_SOURCE_OR_90_GAP_CHAIN_TAMPERED")
    identity = {
        "gitHead": signed["gitHead"],
        "proposalSha256": signed["proposalSha256"],
        "sourceV18ReceiptSha256": signed["integritySha256"],
    }
    _v6_checkpoint(folder / _PRE, {
        **identity, "status": "PRE_CALL_READONLY_PRIOR_REVIEW_RECONCILIATION",
        "historicalOriginalIndex0ReplayAllowed": False,
        "providerCallsAllowed": False, "outsidePdfsAllowed": False,
        "publicationAuthorized": False,
    })

    course = repo / "content" / "chapter-9"
    original = section91_evidence(course, repo, private)
    reused = verified_section91_standing_passes(course, repo, private)
    indexes = [row["originalActivityIndex"] for row in reused]
    digest_fields = ("sourceReviewSha256", "supplementalReviewSliceSha256")
    if (
        original.get("oldUncertainIndex") != 0
        or original.get("originalAssessedUnchanged") != 1
        or original.get("parentSha256") != source["audit"]["packageSha256"]
        or len(original.get("items", [])) != 17
        or {row.get("index") for row in original["items"]} != set(range(1, 18))
        or any(row.get("originalReviewState") != "AGGREGATE_EXISTS"
               for row in original["items"])
        or len(reused) != 17
        or set(indexes) != set(range(1, 18))
        or len(indexes) != len(set(indexes))
        or {row.get("activityId") for row in reused}
            != {row["activityId"] for row in original["items"]}
        or any(
            row.get("status") != "POTENTIALLY_REUSABLE_NOT_RELEASE_ACCEPTED"
            or row.get("sourcePackageSha256") != original["parentSha256"]
            or any(not isinstance(row.get(k), str)
                   or len(row[k]) != 64 for k in digest_fields)
            for row in reused
        )
        or len({row["sourceReviewSha256"] for row in reused}) != 17
    ):
        raise ValueError("V19_ORIGINAL_REVIEW_CLAIMS_NOT_REUSABLE")

    digest = sha256("".join(
        sorted(row["sourceReviewSha256"] for row in reused)
    ).encode("ascii")).hexdigest()
    result = _v6_checkpoint(folder / _RESULT, {
        **identity,
        "status": "REAL_EXISTING_ORIGINAL_REVIEW_CLAIMS_RECONCILED",
        "historicalUncertainOriginalIndex": 0,
        "historicalOriginalIndex0Replayed": False,
        "reusedActivityIndexes": sorted(indexes),
        "reusedIndependentTwoRolePairs": 17,
        "reviewAggregateDigestSha256": digest,
        "originalSourcePackageSha256": original["parentSha256"],
        "formalAcademicPASS": 0,
        "independentProofSlotsStillOpen": 90,
        "providerCalls": 0, "outsidePdfs": 0,
        "publicationAuthorized": False,
    })
    return _v6_checkpoint(folder / _V19, {
        **identity, "status": _STATUS19,
        "resultSha256": result["integritySha256"],
        "nextTaskDispatchActuallyExecuted": True,
        "reusedIndependentTwoRolePairs": 17,
        "oldUncertainRoleReplayed": False,
        "independentAcademicProofsStillOpen": 90,
        "independentScientificAcceptanceComplete": False,
        "newModelCalls": 0, "additionalExternalPdfsRequired": False,
        "publicationAuthorized": False,
        "nextEligibleMilestone":
            "INDEPENDENT_SOURCE_MEANING_ANSWER_VISUAL_TRILINGUAL_PROOF",
    })

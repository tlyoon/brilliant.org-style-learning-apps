"""Exact-source Section9.6 roll-forward after an unrecoverable old Gemini role.

This is an independently versioned CONTENT REPAIR, not a replay of any old
provider request and not permission to submit a new paid review. It uses the
real old original source/role claim and a deterministic physics clarification.
Other unknown failures remain quarantined until a distinct registered remedy.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from app_generator.validation.autonomous_completion import (
    assessment_progress, make_prompt, package_identity,
)
from app_generator.validation.v3_locale_script_integrity import script_findings
from app_generator.validation.v3_versioned_text_repair import store_private_repair

_SECTION = "section-9-6"
_ACTIVITY = "mcq-mod-bat-cut-mass-comparison"
_INDEX = 5
_PARENT = "1620d15e1d645c81301997f0e42d0efbad0a7b2d123eb6b11cba9ec8c04b027f"
_LEGACY = "HISTORICAL_UNRECOVERABLE_GEMINI_VALUEERROR_PRESERVED"
_OLD = {
    "en": ("If a technician cuts the pin vertically into two pieces along this "
           "balance line, how do the masses of the two segments compare?"),
    "ms": ("Jika seorang juruteknik memotong pin itu secara menegak kepada dua "
           "bahagian di sepanjang garisan keseimbangan ini, bagaimanakah "
           "perbandingan jisim kedua-dua segmen tersebut?"),
    "zh": ("如果技术人员沿着这条平衡线将定位销垂直切成两段，那么这两个"
           "部分的质量大小关系如何？"),
}
_NEW = {
    "en": ("A technician cuts the pin vertically into two pieces along this "
           "balance line. The center of mass of the piece on the thick-head "
           "side is 2 cm from the cut, while that of the piece on the "
           "slender-rod side is 8 cm from the cut. How do their masses "
           "compare?"),
    "ms": ("Seorang juruteknik memotong pin itu secara menegak kepada dua "
           "bahagian di sepanjang garisan keseimbangan ini. Pusat jisim "
           "bahagian di sisi kepala tebal berada 2 cm dari garisan potongan, "
           "manakala pusat jisim bahagian di sisi rod langsing berada 8 cm "
           "dari garisan potongan. Bagaimanakah perbandingan jisim "
           "kedua-dua bahagian itu?"),
    "zh": ("技术人员沿着这条平衡线将定位销垂直切成两段。切割后，粗大头部"
           "一侧那段的质心距切面为 2 厘米，而细长导杆一侧那段的质心距"
           "切面为 8 厘米。这两段的质量大小关系如何？"),
}


def stage_known_unrecoverable_section96(
    course: Path, repo: Path, private: Path,
) -> dict:
    """Create one immutable source-bounded replacement and QA input, no API."""
    source = course / _SECTION / "package.json"
    if source.is_symlink() or not source.is_file():
        return {"status": "NO_REGISTERED_HISTORICAL_ROLE_REMEDY"}
    raw = source.read_bytes()
    digest, activities = package_identity(raw)
    if digest != _PARENT:
        return {"status": "NO_REGISTERED_HISTORICAL_ROLE_REMEDY"}
    if len(activities) != 18 or activities[_INDEX]["id"] != _ACTIVITY:
        raise ValueError("V3_ROLLFORWARD_FROZEN_ORIGINAL_IDENTITY_CHANGED")
    if (not private.is_absolute() or private.is_symlink()
            or private.resolve().is_relative_to(repo.resolve())):
        raise ValueError("V3_ROLLFORWARD_PRIVATE_ROOT_REQUIRED")
    batch = private / ("v3-generated-" + digest) / "batches"
    claim_file = batch / f"v3-review-{digest[:12]}-005-0.json"
    semantics_file = batch / f"v3-review-{digest[:12]}-005-1.json"
    assessment_file = batch / ("v3-assessment-" + digest + ".json")
    if any(p.is_symlink() or not p.is_file() or p.stat().st_size > 1_000_000
           for p in (claim_file, semantics_file, assessment_file)):
        return {"status": "HISTORICAL_ROLE_EVIDENCE_UNAVAILABLE"}
    old_capture = claim_file.with_suffix(".response.txt")
    if old_capture.exists() or old_capture.is_symlink():
        # An original response may now be locally recoverable. Never bypass
        # that reconciliation by manufacturing a new role identity.
        return {"status": "STOP_ORIGINAL_RESPONSE_EVIDENCE_MUST_RECONCILE"}
    claim_raw = claim_file.read_bytes()
    claim = json.loads(claim_raw.decode("utf8"))
    semantics = json.loads(semantics_file.read_text(encoding="utf8"))
    original = json.loads(assessment_file.read_text(encoding="utf8"))
    progress = assessment_progress(raw, original)
    prompt_hash = sha256(make_prompt(
        activities[_INDEX], "physics-adversary").encode("utf8")).hexdigest()
    if (progress["activitiesAssessed"] != 6
            or original["reviews"][_INDEX]["status"] != "AI_UNCERTAIN"
            or claim.get("packageSha256") != digest
            or claim.get("activityId") != _ACTIVITY
            or claim.get("roleIndex") != 0
            or claim.get("providerId") != "gemini_api"
            or claim.get("reviewerId") != "v3-gemini-api-physics"
            or claim.get("state") != "AMBIGUOUS"
            or claim.get("reasonCode") != "ValueError"
            or claim.get("promptSha256") != prompt_hash
            or claim.get("responseSha256")
            or semantics.get("state") != "COMPLETE"
            or semantics.get("roleIndex") != 1
            or semantics.get("packageSha256") != digest):
        return {"status": "STOP_UNTRUSTED_UNRECOVERABLE_ROLE_SIGNATURE"}
    # The real original conceptual question does not explicitly give lever
    # arms; a text-only claim should never justify the new answer. This
    # substantive revision supplies measured 2 cm and 8 cm distances so
    # the mass comparison follows from the center-of-mass moment equation.
    # 2*M_head = 8*M_rod implies M_head=4*M_rod (>M_rod).
    if 2 * 4 != 8 or 4 <= 1:
        raise ValueError("V3_ROLLFORWARD_PHYSICS_PROOF_FAILED")
    amended = json.loads(raw.decode("utf8"))
    task = amended["activities"][_INDEX]
    for locale in ("en", "ms", "zh"):
        if task["prompt"][locale].count(_OLD[locale]) != 1:
            raise ValueError("V3_ROLLFORWARD_UNEXPECTED_ORIGINAL_LANGUAGE")
        task["prompt"][locale] = task["prompt"][locale].replace(
            _OLD[locale], _NEW[locale])
    if script_findings(amended):
        raise ValueError("V3_ROLLFORWARD_INVALID_SCRIPT")
    candidate = (json.dumps(amended,ensure_ascii=False,indent=2)+"\n").encode("utf8")
    candidate_sha, new_activities = package_identity(candidate)
    if (candidate_sha == digest or len(new_activities) != len(activities)
            or [a["id"] for a in new_activities] != [a["id"] for a in activities]
            or any(old != new for i,(old,new) in enumerate(
                zip(activities,new_activities)) if i != _INDEX)
            or set(k for k in task if task[k] != activities[_INDEX][k])
               != {"prompt"}):
        raise ValueError("V3_ROLLFORWARD_NOT_AN_EXACT_ONE_ACTIVITY_REPAIR")
    receipt = {
        "contract": "BOSLA_V3_UNRECOVERABLE_ROLE_VERSIONED_REPAIR_V1",
        "parentPackageSha256": digest,
        "candidatePackageSha256": candidate_sha,
        "historicalRoleClaimSha256": sha256(claim_raw).hexdigest(),
        "historicalReviewerStatus": _LEGACY,
        "activityIndex": _INDEX, "activityId": _ACTIVITY,
        "changedFieldPaths": [f"activities[{_INDEX}].prompt.{l}" for l in
                              ("en","ms","zh")],
        "balanceProof": {
            "thickHeadCenterCm": 2, "slenderRodCenterCm": 8,
            "thickToSlenderMassRatio": 4,
        },
        "scope": "NEW_CONTENT_VERSION_NOT_AUTHORIZED_FOR_PAID_REVIEW",
        "status": "PENDING_FRESH_OWNER_AUTHORIZED_TWO_GEMINI_REVIEW",
        "parentModelVerdictModified": False,
        "oldRequestReplayed": False,
        "newModelConsensusPassClaimed": False,
        "versionedScopeAdmitted": False,
        "publicationAuthorized": False,
    }
    # Reuse BSA-175's fsync+atomic-rename hardening, and BSA-174's
    # immutable source/version provenance. Never write source into Git.
    folder = store_private_repair(
        private / "historical-role-rollforward" / _SECTION,
        candidate, receipt)
    # One changed activity only; distinct SHA and prompt from the earlier
    # potentially submitted original review. Never reserve PRE_CALL here.
    slice_package = {
        "schema": "BOSLA_V3_NEW_VERSIONED_ROLE_REVIEW_INPUT_V1",
        "sourceSection": _SECTION,
        "parentPackageSha256": digest,
        "candidatePackageSha256": candidate_sha,
        "sourceActivityIndex": _INDEX,
        "historicalRoleClaimSha256": sha256(claim_raw).hexdigest(),
        "activities": [new_activities[_INDEX]],
    }
    review_raw = (json.dumps(
        slice_package,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")
    review_sha, check = package_identity(review_raw)
    if len(check)!=1 or check[0]!=new_activities[_INDEX] or review_sha==digest:
        raise ValueError("V3_ROLLFORWARD_REVIEW_SLICE_MISMATCH")
    input_receipt = {
        "contract": "BOSLA_V3_NEW_VERSIONED_ROLE_REVIEW_INPUT_V1",
        "candidatePackageSha256": review_sha,
        "parentPackageSha256": candidate_sha,
        "historicalRoleClaimSha256": sha256(claim_raw).hexdigest(),
        "scope": "ONE_CHANGED_ACTIVITY_NEW_VERSION_REQUIRES_PAID_AUTHORIZATION",
        "newModelConsensusPassClaimed": False,
        "publicationAuthorized": False,
    }
    input_folder = store_private_repair(
        private / "historical-role-review-inputs" / _SECTION,
        review_raw, input_receipt)
    if (folder / "package.json").read_bytes() != candidate or (
        input_folder / "package.json").read_bytes()!=review_raw:
        raise ValueError("V3_ROLLFORWARD_CHANGED_PRIVATE_CANDIDATE")
    return {
        "status": "NEW_VERSIONED_SECTION96_REPAIR_STAGED_QA_NOT_AUTHORIZED",
        "parentPackageSha256": digest,
        "candidatePackageSha256": candidate_sha,
        "isolatedReviewInputSha256": review_sha,
        "oldAmbiguousProviderRolePreserved": True,
        "oldRequestReplayed": False,
        "paidGeminiCalls": 0,
        "newModelConsensusPassClaimed": False,
        "versionedScopeAdmitted": False,
        "publicationAuthorized": False,
    }

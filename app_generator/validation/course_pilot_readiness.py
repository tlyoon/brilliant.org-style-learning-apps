"""Offline six-subchapter *candidate* inventory; never an academic or release gate.

This extends the existing Stage-0 roster checker to one course-level selection.
Metadata and matching digests cannot prove independent source accuracy,
EN/MS/ZH meaning, scientific/visual correctness, learner browser behavior or
instructor approval. Decision 0033 excludes rights-holder/rights clearance
from BOSLA's technical-completion evidence fields.
No PDF, network, model, private evidence or learner record is opened here.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Callable

from app_generator.validation.bounded_cross_topic_acceptance import (
    ProductRosterMismatch,
    inspect_stage0_product_roster,
)

_SHA = re.compile(r"[a-f0-9]{64}\Z")
_GIT_SHA = re.compile(r"[a-f0-9]{40}\Z")
_NAME = re.compile(r"sourcefree-pilot-[a-z0-9-]{3,60}\Z")
_PATH = re.compile(
    r"content/chapter-([1-9][0-9]*)/section-([1-9][0-9]*)-"
    r"([1-9][0-9]*)/package\.json\Z"
)
_FIELDS = {
    "scopeId", "baselineGitSha", "chapterNumber", "mode", "cases",
    "modelCallsAllowed", "pdfReadsAllowed", "publicationAllowed",
}
_CASE_FIELDS = {"sectionNumber", "packagePath", "packageSha256"}
_LANGUAGES = frozenset(("en", "ms", "zh"))


def validate_pilot_scope(manifest: dict[str, Any]) -> None:
    """Validate the complete six-case scope before loading any package."""
    if not isinstance(manifest, dict) or set(manifest) != _FIELDS:
        raise ValueError("STRICT_PILOT_MANIFEST_REQUIRED")
    if (not isinstance(manifest["scopeId"], str)
            or not _NAME.fullmatch(manifest["scopeId"])
            or not isinstance(manifest["baselineGitSha"], str)
            or not _GIT_SHA.fullmatch(manifest["baselineGitSha"])):
        raise ValueError("INVALID_FROZEN_PILOT_IDENTITY")
    chapter = manifest["chapterNumber"]
    if type(chapter) is not int or chapter < 1:
        raise ValueError("INVALID_CHAPTER_NUMBER")
    if (manifest["mode"] != "OFFLINE_EXISTING_PACKAGES_ONLY"
            or any(manifest[key] is not False for key in (
                "modelCallsAllowed", "pdfReadsAllowed", "publicationAllowed"
            ))):
        raise ValueError("PILOT_MUST_REMAIN_SOURCE_FREE_AND_UNPUBLISHED")
    cases = manifest["cases"]
    if not isinstance(cases, list) or len(cases) != 6:
        raise ValueError("EXACTLY_SIX_SUBCHAPTER_CANDIDATES_REQUIRED")
    sections: set[int] = set()
    paths: set[str] = set()
    digests: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != _CASE_FIELDS:
            raise ValueError("STRICT_PILOT_CASE_REQUIRED")
        section = case["sectionNumber"]
        path = case["packagePath"]
        digest = case["packageSha256"]
        if (type(section) is not int or section < 1
                or not isinstance(path, str)
                or not isinstance(digest, str)
                or not _SHA.fullmatch(digest)):
            raise ValueError("INVALID_SECTION_OR_PACKAGE_IDENTITY")
        match = _PATH.fullmatch(path)
        if (match is None or int(match[1]) != chapter
                or int(match[2]) != chapter or int(match[3]) != section):
            raise ValueError("CROSS_CHAPTER_OR_UNSAFE_PACKAGE_PATH")
        folded = path.casefold()
        if section in sections or folded in paths or digest in digests:
            raise ValueError("DUPLICATED_SECTION_PATH_OR_PACKAGE_DIGEST")
        sections.add(section)
        paths.add(folded)
        digests.add(digest)


def assess_pilot_candidates(
    manifest: dict[str, Any], loader: Callable[[str], bytes], *,
    observed_git_sha: str,
) -> dict[str, Any]:
    """Read exactly six content packages, preserving independent evidence gaps.

    A successful source-free audit is *not* readiness for a classroom pilot.
    The caller supplies a constrained package loader; the manifest rejects
    traversal and aliases before calling it.
    """
    validate_pilot_scope(manifest)
    if observed_git_sha != manifest["baselineGitSha"]:
        raise ValueError("FROZEN_GIT_REVISION_MISMATCH")
    chapter = manifest["chapterNumber"]
    results: list[dict[str, Any]] = []
    for case in manifest["cases"]:
        section = case["sectionNumber"]
        status = "INVALID_PACKAGE_EVIDENCE"
        visual_plans = 0
        visual_specs = 0
        failure = None
        try:
            raw = loader(case["packagePath"])
            if not isinstance(raw, bytes) or sha256(raw).hexdigest() != case["packageSha256"]:
                raise ValueError("PACKAGE_SHA_MISMATCH")
            package = json.loads(raw.decode("utf-8"))
            inspect_stage0_product_roster(package)
            expected_id = f"chapter-{chapter}-section-{chapter}-{section}"
            expected_source = (
                f"content/source-manifests/chapter-{chapter}-section-{chapter}-{section}.json"
            )
            if (package.get("packageId") != expected_id
                    or package.get("chapter") != f"Chapter {chapter}"
                    or not isinstance(package.get("subchapter"), str)
                    or not re.match(
                        rf"^{chapter}\.{section}(?:\s|$)",
                        package["subchapter"],
                    )
                    or package.get("sourceManifest") != expected_source
                    or package.get("status") not in {"draft", "review", "publishable"}
                    or not isinstance(package.get("locales"), list)
                    or set(package["locales"]) != _LANGUAGES
                    or len(package["locales"]) != len(_LANGUAGES)):
                raise ValueError("PACKAGE_SCOPE_METADATA_MISMATCH")
            activities = package["activities"]
            visual_plans = sum("visualPlan" in item for item in activities)
            visual_specs = sum("visualSpec" in item for item in activities)
            status = "STRUCTURALLY_VALID_SOURCEFREE_CANDIDATE"
        except ProductRosterMismatch:
            status = "INVALID_STAGE0_ROSTER"
            failure = "ACTIVITY_COUNT_TYPE_TIER_OR_ID"
        except (ValueError, TypeError, KeyError, AttributeError, UnicodeError,
                json.JSONDecodeError, OSError):
            # Never put untrusted package/source content or paths into reports.
            failure = "PACKAGE_DIGEST_FORMAT_OR_SCOPE"
        results.append({
            "sectionNumber": section,
            "status": status,
            "issueCategory": failure,
            "declaredVisualPlans": visual_plans,
            "declaredVisualSpecs": visual_specs,
            "allVisualPlansDeclared": visual_plans == 18,
            "visualValueReviewPending": True,
            "academicQA": "REVIEW_REQUIRED",
            # V2: source evidence remains unverified, while the removed
            # rights gate must not reappear in regular pilot-readiness reports.
            "independentSourceVerified": False,
            "independentPhysicsAndTrilingualMeaningVerified": False,
            "independentVisualSemanticsVerified": False,
            "independentBrowserAndAccessibilityVerified": False,
            "publicationAuthorized": False,
        })
    all_structural = all(
        row["status"] == "STRUCTURALLY_VALID_SOURCEFREE_CANDIDATE"
        for row in results
    )
    return {
        "scopeId": manifest["scopeId"],
        "baselineGitSha": manifest["baselineGitSha"],
        "chapterNumber": chapter,
        "caseCount": len(results),
        "structuralCandidateCount": sum(
            row["status"] == "STRUCTURALLY_VALID_SOURCEFREE_CANDIDATE"
            for row in results
        ),
        "status": ("SIX_STRUCTURAL_CANDIDATES_REQUIRE_INDEPENDENT_EVIDENCE"
                   if all_structural else "STOP_INVALID_OR_INCOMPLETE_CANDIDATES"),
        "cases": results,
        "scopeOnly": True,
        "instructorSelectionVerified": False,
        "courseDiagnosticOrPrerequisiteRoutingEnabled": False,
        "institutionalPrivacyApprovalVerified": False,
        "independentAcademicAcceptanceVerified": False,
        "classroomPilotReady": False,
        "publicationAuthorized": False,
    }

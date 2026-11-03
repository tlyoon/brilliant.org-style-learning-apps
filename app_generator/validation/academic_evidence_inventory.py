"""Conservative exact-version inventory of private Section 9.4 evidence.

Receipts establish identity and bounded coverage, not academic truth.
Never accesses a browser, calls an LLM, grants an academic PASS, or publishes.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any

SHA = re.compile(r"[0-9a-f]{64}\Z")
GATES = ("source_fidelity", "answer_correctness", "physics_consistency",
         "visual_semantics", "multilingual_meaning")
STATES = ("PASS", "FAIL", "REVIEW_REQUIRED")
CONTRACTS = {
    "mcq": ("SOURCE_BOUND_MC_Q_BOUNDED_STATEMENT_AUDIT", {
        "originalSourceActivityPassagesReverified": 18,
        "mcqActivitiesChecked": 9,
        "threeLanguageOptionLabelsBoundBySha256": 36}),
    "collision": ("SOURCE_BOUND_EXACT_COLLISION_PROPERTY_GRID_ONLY", {
        "originalSourceActivitiesReverified": 18,
        "mcqAnswerIdRostersChecked": 9,
        "mcqOptionIdentifiersChecked": 36,
        "interactionAnswerModelsCompared": 9}),
    "visual": ("EXACT_SOURCE_TECHNICAL_VISUAL_COVERAGE_ONLY", {
        "activityCount": 18, "screenshotCapturesVerified": 30}),
    "claims": ("EXACT_ORIGINAL_SOURCE_ACADEMIC_CLAIM_COVERAGE", {
        "sourceActivitiesReverified": 18, "activityCount": 18,
        "claimRoleSlots": 180}),
}


def _not_approved(record: dict[str, Any], flag: str) -> None:
    if record.get(flag) is not False:
        raise ValueError("missing or false-positive no-approval flag: " + flag)


def _source_rows(name: str, report: dict[str, Any],
                 matrix_roster: dict[str, dict[str, Any]],
                 exact_roster: dict[str, dict[str, Any]] | None = None
                 ) -> dict[str, dict[str, Any]]:
    rows = report.get("optionChecks" if name == "mcq" else "activities")
    if not isinstance(rows, list):
        raise ValueError("evidence rows are absent")
    if name == "mcq":
        expected_ids = {k for k, v in matrix_roster.items() if v["type"] == "mcq"}
        if len(expected_ids) != 9 or len(rows) != 36:
            raise ValueError("MCQ activity/option counts differ from original package")
        expected_options: dict[tuple[str, str], tuple[str, str]] | None = None
        if exact_roster is not None:
            expected_options = {}
            for aid in expected_ids:
                answer = exact_roster[aid].get("answerKey")
                options = answer.get("options") if isinstance(answer, dict) else None
                correct = answer.get("correct") if isinstance(answer, dict) else None
                if not isinstance(options, list) or len(options) != 4:
                    raise ValueError("exact package MCQ has incomplete answer options")
                identities = [o.get("id") for o in options if isinstance(o, dict)]
                if (len(identities) != 4 or any(not isinstance(oid, str) or not oid
                        for oid in identities) or len(set(identities)) != 4
                        or correct not in identities):
                    raise ValueError("exact package MCQ answer key invalid")
                for option in options:
                    label = option.get("label")
                    if (not isinstance(label, dict) or set(label) != {"en", "ms", "zh"}
                            or any(not isinstance(label[lang], str) or not label[lang].strip()
                                   for lang in ("en", "ms", "zh"))):
                        raise ValueError("exact package multilingual MCQ label invalid")
                    digest = sha256(json.dumps(label, sort_keys=True, ensure_ascii=False,
                        separators=(",", ":")).encode("utf-8")).hexdigest()
                    status = ("BOUNDED_PHYSICS_SUPPORT" if option["id"] == correct
                              else "BOUNDED_PHYSICS_COUNTEREXAMPLE")
                    expected_options[(aid, option["id"])] = (digest, status)
            if len(expected_options) != 36:
                raise ValueError("exact package does not contain 36 MCQ options")
        seen: set[tuple[str, str]] = set()
        summary = {"BOUNDED_PHYSICS_SUPPORT": 0,
                   "BOUNDED_PHYSICS_COUNTEREXAMPLE": 0,
                   "FIGURE_CONTACT_SEMANTICS_PENDING": 0}
        for entry in rows:
            if not isinstance(entry, dict):
                raise ValueError("malformed MCQ option")
            aid, oid = entry.get("activityId"), entry.get("optionId")
            if (aid not in expected_ids or not isinstance(oid, str) or not oid
                    or (aid, oid) in seen or entry.get("status") not in summary):
                raise ValueError("missing, duplicate or unrecognized MCQ option")
            seen.add((aid, oid))
            summary[entry["status"]] += 1
            label_sha = entry.get("exactMultilingualLabelSha256")
            if not isinstance(label_sha, str) or not SHA.fullmatch(label_sha):
                raise ValueError("invalid original option label SHA")
            if expected_options is not None and expected_options.get((aid, oid)) != (
                    label_sha, entry["status"]):
                raise ValueError("MCQ option identity, wording or answer status differs from exact package")
            for key in ("scientificMeaningFullyVerified", "translationMeaningVerified",
                        "sourceFigureInterpretationVerified"):
                _not_approved(entry, key)
        if any(sum(a == aid for a, _ in seen) != 4 for aid in expected_ids):
            raise ValueError("MCQ option roster must contain four choices per activity")
        if summary != {"BOUNDED_PHYSICS_SUPPORT": 9,
                       "BOUNDED_PHYSICS_COUNTEREXAMPLE": 27,
                       "FIGURE_CONTACT_SEMANTICS_PENDING": 0}:
            raise ValueError("bounded MCQ evidence totals mismatch")
        for field, expected in (("boundedAnswerOptionsSupported", 9),
                                ("boundedDistractorsCounterexampled", 27),
                                ("sourceFigureContactSemanticsPending", 0)):
            if type(report.get(field)) is not int or report[field] != expected:
                raise ValueError("bounded physics count is incomplete")
        for flag in ("allOptionMeaningsFullyVerified", "translationMeaningVerified",
                     "originalFigureScientificMeaningAutomaticallyApproved",
                     "independentAcademicReviewerAccepted"):
            _not_approved(report, flag)
        return {aid: {"fourOptionsReported": True} for aid in expected_ids}
    if not isinstance(rows, list) or len(rows) != 18:
        raise ValueError("evidence report requires 18 activity rows")
    result: dict[str, dict[str, Any]] = {}
    for entry in rows:
        if not isinstance(entry, dict) or entry.get("activityId") not in matrix_roster:
            raise ValueError("supporting evidence contains unknown activity")
        aid = entry["activityId"]
        if aid in result or entry.get("academicQA") != "REVIEW_REQUIRED":
            raise ValueError("duplicate or falsely approved activity evidence")
        _not_approved(entry, "publicationAuthorized")
        if name == "visual":
            for flag in ("scientificVisualSemanticsVerified", "trilingualVisualMeaningVerified"):
                _not_approved(entry, flag)
            yes, pixel, captures = (
                entry.get("visualSpecPresent"),
                entry.get("technicalPixelIntegrityVerified"),
                entry.get("technicalVisualCapturesVerified"))
            if (type(yes) is not bool or type(pixel) is not bool or yes != pixel
                    or type(captures) is not int or captures != (6 if yes else 0)):
                raise ValueError("six technical captures required for visual activity")
            result[aid] = {"technicalVisualReported": yes}
        elif name == "claims":
            states = entry.get("claimStates")
            if (not isinstance(states, dict) or not states or
                    any(not isinstance(k, str) or type(n) is not int or n < 0
                        for k, n in states.items()) or sum(states.values()) != 10 or
                    entry.get("originalSourcePassageReverified") is not True):
                raise ValueError("two reviewers x five gates require ten claims per activity")
            run_located = entry.get("reviewRunLocated")
            if type(run_located) is not bool:
                raise ValueError("review-run existence must be explicit")
            if any(states.get(key, 0) for key in ("AMBIGUOUS", "IN_FLIGHT", "SKIPPED_UNSENT")):
                expected_action = "RECONCILE_EXISTING_NONREPLAYABLE_CLAIMS"
            elif not run_located:
                expected_action = "FRESH_INDEPENDENT_REVIEW_NOT_YET_SUBMITTED"
            else:
                expected_action = "INDEPENDENT_DETERMINISTIC_PROOF_REQUIRED"
            if entry.get("nextAction") != expected_action:
                raise ValueError("review next action contradicts immutable claim state")
            result[aid] = {"reviewClaimStates": states,
                           "reviewNextAction": expected_action}
        else:
            raise ValueError("unknown evidence report")
    if set(result) != set(matrix_roster):
        raise ValueError("supporting report activity roster incomplete")
    if name == "visual":
        if exact_roster is not None and any(
                record["technicalVisualReported"] != bool(exact_roster[aid].get("visualSpec"))
                for aid, record in result.items()):
            raise ValueError("visual evidence activity roster contradicts exact package visualSpec")
        if (sum(x["technicalVisualReported"] for x in result.values()) != 5
                or report.get("visualActivities") != 5):
            raise ValueError("exact five visual activities required")
    if name == "claims":
        aggregate: dict[str, int] = {}
        for record in result.values():
            for state, count in record["reviewClaimStates"].items():
                aggregate[state] = aggregate.get(state, 0) + count
        if report.get("claimStates") != aggregate or sum(aggregate.values()) != 180:
            raise ValueError("claim state aggregate mismatches individual reviewer slots")
    return result


def reconcile_evidence(
    matrix: dict[str, Any], *, reports: dict[str, dict[str, Any]] | None = None,
    expected_package_sha256: str, expected_source_sha256: str,
    exact_package: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Join bounded private metadata, keeping all five gates pending."""
    source, package = expected_source_sha256, expected_package_sha256
    if not all(isinstance(s, str) and SHA.fullmatch(s) for s in (source, package)):
        raise ValueError("literal lowercase SHA256 digests required")
    if (not isinstance(matrix, dict) or matrix.get("sourceSha256") != source or
            matrix.get("packageSha256") != package or matrix.get("activityCount") != 18
            or matrix.get("academicQA") != "REVIEW_REQUIRED"):
        raise ValueError("academic matrix must match exact package and original source")
    _not_approved(matrix, "publicationAuthorized")
    rows = matrix.get("activities")
    if not isinstance(rows, list) or len(rows) != 18:
        raise ValueError("18 source matrix activities required")
    exact_roster = None
    if exact_package is not None:
        activities = exact_package.get("activities") if isinstance(exact_package, dict) else None
        if not isinstance(activities, list) or len(activities) != 18:
            raise ValueError("exact private package must contain 18 activities")
        exact_roster = {}
        for activity in activities:
            if not isinstance(activity, dict):
                raise ValueError("invalid exact activity")
            aid = activity.get("id")
            if not isinstance(aid, str) or not aid or aid in exact_roster:
                raise ValueError("duplicate or missing original package activity ID")
            exact_roster[aid] = activity
    roster: dict[str, dict[str, Any]] = {}
    counts = {"PASS": 0, "FAIL": 0, "REVIEW_REQUIRED": 0}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid matrix activity")
        aid, gates = row.get("activityId"), row.get("gates")
        if (not isinstance(aid, str) or not aid or aid in roster
                or not isinstance(gates, dict) or set(gates) != set(GATES)
                or any(x != "REVIEW_REQUIRED" for x in gates.values())
                or row.get("academicQA") != "REVIEW_REQUIRED"
                or row.get("sourceLocationVerified") is not True):
            raise ValueError("matrix has missing or unproven academic gates")
        _not_approved(row, "publicationAuthorized")
        if exact_roster is not None:
            actual = exact_roster.get(aid)
            if actual is None:
                raise ValueError("matrix activity absent from exact package")
            digest = sha256(json.dumps(actual, sort_keys=True, ensure_ascii=False,
                    separators=(",", ":")).encode("utf-8")).hexdigest()
            if row.get("activitySha256") != digest or row.get("type") != actual.get("type"):
                raise ValueError("matrix per-activity digest or type is stale")
        counts["REVIEW_REQUIRED"] += 1
        roster[aid] = row
    if exact_roster is not None and set(exact_roster) != set(roster):
        raise ValueError("package roster differs from academic matrix")
    if matrix.get("counts") != counts or any(type(v) is not int for v in matrix["counts"].values()):
        raise ValueError("invalid PASS/FAIL/REVIEW_REQUIRED aggregate")
    if reports is None:
        reports = {}
    if not isinstance(reports, dict) or not set(reports).issubset(CONTRACTS):
        raise ValueError("unknown report type")
    proven: dict[str, dict[str, dict[str, Any]]] = {}
    for name, report in reports.items():
        status, required = CONTRACTS[name]
        if (not isinstance(report, dict) or report.get("status") != status
                or report.get("sourceSha256") != source
                or report.get("packageSha256") != package
                or report.get("academicQA") != "REVIEW_REQUIRED"):
            raise ValueError("supporting evidence stale or improperly approved")
        _not_approved(report, "publicationAuthorized")
        for key, expected in required.items():
            if type(report.get(key)) is not int or report[key] != expected:
                raise ValueError("supporting report counts are incomplete")
        if name == "visual":
            _not_approved(report, "scientificVisualSemanticsVerified")
            if report.get("formalAcademicPASSCount") != 0:
                raise ValueError("technical pixels do not grant scientific approval")
        if name == "claims":
            _not_approved(report, "modelReviewIsFormalPass")
            if report.get("formalAcademicPASSCount") != 0:
                raise ValueError("reviewer coverage does not confer academic PASS")
        if name in ("mcq", "collision") and report.get("formalAcademicPASS") != 0:
            raise ValueError("bounded physics evidence cannot grant academic PASS")
        if name in ("mcq", "visual", "claims"):
            proven[name] = _source_rows(name, report, roster, exact_roster)
    work = []
    for aid, row in roster.items():
        mode = row.get("type")
        claim = proven.get("claims", {}).get(aid)
        if mode == "mcq" and "mcq" not in reports:
            action = "AUTO_REVERIFY_MCQ_STATEMENT_MODELS"
        elif mode != "mcq" and "collision" not in reports:
            action = "AUTO_REVERIFY_INTERACTION_PHYSICS"
        elif claim and claim.get("reviewNextAction") == "RECONCILE_EXISTING_NONREPLAYABLE_CLAIMS":
            action = "AUTO_RECONCILE_EXISTING_NONREPLAYABLE_CLAIMS_NO_RETRY"
        elif claim and claim.get("reviewNextAction") == "FRESH_INDEPENDENT_REVIEW_NOT_YET_SUBMITTED":
            action = "AUTO_ADMIT_FRESH_INDEPENDENT_REVIEW_AFTER_READINESS_PREFLIGHT"
        elif "claims" not in reports:
            action = "AUTO_RECONCILE_OR_RUN_INDEPENDENT_REVIEW"
        elif "visual" not in reports:
            action = "AUTO_VERIFY_PRIVATE_VISUAL_RECEIPTS"
        else:
            action = "AUTO_INDEPENDENT_SCIENTIFIC_AND_MULTILINGUAL_REVIEW"
        work.append({
            "activityId": aid,
            "outstandingGates": list(GATES),
            "boundedEvidenceReported": {
                "sourceLocation": True,
                "mcqStatements": mode == "mcq" and "mcq" in reports,
                "collisionGrid": "collision" in reports,
                "technicalVisual": "visual" in reports,
                "reviewClaimCoverage": "claims" in reports,
            },
            "nextAutomaticAction": action,
            "immutableNonReplayableReviewClaimPresent": action ==
                "AUTO_RECONCILE_EXISTING_NONREPLAYABLE_CLAIMS_NO_RETRY",
            "formalAcademicPASS": False,
        })
    frequencies = {a: sum(x["nextAutomaticAction"] == a for x in work)
                   for a in sorted({x["nextAutomaticAction"] for x in work})}
    return {
        "status": "SOURCE_BOUND_ACADEMIC_EVIDENCE_INVENTORY_ONLY",
        "supportingReportsOnlyMetadataChecked": True,
        "sourceSha256": source, "packageSha256": package,
        "activityCount": 18, "sourceLocationsReportedVerified": 18,
        "packageActivityDigestsIndependentlyVerified": exact_roster is not None,
        "sourceLocationsIndependentlyReverifiedThisRun": False,
        "boundedReceiptCategoriesReconciled": sorted(reports),
        "missingReceiptCategories": sorted(set(CONTRACTS)-set(reports)),
        "academicCounts": counts, "formalAcademicPASSCount": 0,
        "humanAcademicApprovalRequired": False, "publicationAuthorized": False,
        "nextActionCounts": frequencies, "nextActions": work,
    }

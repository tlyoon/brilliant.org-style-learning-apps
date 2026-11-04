"""Metadata-only academic review prioritization, never academic approval.

Joins exact-source-bound original activity review coverage with multilingual
numeric token triage. Potential Chinese number-word notation equivalences
remain flags, NOT deterministic translation certificates.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

_BAD_STATES=frozenset(("AMBIGUOUS","IN_FLIGHT","SKIPPED_UNSENT"))


def prioritize_academic_review(
    coverage:dict[str,Any], multilingual:dict[str,Any],
) -> dict[str,Any]:
    if (not isinstance(coverage,dict) or not isinstance(multilingual,dict) or
        coverage.get("status")!="EXACT_ORIGINAL_SOURCE_ACADEMIC_CLAIM_COVERAGE" or
        multilingual.get("status")!="SOURCE_BOUND_NUMERIC_TOKEN_TRIAGE" or
        any(not isinstance(coverage.get(k),str) or
            coverage[k]!=multilingual.get(k) for k in ("packageSha256","sourceSha256"))):
        raise ValueError("unmatched exact-source bilingual evidence provenance")
    reviewed=coverage.get("activities")
    localized=multilingual.get("activities")
    if not isinstance(reviewed,list) or not isinstance(localized,list):
        raise ValueError("both full-activity source-bound inventories required")
    n=coverage.get("activityCount")
    if (type(n) is not int or n<1 or n!=len(reviewed) or len(localized)!=n or
        coverage.get("sourceActivitiesReverified")!=n or
        multilingual.get("sourceVerifiedActivities")!=n):
        raise ValueError("full original-source activity evidence coverage required")
    known={}
    for entry in localized:
        if (not isinstance(entry,dict) or not isinstance(entry.get("activityId"),str) or
            entry["activityId"] in known or not isinstance(entry.get("numericTokenDriftFlags"),list)):
            raise ValueError("invalid multilingual triage activity identity")
        for flag in entry["numericTokenDriftFlags"]:
            if (not isinstance(flag,dict) or
                flag.get("reasonCode")!="CROSS_LOCALE_NUMERIC_TOKEN_DIFFERENCE" or
                flag.get("confirmedSemanticEquivalence") is not False):
                raise ValueError("numeric difference is missing unproven status")
        known[entry["activityId"]]=entry
    ids=[x.get("activityId") for x in reviewed if isinstance(x,dict)]
    if len(ids)!=n or len(set(ids))!=n or set(ids)!=set(known):
        raise ValueError("numeric and claim roster activity identities differ")
    rows=[]
    for x in reviewed:
        states=x.get("claimStates")
        if (not isinstance(states,dict) or any(
            type(count) is not int or count<0 for count in states.values()
        ) or sum(states.values())!=10 or
            x.get("originalSourcePassageReverified") is not True or
            x.get("publicationAuthorized") is not False):
            raise ValueError("claim coverage metadata inconsistent or falsely approved")
        flags=known[x["activityId"]]["numericTokenDriftFlags"]
        unresolved=sum(states.get(k,0) for k in _BAD_STATES)
        missing=states.get("NOT_SUBMITTED",0)+states.get("MISSING",0)
        priority=(
            "RECONCILE_EXISTING_NONREPLAYABLE_CLAIMS" if unresolved else
            "INDEPENDENT_MULTILINGUAL_SEMANTIC_REVIEW" if flags else
            "SUBMIT_FRESH_INDEPENDENT_REVIEW_WHEN_AUTHORIZED" if missing else
            "INDEPENDENT_DETERMINISTIC_PHYSICS_VISUAL_PROOF"
        )
        rows.append({
            "activityId":x["activityId"],
            "priority":priority,
            "unreconciledSubmittedOrSkippedClaims":unresolved,
            "missingOrUnsentReviewSlots":missing,
            "multilingualNumericReviewFlags":len(flags),
            "possibleNotationEquivalentFlags":sum(
                str(f.get("candidateReason","")).startswith("POSSIBLE_") for f in flags
            ),
            "semanticEquivalenceProven":False,
            "academicQA":"REVIEW_REQUIRED",
            "publicationAuthorized":False,
        })
    order={
        "RECONCILE_EXISTING_NONREPLAYABLE_CLAIMS":0,
        "INDEPENDENT_MULTILINGUAL_SEMANTIC_REVIEW":1,
        "SUBMIT_FRESH_INDEPENDENT_REVIEW_WHEN_AUTHORIZED":2,
        "INDEPENDENT_DETERMINISTIC_PHYSICS_VISUAL_PROOF":3,
    }
    rows.sort(key=lambda row:(order[row["priority"]],
                               -row["multilingualNumericReviewFlags"],
                               row["activityId"]))
    if sum(row["multilingualNumericReviewFlags"] for row in rows)!=multilingual.get("numericDriftFlagCount"):
        raise ValueError("numeric triage flag totals are inconsistent")
    return {
        "status":"SOURCE_BOUND_AUTONOMOUS_ACADEMIC_REVIEW_QUEUE",
        "sourceSha256":coverage["sourceSha256"],
        "packageSha256":coverage["packageSha256"],
        "activityCount":n,
        "reviewFlagCount":multilingual["numericDriftFlagCount"],
        "priorityCounts":dict(Counter(row["priority"] for row in rows)),
        "activities":rows,
        "numericParityEstablishesTranslation":False,
        "semanticEquivalenceProven":False,
        "academicQA":"REVIEW_REQUIRED",
        "formalAcademicPASSCount":0,
        "publicationAuthorized":False,
    }

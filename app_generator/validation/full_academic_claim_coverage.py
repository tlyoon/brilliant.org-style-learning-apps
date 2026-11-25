"""Private exact-original-source 18-activity academic claim coverage matrix.

This is an inventory of evidence, never independent academic correctness.
Unreviewed claims are NOT_SUBMITTED, not ambiguous and not supported.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster
from app_generator.validation.source_bound_claim_audit import audit_source_bound_claim_run
from app_generator.validation.academic_qa import REQUIRED


def audit_academic_claim_coverage(
    *, package_file:Path, source_pdf:Path, packets_file:Path,
    reviewer_runs_file:Path, expected_count:int=18,
) -> dict[str,Any]:
    source=verify_full_source_packet_roster(
        package_file=package_file,source_pdf=source_pdf,
        packets_file=packets_file,expected_count=expected_count,
    )
    listing=json.loads(reviewer_runs_file.read_text(encoding="utf-8"))
    if (not isinstance(listing,dict) or
        listing.get("packageSha256")!=source["packageSha256"] or
        listing.get("sourceSha256")!=source["sourceSha256"]):
        raise ValueError("review run list not bound to original PDF and corrected package")
    runs=listing.get("runs")
    if not isinstance(runs,list) or len(runs)>expected_count:
        raise ValueError("bounded independent reviewer run list required")
    mapped={}
    ids={entry["activityId"] for entry in source["activityEvidence"]}
    for entry in runs:
        if (not isinstance(entry,dict) or
            not isinstance(entry.get("activityId"),str) or
            entry["activityId"] not in ids or
            entry["activityId"] in mapped or
            not isinstance(entry.get("claimsDir"),str) or
            not isinstance(entry.get("claimPrefix"),str)):
            raise ValueError("reviewer run must have one unique source-bound activity")
        mapped[entry["activityId"]]=entry
    combined=Counter()
    rows=[]
    for item in source["activityEvidence"]:
        aid=item["activityId"]
        record=mapped.get(aid)
        if record is None:
            states={"NOT_SUBMITTED":2*len(REQUIRED)}
        else:
            run=audit_source_bound_claim_run(
                package_file=package_file,pdf_file=source_pdf,
                packets_file=packets_file,
                claims_dir=Path(record["claimsDir"]),
                activity_id=aid,claim_prefix=record["claimPrefix"],
            )
            if run["sourcePacketReverifiedCount"]!=1 or run["publicationAuthorized"] is not False:
                raise ValueError("academic claim source run not bound or not blocked")
            states=run["stateCounts"]
        combined.update(states)
        rows.append({
            "activityId":aid,
            "originalSourcePassageReverified":True,
            "reviewRunLocated":record is not None,
            "claimStates":states,
            "nextAction":(
                "RECONCILE_EXISTING_NONREPLAYABLE_CLAIMS" if any(
                    key in states for key in ("AMBIGUOUS","IN_FLIGHT","SKIPPED_UNSENT")
                ) else "FRESH_INDEPENDENT_REVIEW_NOT_YET_SUBMITTED"
                if not record else "INDEPENDENT_DETERMINISTIC_PROOF_REQUIRED"
            ),
            "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False,
        })
    if sum(combined.values())!=2*len(REQUIRED)*expected_count:
        raise ValueError("review coverage matrix is missing gate or reviewer-role slots")
    return {
        "status":"EXACT_ORIGINAL_SOURCE_ACADEMIC_CLAIM_COVERAGE",
        "packageSha256":source["packageSha256"],
        "sourceSha256":source["sourceSha256"],
        "sourceActivitiesReverified":source["newlyReverifiedSourceActivities"],
        "originalPassagesReverified":source["newlyReverifiedSourcePassages"],
        "activityCount":expected_count,
        "reviewedRunCount":len(mapped),
        "claimRoleSlots":2*len(REQUIRED)*expected_count,
        "claimStates":dict(combined),
        "activities":rows,
        "sourceMeaningProven":False,
        "modelReviewIsFormalPass":False,
        "formalAcademicPASSCount":0,
        "academicQA":"REVIEW_REQUIRED",
        "publicationAuthorized":False,
    }

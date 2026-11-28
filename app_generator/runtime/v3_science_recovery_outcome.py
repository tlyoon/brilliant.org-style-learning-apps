"""BSA315: a recovery is not effective merely because CI passes.

Make decisions only from independently reverified signed scientific progress,
never source-free V36, synthetic tests, elapsed CPU or scheduler heartbeats.
A second *distinct verified code head* with no science gain switches the next
engineering task family; it never claims that the remaining 401 proofs passed.
"""
from __future__ import annotations
import re

_SHA=re.compile(r"[0-9a-f]{64}\Z")
_HEAD=re.compile(r"[0-9a-f]{40}\Z")


def assess_signed_recovery_outcome(state:dict)->dict:
    source=state.get("scienceAcceptance")
    if not isinstance(source,dict):
        return {"status":"BSA315_AWAIT_INDEPENDENT_SOURCE_REVERIFICATION",
                "pivotRequired":False,
                "publicationAuthorized":False}
    count=source.get("acceptedCount")
    no_gain=source.get("noGainOwnerHeads")
    evidence=source.get("independentReceiptSha256")
    head=source.get("lastVerifiedHead")
    if (type(count) is not int or not 0<=count<=429
        or type(no_gain) is not int or no_gain<0
        or not isinstance(evidence,str) or not _SHA.fullmatch(evidence)
        or not isinstance(head,str) or not _HEAD.fullmatch(head)):
        return {"status":"BSA315_REJECT_UNTRUSTED_RECOVERY_METRICS",
                "pivotRequired":False,
                "publicationAuthorized":False}
    pivot=no_gain>=2
    return {
        "status":("BSA315_TWO_VERIFIED_NO_GAIN_HEADS_REQUIRE_NEW_PROOF_FAMILY"
                  if pivot else
                  "BSA315_SIGNED_RECOVERY_MONITORING"),
        "acceptedCount":count,
        "pendingCount":429-count,
        "noGainDistinctVerifiedOwnerHeads":no_gain,
        "lastVerifiedHead":head,
        "pivotRequired":pivot,
        "nextWorkFamily":(
            "INDEPENDENT_ORIGINAL_SOURCE_TRILINGUAL_OR_DIAGRAM_SEMANTIC_PROOF"
            if pivot else
            "CONTINUE_NEXT_ELIGIBLE_ORIGINAL_SOURCE_PROOF"),
        "measuredScienceGainRequired":True,
        "neverCountEngineeringTestsOrCodeCommits":True,
        "publicationAuthorized":False}

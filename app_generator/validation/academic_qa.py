"""Evidence-based academic QA decisions, deliberately separate from publication.

Unverified model assertions cannot satisfy independently checked requirements.
Only a trusted deterministic checker, or an explicitly approved independent
source-verification receipt, can support an automated PASS.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Sequence

Status = Literal["PASS", "FAIL", "REVIEW_REQUIRED"]
REQUIRED = ("source_fidelity", "answer_correctness", "physics_consistency",
            "visual_semantics", "multilingual_meaning")

@dataclass(frozen=True)
class Finding:
    gate: str
    result: Status
    evidence_kind: str
    evidence_ref: str
    detail: str
    independently_verified: bool = False

    def __post_init__(self):
        if self.result not in ("PASS", "FAIL", "REVIEW_REQUIRED"):
            raise ValueError("unknown academic QA result")
        if not self.gate or not self.detail:
            raise ValueError("finding requires gate and detail")
        if self.result == "PASS" and (not self.independently_verified or
                                     self.evidence_kind not in
                                     {"deterministic", "source_verified"} or not self.evidence_ref):
            raise ValueError("PASS requires independent trustworthy supporting evidence")

def decide(findings: Sequence[Finding], required: Sequence[str] = REQUIRED) -> dict:
    """Conservative three-valued aggregation; failed evidence wins over unknown."""
    if not required or len(set(required)) != len(required):
        raise ValueError("required QA gates must be unique and nonempty")
    if any(x.gate not in required for x in findings):
        raise ValueError("unknown QA gate")
    outcomes = {}
    for gate in required:
        members = [x for x in findings if x.gate == gate]
        if any(m.result == "FAIL" for m in members):
            status = "FAIL"
        elif members and all(m.result == "PASS" for m in members):
            status = "PASS"
        else:
            status = "REVIEW_REQUIRED"
        outcomes[gate] = status
    overall = ("FAIL" if "FAIL" in outcomes.values() else
               "PASS" if all(v == "PASS" for v in outcomes.values()) else
               "REVIEW_REQUIRED")
    return {
        "academicQA": overall,
        "gates": outcomes,
        "findings": [
            {"gate": f.gate, "result": f.result, "evidenceKind": f.evidence_kind,
             "evidenceRef": f.evidence_ref, "detail": f.detail,
             "independentlyVerified": f.independently_verified}
            for f in findings
        ],
        "humanReviewed": False,
        "publicationAuthorized": False,
    }

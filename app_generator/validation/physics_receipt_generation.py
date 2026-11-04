"""Reproducible private source-bound exact physics witness receipts.

Supported scenarios are deliberately finite, deterministic, source-free numeric
witnesses; this never proves an entire activity's translations or visuals.
Package and original source must exactly match prior independently verified
private source packets. All report outputs remain REVIEW_REQUIRED.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.validation.physics_proofs import KNOWN_CASES, audit_proofs
from app_generator.validation.reviewer_source_packets import verified_source_packet

# Source-free finite exact-rational sample witnesses. These are mathematical
# counterexample/identity checks, NOT alleged textbook measurements.
WITNESSES: dict[str, dict[str, str]] = {
    "mcq-collision-types-concept": {"m1":"2","m2":"3","u":"5","e":"1/2"},
    "mcq-impulse-approximation-basis": {
        "f_internal":"1000","f_external":"1","duration":"1/100"},
    "mcq-perfectly-inelastic-outcome": {"m":"2","u":"4"},
    "mcq-equal-mass-elastic-transfer": {"m":"2","u":"4"},
    "mcq-newton-cradle-multi-ball": {"m":"1","u":"6"},
    "mcq-extreme-mass-heavy-target": {"m":"1","M":"100","u":"5"},
    "mcq-ballistic-pendulum-stages": {"m1":"1","m2":"9","u":"10","g":"10"},
    "mcq-spring-collision-intermediate": {"m":"2","u":"3","k":"2","x":"2"},
    "mcq-relative-velocity-scope": {"m1":"2","m2":"3","u1":"4","u2":"0"},
}


def generate_bounded_physics_receipts(
    package_file: Path, pdf: Path, source_packets_file: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build and re-audit all known physics witnesses, without publishing."""
    if (not package_file.is_file() or not pdf.is_file() or
            not source_packets_file.is_file() or
            pdf.read_bytes()[:5] != b"%PDF-"):
        raise ValueError("original private PDF, package and source packets required")
    package_raw=package_file.read_bytes()
    pkg_sha=sha256(package_raw).hexdigest()
    pdf_sha=sha256(pdf.read_bytes()).hexdigest()
    package=json.loads(package_raw)
    packets=json.loads(source_packets_file.read_text(encoding="utf-8"))
    activities=package.get("activities",[])
    if (not isinstance(activities,list) or len(activities)!=18 or
        len({x.get("id") for x in activities})!=18 or
        not isinstance(packets.get("packets"),dict) or
        len(packets["packets"])!=18 or
        packets.get("packageSha256")!=pkg_sha or
        packets.get("sourceSha256")!=pdf_sha or
        set(WITNESSES)!=set(KNOWN_CASES)):
        raise ValueError("source packets or activity identity not exact")
    by_id={a["id"]:a for a in activities}
    proofs=[]
    for activity_id, params in WITNESSES.items():
        model, expected_key=KNOWN_CASES[activity_id]
        if by_id[activity_id].get("answerKey",{}).get("correct")!=expected_key:
            raise ValueError("activity answer key differs from approved bounded proof")
        entry=packets["packets"].get(activity_id)
        if not isinstance(entry,dict):
            raise ValueError("approved activity source packet absent")
        anchors=entry.get("sourceAnchors")
        if not isinstance(anchors,list) or len(anchors)!=1:
            raise ValueError("exactly one independently verified passage required")
        fresh=verified_source_packet(pdf,pdf_sha,activity_id,anchors)
        if (fresh.get("sourceEvidence") != entry.get("sourceEvidence") or
            fresh.get("passageSha256") != entry.get("passageSha256") or
            fresh.get("verifiedPages") != entry.get("verifiedPages")):
            raise ValueError("cached source passage does not reverify independently")
        proofs.append({"activityId":activity_id,"model":model,
                       "parameters":params,"anchor":anchors[0]})
    canonical=sha256(json.dumps(package,ensure_ascii=False,sort_keys=True,
                               separators=(",",":")).encode("utf-8")).hexdigest()
    receipts={"sourceSha256":pdf_sha,"packageCanonicalSha256":canonical,
              "proofs":proofs}
    audit=audit_proofs(package,pdf,pdf_sha,receipts)
    if (audit["boundedPropositionsVerified"]!=len(WITNESSES) or
        audit["failedWitnesses"] or audit["unresolvedReceipts"] or
        audit["academicActivitiesPassed"]!=0 or
        audit["publicationAuthorized"] is not False):
        raise ValueError("one or more bounded physics witnesses failed source/identity check")
    return receipts,audit

"""Migrate earlier literal PDF anchors to a NEW exact-package private review packet.

This module proves *only* that each quotation occurs on its claimed page.
A reused anchor does not prove new activity wording/answers are correct.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any,Callable

from app_generator.validation.reviewer_source_packets import verified_source_packet
from app_generator.validation.source_passages import extract_pages

def digest(obj: Any) -> str:
    return sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False,
                             separators=(",",":")).encode("utf-8")).hexdigest()

def migrate_anchor_packets(
    *, pdf:Path, source_sha256:str, prior_package:Path,
    target_package:Path, prior_receipts:list[Path],
    extractor:Callable[[Path],tuple[str,...]]=extract_pages,
) -> dict[str,Any]:
    if not isinstance(source_sha256,str) or len(source_sha256)!=64 or any(
        ch not in "0123456789abcdef" for ch in source_sha256
    ):
        raise ValueError("invalid controlled PDF digest")
    pdf_data=pdf.read_bytes()
    if pdf_data[:5]!=b"%PDF-" or sha256(pdf_data).hexdigest()!=source_sha256:
        raise ValueError("controlled original PDF SHA256 mismatch")
    prior=json.loads(prior_package.read_text(encoding="utf-8"))
    target_raw=target_package.read_bytes()
    target=json.loads(target_raw.decode("utf-8"))
    old_acts=prior.get("activities",[])
    new_acts=target.get("activities",[])
    if not isinstance(old_acts,list) or not isinstance(new_acts,list) or not new_acts:
        raise ValueError("both source and target need nonempty activities")
    old={a["id"]:a for a in old_acts if isinstance(a,dict) and isinstance(a.get("id"),str)}
    new={a["id"]:a for a in new_acts if isinstance(a,dict) and isinstance(a.get("id"),str)}
    if (len(old)!=len(old_acts) or len(new)!=len(new_acts)
        or set(old)!=set(new)):
        raise ValueError("cross-version activity set mismatch; do not fabricate source coverage")
    if not isinstance(prior_receipts,list) or not prior_receipts:
        raise ValueError("prior anchor receipt paths required")
    anchors={}
    prior_digest=digest(prior)
    for file in prior_receipts:
        receipt=json.loads(file.read_text(encoding="utf-8"))
        if (receipt.get("sourceSha256")!=source_sha256 or
            receipt.get("packageCanonicalSha256")!=prior_digest or
            not isinstance(receipt.get("proofs"),list)):
            raise ValueError("prior proof receipt does not match original PDF/package")
        for item in receipt["proofs"]:
            if not isinstance(item,dict):
                raise ValueError("source receipt proof must be object")
            aid=item.get("activityId")
            anchor=item.get("anchor")
            if (aid not in old or aid in anchors or
                not isinstance(anchor,dict) or anchor.get("activityId")!=aid):
                raise ValueError("duplicate, unknown or mismatched source anchor")
            anchors[aid]=anchor
    if set(anchors)!=set(new):
        raise ValueError("not all target activities have independently locatable anchors")
    pages=extractor(pdf)
    if not pages:
        raise ValueError("no controlled textbook pages extracted")
    def same_pages(_:Path) -> tuple[str,...]:
        return pages
    packets={}
    changed=[]
    for aid in sorted(new):
        packet=verified_source_packet(pdf,source_sha256,aid,[anchors[aid]],
                                      extractor=same_pages)
        altered=digest(old[aid])!=digest(new[aid])
        packet["priorActivitySha256"]=digest(old[aid])
        packet["targetActivitySha256"]=digest(new[aid])
        packet["sourceLocationOnly"]=True
        packet["sourceInterpretationVerified"]=False
        packet["activityContentChangedSincePrior"]=altered
        if altered:changed.append(aid)
        packets[aid]=packet
    return {
        "sourceSha256":source_sha256,
        "priorPackageCanonicalSha256":prior_digest,
        "packageSha256":sha256(target_raw).hexdigest(),
        "targetPackageCanonicalSha256":digest(target),
        "packets":packets,
        "activityCount":len(new),
        "verifiedSourceLocations":len(packets),
        "changedActivityIds":changed,
        "sourceInterpretationVerified":False,
        "academicQA":"REVIEW_REQUIRED",
        "humanReviewRequired":False,
        "publicationAuthorized":False,
    }

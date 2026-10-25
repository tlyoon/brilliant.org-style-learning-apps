"""Trusted, versioned private PDF source packets for independent academic AI.

The passage text is emitted ONLY to the local review run, never into the
public repository or a public GitHub PR. Presence != academic correctness.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from app_generator.validation.source_passages import extract_pages, check_anchor


def verified_source_packet(
    pdf: Path,
    expected_sha256: str,
    activity_id: str,
    anchors: list[dict[str, Any]],
    *,
    extractor=extract_pages,
    max_quote_chars: int = 1400,
    max_passages: int = 4,
) -> dict[str, Any]:
    if not isinstance(activity_id,str) or not activity_id.strip():
        raise ValueError("activity must have a stable identifier")
    if not isinstance(expected_sha256,str) or len(expected_sha256)!=64 or any(
        c not in "0123456789abcdef" for c in expected_sha256
    ):
        raise ValueError("expected controlled PDF SHA-256 must be canonical")
    if not pdf.is_file() or sha256(pdf.read_bytes()).hexdigest()!=expected_sha256:
        raise ValueError("controlled original PDF does not match source hash")
    if not isinstance(anchors,list) or not (1<=len(anchors)<=max_passages):
        raise ValueError("source evidence requires bounded explicit page quotes")
    if not isinstance(max_quote_chars,int) or not 120<=max_quote_chars<=5000:
        raise ValueError("source packet excerpt bound is invalid")
    pages=extractor(pdf)
    if not pages:
        raise ValueError("controlled PDF yielded no pages")
    verified=[]
    observed=set()
    for anchor in anchors:
        if not isinstance(anchor,dict) or anchor.get("activityId")!=activity_id:
            raise ValueError("source evidence references unrelated learning activity")
        excerpt=anchor.get("quotedText")
        if not isinstance(excerpt,str) or not 40<=len(excerpt)<=max_quote_chars:
            raise ValueError("source passage absent, truncated or outside allowed bound")
        checked=check_anchor(pages,anchor)
        if checked.get("status")!="VERIFIED_TEXT_ONLY":
            raise ValueError("source passage not independently verified: "+str(checked.get("reason")))
        page=checked["pageIndex"]
        key=(page,checked["quoteSha256"])
        if key in observed:
            raise ValueError("duplicate source passage receipt")
        observed.add(key)
        verified.append({
            "page":page,
            "quote":excerpt,
            "quoteSha256":checked["quoteSha256"],
        })
    if not verified:
        raise ValueError("source evidence has no validated PDF passage")
    verified.sort(key=lambda x:(x["page"],x["quoteSha256"]))
    # Exact passage retained for private reviewer context only.
    evidence="\n\n".join(
        f"[PDF physical page {item['page']}; passage SHA256 {item['quoteSha256']}]\n{item['quote']}"
        for item in verified
    )
    if len(evidence)<40:
        raise ValueError("verified source evidence is insufficient")
    return {
        "activityId":activity_id,
        "sourceSha256":expected_sha256,
        "verifiedPages":sorted({entry["page"] for entry in verified}),
        "sourceEvidence":evidence,
        "passageCount":len(verified),
        "passageSha256":[entry["quoteSha256"] for entry in verified],
        "sourceInterpretationVerified":False,
        "humanReviewRequired":False,
    }


def source_packets_for_activities(
    pdf: Path, sha: str,
    package: dict[str,Any],
    private_anchors: list[dict[str,Any]],
    *, extractor=extract_pages,
) -> dict[str,dict[str,Any]]:
    acts=package.get("activities")
    if not isinstance(acts,list) or not acts:
        raise ValueError("nonempty installed package required")
    ids=[a.get("id") for a in acts if isinstance(a,dict)]
    if len(ids)!=len(acts) or len(ids)!=len(set(ids)):
        raise ValueError("invalid or duplicate generated activity IDs")
    if not isinstance(private_anchors,list) or any(not isinstance(a,dict) for a in private_anchors):
        raise ValueError("private anchor file must contain objects")
    if any(a.get("activityId") not in ids for a in private_anchors):
        raise ValueError("source quotes reference unknown activity")
    # Extract once, then use in every distinct packet without changing any
    # source quote. This is an optimization, not a weaker proof.
    if sha256(pdf.read_bytes()).hexdigest()!=sha:
        raise ValueError("controlled source PDF hash differs")
    pages=extractor(pdf)
    def same_pages(_:Path) -> tuple[str,...]:
        return pages
    return {
        id_:verified_source_packet(
            pdf,sha,id_,[a for a in private_anchors if a["activityId"]==id_],
            extractor=same_pages,
        )
        for id_ in ids
    }

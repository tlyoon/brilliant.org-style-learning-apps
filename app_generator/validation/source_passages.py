"""Hash-bound, page-specific textbook passage evidence; no automatic semantics PASS.

Literal source text presence is independent of Gemini, but does NOT establish
that a mathematical conclusion or translation is correct.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import unicodedata
from pathlib import Path
from typing import Any


def _normalized(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip().casefold()


def extract_pages(source_pdf: Path, *, tool: str = "pdftotext") -> tuple[str, ...]:
    if not source_pdf.is_file() or source_pdf.stat().st_size > 50_000_000:
        raise ValueError("private source PDF missing or unexpectedly large")
    with source_pdf.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise ValueError("controlled source is not a PDF")
    run = subprocess.run(
        [tool, "-layout", "-enc", "UTF-8", str(source_pdf), "-"],
        capture_output=True, timeout=90, check=False,
    )
    if run.returncode != 0:
        raise ValueError("source PDF text extraction failed")
    pages = tuple(part for part in run.stdout.decode("utf-8", errors="replace").split("\f") if part.strip())
    if not pages:
        raise ValueError("controlled PDF yielded no usable text")
    return pages


def check_anchor(pages: tuple[str, ...], anchor: dict[str, Any]) -> dict[str, Any]:
    """Check exact passage text on a PDF page; report no raw textbook excerpt."""
    claim = anchor.get("activityId")
    index = anchor.get("pageIndex")
    excerpt = anchor.get("quotedText")
    if (
        not isinstance(claim, str) or not claim
        or type(index) is not int or not 1 <= index <= len(pages)
        or not isinstance(excerpt, str)
    ):
        return {"activityId": claim, "status": "REVIEW_REQUIRED", "reason": "invalid or unlocated source anchor"}
    normalized = _normalized(excerpt)
    if len(normalized) < 40 or len(normalized.split()) < 7:
        return {"activityId": claim, "status": "REVIEW_REQUIRED", "reason": "short or nonspecific textbook quotation"}
    if "\ufffd" in normalized:
        return {"activityId": claim, "status": "REVIEW_REQUIRED", "reason": "source quotation has corrupt extraction characters"}
    pages_containing = [i + 1 for i, page in enumerate(pages) if normalized in _normalized(page)]
    if not pages_containing:
        # PDF text extraction is not lossless (especially equations/figures).
        # Unlocated text is not independent proof that the PDF lacks it.
        return {"activityId": claim, "status": "REVIEW_REQUIRED",
                "reason": "passage not located in extracted PDF text; inspect source page"}
    if len(pages_containing) != 1:
        return {"activityId": claim, "status": "REVIEW_REQUIRED", "reason": "quotation appears on multiple PDF pages"}
    if pages_containing != [index]:
        return {"activityId": claim, "status": "FAIL", "reason": "quoted source passage is assigned to wrong PDF page"}
    return {
        "activityId": claim, "pageIndex": index,
        "status": "VERIFIED_TEXT_ONLY",
        "quoteSha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "reason": "literal extracted passage located; scientific interpretation and translation unverified",
    }


def audit_source_anchors(
    package: dict[str, Any], pdf: Path, expected_sha256: str,
    anchors: list[dict[str, Any]], *, tool: str = "pdftotext",
) -> dict[str, Any]:
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    if digest != expected_sha256:
        raise ValueError("controlled source PDF bytes differ from expected manifest SHA-256")
    pages = extract_pages(pdf, tool=tool)
    activity_ids = [item.get("id") for item in package.get("activities", [])]
    if not activity_ids or len(activity_ids) != len(set(activity_ids)):
        raise ValueError("package has missing or duplicated activity IDs")
    if any(not isinstance(item, dict) for item in anchors):
        raise ValueError("anchor evidence must be a list of objects")
    if len(anchors) != len({item.get("activityId") for item in anchors}):
        raise ValueError("duplicate anchor receipt: ambiguous or conflicting claims")
    if any(item.get("activityId") not in activity_ids for item in anchors):
        raise ValueError("anchor references an unknown learning activity")
    lookup = {item["activityId"]: item for item in anchors}
    results = [
        check_anchor(pages, lookup[id_]) if id_ in lookup
        else {"activityId": id_, "status": "REVIEW_REQUIRED", "reason": "no source-specific passage evidence"}
        for id_ in activity_ids
    ]
    return {
        "pdfSha256": digest,
        "pdfPages": len(pages),
        "activityCount": len(activity_ids),
        "passageLocationVerified": sum(x["status"] == "VERIFIED_TEXT_ONLY" for x in results),
        "pending": sum(x["status"] == "REVIEW_REQUIRED" for x in results),
        "fail": sum(x["status"] == "FAIL" for x in results),
        "sourceMeaningVerified": False,
        "academicQAPass": False,
        "publicationAuthorized": False,
        "results": results,
    }

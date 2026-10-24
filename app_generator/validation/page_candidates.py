"""Provider-free private PDF page retrieval for human/independent verifier triage.

BM25 lexical overlap is a suggested reading order, not scientific evidence.
Never expose raw copyrighted PDF passages in a report or let a retrieval
score yield an academic PASS.
"""
from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

from app_generator.validation.source_passages import extract_pages

STOP = frozenset("""
the and for are was were with from into upon during what which when where why how
that this these those their there about would could should have has had does did
who whose will shall then than also only both either all any some each one two
three four between through along after before under over above below much many
other same different given consider identify correctly statement describes
particles particle collision collisions one dimensional dimension isolated
system systems initial final scenario object objects correct represents
""".split())
TOKEN = re.compile(r"[a-z]{3,}")


def words(text: str) -> list[str]:
    value = unicodedata.normalize("NFKC", text).casefold()
    return [m for m in TOKEN.findall(value) if m not in STOP]


def propose_pages(pages: tuple[str, ...], activity: dict[str, Any], limit: int = 3) -> dict[str, Any]:
    prompt = activity.get("prompt", {})
    query = prompt.get("en", "") if isinstance(prompt, dict) else ""
    query_words = set(words(query))
    result: dict[str, Any] = {
        "activityId": activity.get("id"),
        "status": "REVIEW_REQUIRED",
        "sourceInterpretationVerified": False,
        "pageCandidates": [],
    }
    if len(query_words) < 3:
        result["reason"] = "insufficient English physics query terms"
        return result
    token_counts = [Counter(words(page)) for page in pages]
    page_lengths = [sum(c.values()) for c in token_counts]
    avg_len = sum(page_lengths)/len(page_lengths) if page_lengths else 0
    if not avg_len:
        result["reason"] = "no usable private PDF text"
        return result
    doc_freq = Counter(token for counts in token_counts for token in counts)
    scored = []
    for i, (counts, length) in enumerate(zip(token_counts, page_lengths), start=1):
        common = query_words.intersection(counts)
        if len(common) < 2:
            continue
        bm25 = 0.0
        for token in common:
            frequency = counts[token]
            idf = math.log(1 + (len(pages) - doc_freq[token] + 0.5) / (doc_freq[token] + 0.5))
            bm25 += idf * (frequency * 2.2)/(frequency + 1.2*(0.25+0.75*length/avg_len))
        scored.append({
            "pageIndex": i,
            "lexicalScore": round(bm25, 4),
            "sharedTokens": len(common),
            "queryTokens": len(query_words),
            "coverage": round(len(common)/len(query_words), 3),
        })
    scored.sort(key=lambda item: (-item["lexicalScore"], item["pageIndex"]))
    result["pageCandidates"] = scored[:limit]
    result["reason"] = (
        "lexical reading suggestions only; not evidence of physics correctness"
        if scored else "no page with sufficient lexical overlap"
    )
    return result


def audit_page_candidates(
    package: dict[str, Any], pdf: Path, expected_sha256: str, *, tool: str = "pdftotext"
) -> dict[str, Any]:
    actual = hashlib.sha256(pdf.read_bytes()).hexdigest()
    if actual != expected_sha256:
        raise ValueError("source PDF SHA mismatch; stop retrieval")
    pages = extract_pages(pdf, tool=tool)
    activities = package.get("activities")
    if not isinstance(activities, list) or not activities:
        raise ValueError("missing learning activities")
    results = [propose_pages(pages, a) for a in activities]
    return {
        "controlledPdfSha256": actual,
        "pageCount": len(pages),
        "activitiesExamined": len(results),
        "activitiesWithSuggestions": sum(bool(a["pageCandidates"]) for a in results),
        "academicallyVerified": 0,
        "academicStatus": "REVIEW_REQUIRED",
        "publicationAuthorized": False,
        "results": results,
    }

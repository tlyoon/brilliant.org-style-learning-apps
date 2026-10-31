"""Exact-source, narrow Chinese numeric-notation reconciliation.

Reconciles Arabic numeral token multisets only, after tightly scoped
literal notational substitutions. Never certifies translation meaning,
physics accuracy, accessibility, figure semantics, or academic PASS.
Returns metadata only, never original textbook or localized source text.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any
import unicodedata

from app_generator.validation.multilingual_numeric_triage import (
    _triplets, _notation_candidate, numeric_tokens,
    audit_source_bound_multilingual_numeric_triage,
)

_ONE = re.compile(r"(?<![0-9A-Za-z])1\s*-?\s*[dD]\b")
_TWO = re.compile(r"(?<![0-9A-Za-z])2\s*-?\s*[dD]\b")
# Only explicit equivalents of the 1D physics dimension term. This does
# not establish complete translated sentence meaning or textbook accuracy.
_EN_ONE_WORD = re.compile(r"\bone[\s-]+dimensional\b", re.IGNORECASE)
_MS_ONE_WORD = re.compile(r"\bsatu\s+dimensi\b", re.IGNORECASE)
_MIXED_DIMENSION_RULE = "EXACT_MIXED_WRITTEN_ONE_DIMENSION_NOTATION"


def _normalize_only_warranted_zh(texts: dict[str, str]) -> tuple[str, str]:
    """Return reason and rewritten ZH, with no broad Chinese numeral parsing."""
    normalized = {
        lang: unicodedata.normalize("NFKC", texts[lang])
        for lang in ("en", "ms", "zh")
    }
    counters = {lang: Counter(numeric_tokens(normalized[lang]))
                for lang in normalized}
    candidate = _notation_candidate(texts, counters)
    en, ms, zh = normalized["en"], normalized["ms"], normalized["zh"]
    if candidate == "POSSIBLE_ONE_DIMENSION_NOTATION":
        missing = counters["en"] - counters["zh"]
        count = missing.get("1", 0)
        if (count > 0 and len(missing) == 1 and
                len(_ONE.findall(en)) == count and zh.count("\u4e00\u7ef4") == count):
            return ("EXACT_DIMENSION_1_NUMERIC_NORMALIZATION",
                    zh.replace("\u4e00\u7ef4", "1D", count))
        # A single field may spell the *second* 1D reference out:
        # EN "one-dimensional", MS "satu dimensi", ZH written "one dimension".
        # Do not reconcile unless BOTH alphabetic-language counts and the
        # exact full Chinese written-dimension occurrence count agree.
        spelled_en = len(_EN_ONE_WORD.findall(en))
        spelled_ms = len(_MS_ONE_WORD.findall(ms))
        if (count > 0 and len(missing) == 1 and
                len(_ONE.findall(en)) == count and
                len(_ONE.findall(ms)) == count and
                spelled_en > 0 and spelled_en == spelled_ms and
                zh.count("\u4e00\u7ef4") == count + spelled_en):
            return (_MIXED_DIMENSION_RULE,
                    zh.replace("\u4e00\u7ef4", "1D", count + spelled_en))
    elif candidate == "POSSIBLE_TWO_DIMENSION_NOTATION":
        missing = counters["en"] - counters["zh"]
        count = missing.get("2", 0)
        if (count > 0 and len(missing) == 1 and
                len(_TWO.findall(en)) == count and zh.count("\u4e8c\u7ef4") == count):
            return ("EXACT_DIMENSION_2_NUMERIC_NORMALIZATION",
                    zh.replace("\u4e8c\u7ef4", "2D", count))
    elif candidate == "POSSIBLE_WRITTEN_ZERO_NOTATION":
        missing = counters["en"] - counters["zh"]
        if (missing == Counter({"0": 1}) and
                zh.count("\u96f6") == 1 and "\u52a8\u91cf" in zh and
                "momentum" in en.casefold()):
            return ("EXACT_MOMENTUM_ZERO_NUMERIC_NORMALIZATION",
                    zh.replace("\u96f6", "0", 1))
    return ("NOTATION_NOT_STRICTLY_RESOLVED", zh)


def audit_private_narrow_numeric_notation(
    *, package_file: Path, source_pdf: Path, source_packets_file: Path,
) -> dict[str, Any]:
    """Independently re-verify all 18 original source packets before audit."""
    triage = audit_source_bound_multilingual_numeric_triage(
        package_file=package_file,
        source_pdf=source_pdf,
        source_packets_file=source_packets_file,
    )
    data = package_file.read_bytes()
    package = json.loads(data.decode("utf-8"))
    if (sha256(data).hexdigest() != triage["packageSha256"] or
            triage["sourceVerifiedActivities"] != 18 or
            triage["publicationAuthorized"] is not False or
            triage["academicPASS"] != 0):
        raise ValueError("exact private source-bound triage no longer verifiable")
    activities = package["activities"]
    triage_rows = {row["activityId"]: row for row in triage["activities"]}
    if len(triage_rows) != 18 or len(activities) != 18:
        raise ValueError("source-bound triage activity roster incomplete")
    rows: list[dict[str, Any]] = []
    for activity in activities:
        aid = activity["id"]
        flags = triage_rows[aid]["numericTokenDriftFlags"]
        source_fields = dict(_triplets(activity))
        if len(source_fields) != triage_rows[aid]["localizedFieldsChecked"]:
            raise ValueError("localized field roster drifted during audit")
        for flag in flags:
            field = flag["field"]
            if field not in source_fields:
                raise ValueError("flagged localized field is absent")
            triplet = source_fields[field]
            before = {lang: Counter(numeric_tokens(triplet[lang]))
                      for lang in ("en", "ms", "zh")}
            if not (before["en"] != before["zh"] or
                    before["en"] != before["ms"]):
                raise ValueError("numeric drift flag not reproduced")
            if _notation_candidate(triplet, before) != flag["candidateReason"]:
                raise ValueError("narrow notation classification has drifted")
            reason, rewritten = _normalize_only_warranted_zh(triplet)
            after_zh = Counter(numeric_tokens(rewritten))
            if reason == _MIXED_DIMENSION_RULE:
                # Compare the TWO notation representations only after
                # rewriting literal 1D words in EN and MS, not by changing
                # any user-facing text. Other numerical tokens must match.
                en_effective = _EN_ONE_WORD.sub(
                    "1D", unicodedata.normalize("NFKC", triplet["en"]))
                ms_effective = _MS_ONE_WORD.sub(
                    "1D", unicodedata.normalize("NFKC", triplet["ms"]))
                en_numeric = Counter(numeric_tokens(en_effective))
                ms_numeric = Counter(numeric_tokens(ms_effective))
            else:
                en_numeric, ms_numeric = before["en"], before["ms"]
            match = (reason != "NOTATION_NOT_STRICTLY_RESOLVED" and
                     en_numeric == ms_numeric == after_zh)
            rows.append({
                "activityId": aid, "field": field,
                "originalCandidateReason": flag["candidateReason"],
                "normalizationRule": reason,
                "narrowNumericNotationMatched": match,
                "wholeTranslationMeaningVerified": False,
                "physicsMeaningVerified": False,
                "academicQA": "REVIEW_REQUIRED",
            })
    if len(rows) != triage["numericDriftFlagCount"]:
        raise ValueError("numeric drift row count changed in source-bound audit")
    return {
        "status": "SOURCE_BOUND_NARROW_NUMERIC_NOTATION_AUDIT_ONLY",
        "sourceSha256": triage["sourceSha256"],
        "packageSha256": triage["packageSha256"],
        "sourceVerifiedActivities": 18,
        "totalLocalizedFieldsChecked": triage["localizedFieldsChecked"],
        "originalNumericDriftFlags": len(rows),
        "narrowNumericNotationMatches": sum(x["narrowNumericNotationMatched"] for x in rows),
        "remainingUnresolvedNumericFlags": sum(not x["narrowNumericNotationMatched"] for x in rows),
        "numericNotationMatchProvesTranslation": False,
        "wholeTranslationMeaningVerified": False,
        "physicsMeaningVerified": False,
        "academicQA": "REVIEW_REQUIRED",
        "academicPASS": 0, "publicationAuthorized": False,
        "flags": rows,
    }

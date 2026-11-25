"""Source-free Unicode script contamination preflight for BOSLA V3.

This is a lexical integrity check only. It does not replace the two Gemini
reviewers, validate translation meaning, or grant publication rights.

Return source-free findings (path and codepoint only), not private prompt text.
Runs on exact frozen package bytes BEFORE any newly eligible paid reviewer.
"""
from __future__ import annotations

import unicodedata
from typing import Any

MAX_FINDINGS = 64

# Scripts unlikely to be intentional in the EN/MS/ZH learner content.
# Greek letters and mathematical symbols are deliberately not banned.
_DISALLOWED_ALL = (
    "THAI", "ARABIC", "CYRILLIC", "HEBREW", "DEVANAGARI",
    "HANGUL", "BENGALI", "TAMIL", "TELUGU",
)
_DISALLOWED_LATIN = ("CJK UNIFIED IDEOGRAPH", "CJK COMPATIBILITY IDEOGRAPH",
                      "HIRAGANA", "KATAKANA", "BOPOMOFO")


def script_findings(package: dict[str, Any]) -> list[dict[str, str]]:
    """Find unexpected foreign-script glyphs in tagged activity localizations.

    We never scan the source manifest, citations, provenance, or text from
    untrusted model responses. The primary failure being detected is Thai
    codepoints inserted mid-word in a Malay question, as in BSA-173.
    """
    if not isinstance(package, dict) or not isinstance(package.get("activities"), list):
        raise ValueError("V3_SCRIPT_INVALID_PACKAGE")
    findings: list[dict[str, str]] = []
    for index, activity in enumerate(package["activities"]):
        if not isinstance(activity, dict) or not isinstance(activity.get("id"), str):
            raise ValueError("V3_SCRIPT_INVALID_ACTIVITY")
        def scan(value: Any, path: str):
            if isinstance(value, dict):
                for key, item in value.items():
                    if key in ("en", "ms", "zh") and isinstance(item, str):
                        for char in item:
                            name = unicodedata.name(char, "")
                            reject = (
                                char == "\ufffd" or
                                any(x in name for x in _DISALLOWED_ALL) or
                                (key in ("en", "ms") and
                                 any(x in name for x in _DISALLOWED_LATIN))
                            )
                            if reject:
                                findings.append({
                                    "activityId": activity["id"],
                                    "path": f"activities[{index}].{path}.{key}",
                                    "codepoint": f"U+{ord(char):04X}",
                                    "scriptName": (
                                        "REPLACEMENT_CHARACTER" if char == "\ufffd"
                                        else next((s for s in _DISALLOWED_ALL +
                                                   _DISALLOWED_LATIN if s in name),
                                                  "OTHER")),
                                })
                                if len(findings) > MAX_FINDINGS:
                                    raise ValueError("V3_SCRIPT_EXCESSIVE_CORRUPTION")
                    elif isinstance(item, (dict, list)):
                        scan(item, f"{path}.{key}" if path else key)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, (dict, list)):
                        scan(item, f"{path}[{i}]")
        scan(activity, "")
    return findings

"""Strict extraction of machine-readable Gemini responses."""

from __future__ import annotations

import json
from typing import Any

from app_generator.errors import ResponseContractError

BEGIN = "BEGIN_JSON"
END = "END_JSON"


def _reject_surrogates(value: Any, path: str = "response") -> None:
    if isinstance(value, str) and any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise ResponseContractError(f"Malformed Unicode surrogate in {path}")
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_surrogates(item, f"{path}[{index}]")
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_surrogates(item, f"{path}.{key}")


def parse_json_response(raw: str) -> Any:
    text = raw.strip().lstrip("\ufeff")
    if not text:
        raise ResponseContractError("Gemini returned an empty response")
    if BEGIN in text or END in text:
        if text.count(BEGIN) != 1 or text.count(END) != 1:
            raise ResponseContractError("Response contains duplicate or incomplete JSON sentinels")
        prefix, remainder = text.split(BEGIN, 1)
        payload, suffix = remainder.split(END, 1)
        if prefix.strip() or suffix.strip():
            raise ResponseContractError("Response contains prose outside the JSON sentinels")
        text = payload.strip()
    elif text.startswith("```"):
        lines = text.splitlines()
        if len(lines) < 3 or not lines[-1].strip().startswith("```"):
            raise ResponseContractError("Response contains an incomplete Markdown fence")
        if lines[-1].strip() != "```":
            raise ResponseContractError("Unexpected content after the closing Markdown fence")
        text = "\n".join(lines[1:-1]).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ResponseContractError(f"Response is not complete valid JSON: {exc}") from exc
    _reject_surrogates(parsed)
    return parsed

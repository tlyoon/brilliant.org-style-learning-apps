"""Bounded Gemini API-key selection, without transporting source PDFs or secrets.

On Windows, discover numbered Gemini credentials from
%LOCALAPPDATA%/Microvid/.env. The file is read locally without command
evaluation, and keys are never logged or serialized. Capacity errors 503/504
may advance a source-free probe to the next distinct candidate; auth, quota,
unknown and transport errors never cause account-hopping.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping, TypeVar

from app_generator.errors import AuthenticationRequired, GeminiApiError, TransientGeminiError

_MAX_KEYS = 8
_NUMBERED = re.compile(r"GEMINI_API_KEY_([1-9][0-9]*)\Z")
_ALLOWED = {"GEMINI_API_KEY", "GOOGLE_API_KEY"}
T = TypeVar("T")


@dataclass(frozen=True)
class ApiKeyCandidate:
    label: str
    secret: str = field(repr=False)


def _dotenv_values(path: Path) -> dict[str, str]:
    """Read only supported simple dotenv assignments; never execute or expand."""
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except FileNotFoundError:
        return {}
    except (OSError, UnicodeError):
        # A malformed/inaccessible optional file must not change auth policy.
        return {}

    values: dict[str, str] = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        if name not in _ALLOWED and not _NUMBERED.fullmatch(name):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] in {'"', "'"} and value[-1] == value[0]:
            value = value[1:-1]
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        if value:
            values[name] = value
    return values


def find_gemini_keys(
    *,
    environ: Mapping[str, str] | None = None,
    dotenv_path: Path | None = None,
) -> tuple[ApiKeyCandidate, ...]:
    """Prioritize explicit process credentials, then numbered keys, then default.

    Never searches outside the Windows LocalAppData/Microvid default folder
    unless a path is explicitly injected by a unit test. Duplicate values are
    tested only once; the result carries only a non-secret variable label.
    """
    env = os.environ if environ is None else environ
    raw: list[tuple[str, str]] = [
        ("GOOGLE_API_KEY (environment)", env.get("GOOGLE_API_KEY", "")),
        ("GEMINI_API_KEY (environment)", env.get("GEMINI_API_KEY", "")),
    ]
    if dotenv_path is None:
        local = env.get("LOCALAPPDATA", "").strip()
        dotenv_path = Path(local) / "Microvid" / ".env" if local else None

    if dotenv_path is not None:
        values = _dotenv_values(dotenv_path)
        numbered = sorted(
            (name for name in values if _NUMBERED.fullmatch(name)),
            key=lambda name: int(_NUMBERED.fullmatch(name).group(1)),
        )
        raw.extend((name, values[name]) for name in numbered)
        raw.extend((name, values[name]) for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY") if name in values)

    results: list[ApiKeyCandidate] = []
    seen: set[str] = set()
    for name, secret in raw:
        if secret and secret not in seen:
            seen.add(secret)
            results.append(ApiKeyCandidate(label=name, secret=secret))
            if len(results) == _MAX_KEYS:
                break
    return tuple(results)


def error_status(exc: BaseException) -> int | None:
    for attr in ("status_code", "code"):
        value = getattr(exc, attr, None)
        if callable(value):
            try:
                value = value()
            except Exception:
                continue
        try:
            return int(value)
        except (ValueError, TypeError):
            pass
    return None


def select_healthy_key(
    candidates: tuple[ApiKeyCandidate, ...],
    probe: Callable[[ApiKeyCandidate], T],
) -> tuple[ApiKeyCandidate, T]:
    """Probe one key at a time; advance *only* on explicit 503/504 responses.

    A probe must be source-free. No PDF stage or other non-idempotent payload
    may be retried by this function.
    """
    if not candidates:
        raise AuthenticationRequired("No Gemini API keys were found")
    for candidate in candidates:
        try:
            outcome = probe(candidate)
            return candidate, outcome
        except Exception as exc:
            status = error_status(exc)
            if status in {503, 504}:
                continue
            if status in {401, 403}:
                raise AuthenticationRequired(
                    f"Gemini API key {candidate.label} was denied (HTTP {status}); rotation stopped"
                ) from exc
            if status == 429:
                raise TransientGeminiError(
                    "Gemini quota/rate limit (HTTP 429); key rotation prohibited"
                ) from exc
            raise GeminiApiError(
                f"Gemini API key preflight stopped ({type(exc).__name__}); "
                "no source request was sent"
            ) from exc
    raise TransientGeminiError(
        "All available Gemini API keys returned 503/504 during source-free preflight; "
        "no PDF generation request was sent"
    )


def build_keyed_gemini_client(
    genai: object, types: object, config: object, *, probe_keys: bool = False
) -> object | None:
    """Build one SDK client, probing numbered keys without attaching any PDF.

    Doctor calls without probes. Actual generation preparation probes up to the
    configured bounded key pool if multiple distinct keys exist.
    """
    import logging

    candidates = find_gemini_keys()
    if not candidates:
        return None

    def make_client(candidate: ApiKeyCandidate) -> object:
        return genai.Client(
            api_key=candidate.secret,
            http_options=types.HttpOptions(
                timeout=config.gemini_api_timeout_seconds * 1000,
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        )

    if not probe_keys or len(candidates) == 1:
        return make_client(candidates[0])

    def check(candidate: ApiKeyCandidate) -> object:
        client = make_client(candidate)
        try:
            response = client.models.generate_content(
                model=config.gemini_api_model,
                contents="Reply with exactly the word READY.",
                config=types.GenerateContentConfig(
                    temperature=0,
                    max_output_tokens=128,
                ),
            )
            if not str(getattr(response, "text", "") or "").strip():
                raise GeminiApiError("Source-free Gemini preflight returned empty text")
            return client
        except BaseException:
            client.close()
            raise

    selected, client = select_healthy_key(candidates, check)
    logging.getLogger(__name__).info(
        "Gemini source-free preflight selected credential label %s", selected.label
    )
    return client

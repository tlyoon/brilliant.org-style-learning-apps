"""Bounded Gemini API-key selection, without transporting source PDFs or secrets.

On Windows, discover numbered Gemini credentials from
%LOCALAPPDATA%/Microvid/.env. The file is read locally without command
evaluation, and keys are never logged or serialized. Explicit key/project access and billing errors (401/402/403) or capacity errors
(503/504) may advance a source-free probe to the next distinct candidate.
Quota 429, malformed requests, unknown and transport errors stop immediately.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping, TypeVar

from app_generator.errors import (
    AuthenticationRequired, ExternalExecutionDenied, GeminiApiError,
    TransientGeminiError,
)

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
    """Try each distinct credential once using a source-free provider probe.

    Only HTTP 401/402/403 (key/project authorization or billing) and 503/504
    (temporary provider capacity) can select a *different* configured key.
    Provider quota 429, bad requests, and ambiguous/unknown transport outcomes
    stop immediately. Never call this with a PDF or other submitted job.
    """
    if not candidates:
        raise AuthenticationRequired("No Gemini API keys were found")
    failures: list[int] = []
    for candidate in candidates:
        try:
            return candidate, probe(candidate)
        except ExternalExecutionDenied:
            # A host/connector refusal is NOT a provider HTTP 403 even if an
            # upstream wrapper attaches status_code=403. The denied operation
            # remains terminal: do not rotate keys or reroute execution.
            raise
        except Exception as exc:
            status = error_status(exc)
            if status in {401, 402, 403, 503, 504}:
                # Only log the configured variable label and numeric status,
                # never the key value or potentially sensitive error text.
                import logging
                logging.getLogger(__name__).info(
                    "Gemini source-free preflight candidate %s returned HTTP %d; "
                    "trying next distinct credential", candidate.label, status,
                )
                failures.append(status)
                continue
            if status == 429:
                raise TransientGeminiError(
                    "Gemini quota/rate limit (HTTP 429); key rotation prohibited"
                ) from exc
            raise GeminiApiError(
                f"Gemini API key preflight stopped ({type(exc).__name__}); "
                "no source request was sent"
            ) from exc

    # This is a terminal source-free result, not permission to replay a
    # source-bearing call. Status codes are safe to report; secrets are not.
    if 402 in failures:
        raise GeminiApiError(
            "No usable Gemini API key; HTTP 402 billing/payment restriction "
            "was reported for at least one candidate. Check project/model "
            "billing configuration. No PDF generation request was sent"
        )
    if any(code in {401, 403} for code in failures):
        raise AuthenticationRequired(
            "No usable Gemini API key; one or more configured credentials "
            "returned HTTP 401/403 and the remaining candidates failed "
            "source-free preflight. No PDF generation request was sent"
        )
    raise TransientGeminiError(
        "All available Gemini API keys returned 503/504 during source-free "
        "preflight; no PDF generation request was sent"
    )


def build_keyed_gemini_client(
    genai: object, types: object, config: object, *, probe_keys: bool = True
) -> object | None:
    """Build one SDK client, probing numbered keys without attaching any PDF.

    Every normal call probes the configured bounded key pool without source
    attachment. Only explicit non-generating checks (doctor) may set
    probe_keys=False; callers that send source must use the safe default.
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

    if not probe_keys:
        return make_client(candidates[0])

    def check(candidate: ApiKeyCandidate) -> object:
        client = make_client(candidate)
        try:
            response = client.models.generate_content(
                model=config.gemini_api_model,
                contents="Reply with exactly the word READY.",
                config=types.GenerateContentConfig(
                    # Gemini 3.8 Flash no longer accepts legacy sampling
                    # controls; output budget includes reasoning tokens.
                    max_output_tokens=512,
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

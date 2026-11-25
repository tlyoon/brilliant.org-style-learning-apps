"""Shared source-free failure classification for independent model reviewers.

This policy is used by legacy academic review and current V3 generated-text
review. It never grants browser ownership, model access or execution rights.
"""
from __future__ import annotations

from app_generator.errors import (
    ResponseContractError, TransientGeminiError, UiContractError,
)

# Two genuinely uncaptured UI/transport attempts open the circuit for a role.
# A model's captured but invalid JSON is not a transport availability failure.
UNCAPTURED_ROLE_CIRCUIT_THRESHOLD = 2
# Shared capability-wide failures: do not send a second reviewer request
# for the same activity once one of these errors has interrupted Google.
SERVER_CAPACITY_ERROR_NAMES = frozenset({
    "ServerError", "ServiceUnavailable", "TransientGeminiError",
})
_UNCAPTURED_ERRORS = (
    UiContractError, ResponseContractError, TransientGeminiError,
    TimeoutError, ConnectionError,
)
UNCAPTURED_TRANSPORT_ERROR_CODES = frozenset(cls.__name__
                                              for cls in _UNCAPTURED_ERRORS)


def sanitized_provider_failure_metadata(exc: BaseException) -> dict:
    """Keep ONLY numeric HTTP status and canonical cause, never response text.

    google-genai ClientError may mean 400, 401, 403, 404, 429 or another
    provider rejection. Saving its bare class name alone loses the facts
    needed to stop safely and diagnose whether the problem is quota, auth,
    invalid input, or service capacity. Older uncaptured claims are NEVER
    retroactively reclassified or replayed by this helper.
    """
    if type(exc).__name__ not in {
        "ClientError", "ServerError", "APIError",
        "GeminiApiError", "TransientGeminiError",
    }:
        return {}
    from app_generator.llm.gemini_key_failover import error_status
    from app_generator.runtime.v3_gemini_diagnostics import classify_google_failure
    code = error_status(exc)
    if type(code) is not int or not 400 <= code <= 599:
        return {"providerFailureClass": "UNCLASSIFIED_PROVIDER_ERROR"}
    return {
        "providerHttpStatus": code,
        "providerFailureClass": classify_google_failure(code, type(exc).__name__),
    }


def is_uncaptured_reviewer_transport_error(exc: BaseException) -> bool:
    """Only count failures before a usable answer was returned by ask()."""
    return isinstance(exc, _UNCAPTURED_ERRORS)

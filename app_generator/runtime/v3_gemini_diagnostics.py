"""Bounded source-free Gemini SDK diagnosis for BOSLA Yoga 6.

Uses models.get (a metadata GET), NOT generate_content. The result confirms
only metadata authorization/reachability; it cannot prove model capacity for
a generation request. No source PDFs, activity JSON or prompt contents,
secrets, error response bodies, or raw exception text enter the report.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Callable

from app_generator.llm.gemini_api import build_v3_native_text_sdk_components
from app_generator.llm.gemini_key_failover import (
    error_status, find_gemini_keys,
)

MAX_CANDIDATES = 2
METADATA_TIMEOUT_SECONDS = 15


def classify_google_failure(http_status: int | None, exception_name: str) -> str:
    if http_status in (401, 403):
        return "AUTH_OR_PROJECT_DENIED"
    if http_status == 402:
        return "BILLING_RESTRICTED"
    if http_status == 404:
        return "MODEL_NOT_FOUND"
    if http_status == 429:
        return "QUOTA_OR_RATE_LIMIT"
    if http_status in (500, 502, 503, 504, 529):
        return "PROVIDER_CAPACITY"
    if http_status in (400, 422):
        return "INVALID_MODEL_REQUEST"
    if http_status in (408, 409) or exception_name in (
        "TimeoutError", "ConnectError", "ReadTimeout", "ConnectionError",
    ):
        return "TRANSPORT_UNCERTAIN"
    return "UNCLASSIFIED_PROVIDER_ERROR"


def diagnose_model_metadata(
    config: Any, *,
    preferred_offset: int = 0,
    max_candidates: int = MAX_CANDIDATES,
    make_sdk_components: Callable[..., tuple] = build_v3_native_text_sdk_components,
    count_credentials: Callable[[], tuple] = find_gemini_keys,
) -> dict:
    """Inspect at most two preconfigured keys without a model-generation call.

    On 429, unknown transport or an explicit external denial, stop immediately.
    SDK metadata requests are bounded to 15s each and have zero SDK retries.
    The selected index applies only to a NEW, still-unsubmitted activity.
    """
    if (type(preferred_offset) is not int or preferred_offset < 0 or
        type(max_candidates) is not int or not 1 <= max_candidates <= 2):
        raise ValueError("V3_INVALID_SOURCE_FREE_DIAGNOSTIC_BUDGET")
    candidates = count_credentials()
    count = min(len(candidates), max_candidates)
    if not count:
        return {"status": "STOP_NO_GEMINI_CREDENTIAL", "attempts": [],
                "selectedCandidateIndex": None, "sourceFree": True}
    model = getattr(config, "gemini_api_model", None)
    if not isinstance(model, str) or not model.startswith("gemini-"):
        raise ValueError("V3_INVALID_DIAGNOSTIC_MODEL")
    attempts: list[dict] = []
    short_config = SimpleNamespace(
        gemini_api_model=model,
        gemini_api_timeout_seconds=METADATA_TIMEOUT_SECONDS,
    )
    for step in range(count):
        index = (preferred_offset + step) % len(candidates)
        client = None
        try:
            create, _ = make_sdk_components(
                short_config, candidate_offset=index)
            client = create("physics")
            # The only provider operation: a source-free metadata GET.
            response = client.models.get(model=model)
            if response is None:
                raise ValueError("V3_EMPTY_PROVIDER_MODEL_METADATA")
            attempts.append({"candidateIndex": index, "httpStatus": 200,
                             "classification": "MODEL_METADATA_ACCESSIBLE"})
            return {"status": "READY_SOURCE_FREE_ONLY",
                    "sourceFree": True, "attempts": attempts,
                    "selectedCandidateIndex": index}
        except Exception as exc:
            # A denied host/platform operation is terminal, NOT a Google 403.
            from app_generator.errors import ExternalExecutionDenied
            if isinstance(exc, ExternalExecutionDenied):
                raise
            code = error_status(exc)
            kind = classify_google_failure(code, type(exc).__name__)
            attempts.append({"candidateIndex": index, "httpStatus": code,
                             "classification": kind,
                             "errorClass": type(exc).__name__})
            if kind in ("QUOTA_OR_RATE_LIMIT", "TRANSPORT_UNCERTAIN",
                        "UNCLASSIFIED_PROVIDER_ERROR",
                        "INVALID_MODEL_REQUEST"):
                return {"status": "STOP_"+kind, "sourceFree": True,
                        "attempts": attempts, "selectedCandidateIndex": None}
        finally:
            if client is not None:
                closer = getattr(client, "close", None)
                if callable(closer):
                    closer()
    return {"status": "STOP_METADATA_NOT_AVAILABLE", "sourceFree": True,
            "attempts": attempts, "selectedCandidateIndex": None}

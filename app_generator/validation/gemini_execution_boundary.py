"""Fail-closed boundary classifier for Gemini tool denials and provider errors.

This module does not run tools, read credentials, authorize an operation or
probe the network. It accepts only *structured* nonsecret observations. The
origin of a failure must be supplied by the trusted executor; raw exception
text, an HTTP-like code on a tool denial, or operator speculation cannot prove
that a Gemini provider request was sent.
"""
from __future__ import annotations

from typing import Any

ORIGINS = frozenset(("HOST_OR_CONNECTOR", "GEMINI_PROVIDER", "LOCAL_RUNTIME", "UNKNOWN"))
STAGES = frozenset(("SOURCE_FREE_PREFLIGHT", "SOURCE_BEARING_GENERATION"))
DISPATCH = frozenset(("DENIED_BEFORE_EXECUTION", "STARTED", "UNKNOWN"))
# An operator-supplied metadata label is not an independently verified receipt.
EVIDENCE = frozenset(("HISTORICAL_REPORT", "TOOL_RESULT_METADATA"))
ROTATABLE_PROVIDER_CODES = frozenset((401, 402, 403, 503, 504))


def classify_gemini_attempt(observation: dict[str, Any]) -> dict[str, Any]:
    """Classify one attempt without executing it or claiming an access grant.

    A provider HTTP 403 can justify selecting another *already configured*
    credential only during an authorized source-free preflight. An upstream
    executor denying dispatch, even with a 403-like error, is different and
    must NEVER authorize an API-key rotation or an alternate tool path.
    """
    fields = {"origin", "stage", "dispatch", "providerHttpStatus", "evidence"}
    if not isinstance(observation, dict) or set(observation) != fields:
        raise ValueError("expected only canonical, nonsecret attempt metadata")
    origin = observation["origin"]
    stage = observation["stage"]
    dispatch = observation["dispatch"]
    status = observation["providerHttpStatus"]
    evidence = observation["evidence"]
    if origin not in ORIGINS or stage not in STAGES or dispatch not in DISPATCH or evidence not in EVIDENCE:
        raise ValueError("invalid boundary enum")
    if status is not None and (type(status) is not int or not 400 <= status <= 599):
        raise ValueError("provider failure requires a 4xx/5xx HTTP status")
    if origin == "HOST_OR_CONNECTOR":
        if dispatch != "DENIED_BEFORE_EXECUTION" or status is not None:
            raise ValueError("upstream denial cannot include provider HTTP")
        outcome = "BLOCKED_EXTERNAL"
        safe_next = "REQUEST_APPROVED_EXECUTION_REVIEW"
        request_sent = False
        rotation = False
    elif origin == "GEMINI_PROVIDER":
        if dispatch != "STARTED" or status is None:
            raise ValueError("provider HTTP requires a dispatched request")
        request_sent = True
        rotation = stage == "SOURCE_FREE_PREFLIGHT" and status in ROTATABLE_PROVIDER_CODES
        if stage == "SOURCE_BEARING_GENERATION":
            outcome = "SOURCE_BEARING_RESPONSE_REQUIRES_RECONCILIATION"
            safe_next = "RECONCILE_ORIGINAL_REQUEST"
        elif status == 429:
            outcome = "PROVIDER_QUOTA_STOP"
            safe_next = "RESPECT_QUOTA_AND_WAIT_FOR_SEPARATE_AUTHORIZATION"
        elif rotation:
            outcome = "PROVIDER_SOURCE_FREE_KEY_ROTATION_ELIGIBLE"
            safe_next = "EXISTING_SHARED_CLIENT_ONLY_IF_OPERATION_ALREADY_AUTHORIZED"
        else:
            outcome = "PROVIDER_RESPONSE_NOT_ELIGIBLE_FOR_ROTATION"
            safe_next = "STOP_AND_RECONCILE"
    elif origin == "LOCAL_RUNTIME":
        if dispatch != "STARTED" or status is not None:
            raise ValueError("local failure cannot claim provider HTTP")
        outcome = "LOCAL_EXECUTION_FAILURE"
        safe_next = "REPAIR_LOCAL_ENVIRONMENT_WITHOUT_PROVIDER_REPLAY"
        # A local failure after the executor started can occur *after*
        # provider dispatch; do not label its sending state as definitely false.
        request_sent = True
        rotation = False
    else:
        if dispatch != "UNKNOWN" or status is not None:
            raise ValueError("uncertain execution cannot claim provider response")
        outcome = "UNVERIFIED_EXECUTION_STATE"
        safe_next = "PRESERVE_EVIDENCE_AND_STOP"
        request_sent = False
        rotation = False
    return {
        "status": outcome,
        "failureOrigin": origin,
        "stage": stage,
        "evidence": evidence,
        "dispatchIndependentlyVerified": False,
        "providerResponseClaimed": origin == "GEMINI_PROVIDER",
        "providerResponseIndependentlyVerified": False,
        "providerRequestMayHaveBeenSent": request_sent or origin == "UNKNOWN",
        "providerHttpStatus": status if origin == "GEMINI_PROVIDER" else None,
        "keyRotationEligibleWithinExistingAuthorizedPreflight": rotation,
        "safeNextAction": safe_next,
        "authorizesNewExecution": False,
        "authorizesToolRerouting": False,
        "allowsSourceReplay": False,
        "unblocksExistingDeniedOperation": False,
        "publicationAuthorized": False,
    }

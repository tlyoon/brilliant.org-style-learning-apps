"""BSA288: capacity-aware admission without synthetic daily Codex quotas.

Owner scheduler serializes calls under its Windows lock; this module is pure.
Do not preflight the provider with a chargeable request. Only real response
errors establish provider capacity status, and no unknown requests are replayed.
Provider CLI usage tokens are not invoice-equivalent USD billing evidence.
"""
from __future__ import annotations

from datetime import datetime
import math
import os
import re
from typing import Any

_MIN_SPACING_SECONDS=120
_MAX_COOLDOWN_SECONDS=12*3600
_PROVIDER_ERROR_MARKERS={
    "BILLING_REQUIRED":(
        r"(?i)\binsufficient_quota\b",
        r"(?i)\b(?:billing|credits?)\s+(?:limit|exhausted|disabled|required)\b",
        r"(?i)\bpayment_required\b",
    ),
    "AUTHORIZATION_DENIED":(
        r"(?i)\bunauthorized\s*[:=]?\s*401\b",
        r"(?i)\b(?:invalid_api_key|authentication_failed|401\s+unauthorized)\b",
    ),
    "PROVIDER_RATE_LIMIT":(
        r"(?i)\b(?:rate_limit_exceeded|rate.?limit(?:ed)?\s+(?:requests?|exceeded)|too many requests)\b",
        r"(?i)\b(?:http\s*429|429\s+too\s+many\s+requests)\b",
        r"(?i)\b(?:usage_limit_reached|quota_exceeded)\b",
    ),
    "PROVIDER_TEMPORARY_UNAVAILABLE":(
        r"(?i)\b(?:http\s*50[234]|(?:502|503|504)\s+(?:bad gateway|service unavailable|gateway timeout))\b",
        r"(?i)\b(?:server_error|provider_unavailable|upstream timeout|connection reset)\b",
    ),
}

def classify_provider_result(exit_code:int, log_excerpt:str)->str:
    if type(exit_code) is not int:
        raise ValueError("BSA288_INVALID_CODEX_EXIT_STATUS")
    if exit_code==0:
        return "AVAILABLE_LAST_OBSERVED"
    excerpt=log_excerpt[-12000:]
    for family,markers in _PROVIDER_ERROR_MARKERS.items():
        if any(re.search(pattern,excerpt) for pattern in markers):
            return family
    return "NONPROVIDER_OR_UNKNOWN_FAILURE"


def observed_cli_tokens(log_excerpt:str)->int|None:
    """Read only terminal Codex CLI 'tokens used' footer, never invent cost."""
    matches=re.findall(r"(?im)^tokens used\s*\r?\n\s*([0-9][0-9,]*)\s*$",
                       log_excerpt[-15000:])
    if not matches:
        return None
    value=int(matches[-1].replace(",",""))
    return value if value<=100_000_000 else None


def _daily_counter(state:dict[str,Any], now_epoch:float)->None:
    today=datetime.fromtimestamp(now_epoch).strftime("%Y-%m-%d")
    if state.get("codexDay")!=today:
        state["codexDay"]=today
        state["codexCount"]=0


def _optional_cost_limit(raw:str|None)->float|None:
    if raw is None or not raw.strip():
        return None
    try:
        value=float(raw)
    except ValueError as exc:
        raise ValueError("BSA288_INVALID_EXPLICIT_COST_LIMIT") from exc
    if not math.isfinite(value) or value<0:
        raise ValueError("BSA288_INVALID_EXPLICIT_COST_LIMIT")
    return value


def admission_decision(
    state:dict[str,Any], *, now_epoch:float,
    explicit_max_usd_per_day:str|None=None,
)->dict[str,Any]:
    """No artificial call/day gate; preserve real provider and spending limits."""
    _daily_counter(state,now_epoch)
    cap=_optional_cost_limit(explicit_max_usd_per_day)
    gate=state.get("codexProviderGate")
    if not isinstance(gate,dict):
        gate={}
    if cap is not None:
        # Codex CLI's usage footer is token-only, not an authenticated price.
        # Until authoritative priced usage exists, fail closed rather than
        # guess whether a user-defined USD spending ceiling was crossed.
        return {"allowed":False,"status":"BSA288_EXPLICIT_COST_CAP_UNMETERED_STOP",
                "reason":"USD cost cannot be established from Codex CLI token footer"}
    until=float(gate.get("blockedUntilEpoch",0) or 0)
    if not math.isfinite(until):
        return {"allowed":False,"status":"BSA288_PERSISTED_PROVIDER_GATE_UNTRUSTED"}
    if until>now_epoch:
        return {"allowed":False,"status":"BSA288_OBSERVED_PROVIDER_BACKOFF",
                "reason":str(gate.get("lastClass","provider failure")),
                "nextRetryEpoch":until}
    last=float(gate.get("lastInvocationEpoch",0) or 0)
    if not math.isfinite(last):
        return {"allowed":False,"status":"BSA288_PERSISTED_PROVIDER_GATE_UNTRUSTED"}
    if gate.get("lastClass")=="IN_FLIGHT_UNCONFIRMED":
        return {"allowed":False,"status":"BSA288_UNCERTAIN_CODEX_REQUEST_QUARANTINED",
                "reason":"An earlier Codex request has no confirmed outcome; do not replay it"}
    if last>now_epoch+60:
        return {"allowed":False,"status":"BSA288_PERSISTED_CLOCK_SAFETY_STOP"}
    if last>0 and now_epoch-last<_MIN_SPACING_SECONDS:
        return {"allowed":False,"status":"BSA288_MODEL_INVOCATION_SPACING",
                "nextRetryEpoch":last+_MIN_SPACING_SECONDS}
    return {"allowed":True,"status":"BSA288_REAL_PROVIDER_ELIGIBLE",
            "legacyDailyAttemptsObserved":int(state.get("codexCount",0)),
            "costUsd":"NOT_REPORTED_BY_PROVIDER"}


def record_invocation_start(state:dict[str,Any],*,now_epoch:float)->None:
    _daily_counter(state,now_epoch)
    gate=state.setdefault("codexProviderGate",{})
    if not isinstance(gate,dict):
        raise ValueError("BSA288_UNTRUSTED_PROVIDER_GATE")
    gate["lastInvocationEpoch"]=now_epoch
    gate["lastClass"]="IN_FLIGHT_UNCONFIRMED"
    state["codexCount"]=int(state.get("codexCount",0))+1


def record_invocation_outcome(
    state:dict[str,Any],*,now_epoch:float,exit_code:int,log_excerpt:str,
)->dict[str,Any]:
    classification=classify_provider_result(exit_code,log_excerpt)
    gate=state.setdefault("codexProviderGate",{})
    if not isinstance(gate,dict):
        raise ValueError("BSA288_UNTRUSTED_PROVIDER_GATE")
    prev_class=gate.get("lastFailureClass")
    failures=int(gate.get("consecutiveFailures",0) or 0)+1 if (
        classification!="AVAILABLE_LAST_OBSERVED" and
        classification==prev_class) else 1
    gate["lastClass"]=classification
    gate["lastObservedAtEpoch"]=now_epoch
    tokens=observed_cli_tokens(log_excerpt)
    if tokens is not None:
        gate["lastReportedTokens"]=tokens
        gate["totalReportedTokens"]=int(gate.get("totalReportedTokens",0))+tokens
    gate["usdCost"]="UNAVAILABLE_FROM_CLI"
    if classification=="AVAILABLE_LAST_OBSERVED":
        gate["consecutiveFailures"]=0
        gate["lastFailureClass"]=None
        gate["blockedUntilEpoch"]=0
    else:
        gate["consecutiveFailures"]=min(failures,30)
        gate["lastFailureClass"]=classification
        initial={
            "BILLING_REQUIRED":24*3600,
            "AUTHORIZATION_DENIED":12*3600,
            "PROVIDER_RATE_LIMIT":15*60,
            "PROVIDER_TEMPORARY_UNAVAILABLE":5*60,
            "NONPROVIDER_OR_UNKNOWN_FAILURE":5*60,
        }[classification]
        interval=min(_MAX_COOLDOWN_SECONDS,initial*2**min(failures-1,5))
        # When the real provider gives a Retry-After header, honor it
        # instead of blindly issuing another request on the next task tick.
        if classification=="PROVIDER_RATE_LIMIT":
            hints=re.findall(
                r"(?im)^retry-after\s*:\s*([0-9]{1,6})\s*(?:seconds?)?\s*$",
                log_excerpt[-12000:])
            if hints:
                interval=max(interval,min(24*3600,int(hints[-1])))
        # Billing exhaustion is not fixable by high-frequency retry; recheck
        # after at least a day, unless code is explicitly reconfigured.
        if classification=="BILLING_REQUIRED":
            interval=max(interval,24*3600)
        gate["blockedUntilEpoch"]=now_epoch+interval
    # Small, bounded, privacy-safe provider telemetry, not an academic receipt.
    recent=state.setdefault("codexInvocationHistory",[])
    if not isinstance(recent,list):
        raise ValueError("BSA288_UNTRUSTED_INVOCATION_HISTORY")
    recent.append({"atEpoch":now_epoch,"exitCode":exit_code,
                   "providerClass":classification,"tokensReported":tokens,
                   "usdCost":None})
    del recent[:-24]
    return {"providerClass":classification,
            "nextRetryEpoch":gate.get("blockedUntilEpoch",0),
            "tokensReported":tokens,"usdCost":None}

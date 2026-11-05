"""Typed, bounded, source-free error classification for activity repair.

Records diagnostic CATEGORIES only; never records the provider exception text,
prompt, response, source excerpt, credential or source PDF location.
"""
from __future__ import annotations

from app_generator.errors import ResponseContractError

KINDS = frozenset((
    "STABLE_FIELD", "STABLE_MISCONCEPTIONS", "STABLE_PREREQUISITE",
    "STABLE_INTERNAL_IDS", "INTERACTION_SOLUTION", "SCHEMA_VALIDATION",
    "PLAN_CONTRACT", "RESPONSE_SHAPE", "UNKNOWN_CONTRACT",
))


class StableRepairContractError(ValueError):
    def __init__(self, category: str, field: str) -> None:
        if category not in KINDS or not field or len(field) > 32:
            raise ValueError("unknown stable repair contract category")
        self.category = category
        self.field = field
        super().__init__(f"Repair attempted to change stable {field}")


class InteractionSolutionError(ResponseContractError):
    category = "INTERACTION_SOLUTION"


def classify_repair_failure(exc: Exception) -> dict[str, str]:
    if isinstance(exc, StableRepairContractError):
        return {"category": exc.category, "field": exc.field}
    if isinstance(exc, InteractionSolutionError):
        return {"category": exc.category, "field": "interaction"}
    if isinstance(exc, ResponseContractError):
        message = str(exc)
        if "violates schema-1.1" in message:
            return {"category": "SCHEMA_VALIDATION", "field": "activity"}
        if ("changed its planned" in message or "must omit interactionMode" in message):
            return {"category": "PLAN_CONTRACT", "field": "activity"}
        if ("must return one complete activity object" in message or
                "BEGIN_JSON" in message or "JSON" in message):
            return {"category": "RESPONSE_SHAPE", "field": "response"}
    return {"category": "UNKNOWN_CONTRACT", "field": "unspecified"}

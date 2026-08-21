"""Dynamic model discovery, ranking, and fallback classification."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable

from app_generator.errors import UiContractError


@dataclass(frozen=True)
class ModelOption:
    label: str
    description: str = ""
    selected: bool = False
    recommended: bool = False
    disabled: bool = False
    ui_index: int = 0


class ModelFailure(StrEnum):
    UNAVAILABLE = "MODEL_UNAVAILABLE"
    ENTITLEMENT = "MODEL_ENTITLEMENT_ERROR"
    QUOTA = "MODEL_QUOTA_EXHAUSTED"
    RATE_LIMIT = "MODEL_RATE_LIMITED"
    CAPACITY = "MODEL_CAPACITY_ERROR"
    OUTPUT_TRUNCATED = "OUTPUT_TRUNCATED"
    CONTEXT_LIMIT = "CONTEXT_LIMIT"
    RESPONSE_SIZE = "RESPONSE_SIZE_LIMIT"
    UNKNOWN = "UNKNOWN_MODEL_ERROR"

    @property
    def permits_model_fallback(self) -> bool:
        return self in {
            self.UNAVAILABLE, self.ENTITLEMENT, self.QUOTA, self.RATE_LIMIT, self.CAPACITY,
        }


ERROR_PATTERNS: tuple[tuple[ModelFailure, re.Pattern[str]], ...] = (
    (ModelFailure.OUTPUT_TRUNCATED, re.compile(r"truncat|incomplete response", re.I)),
    (ModelFailure.CONTEXT_LIMIT, re.compile(r"context (?:window|limit)|too much context", re.I)),
    (ModelFailure.RESPONSE_SIZE, re.compile(r"response (?:size|length)|output limit", re.I)),
    (ModelFailure.QUOTA, re.compile(r"quota|usage limit", re.I)),
    (ModelFailure.RATE_LIMIT, re.compile(r"rate limit|too many requests|try again later", re.I)),
    (ModelFailure.ENTITLEMENT, re.compile(r"upgrade|not available for your (?:plan|account)|entitlement", re.I)),
    (ModelFailure.CAPACITY, re.compile(r"capacity|overloaded|temporarily busy", re.I)),
    (ModelFailure.UNAVAILABLE, re.compile(r"model.*unavailable|could not use.*model", re.I)),
)


def classify_model_failure(message: str) -> ModelFailure:
    for failure, pattern in ERROR_PATTERNS:
        if pattern.search(message):
            return failure
    return ModelFailure.UNKNOWN


def rank_models(
    options: Iterable[ModelOption],
    preference_patterns: Iterable[str],
    *,
    allow_unknown_fallback: bool,
) -> list[ModelOption]:
    patterns = [re.compile(pattern, re.I) for pattern in preference_patterns]
    candidates = [option for option in options if not option.disabled and option.label.strip()]
    if not candidates:
        raise UiContractError("Gemini model selector exposed no enabled models")

    ranked: list[tuple[tuple[int, int, int], ModelOption]] = []
    unknown: list[ModelOption] = []
    for option in candidates:
        text = f"{option.label} {option.description}"
        match_index = next((index for index, pattern in enumerate(patterns) if pattern.search(text)), None)
        if match_index is None:
            unknown.append(option)
            continue
        ranked.append(((match_index, 0 if option.recommended else 1, option.ui_index), option))
    ranked.sort(key=lambda item: item[0])
    ordered = [option for _, option in ranked]
    if allow_unknown_fallback:
        unknown.sort(key=lambda option: (0 if option.selected or option.recommended else 1, option.ui_index))
        ordered.extend(unknown)
    if not ordered:
        discovered = ", ".join(option.label for option in candidates)
        raise UiContractError(f"No discovered model matched the configured policy: {discovered}")
    return ordered

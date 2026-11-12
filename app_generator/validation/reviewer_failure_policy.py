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
_UNCAPTURED_ERRORS = (
    UiContractError, ResponseContractError, TransientGeminiError,
    TimeoutError, ConnectionError,
)
UNCAPTURED_TRANSPORT_ERROR_CODES = frozenset(cls.__name__
                                              for cls in _UNCAPTURED_ERRORS)


def is_uncaptured_reviewer_transport_error(exc: BaseException) -> bool:
    """Only count failures before a usable answer was returned by ask()."""
    return isinstance(exc, _UNCAPTURED_ERRORS)
